/**
 * Enhanced API client for Sovera with RBAC and new features
 */

import { 
  User, 
  Project, 
  ProjectCreate, 
  ProjectUpdate,
  ProjectMembership,
  ProjectInvitation,
  MembershipInvite,
  UserMembership,
  TableSchema,
  TableInfo,
  TableRow,
  FileInfo,
  FileUploadRequest,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  DashboardStats,
  ActivityItem,
  ApiError
} from './types';

export class ApiClient {
  private baseUrl: string;
  private authToken?: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = undefined;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.authToken}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const error: ApiError = {
          detail: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          status_code: response.status
        };
        throw error;
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }
      
      return response.text() as unknown as T;
    } catch (error) {
      if (error instanceof Error && 'status_code' in error) {
        throw error;
      }
      throw {
        detail: error instanceof Error ? error.message : 'Network error',
        status_code: 0
      } as ApiError;
    }
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AuthTokens> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    return this.request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type to let browser set it for FormData
    });
  }

  async register(userData: RegisterRequest): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Projects endpoints
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/projects/');
  }

  async getProject(id: number): Promise<Project> {
    return this.request<Project>(`/projects/${id}`);
  }

  async createProject(project: ProjectCreate): Promise<Project> {
    return this.request<Project>('/projects/', {
      method: 'POST',
      body: JSON.stringify(project),
    });
  }

  async updateProject(id: number, project: ProjectUpdate): Promise<Project> {
    return this.request<Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(project),
    });
  }

  async deleteProject(id: number): Promise<void> {
    return this.request<void>(`/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // Members endpoints
  async getProjectMembers(projectId: number): Promise<ProjectMembership[]> {
    return this.request<ProjectMembership[]>(`/projects/${projectId}/members`);
  }

  async inviteUserToProject(projectId: number, invitation: Omit<MembershipInvite, 'project_id'>): Promise<ProjectMembership> {
    return this.request<ProjectMembership>(`/projects/${projectId}/members/invite`, {
      method: 'POST',
      body: JSON.stringify({ ...invitation, project_id: projectId }),
    });
  }

  async updateProjectMember(projectId: number, membershipId: number, updates: { role?: string; status?: string }): Promise<ProjectMembership> {
    return this.request<ProjectMembership>(`/projects/${projectId}/members/${membershipId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async removeProjectMember(projectId: number, membershipId: number): Promise<void> {
    return this.request<void>(`/projects/${projectId}/members/${membershipId}`, {
      method: 'DELETE',
    });
  }

  async getUserInvitations(): Promise<ProjectInvitation[]> {
    return this.request<ProjectInvitation[]>('/invitations');
  }

  async acceptInvitation(invitationId: number): Promise<void> {
    return this.request<void>(`/invitations/${invitationId}/accept`, {
      method: 'POST',
    });
  }

  async rejectInvitation(invitationId: number): Promise<void> {
    return this.request<void>(`/invitations/${invitationId}/reject`, {
      method: 'POST',
    });
  }

  async getUserMembership(projectId: number): Promise<UserMembership> {
    return this.request<UserMembership>(`/projects/${projectId}/members/me`);
  }

  // Tables endpoints
  async getTables(projectId: number): Promise<TableInfo[]> {
    return this.request<TableInfo[]>(`/projects/${projectId}/tables/`);
  }

  async createTable(projectId: number, schema: TableSchema): Promise<any> {
    return this.request<any>(`/projects/${projectId}/tables/`, {
      method: 'POST',
      body: JSON.stringify(schema),
    });
  }

  async getTableSchema(projectId: number, tableName: string): Promise<any> {
    return this.request<any>(`/projects/${projectId}/tables/${tableName}/schema`);
  }

  async dropTable(projectId: number, tableName: string): Promise<void> {
    return this.request<void>(`/projects/${projectId}/tables/${tableName}`, {
      method: 'DELETE',
    });
  }

  // Table rows endpoints
  async getTableRows(projectId: number, tableName: string, params?: {
    limit?: number;
    offset?: number;
  }): Promise<TableRow[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    
    const query = searchParams.toString();
    const endpoint = `/projects/${projectId}/tables/${tableName}/rows${query ? `?${query}` : ''}`;
    
    return this.request<TableRow[]>(endpoint);
  }

  async insertTableRow(projectId: number, tableName: string, data: Record<string, any>): Promise<{ data: TableRow }> {
    return this.request<{ data: TableRow }>(`/projects/${projectId}/tables/${tableName}/rows`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTableRow(projectId: number, tableName: string, rowId: number, data: Record<string, any>): Promise<TableRow> {
    return this.request<TableRow>(`/projects/${projectId}/tables/${tableName}/rows/${rowId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTableRow(projectId: number, tableName: string, rowId: number): Promise<void> {
    return this.request<void>(`/projects/${projectId}/tables/${tableName}/rows/${rowId}`, {
      method: 'DELETE',
    });
  }

  // Files endpoints
  async getFiles(projectId: number): Promise<FileInfo[]> {
    return this.request<FileInfo[]>(`/projects/${projectId}/files/`);
  }

  async uploadFile(projectId: number, file: File, path?: string): Promise<FileInfo> {
    const formData = new FormData();
    formData.append('file', file);
    if (path) formData.append('path', path);

    return this.request<FileInfo>(`/projects/${projectId}/files/upload`, {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type to let browser set it for FormData
    });
  }

  async deleteFile(projectId: number, filename: string): Promise<void> {
    return this.request<void>(`/projects/${projectId}/files/${filename}`, {
      method: 'DELETE',
    });
  }

  async getFileDownloadUrl(projectId: number, filename: string): Promise<string> {
    return `${this.baseUrl}/projects/${projectId}/files/${filename}`;
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  async getRecentActivity(): Promise<ActivityItem[]> {
    return this.request<ActivityItem[]>('/dashboard/activity');
  }

  // WebSocket connection
  createWebSocketConnection(projectId: number, tableName: string): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/projects/${projectId}/tables/${tableName}`);
    return ws;
  }
}

// Global API client instance
export const apiClient = new ApiClient();

// Helper function to handle API errors
export function handleApiError(error: ApiError): string {
  switch (error.status_code) {
    case 401:
      return 'Authentication required. Please log in.';
    case 403:
      return 'Access denied. You do not have permission to perform this action.';
    case 404:
      return 'Resource not found.';
    case 409:
      return 'Conflict. The resource already exists.';
    case 422:
      return 'Validation error. Please check your input.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return error.detail || 'An unexpected error occurred.';
  }
}

// Helper function to get auth token from cookies
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'auth_token') {
      return decodeURIComponent(value);
    }
  }
  return null;
}

// Helper function to set auth token as cookie
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  
  document.cookie = `auth_token=${encodeURIComponent(token)}; path=/; max-age=86400; secure; samesite=strict`;
  apiClient.setAuthToken(token);
}

// Helper function to clear auth token
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  
  document.cookie = 'auth_token=; path=/; max-age=0';
  apiClient.clearAuthToken();
}