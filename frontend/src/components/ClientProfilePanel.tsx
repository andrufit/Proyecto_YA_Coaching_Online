import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  addAssessment,
  ApiError,
  getAssessments,
  getProfile,
  saveProfile,
} from "../services/clientProfile";
import type {
  BodyAssessment,
  ClientProfile,
  ProfileData,
} from "../services/clientProfile";

import "./ClientProfilePanel.css";

type Props = {
  token: string;
  onSessionExpired: () => void;
};

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "No fue posible completar la solicitud.";
}

function field(form: FormData, name: string): string {
  return String(form.get(name) ?? "").trim();
}

function optionalField(form: FormData, name: string): string | null {
  return field(form, name) || null;
}

export default function ClientProfilePanel({
  token,
  onSessionExpired,
}: Props) {
  const [profile, setProfile] = useState<ClientProfile | null>(null);
  const [assessments, setAssessments] = useState<BodyAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setLoadError("");

      try {
        const current = await getProfile(token);
        const history = current ? await getAssessments(token) : [];

        if (active) {
          setProfile(current);
          setAssessments(history);
        }
      } catch (requestError) {
        if (active) {
          setLoadError(errorMessage(requestError));
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token, reload]);

  function handleError(requestError: unknown) {
    if (requestError instanceof ApiError && requestError.status === 401) {
      onSessionExpired();
      return;
    }
    setError(errorMessage(requestError));
  }

  async function handleProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const fullName = field(form, "full_name").replace(/\s+/g, " ");

    if (fullName.length < 2) {
      setError("Escribe un nombre de al menos dos caracteres.");
      return;
    }

    const data: ProfileData = {
      full_name: fullName,
      birth_date: field(form, "birth_date"),
      sex: field(form, "sex") as ProfileData["sex"],
      height_cm: field(form, "height_cm"),
      goal: field(form, "goal") as ProfileData["goal"],
      training_level: field(
        form,
        "training_level",
      ) as ProfileData["training_level"],
      medical_restrictions: optionalField(form, "medical_restrictions"),
    };

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const saved = await saveProfile(token, data, profile !== null);
      setProfile(saved);
      setNotice("Perfil guardado correctamente.");
    } catch (requestError) {
      handleError(requestError);
    } finally {
      setBusy(false);
    }
  }

  async function handleAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const element = event.currentTarget;
    const form = new FormData(element);

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const saved = await addAssessment(token, {
        weight_kg: field(form, "weight_kg"),
        body_fat_percentage: optionalField(form, "body_fat_percentage"),
        waist_cm: optionalField(form, "waist_cm"),
        hip_cm: optionalField(form, "hip_cm"),
        chest_cm: optionalField(form, "chest_cm"),
        notes: optionalField(form, "notes"),
      });

      setAssessments((previous) =>
        [saved, ...previous].sort(
          (a, b) =>
            b.assessment_date.localeCompare(a.assessment_date) ||
            b.id - a.id,
        ),
      );
      element.reset();
      setNotice("Valoración registrada correctamente.");
    } catch (requestError) {
      handleError(requestError);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p role="status">Cargando tu perfil...</p>;

  if (loadError) {
    return (
      <section className="client-panel">
        <p role="alert">{loadError}</p>
        <button type="button" onClick={() => setReload((value) => value + 1)}>
          Reintentar
        </button>
        <button type="button" onClick={onSessionExpired}>
          Volver al inicio de sesión
        </button>
      </section>
    );
  }

  return (
    <section className="client-panel">
      <h2>Mi perfil y seguimiento</h2>

      {error && <p className="client-error" role="alert">{error}</p>}
      {notice && <p className="client-notice" role="status">{notice}</p>}

      <form onSubmit={handleProfile} key={profile?.id ?? "new"}>
        <h3>{profile ? "Editar mi perfil" : "Completar mi perfil"}</h3>

        <fieldset disabled={busy} className="client-grid">
          <label>
            Nombre completo
            <input
              name="full_name"
              defaultValue={profile?.full_name ?? ""}
              required
              minLength={2}
              maxLength={150}
              autoComplete="name"
            />
          </label>

          <label>
            Fecha de nacimiento
            <input
              name="birth_date"
              type="date"
              defaultValue={profile?.birth_date ?? ""}
              required
            />
          </label>

          <label>
            Sexo
            <select name="sex" defaultValue={profile?.sex ?? ""} required>
              <option value="" disabled>Selecciona una opción</option>
              <option value="female">Femenino</option>
              <option value="male">Masculino</option>
              <option value="other">Otro</option>
              <option value="prefer_not_to_say">Prefiero no indicarlo</option>
            </select>
          </label>

          <label>
            Estatura (cm)
            <input
              name="height_cm"
              type="number"
              min="0.01"
              max="300"
              step="0.01"
              defaultValue={profile?.height_cm ?? ""}
              required
            />
          </label>

          <label>
            Objetivo
            <select name="goal" defaultValue={profile?.goal ?? "maintenance"}>
              <option value="fat_loss">Pérdida de grasa</option>
              <option value="muscle_gain">Ganancia muscular</option>
              <option value="maintenance">Mantenimiento</option>
              <option value="performance">Rendimiento</option>
            </select>
          </label>

          <label>
            Nivel de entrenamiento
            <select
              name="training_level"
              defaultValue={profile?.training_level ?? "beginner"}
            >
              <option value="beginner">Principiante</option>
              <option value="intermediate">Intermedio</option>
              <option value="advanced">Avanzado</option>
            </select>
          </label>

          <label className="client-wide">
            Restricciones médicas (opcional)
            <textarea
              name="medical_restrictions"
              maxLength={2000}
              defaultValue={profile?.medical_restrictions ?? ""}
            />
          </label>

          <button type="submit">
            {busy ? "Procesando..." : "Guardar perfil"}
          </button>
        </fieldset>
      </form>

      {profile && (
        <>
          <form onSubmit={handleAssessment}>
            <h3>Registrar valoración de hoy</h3>

            <fieldset disabled={busy} className="client-grid">
              <label>
                Peso (kg)
                <input
                  name="weight_kg"
                  type="number"
                  min="0.01"
                  max="500"
                  step="0.01"
                  required
                />
              </label>

              <label>
                Grasa corporal % (opcional)
                <input
                  name="body_fat_percentage"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                />
              </label>

              {[
                ["waist_cm", "Cintura"],
                ["hip_cm", "Cadera"],
                ["chest_cm", "Pecho"],
              ].map(([name, label]) => (
                <label key={name}>
                  {label} en cm (opcional)
                  <input
                    name={name}
                    type="number"
                    min="0.01"
                    max="500"
                    step="0.01"
                  />
                </label>
              ))}

              <label className="client-wide">
                Notas (opcional)
                <textarea name="notes" maxLength={2000} />
              </label>

              <button type="submit">
                {busy ? "Procesando..." : "Registrar valoración"}
              </button>
            </fieldset>
          </form>

          <h3>Historial de valoraciones</h3>

          {assessments.length === 0 ? (
            <p>Todavía no tienes valoraciones registradas.</p>
          ) : (
            <div className="client-table">
              <table>
                <caption>Mediciones, de la más reciente a la más antigua</caption>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Peso (kg)</th>
                    <th>Grasa (%)</th>
                    <th>Cintura (cm)</th>
                    <th>Cadera (cm)</th>
                    <th>Pecho (cm)</th>
                    <th>Notas</th>
                  </tr>
                </thead>
                <tbody>
                  {assessments.map((item) => (
                    <tr key={item.id}>
                      <td>{item.assessment_date.split("-").reverse().join("/")}</td>
                      <td>{item.weight_kg}</td>
                      <td>{item.body_fat_percentage ?? "—"}</td>
                      <td>{item.waist_cm ?? "—"}</td>
                      <td>{item.hip_cm ?? "—"}</td>
                      <td>{item.chest_cm ?? "—"}</td>
                      <td>{item.notes ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}