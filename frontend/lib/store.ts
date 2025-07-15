/**
 * Zustand store for Sovera application state management
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { 
  User, 
  Project, 
  ProjectMembership, 
  UserMembership, 
  TableInfo, 
  TableRow, 
  FileInfo,
  Toast,
  LoadingState,
  TableState,
  ProjectState
} from './types';
import { apiClient, handleApiError } from './api-client';

// Auth Store
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ loading: true, error: null });
        try {
          const tokens = await apiClient.login({ username: email, password });
          apiClient.setAuthToken(tokens.access_token);
          
          // Get user info
          const user = await apiClient.getCurrentUser();
          set({ user, isAuthenticated: true, loading: false });
          
          // Store token in cookie
          if (typeof window !== 'undefined') {
            document.cookie = `auth_token=${tokens.access_token}; path=/; max-age=86400; secure; samesite=strict`;
          }
        } catch (error: any) {
          set({ error: handleApiError(error), loading: false });
          throw error;
        }
      },

      register: async (email: string, password: string) => {
        set({ loading: true, error: null });
        try {
          const user = await apiClient.register({ email, password });
          set({ user, loading: false });
          
          // Auto-login after registration
          await get().login(email, password);
        } catch (error: any) {
          set({ error: handleApiError(error), loading: false });
          throw error;
        }
      },

      logout: () => {
        apiClient.clearAuthToken();
        if (typeof window !== 'undefined') {
          document.cookie = 'auth_token=; path=/; max-age=0';
        }
        set({ user: null, isAuthenticated: false, error: null });
      },

      checkAuth: async () => {
        // Check if token exists in cookie
        if (typeof window !== 'undefined') {
          const cookies = document.cookie.split(';');
          const authCookie = cookies.find(cookie => cookie.trim().startsWith('auth_token='));
          
          if (authCookie) {
            const token = authCookie.split('=')[1];
            apiClient.setAuthToken(token);
            
            try {
              const user = await apiClient.getCurrentUser();
              set({ user, isAuthenticated: true });
            } catch (error) {
              // Token is invalid, clear it
              get().logout();
            }
          }
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Projects Store
interface ProjectsState extends ProjectState {
  members: ProjectMembership[];
  loadProjects: () => Promise<void>;
  loadProject: (id: number) => Promise<void>;
  createProject: (project: any) => Promise<Project>;
  updateProject: (id: number, project: any) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  loadMembers: (projectId: number) => Promise<void>;
  inviteMember: (projectId: number, invitation: any) => Promise<void>;
  removeMember: (projectId: number, membershipId: number) => Promise<void>;
  loadUserMembership: (projectId: number) => Promise<void>;
  setCurrentProject: (project: Project) => void;
  clearError: () => void;
}

export const useProjectsStore = create<ProjectsState>((set, get) => ({
  current_project: undefined,
  projects: [],
  members: [],
  membership: undefined,
  loading: false,
  error: undefined,

  loadProjects: async () => {
    set({ loading: true, error: undefined });
    try {
      const projects = await apiClient.getProjects();
      set({ projects, loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
    }
  },

  loadProject: async (id: number) => {
    set({ loading: true, error: undefined });
    try {
      const project = await apiClient.getProject(id);
      set({ current_project: project, loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
    }
  },

  createProject: async (project: any) => {
    set({ loading: true, error: undefined });
    try {
      const newProject = await apiClient.createProject(project);
      set(state => ({ 
        projects: [...state.projects, newProject], 
        loading: false 
      }));
      return newProject;
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  updateProject: async (id: number, project: any) => {
    set({ loading: true, error: undefined });
    try {
      const updatedProject = await apiClient.updateProject(id, project);
      set(state => ({
        projects: state.projects.map(p => p.id === id ? updatedProject : p),
        current_project: state.current_project?.id === id ? updatedProject : state.current_project,
        loading: false
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  deleteProject: async (id: number) => {
    set({ loading: true, error: undefined });
    try {
      await apiClient.deleteProject(id);
      set(state => ({
        projects: state.projects.filter(p => p.id !== id),
        current_project: state.current_project?.id === id ? undefined : state.current_project,
        loading: false
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  loadMembers: async (projectId: number) => {
    set({ loading: true, error: undefined });
    try {
      const members = await apiClient.getProjectMembers(projectId);
      set({ members, loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
    }
  },

  inviteMember: async (projectId: number, invitation: any) => {
    set({ loading: true, error: undefined });
    try {
      const newMember = await apiClient.inviteUserToProject(projectId, invitation);
      set(state => ({ 
        members: [...state.members, newMember], 
        loading: false 
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  removeMember: async (projectId: number, membershipId: number) => {
    set({ loading: true, error: undefined });
    try {
      await apiClient.removeProjectMember(projectId, membershipId);
      set(state => ({
        members: state.members.filter(m => m.id !== membershipId),
        loading: false
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  loadUserMembership: async (projectId: number) => {
    try {
      const membership = await apiClient.getUserMembership(projectId);
      set({ membership });
    } catch (error: any) {
      set({ error: handleApiError(error) });
    }
  },

  setCurrentProject: (project: Project) => {
    set({ current_project: project });
  },

  clearError: () => set({ error: undefined }),
}));

// Tables Store
interface TablesState {
  tables: TableInfo[];
  currentTable: TableState;
  loading: boolean;
  error?: string;
  loadTables: (projectId: number) => Promise<void>;
  createTable: (projectId: number, schema: any) => Promise<void>;
  dropTable: (projectId: number, tableName: string) => Promise<void>;
  loadTableData: (projectId: number, tableName: string, params?: { limit?: number; offset?: number }) => Promise<void>;
  insertRow: (projectId: number, tableName: string, data: any) => Promise<void>;
  updateRow: (projectId: number, tableName: string, rowId: number, data: any) => Promise<void>;
  deleteRow: (projectId: number, tableName: string, rowId: number) => Promise<void>;
  clearError: () => void;
}

export const useTablesStore = create<TablesState>((set, get) => ({
  tables: [],
  currentTable: {
    data: [],
    columns: [],
    loading: false,
    pagination: {
      page: 1,
      per_page: 10,
      total: 0,
      total_pages: 0,
    },
  },
  loading: false,
  error: undefined,

  loadTables: async (projectId: number) => {
    set({ loading: true, error: undefined });
    try {
      const tables = await apiClient.getTables(projectId);
      set({ tables, loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
    }
  },

  createTable: async (projectId: number, schema: any) => {
    set({ loading: true, error: undefined });
    try {
      await apiClient.createTable(projectId, schema);
      // Reload tables after creation
      await get().loadTables(projectId);
      set({ loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  dropTable: async (projectId: number, tableName: string) => {
    set({ loading: true, error: undefined });
    try {
      await apiClient.dropTable(projectId, tableName);
      // Reload tables after deletion
      await get().loadTables(projectId);
      set({ loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  loadTableData: async (projectId: number, tableName: string, params?: { limit?: number; offset?: number }) => {
    set(state => ({ 
      currentTable: { ...state.currentTable, loading: true, error: undefined } 
    }));
    
    try {
      const [data, schema] = await Promise.all([
        apiClient.getTableRows(projectId, tableName, params),
        apiClient.getTableSchema(projectId, tableName)
      ]);
      
      set(state => ({
        currentTable: {
          ...state.currentTable,
          data,
          columns: schema.columns || [],
          loading: false,
          pagination: {
            ...state.currentTable.pagination,
            page: Math.floor((params?.offset || 0) / (params?.limit || 10)) + 1,
            per_page: params?.limit || 10,
          },
        },
      }));
    } catch (error: any) {
      set(state => ({
        currentTable: { 
          ...state.currentTable, 
          loading: false, 
          error: handleApiError(error) 
        },
      }));
    }
  },

  insertRow: async (projectId: number, tableName: string, data: any) => {
    try {
      const result = await apiClient.insertTableRow(projectId, tableName, data);
      set(state => ({
        currentTable: {
          ...state.currentTable,
          data: [...state.currentTable.data, result.data],
        },
      }));
    } catch (error: any) {
      set(state => ({
        currentTable: { 
          ...state.currentTable, 
          error: handleApiError(error) 
        },
      }));
      throw error;
    }
  },

  updateRow: async (projectId: number, tableName: string, rowId: number, data: any) => {
    try {
      const updatedRow = await apiClient.updateTableRow(projectId, tableName, rowId, data);
      set(state => ({
        currentTable: {
          ...state.currentTable,
          data: state.currentTable.data.map(row => 
            row.id === rowId ? updatedRow : row
          ),
        },
      }));
    } catch (error: any) {
      set(state => ({
        currentTable: { 
          ...state.currentTable, 
          error: handleApiError(error) 
        },
      }));
      throw error;
    }
  },

  deleteRow: async (projectId: number, tableName: string, rowId: number) => {
    try {
      await apiClient.deleteTableRow(projectId, tableName, rowId);
      set(state => ({
        currentTable: {
          ...state.currentTable,
          data: state.currentTable.data.filter(row => row.id !== rowId),
        },
      }));
    } catch (error: any) {
      set(state => ({
        currentTable: { 
          ...state.currentTable, 
          error: handleApiError(error) 
        },
      }));
      throw error;
    }
  },

  clearError: () => set(state => ({ 
    error: undefined,
    currentTable: { ...state.currentTable, error: undefined }
  })),
}));

// Files Store
interface FilesState {
  files: FileInfo[];
  loading: boolean;
  error?: string;
  loadFiles: (projectId: number) => Promise<void>;
  uploadFile: (projectId: number, file: File, path?: string) => Promise<void>;
  deleteFile: (projectId: number, filename: string) => Promise<void>;
  clearError: () => void;
}

export const useFilesStore = create<FilesState>((set, get) => ({
  files: [],
  loading: false,
  error: undefined,

  loadFiles: async (projectId: number) => {
    set({ loading: true, error: undefined });
    try {
      const files = await apiClient.getFiles(projectId);
      set({ files, loading: false });
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
    }
  },

  uploadFile: async (projectId: number, file: File, path?: string) => {
    set({ loading: true, error: undefined });
    try {
      const newFile = await apiClient.uploadFile(projectId, file, path);
      set(state => ({ 
        files: [...state.files, newFile], 
        loading: false 
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  deleteFile: async (projectId: number, filename: string) => {
    set({ loading: true, error: undefined });
    try {
      await apiClient.deleteFile(projectId, filename);
      set(state => ({
        files: state.files.filter(f => f.filename !== filename),
        loading: false
      }));
    } catch (error: any) {
      set({ error: handleApiError(error), loading: false });
      throw error;
    }
  },

  clearError: () => set({ error: undefined }),
}));

// Toast Store
interface ToastState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { ...toast, id };
    
    set(state => ({ toasts: [...state.toasts, newToast] }));
    
    // Auto-remove toast after duration
    setTimeout(() => {
      set(state => ({ toasts: state.toasts.filter(t => t.id !== id) }));
    }, toast.duration || 5000);
  },

  removeToast: (id: string) => {
    set(state => ({ toasts: state.toasts.filter(t => t.id !== id) }));
  },

  clearToasts: () => set({ toasts: [] }),
}));