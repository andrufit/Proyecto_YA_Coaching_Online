import type {
  AccessToken,
  RegisterData,
  User,
} from "../types/auth";


const API_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";


type ValidationDetail = {
  msg?: string;
};


type ApiErrorBody = {
  detail?: string | ValidationDetail[];
};


async function getErrorMessage(
  response: Response,
): Promise<string> {
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
    return "No fue posible procesar la respuesta.";
  }

  return `Error HTTP ${response.status}`;
}


export async function registerUser(
  data: RegisterData,
): Promise<User> {
  const response = await fetch(
    `${API_URL}/api/v1/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (await response.json()) as User;
}


export async function loginUser(
  email: string,
  password: string,
): Promise<AccessToken> {
  const formData = new URLSearchParams();

  formData.set("username", email);
  formData.set("password", password);

  const response = await fetch(
    `${API_URL}/api/v1/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
      body: formData,
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (await response.json()) as AccessToken;
}


export async function getCurrentUser(
  accessToken: string,
): Promise<User> {
  const response = await fetch(
    `${API_URL}/api/v1/users/me`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (await response.json()) as User;
}