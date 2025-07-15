// Hardcodé temporairement pour forcer la bonne URL
const API_BASE_URL = 'http://localhost:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    
    // Récupérer le token depuis le localStorage côté client
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('sovera-token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const requestHeaders = new Headers(options.headers as Record<string, string>);
    
    // Ajouter Content-Type JSON seulement si pas déjà défini et pas FormData
    if (!requestHeaders.has('Content-Type') && !(options.body instanceof FormData)) {
      requestHeaders.set('Content-Type', 'application/json');
    }

    if (this.token) {
      requestHeaders.set('Authorization', `Bearer ${this.token}`);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: requestHeaders,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let errorMessage = `HTTP error! status: ${response.status}`;
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((err: any) => err.msg || err.detail).join(', ');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          }
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('API Error:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'An error occurred' 
      };
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('sovera-token', token);
      } else {
        localStorage.removeItem('sovera-token');
      }
    }
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string }>> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    return this.request('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
  }

  async register(email: string, password: string): Promise<ApiResponse<any>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    return this.request('/auth/me');
  }

  // Projects endpoints
  async getProjects(): Promise<ApiResponse<any[]>> {
    return this.request('/projects/');
  }

  async createProject(name: string, description?: string): Promise<ApiResponse<any>> {
    return this.request('/projects/', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async getProject(id: number): Promise<ApiResponse<any>> {
    return this.request(`/projects/${id}`);
  }

  async updateProject(id: number, data: any): Promise<ApiResponse<any>> {
    return this.request(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: number): Promise<ApiResponse<any>> {
    return this.request(`/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // Items endpoints
  async getItems(projectId: number, params?: {
    offset?: number;
    limit?: number;
    search?: string;
    sort_by?: string;
    order?: string;
  }): Promise<ApiResponse<any[]>> {
    const searchParams = new URLSearchParams();
    searchParams.append('project_id', projectId.toString());
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    return this.request(`/items/?${searchParams.toString()}`);
  }

  async createItem(projectId: number, label: string, content: string): Promise<ApiResponse<any>> {
    return this.request(`/items/?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify({ label, content }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async updateItem(projectId: number, itemId: number, label?: string, content?: string): Promise<ApiResponse<any>> {
    const updateData: any = {};
    if (label !== undefined) updateData.label = label;
    if (content !== undefined) updateData.content = content;

    return this.request(`/items/${itemId}?project_id=${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteItem(projectId: number, itemId: number): Promise<ApiResponse<any>> {
    return this.request(`/items/${itemId}?project_id=${projectId}`, {
      method: 'DELETE',
    });
  }

  // Files endpoints
  async uploadFile(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/files/upload/', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    });
  }

  async getFiles(): Promise<ApiResponse<string[]>> {
    return this.request('/files/files/');
  }

  async getFileUrl(filename: string): Promise<ApiResponse<{ url: string }>> {
    return this.request(`/files/file/${filename}`);
  }

  async deleteFile(filename: string): Promise<ApiResponse<any>> {
    return this.request(`/files/file/${filename}`, {
      method: 'DELETE',
    });
  }

  // Monitoring endpoints
  async getSystemInfo(): Promise<ApiResponse<any>> {
    return this.request('/system/info');
  }

  async pingHosts(): Promise<ApiResponse<any>> {
    return this.request('/system/ping');
  }

  async getSystemLogs(): Promise<ApiResponse<{ logs: string[] }>> {
    return this.request('/system/logs');
  }

  async createBackup(): Promise<ApiResponse<any>> {
    return this.request('/system/backup', {
      method: 'POST',
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;