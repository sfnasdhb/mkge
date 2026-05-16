export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "researcher" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user?: User;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}

export type DocumentStatus = "queued" | "parsing" | "extracting" | "verifying" | "done" | "failed";

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_size: number;
  status: DocumentStatus;
  error_message?: string;
  entity_count: number;
  relation_count: number;
  created_at: string;
  processed_at?: string;
}
