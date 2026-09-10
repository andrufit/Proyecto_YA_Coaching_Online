import type { User } from "../types/auth";
import type {
  BodyAssessment,
  ClientProfile,
} from "./clientProfile";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export class ManagementError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ManagementError";
    this.status = status;
  }
}

export type Assignment = {
  id: number;
  client_id: number;
  coach_id: number;
  created_at: string;
  updated_at: string;
};

async function request<T>(
  token: string,
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;

    try {
      const data = (await response.json()) as {
        detail?: string | { msg?: string }[];
      };

      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail
          .map((item) => item.msg ?? "Dato inválido")
          .join(". ");
      }
    } catch {
      message = "El servidor no devolvió una respuesta válida.";
    }

    if (response.status === 401) {
      message = "Tu sesión no es válida. Cierra sesión e ingresa nuevamente.";
    }

    throw new ManagementError(response.status, message);
  }

  return (await response.json()) as T;
}

// Recorre las páginas para que los selectores no omitan usuarios.
export async function getUsers(
  token: string,
  path: string,
): Promise<User[]> {
  const users: User[] = [];

  for (let offset = 0; ; offset += 100) {
    const page = await request<User[]>(
      token,
      `${path}?offset=${offset}&limit=100`,
    );

    users.push(...page);

    if (page.length < 100) return users;
  }
}

export function createCoach(
  token: string,
  email: string,
  password: string,
): Promise<User> {
  return request<User>(token, "/admin/coaches", "POST", {
    email,
    password,
  });
}

export async function getAssignment(
  token: string,
  clientId: number,
): Promise<Assignment | null> {
  try {
    return await request<Assignment>(
      token,
      `/admin/clients/${clientId}/coach`,
    );
  } catch (error) {
    if (error instanceof ManagementError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function saveAssignment(
  token: string,
  clientId: number,
  coachId: number,
): Promise<Assignment> {
  return request<Assignment>(
    token,
    `/admin/clients/${clientId}/coach`,
    "PUT",
    { coach_id: coachId },
  );
}

export async function getCoachProfile(
  token: string,
  clientId: number,
): Promise<ClientProfile> {
  return request<ClientProfile>(
    token,
    `/coach/clients/${clientId}/profile`,
  );
}

export function getCoachAssessments(
  token: string,
  clientId: number,
  offset = 0,
): Promise<BodyAssessment[]> {
  return request<BodyAssessment[]>(
    token,
    `/coach/clients/${clientId}/assessments?offset=${offset}&limit=20`,
  );
}