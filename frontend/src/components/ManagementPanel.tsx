import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import TrainingPlanPanel from "./TrainingPlanPanel";
import NutritionPlanPanel from "./NutritionPlanPanel";

import type { User } from "../types/auth";
import type {
  BodyAssessment,
  ClientProfile,
} from "../services/clientProfile";
import {
  createCoach,
  getAssignment,
  getCoachAssessments,
  getCoachProfile,
  getUsers,
  saveAssignment,
} from "../services/management";

import "./ManagementPanel.css";

type Props = {
  token: string;
  role: "admin" | "coach";
};

function message(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "No fue posible completar la operación.";
}

function AssignmentEditor({
  token,
  client,
  coaches,
}: {
  token: string;
  client: User;
  coaches: User[];
}) {
  const [coachId, setCoachId] = useState("");
  const [currentCoachId, setCurrentCoachId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const assignment = await getAssignment(token, client.id);
        if (!active) return;

        setCurrentCoachId(assignment?.coach_id ?? null);
        setCoachId(assignment ? String(assignment.coach_id) : "");
      } catch (requestError) {
        if (active) setError(message(requestError));
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => { active = false; };
  }, [token, client.id, retry]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!coachId) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const saved = await saveAssignment(token, client.id, Number(coachId));
      setCurrentCoachId(saved.coach_id);
      setNotice("Entrenador asignado correctamente.");
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p role="status">Consultando asignación...</p>;

  const currentCoach = coaches.find((item) => item.id === currentCoachId);

  return (
    <form onSubmit={submit}>
      <h3>Entrenador de {client.email}</h3>

      <p>
        Asignación actual:{" "}
        {currentCoach
          ? currentCoach.email
          : currentCoachId
            ? `Entrenador #${currentCoachId}`
            : "Sin entrenador asignado"}
      </p>

      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setError("");
              setLoading(true);
              setRetry((value) => value + 1);
            }}
          >
            Consultar nuevamente
          </button>
        </div>
      )}

      {notice && <p role="status">{notice}</p>}

      <fieldset disabled={busy || !client.is_active || Boolean(error)}>
        <label>
          Seleccionar entrenador
          <select
            value={coachId}
            required
            onChange={(event) => setCoachId(event.target.value)}
          >
            <option value="">Selecciona un entrenador</option>
            {coaches.map((coach) => (
              <option
                key={coach.id}
                value={coach.id}
                disabled={!coach.is_active}
              >
                {coach.email}{!coach.is_active ? " (inactivo)" : ""}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={!coachId}>
          {busy ? "Guardando..." : "Guardar asignación"}
        </button>
      </fieldset>

      {!client.is_active && <p>Este cliente está desactivado.</p>}
    </form>
  );
}

function CoachDetails({
  token,
  client,
}: {
  token: string;
  client: User;
}) {
  const [profile, setProfile] = useState<ClientProfile | null>(null);
  const [history, setHistory] = useState<BodyAssessment[]>([]);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [nextProfile, nextHistory] = await Promise.all([
          getCoachProfile(token, client.id),
          getCoachAssessments(token, client.id, offset),
        ]);

        if (active) {
          setProfile(nextProfile);
          setHistory(nextHistory);
        }
      } catch (requestError) {
        if (active) {
          setProfile(null);
          setHistory([]);
          setError(message(requestError));
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => { active = false; };
  }, [token, client.id, offset, retry]);

  function changePage(nextOffset: number) {
    setLoading(true);
    setError("");
    setOffset(nextOffset);
  }

  if (loading) return <p role="status">Cargando información del cliente...</p>;

  if (error) {
    return (
      <div>
        <p role="alert">{error}</p>
        <button
          type="button"
          onClick={() => {
            setError("");
            setLoading(true);
            setRetry((value) => value + 1);
          }}
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!profile) return null;

  const goals = {
    fat_loss: "Pérdida de grasa",
    muscle_gain: "Ganancia muscular",
    maintenance: "Mantenimiento",
    performance: "Rendimiento",
  };

  const levels = {
    beginner: "Principiante",
    intermediate: "Intermedio",
    advanced: "Avanzado",
  };

  const sexes = {
    female: "Femenino",
    male: "Masculino",
    other: "Otro",
    prefer_not_to_say: "Prefiere no indicarlo",
  };

  return (
    <article>
      <h3>{profile.full_name}</h3>
      <p>{client.email}</p>

      <dl className="management-details">
        <div><dt>Nacimiento</dt><dd>{profile.birth_date}</dd></div>
        <div><dt>Sexo</dt><dd>{sexes[profile.sex]}</dd></div>
        <div><dt>Estatura</dt><dd>{profile.height_cm} cm</dd></div>
        <div><dt>Objetivo</dt><dd>{goals[profile.goal]}</dd></div>
        <div><dt>Nivel</dt><dd>{levels[profile.training_level]}</dd></div>
        <div>
          <dt>Restricciones médicas</dt>
          <dd>{profile.medical_restrictions || "Sin información registrada"}</dd>
        </div>
      </dl>

      <h3>Valoraciones corporales</h3>

      {history.length === 0 ? (
        <p>
          {offset === 0
            ? "Todavía no hay valoraciones registradas."
            : "No hay más valoraciones."}
        </p>
      ) : (
        <div className="management-table">
          <table>
            <caption>Registros del cliente seleccionado</caption>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Peso kg</th>
                <th>Grasa %</th>
                <th>Cintura cm</th>
                <th>Cadera cm</th>
                <th>Pecho cm</th>
                <th>Notas</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
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

      <div className="management-actions">
        <button
          type="button"
          disabled={offset === 0}
          onClick={() => changePage(Math.max(0, offset - 20))}
        >
          Anterior
        </button>
        <span>Página {offset / 20 + 1}</span>
        <button
          type="button"
          disabled={history.length < 20}
          onClick={() => changePage(offset + 20)}
        >
          Siguiente
        </button>
      </div>
    </article>
  );
}

export default function ManagementPanel({ token, role }: Props) {
  const [clients, setClients] = useState<User[]>([]);
  const [coaches, setCoaches] = useState<User[]>([]);
  const [detailTab, setDetailTab] = useState("profile");
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [nextClients, nextCoaches] = await Promise.all([
          getUsers(
            token,
            role === "admin" ? "/admin/clients" : "/coach/clients",
          ),
          role === "admin"
            ? getUsers(token, "/admin/coaches")
            : Promise.resolve([] as User[]),
        ]);

        if (active) {
          setClients(nextClients);
          setCoaches(nextCoaches);
        }
      } catch (requestError) {
        if (active) setLoadError(message(requestError));
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => { active = false; };
  }, [token, role, reload]);

  async function submitCoach(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const coach = await createCoach(
        token,
        String(data.get("email") ?? "").trim(),
        String(data.get("password") ?? ""),
      );

      setCoaches((previous) => [...previous, coach]);
      form.reset();
      setNotice(`Entrenador creado: ${coach.email}`);
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setBusy(false);
    }
  }

  const selectedClient = clients.find(
    (client) => String(client.id) === selectedId,
  );

  return (
    <section className="management-panel">
      <h2>
        {role === "admin" ? "Administración" : "Mis clientes"}
      </h2>

      <button
        type="button"
        disabled={loading || busy}
        onClick={() => {
          setSelectedId("");
          setLoadError("");
          setLoading(true);
          setReload((value) => value + 1);
        }}
      >
        Actualizar lista
      </button>

      {loading ? (
        <p role="status">Cargando cuentas...</p>
      ) : loadError ? (
        <p role="alert">{loadError}</p>
      ) : (
        <>
          {role === "admin" && (
            <form onSubmit={submitCoach}>
              <h3>Crear entrenador</h3>

              <fieldset disabled={busy}>
                <label>
                  Correo del entrenador
                  <input name="email" type="email" required />
                </label>

                <label>
                  Contraseña inicial
                  <input
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    minLength={8}
                    maxLength={128}
                    required
                  />
                </label>

                <button type="submit">
                  {busy ? "Creando..." : "Crear entrenador"}
                </button>
              </fieldset>

              {error && <p role="alert">{error}</p>}
              {notice && <p role="status">{notice}</p>}
            </form>
          )}

          <h3>
            {role === "admin"
              ? "Asignar o cambiar entrenador"
              : "Consultar cliente"}
          </h3>

          {clients.length === 0 ? (
            <p>
              {role === "admin"
                ? "Todavía no hay clientes registrados."
                : "Todavía no tienes clientes activos asignados."}
            </p>
          ) : (
            <label>
              Cliente
              <select
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
              >
                <option value="">Selecciona un cliente</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.email}
                    {!client.is_active ? " (inactivo)" : ""}
                  </option>
                ))}
              </select>
            </label>
          )}

          {selectedClient && (
            role === "admin" ? (
              <AssignmentEditor
                key={`${token}-${selectedClient.id}`}
                token={token}
                client={selectedClient}
                coaches={coaches}
              />
            ) : (
              <>
                <div className="detail-tabs" aria-label="Información del cliente">
                  {[["profile", "Perfil y valoraciones"], ["training", "Entrenamiento"], ["nutrition", "Nutrición"]].map(([value,label]) => <button type="button" key={value} aria-pressed={detailTab === value} className={detailTab === value ? "active" : ""} onClick={() => setDetailTab(value)}>{label}</button>)}
                </div>
                <div hidden={detailTab !== "profile"}><CoachDetails key={`${token}-${selectedClient.id}`} token={token} client={selectedClient} /></div>
                <div hidden={detailTab !== "training"}><TrainingPlanPanel token={token} clientId={selectedClient.id} /></div>
                <div hidden={detailTab !== "nutrition"}><NutritionPlanPanel token={token} clientId={selectedClient.id} /></div>
              </>
            )
          )}
        </>
      )}
    </section>
  );
}