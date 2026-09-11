export type TrainingExerciseWrite = {
  position: number;
  name: string;
  sets: number;
  repetitions: string;
  rest_seconds: number;
  notes: string | null;
};

export type TrainingDayWrite = {
  position: number;
  name: string;
  exercises: TrainingExerciseWrite[];
};

export type TrainingPlanWrite = {
  title: string;
  instructions: string | null;
  days: TrainingDayWrite[];
};

export type TrainingExerciseRead = TrainingExerciseWrite & {
  id: number;
};

export type TrainingDayRead = {
  id: number;
  position: number;
  name: string;
  exercises: TrainingExerciseRead[];
};

export type TrainingPlanRead = {
  id: number;
  client_id: number;
  title: string;
  instructions: string | null;
  created_at: string;
  updated_at: string;
  days: TrainingDayRead[];
};

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

type ErrorBody = {
  detail?: string | { msg?: string }[];
};

async function readError(response: Response): Promise<string> {
  if (response.status === 401) {
    return "Tu sesión venció. Cierra sesión e ingresa nuevamente.";
  }

  try {
    const body = (await response.json()) as ErrorBody;

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => item.msg || "Dato inválido")
        .join(". ");
    }
  } catch {
    return "No fue posible interpretar la respuesta del servidor.";
  }

  return `Error HTTP ${response.status}`;
}

export async function getTrainingPlan(
  token: string,
  clientId?: number,
): Promise<TrainingPlanRead | null> {
  const path =
    clientId === undefined
      ? "/users/me/training-plan"
      : `/coach/clients/${clientId}/training-plan`;

  const response = await fetch(`${API_URL}/api/v1${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const detail = await readError(response);

    // Solo interpretamos como plan vacío el mensaje específico.
    // Un 404 por falta de asignación debe mostrarse como error.
    const missingPlan =
      detail === "Todavía no tienes un plan de entrenamiento." ||
      detail ===
        "El cliente todavía no tiene un plan de entrenamiento.";

    if (response.status === 404 && missingPlan) {
      return null;
    }

    throw new Error(detail);
  }

  return (await response.json()) as TrainingPlanRead;
}

export async function saveTrainingPlan(
  token: string,
  clientId: number,
  data: TrainingPlanWrite,
): Promise<TrainingPlanRead> {
  const response = await fetch(
    `${API_URL}/api/v1/coach/clients/${clientId}/training-plan`,
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
    throw new Error(await readError(response));
  }

  return (await response.json()) as TrainingPlanRead;
}