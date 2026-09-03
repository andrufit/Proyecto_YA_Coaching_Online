import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import "./App.css";

import {
  getCurrentUser,
  loginUser,
  registerUser,
} from "./services/auth";
import type { User } from "./types/auth";


type AuthMode = "login" | "register";

const TOKEN_KEY = "ya_access_token";


function App() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [accessToken, setAccessToken] = useState<
    string | null
  >(() => sessionStorage.getItem(TOKEN_KEY));

  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [isSessionLoading, setIsSessionLoading] =
    useState(Boolean(accessToken));

  useEffect(() => {
    if (!accessToken) {
      setUser(null);
      setIsSessionLoading(false);
      return;
    }

    let isActive = true;

    async function loadCurrentUser() {
      setIsSessionLoading(true);

      try {
        const currentUser =
          await getCurrentUser(accessToken as string);

        if (isActive) {
          setUser(currentUser);
        }
      } catch {
        if (isActive) {
          sessionStorage.removeItem(TOKEN_KEY);
          setAccessToken(null);
          setUser(null);
          setError(
            "Tu sesión venció. Inicia sesión nuevamente.",
          );
        }
      } finally {
        if (isActive) {
          setIsSessionLoading(false);
        }
      }
    }

    loadCurrentUser();

    return () => {
      isActive = false;
    };
  }, [accessToken]);

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setError("");
    setPassword("");
    setConfirmPassword("");
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");

    if (
      mode === "register" &&
      password !== confirmPassword
    ) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await registerUser({
          email,
          password,
        });
      }

      const token = await loginUser(
        email,
        password,
      );

      sessionStorage.setItem(
        TOKEN_KEY,
        token.access_token,
      );

      setAccessToken(token.access_token);
      setPassword("");
      setConfirmPassword("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Ocurrió un error inesperado.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY);
    setAccessToken(null);
    setUser(null);
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setError("");
    setMode("login");
  }

  if (isSessionLoading) {
    return (
      <main className="loading-screen">
        <div className="loader" />
        <p>Validando sesión segura...</p>
      </main>
    );
  }

  if (user) {
    return (
      <main className="dashboard-shell">
        <header className="dashboard-header">
          <div className="brand-inline">
            <span className="brand-mark">Y&A</span>

            <div>
              <strong>Y&A Coaching Online</strong>
              <span>Plataforma de seguimiento</span>
            </div>
          </div>

          <button
            className="logout-button"
            type="button"
            onClick={logout}
          >
            Cerrar sesión
          </button>
        </header>

        <section className="dashboard-content">
          <div className="welcome-copy">
            <span className="eyebrow">
              CUENTA AUTENTICADA
            </span>

            <h1>Bienvenido a tu espacio personal</h1>

            <p>
              Tu sesión está protegida y el frontend se
              encuentra conectado correctamente con la API.
            </p>
          </div>

          <article className="profile-card">
            <div className="profile-avatar">
              {user.email.charAt(0).toUpperCase()}
            </div>

            <div className="profile-heading">
              <span>Perfil activo</span>
              <h2>{user.email}</h2>
            </div>

            <dl className="profile-details">
              <div>
                <dt>Identificador</dt>
                <dd>#{user.id}</dd>
              </div>

              <div>
                <dt>Rol</dt>
                <dd>{user.role}</dd>
              </div>

              <div>
                <dt>Estado</dt>
                <dd className="active-status">
                  Activo
                </dd>
              </div>

              <div>
                <dt>Fecha de registro</dt>
                <dd>
                  {new Intl.DateTimeFormat(
                    "es-CO",
                    {
                      dateStyle: "long",
                    },
                  ).format(
                    new Date(user.created_at),
                  )}
                </dd>
              </div>
            </dl>
          </article>
        </section>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <section className="brand-panel">
        <div className="brand-content">
          <div className="brand-inline brand-light">
            <span className="brand-mark">Y&A</span>

            <div>
              <strong>Y&A Coaching Online</strong>
              <span>Entrenamiento y nutrición</span>
            </div>
          </div>

          <div className="brand-message">
            <span className="eyebrow eyebrow-light">
              TU PROGRESO, ORGANIZADO
            </span>

            <h1>
              Construye hábitos que puedas mantener.
            </h1>

            <p>
              Una plataforma creada para acompañar tu
              entrenamiento, nutrición y evolución.
            </p>
          </div>

          <div className="security-note">
            <span className="security-icon">✓</span>
            Acceso protegido con autenticación segura
          </div>
        </div>
      </section>

      <section className="form-panel">
        <div className="auth-card">
          <div className="auth-heading">
            <span className="eyebrow">
              ACCESO SEGURO
            </span>

            <h2>
              {mode === "login"
                ? "Inicia sesión"
                : "Crea tu cuenta"}
            </h2>

            <p>
              {mode === "login"
                ? "Ingresa tus datos para continuar."
                : "Regístrate para comenzar tu proceso."}
            </p>
          </div>

          <div className="mode-selector">
            <button
              type="button"
              className={
                mode === "login" ? "active" : ""
              }
              onClick={() => changeMode("login")}
            >
              Ingresar
            </button>

            <button
              type="button"
              className={
                mode === "register" ? "active" : ""
              }
              onClick={() => changeMode("register")}
            >
              Registrarme
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <label htmlFor="email">
              Correo electrónico
            </label>

            <input
              id="email"
              type="email"
              value={email}
              placeholder="nombre@correo.com"
              autoComplete="email"
              required
              onChange={(event) =>
                setEmail(event.target.value)
              }
            />

            <label htmlFor="password">
              Contraseña
            </label>

            <input
              id="password"
              type="password"
              value={password}
              placeholder="Mínimo 8 caracteres"
              minLength={8}
              maxLength={128}
              autoComplete={
                mode === "login"
                  ? "current-password"
                  : "new-password"
              }
              required
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />

            {mode === "register" && (
              <>
                <label htmlFor="confirm-password">
                  Confirmar contraseña
                </label>

                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  placeholder="Repite tu contraseña"
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value,
                    )
                  }
                />
              </>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <button
              className="submit-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Procesando..."
                : mode === "login"
                  ? "Iniciar sesión"
                  : "Crear cuenta"}
            </button>
          </form>

          <p className="privacy-copy">
            Nunca mostraremos ni almacenaremos tu
            contraseña original.
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;