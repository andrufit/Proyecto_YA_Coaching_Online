const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export type ProfileData = {
  full_name: string;
  birth_date: string;
  sex: "female" | "male" | "other" | "prefer_not_to_say";
  height_cm: string;
  goal: "fat_loss" | "muscle_gain" | "maintenance" | "performance";
  training_level: "beginner" | "intermediate" | "advanced";
  medical_restrictions: string | null;
};

export type ClientProfile = ProfileData & {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
};

export type AssessmentData = {
  weight_kg: string;
  body_fat_percentage: string | null;
  waist_cm: string | null;
  hip_cm: string | null;
  chest_cm: string | null;
  notes: string | null;
};

export type BodyAssessment = AssessmentData & {
  id: number;
  client_profile_id: number;
  assessment_date: string;
  created_at: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  token: string,
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  const response = await fetch(
    `${API_URL}/api/v1/client-profile${path}`,
    {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(data === undefined
          ? {}
          : { "Content-Type": "application/json" }),
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    },
  );

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;

    try {
      const body = (await response.json()) as {
        detail?: string | { msg?: string }[];
      };

      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((item) => item.msg ?? "Dato inválido")
          .join(". ");
      }
    } catch {
      message = "No fue posible interpretar la respuesta del servidor.";
    }

    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export async function getProfile(
  token: string,
): Promise<ClientProfile | null> {
  try {
    return await request<ClientProfile>(token, "/me");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function saveProfile(
  token: string,
  data: ProfileData,
  exists: boolean,
): Promise<ClientProfile> {
  return request<ClientProfile>(
    token,
    exists ? "/me" : "",
    exists ? "PATCH" : "POST",
    data,
  );
}

export function getAssessments(
  token: string,
): Promise<BodyAssessment[]> {
  return request<BodyAssessment[]>(token, "/me/assessments");
}

export function addAssessment(
  token: string,
  data: AssessmentData,
): Promise<BodyAssessment> {
  return request<BodyAssessment>(
    token,
    "/me/assessments",
    "POST",
    data,
  );
}