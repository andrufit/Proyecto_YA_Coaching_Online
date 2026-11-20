import FormDialog from "./FormDialog";
import "./WorkspaceExperience.css";
import { useEffect, useRef, useState } from "react";
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
  const [editor, setEditor] = useState<"profile" | "assessment" | null>(null);
  const [dirty, setDirty] = useState(false);
  const submitting = useRef(false);
  function openEditor(value: "profile" | "assessment") {
    setError(""); setNotice(""); setDirty(false); setEditor(value);
  }

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
    if (submitting.current) return;
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

    submitting.current = true;
    setBusy(true);
    setError("");
    setNotice("");

    try {
      const saved = await saveProfile(token, data, profile !== null);
      setProfile(saved);
      setNotice("Perfil guardado correctamente.");
      setDirty(false); setEditor(null);
    } catch (requestError) {
      handleError(requestError);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  async function handleAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    const element = event.currentTarget;
    const form = new FormData(element);

    submitting.current = true;
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
      setDirty(false); setEditor(null);
      setNotice("Valoración registrada correctamente.");
    } catch (requestError) {
      handleError(requestError);
    } finally {
      submitting.current = false;
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
      <div className="experience-heading"><div><p className="experience-kicker">MI PROGRESO</p><h2>Mi perfil y seguimiento</h2><p>Tu punto de partida y cada avance, en un solo lugar.</p></div></div>
      <div className="experience-summary-grid">
        <article className="experience-summary"><span>Mi perfil</span><h3>{profile?.full_name || "Completa tu perfil"}</h3><p>{profile ? `${profile.height_cm} cm de estatura` : "Comparte tus datos y objetivos con tu entrenador."}</p><button type="button" onClick={() => openEditor("profile")}>{profile ? "Editar mi perfil" : "Completar mi perfil"}</button></article>
        <article className="experience-summary"><span>Último peso registrado</span><h3>{assessments.length ? `${assessments[0].weight_kg} kg` : "Sin registro"}</h3><p>{assessments.length ? assessments[0].assessment_date.split("-").reverse().join("/") : "Registra tus medidas para consultar tu evolución."}</p><button type="button" disabled={!profile} onClick={() => openEditor("assessment")}>Registrar medidas</button>{!profile && <small>Completa primero tu perfil.</small>}</article>
      </div>
      {profile && <dl className="management-details experience-summary">
        <div><dt>Objetivo</dt><dd>{{fat_loss: "Pérdida de grasa", muscle_gain: "Ganancia muscular", maintenance: "Mantenimiento", performance: "Rendimiento"}[profile.goal]}</dd></div>
        <div><dt>Nivel</dt><dd>{{beginner: "Principiante", intermediate: "Intermedio", advanced: "Avanzado"}[profile.training_level]}</dd></div>
        <div><dt>Restricciones médicas</dt><dd>{profile.medical_restrictions || "Sin información registrada"}</dd></div>
      </dl>}

      {error && <p className="client-error" role="alert">{error}</p>}
      {notice && <p className="client-notice" role="status">{notice}</p>}

      {editor === "profile" && <FormDialog wide title={profile ? "Editar mi perfil" : "Completar mi perfil"} description="Actualiza tus datos, objetivo y nivel de entrenamiento." dirty={dirty} busy={busy} onClose={() => setEditor(null)}>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={handleProfile} onChange={() => setDirty(true)} key={profile?.id ?? "new"}>
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
      </FormDialog>}

      {profile && (
        <>
          {editor === "assessment" && <FormDialog wide title="Registrar medidas" description="Solo el peso es obligatorio. Completa las medidas que tengas disponibles." dirty={dirty} busy={busy} onClose={() => setEditor(null)}>
          {error && <p role="alert">{error}</p>}
          <form onSubmit={handleAssessment} onChange={() => setDirty(true)}>
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
          </FormDialog>}

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