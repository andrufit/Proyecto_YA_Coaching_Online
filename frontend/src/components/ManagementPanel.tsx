import "./WorkspaceExperience.css";
import { useEffect, useState } from "react";
import TrainingPlanPanel from "./TrainingPlanPanel";
import NutritionPlanPanel from "./NutritionPlanPanel";
import AdminManagementPanel from "./AdminManagementPanel";
import type { User } from "../types/auth";
import type { BodyAssessment, ClientProfile } from "../services/clientProfile";
import { getCoachAssessments, getCoachProfile, getUsers } from "../services/management";
import "./ManagementPanel.css";

function message(error: unknown): string {
  return error instanceof Error ? error.message : "No fue posible completar la operación.";
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

function CoachManagementPanel({ token }: { token: string }) {
  const [clients, setClients] = useState<User[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [detailTab, setDetailTab] = useState("profile");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    void getUsers(token, "/coach/clients")
      .then(users => { if (active) setClients(users); })
      .catch(failure => { if (active) setError(message(failure)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token, reload]);
  const selectedClient = clients.find(client => String(client.id) === selectedId);
  const visible = clients.filter(client => client.email.toLowerCase().includes(query.trim().toLowerCase()));
  return <section className="management-panel experience-coach">
    <div className="experience-heading"><div><p className="experience-kicker">ESPACIO DEL ENTRENADOR</p><h2>{selectedClient ? "Ficha del cliente" : "Mis clientes"}</h2><p>{selectedClient ? selectedClient.email : `${clients.length} clientes asignados · Elige una ficha para preparar sus planes.`}</p></div>
    {selectedClient ? <button type="button" onClick={() => setSelectedId("")}>Volver a mis clientes</button> : <button type="button" disabled={loading} onClick={() => {
      setError(""); setLoading(true); setReload(value => value + 1);
    }}>Actualizar lista</button>}</div>
    {loading ? <p role="status">Cargando clientes...</p> : error ? <p role="alert">{error}</p> : <>
      {!selectedClient && <><label className="experience-search">Buscar cliente por correo<input type="search" value={query} placeholder="Escribe el correo del cliente" onChange={event => setQuery(event.target.value)} /></label>
      {!clients.length ? <div className="experience-empty"><h3>Tu próximo acompañamiento empieza aquí</h3><p>Los clientes aparecerán cuando el administrador te los asigne.</p></div> : !visible.length ? <p role="status">No encontramos clientes con ese correo.</p> : <div className="experience-client-grid">{visible.map(client => <article className="experience-client-card" key={client.id}>
        <span className="avatar" aria-hidden="true">{client.email.slice(0, 2).toUpperCase()}</span><h3>{client.email}</h3><p>{client.is_active ? "Cuenta activa" : "Cuenta inactiva"}</p>
        <button type="button" onClick={() => { setSelectedId(String(client.id)); setDetailTab("profile"); }}>Abrir ficha<span className="experience-sr-only"> de {client.email}</span></button>
      </article>)}</div>}</>}
      {selectedClient && <div key={selectedClient.id}>
        <div className="detail-tabs" aria-label="Información del cliente">
          {[["profile", "Perfil y progreso"], ["training", "Entrenamiento"], ["nutrition", "Alimentación"]].map(([value, label]) =>
            <button type="button" key={value} aria-pressed={detailTab === value} className={detailTab === value ? "active" : ""} onClick={() => setDetailTab(value)}>{label}</button>)}
        </div>
        <div hidden={detailTab !== "profile"}><CoachDetails token={token} client={selectedClient} /></div>
        <div hidden={detailTab !== "training"}><TrainingPlanPanel token={token} clientId={selectedClient.id} /></div>
        <div hidden={detailTab !== "nutrition"}><NutritionPlanPanel token={token} clientId={selectedClient.id} /></div>
      </div>}
    </>}
  </section>;
}

export default function ManagementPanel({ token, role }: { token: string; role: "admin" | "coach" }) {
  return role === "admin" ? <AdminManagementPanel token={token} /> : <CoachManagementPanel token={token} />;
}