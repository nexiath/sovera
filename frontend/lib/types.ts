/**
 * Type definitions for Sovera API
 */

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  slug: string;
  api_key: string;
  owner_id: number;
  created_at: string;
  db_name: string;
  bucket_name: string;
  max_items: number;
  storage_limit_mb: number;
  api_rate_limit: number;
  webhook_url?: string;
  is_public: boolean;
  auto_backup: boolean;
  backup_retention_days: number;
  provisioning_status: 'pending' | 'completed' | 'failed';
}

export interface ProjectCreate {
  name: string;
  description?: string;
  max_items?: number;
  storage_limit_mb?: number;
  api_rate_limit?: number;
  webhook_url?: string;
  is_public?: boolean;
  auto_backup?: boolean;
  backup_retention_days?: number;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  max_items?: number;
  storage_limit_mb?: number;
  api_rate_limit?: number;
  webhook_url?: string;
  is_public?: boolean;
  auto_backup?: boolean;
  backup_retention_days?: number;
}

export type ProjectRole = 'owner' | 'editor' | 'viewer';
export type InvitationStatus = 'pending' | 'accepted' | 'rejected' | 'expired';

export interface ProjectMembership {
  id: number;
  project_id: number;
  project_name: string;
  user_id: number;
  user_email: string;
  role: ProjectRole;
  status: InvitationStatus;
  invited_at: string;
  accepted_at?: string;
  inviter_email?: string;
}

export interface ProjectInvitation {
  id: number;
  project_id: number;
  project_name: string;
  project_description?: string;
  role: ProjectRole;
  invited_by_name?: string;
  invited_by_email: string;
  invited_at: string;
  message?: string;
  status: InvitationStatus;
}

export interface MembershipInvite {
  project_id: number;
  user_email: string;
  role: ProjectRole;
  message?: string;
}

export interface UserMembership {
  project_id: number;
  project_name?: string;
  role: ProjectRole;
  permissions: string[];
  is_owner: boolean;
}

export type ColumnType = 
  | 'INTEGER' | 'BIGINT' | 'SMALLINT' | 'DECIMAL' | 'NUMERIC' | 'REAL' | 'DOUBLE PRECISION'
  | 'TEXT' | 'VARCHAR' | 'CHAR'
  | 'TIMESTAMP' | 'TIMESTAMPTZ' | 'DATE' | 'TIME'
  | 'BOOLEAN'
  | 'JSON' | 'JSONB'
  | 'UUID';

export interface ColumnSchema {
  name: string;
  type: ColumnType;
  nullable: boolean;
  primary_key: boolean;
  unique: boolean;
  default?: string;
  length?: number;
}

export interface TableSchema {
  table_name: string;
  columns: ColumnSchema[];
}

export interface TableInfo {
  table_name: string;
  column_count: number;
  row_count?: number;
  created_at?: string;
  size_mb?: number;
}

export interface TableRow {
  [key: string]: any;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface FileInfo {
  id: number;
  filename: string;
  file_path: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
  download_url?: string;
}

export interface FileUploadRequest {
  file: File;
  path?: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string; // Actually email
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface WebSocketMessage {
  type: 'table_update' | 'table_insert' | 'table_delete';
  table_name: string;
  data: any;
  timestamp: string;
}

// Dashboard specific types
export interface DashboardStats {
  total_projects: number;
  total_tables: number;
  total_rows: number;
  storage_used_mb: number;
  api_calls_today: number;
  active_projects: number;
}

export interface ActivityItem {
  id: string;
  type: 'table_created' | 'data_inserted' | 'member_invited' | 'project_created';
  description: string;
  timestamp: string;
  project_id: number;
  project_name: string;
  user_email?: string;
}

// Form types
export interface TableFormData {
  table_name: string;
  columns: {
    name: string;
    type: ColumnType;
    nullable: boolean;
    primary_key: boolean;
    unique: boolean;
    default?: string;
    length?: number;
  }[];
}

export interface ProjectFormData extends ProjectCreate {}

export interface InviteMemberFormData {
  email: string;
  role: ProjectRole;
  message?: string;
}

// UI State types
export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface TableState {
  data: TableRow[];
  columns: ColumnSchema[];
  loading: boolean;
  error?: string;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

export interface ProjectState {
  current_project?: Project;
  projects: Project[];
  membership?: UserMembership;
  loading: boolean;
  error?: string;
}