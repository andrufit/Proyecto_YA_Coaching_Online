export type UserRole = "admin" | "coach" | "client";

export type User = {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type AccessToken = {
  access_token: string;
  token_type: "bearer";
};

export type RegisterData = {
  email: string;
  password: string;
};