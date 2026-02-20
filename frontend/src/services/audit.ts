import api from "@/lib/api";

export interface AuditLog {
  id: number;
  user_id: number | null;
  user_email: string | null;
  action: string;
  table_name: string;
  record_id: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  endpoint: string | null;
  method: string | null;
  description: string | null;
  created_at: string;
}

export interface AuditLogFilters {
  user_id?: number;
  table_name?: string;
  action?: string;
  record_id?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

export interface AuditLogResponse {
  items: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}

export const auditApi = {
  getAuditLogs: async (filters: AuditLogFilters = {}): Promise<AuditLogResponse> => {
    const params = new URLSearchParams();
    
    if (filters.user_id) params.append("user_id", filters.user_id.toString());
    if (filters.table_name) params.append("table_name", filters.table_name);
    if (filters.action) params.append("action", filters.action);
    if (filters.record_id) params.append("record_id", filters.record_id);
    if (filters.start_date) params.append("start_date", filters.start_date);
    if (filters.end_date) params.append("end_date", filters.end_date);
    if (filters.skip !== undefined) params.append("skip", filters.skip.toString());
    if (filters.limit !== undefined) params.append("limit", filters.limit.toString());

    const response = await api.get<AuditLogResponse>(`/audit/?${params.toString()}`);
    return response.data;
  },

  getAuditLogById: async (id: number): Promise<AuditLog> => {
    const response = await api.get<AuditLog>(`/audit/${id}`);
    return response.data;
  },

  getAuditedTables: async (): Promise<string[]> => {
    const response = await api.get<string[]>("/audit/tables/list");
    return response.data;
  },

  getAuditActions: async (): Promise<string[]> => {
    const response = await api.get<string[]>("/audit/actions/list");
    return response.data;
  },
};
