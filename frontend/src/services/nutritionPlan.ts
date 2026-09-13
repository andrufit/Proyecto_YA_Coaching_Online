export type NutritionFoodWrite = {
  position: number;
  name: string;
  quantity: string;
  notes: string | null;
};

export type NutritionMealWrite = {
  position: number;
  name: string;
  notes: string | null;
  foods: NutritionFoodWrite[];
};

export type NutritionPlanWrite = {
  title: string;
  instructions: string | null;
  meals: NutritionMealWrite[];
};

export type NutritionFoodRead = NutritionFoodWrite & {
  id: number;
};

export type NutritionMealRead = {
  id: number;
  position: number;
  name: string;
  notes: string | null;
  foods: NutritionFoodRead[];
};

export type NutritionPlanRead = {
  id: number;
  client_id: number;
  title: string;
  instructions: string | null;
  created_at: string;
  updated_at: string;
  meals: NutritionMealRead[];
};

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

type ValidationDetail = {
  msg?: string;
};

type ApiErrorBody = {
  detail?: string | ValidationDetail[];
};

export class NutritionPlanError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "NutritionPlanError";
    this.status = status;
  }
}

async function readError(response: Response): Promise<string> {
  if (response.status === 401) {
    return "Tu sesión venció. Inicia sesión nuevamente.";
  }

  try {
    const body = (await response.json()) as ApiErrorBody;

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => item.msg ?? "Dato inválido")
        .join(". ");
    }
  } catch {
    return "No fue posible procesar la respuesta del servidor.";
  }

  return `Error HTTP ${response.status}`;
}

export async function getNutritionPlan(
  token: string,
  clientId?: number,
): Promise<NutritionPlanRead | null> {
  const path =
    clientId === undefined
      ? "/api/v1/users/me/nutrition-plan"
      : `/api/v1/coach/clients/${clientId}/nutrition-plan`;

  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const message = await readError(response);

    const isMissingPlan =
      response.status === 404 &&
      (
        message === "Todavía no tienes un plan nutricional." ||
        message ===
          "El cliente todavía no tiene un plan nutricional."
      );

    if (isMissingPlan) {
      return null;
    }

    throw new NutritionPlanError(message, response.status);
  }

  return (await response.json()) as NutritionPlanRead;
}

export async function saveNutritionPlan(
  token: string,
  clientId: number,
  data: NutritionPlanWrite,
): Promise<NutritionPlanRead> {
  const response = await fetch(
    `${API_URL}/api/v1/coach/clients/${clientId}/nutrition-plan`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    throw new NutritionPlanError(
      await readError(response),
      response.status,
    );
  }

  return (await response.json()) as NutritionPlanRead;
}