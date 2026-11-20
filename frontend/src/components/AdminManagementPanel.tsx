import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import type { User } from "../types/auth";
import { createCoach, getAssignment, getUsers, saveAssignment } from "../services/management";
import FormDialog from "./FormDialog";
import "./AdminManagementPanel.css";

function errorText(error: unknown) {
  return error instanceof Error ? error.message : "No fue posible completar la operación.";
}

function CreateCoachForm({ token, onClose, onSaved }: {
  token: string; onClose: () => void; onSaved: (coach: User) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const confirmationInput = useRef<HTMLInputElement>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    if (password !== confirmation) {
      setPasswordError("Las contraseñas no coinciden.");
      confirmationInput.current?.focus();
      return;
    }
    pending.current = true;
    setBusy(true); setError("");
    try { onSaved(await createCoach(token, email.trim(), password)); }
    catch (failure) { setError(errorText(failure)); }
    finally { pending.current = false; setBusy(false); }
  }

  return <FormDialog title="Nuevo entrenador" description="Crea una cuenta con acceso al seguimiento de sus clientes asignados."
    dirty={Boolean(email || password || confirmation)} busy={busy} onClose={onClose}>
    <form onSubmit={submit}>
      <fieldset disabled={busy}>
        <label>Correo del entrenador<input name="email" type="email" autoComplete="off" required maxLength={255}
          value={email} onChange={event => setEmail(event.target.value)} /></label>
        <label>Contraseña inicial<input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128}
          aria-describedby="coach-password-help" value={password} onChange={event => { setPassword(event.target.value); setPasswordError(""); }} /></label>
        <small id="coach-password-help">Entre 8 y 128 caracteres. No se enviará un correo de invitación automáticamente.</small>
        <label>Confirmar contraseña<input ref={confirmationInput} name="confirmation" type="password" autoComplete="new-password" required
          aria-invalid={Boolean(passwordError)} aria-describedby={passwordError ? "coach-password-error" : undefined}
          value={confirmation} onChange={event => { setConfirmation(event.target.value); setPasswordError(""); }} /></label>
        {passwordError && <p id="coach-password-error" role="alert">{passwordError}</p>}
        {error && <p role="alert">{error}</p>}
        <button type="submit">{busy ? "Creando cuenta…" : "Crear entrenador"}</button>
      </fieldset>
    </form>
  </FormDialog>;
}

function AssignmentForm({ token, client, coaches, onClose, onSaved }: {
  token: string; client: User; coaches: User[]; onClose: () => void; onSaved: (text: string) => void;
}) {
  const [current, setCurrent] = useState<number | null>(null);
  const [chosen, setChosen] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    void getAssignment(token, client.id).then(assignment => {
      if (active) { setCurrent(assignment?.coach_id ?? null); setChosen(assignment ? String(assignment.coach_id) : ""); }
    }).catch(failure => { if (active) setLoadError(errorText(failure)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token, client.id, retry]);

  const selected = coaches.find(coach => String(coach.id) === chosen);
  const dirty = !loading && chosen !== (current === null ? "" : String(current));
  const currentName = coaches.find(coach => coach.id === current)?.email ?? (current === null ? "Sin entrenador" : `Entrenador #${current}`);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current || !dirty || !selected?.is_active || !client.is_active) return;
    pending.current = true; setBusy(true); setError("");
    try {
      await saveAssignment(token, client.id, selected.id);
      onSaved(`Asignación guardada: ${client.email} → ${selected.email}.`);
    } catch (failure) { setError(errorText(failure)); }
    finally { pending.current = false; setBusy(false); }
  }

  return <FormDialog title="Asignar entrenador" description={`Cliente: ${client.email}`} dirty={dirty} busy={busy} onClose={onClose}>
    {loading ? <p role="status">Consultando la asignación actual…</p> : loadError ? <>
      <p role="alert">{loadError}</p><button type="button" onClick={() => { setLoadError(""); setLoading(true); setRetry(value => value + 1); }}>Reintentar consulta</button>
    </> : <form onSubmit={submit}>
      <p>Entrenador actual: <strong>{currentName}</strong></p>
      {!coaches.some(coach => coach.is_active) && <p>No hay entrenadores activos. Cierra este formulario y crea uno desde Nuevo entrenador.</p>}
      <fieldset disabled={busy || !client.is_active}>
        <label>Entrenador<select value={chosen} required onChange={event => { setChosen(event.target.value); setError(""); }}>
          <option value="">Selecciona un entrenador</option>
          {coaches.map(coach => <option key={coach.id} value={coach.id} disabled={!coach.is_active}>{coach.email}{coach.is_active ? "" : " (inactivo)"}</option>)}
        </select></label>
        {dirty && selected && <p className="assignment-summary">Al guardar, <strong>{selected.email}</strong> será el entrenador de este cliente.{current !== null && " El entrenador anterior perderá el acceso."}</p>}
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={!dirty || !selected?.is_active}>{busy ? "Guardando…" : "Guardar asignación"}</button>
      </fieldset>
    </form>}
  </FormDialog>;
}

export default function AdminManagementPanel({ token }: { token: string }) {
  const [clients, setClients] = useState<User[]>([]);
  const [coaches, setCoaches] = useState<User[]>([]);
  const [view, setView] = useState<"clients" | "coaches">("clients");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  const [creating, setCreating] = useState(false);
  const [selectedClient, setSelectedClient] = useState<User | null>(null);

  useEffect(() => {
    let active = true;
    void Promise.all([getUsers(token, "/admin/clients"), getUsers(token, "/admin/coaches")])
      .then(([nextClients, nextCoaches]) => { if (active) { setClients(nextClients); setCoaches(nextCoaches); } })
      .catch(failure => { if (active) setError(errorText(failure)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token, reload]);

  const users = view === "clients" ? clients : coaches;
  const filtered = users.filter(user => user.email.toLowerCase().includes(query.trim().toLowerCase())
    && (status === "all" || user.is_active === (status === "active")));

  function refresh() { setError(""); setLoading(true); setReload(value => value + 1); }

  return <section className="management-panel admin-management" aria-label="Gestión de cuentas">
    <header className="admin-toolbar"><div><h2>Gestiona tu equipo y tus clientes</h2><p>Consulta las cuentas y abre un formulario solo cuando necesites hacer un cambio.</p></div>
      <div className="admin-toolbar-actions"><button type="button" disabled={loading} onClick={refresh}>Actualizar</button>
        <button type="button" className="admin-primary" disabled={loading || Boolean(error)} onClick={() => setCreating(true)}>+ Nuevo entrenador</button></div>
    </header>
    {notice && <p role="status">{notice}</p>}
    <div className="admin-sections" role="group" aria-label="Tipo de cuenta">
      <button type="button" aria-pressed={view === "clients"} onClick={() => { setView("clients"); setQuery(""); setStatus("all"); }}>Clientes <span>{clients.length}</span></button>
      <button type="button" aria-pressed={view === "coaches"} onClick={() => { setView("coaches"); setQuery(""); setStatus("all"); }}>Entrenadores <span>{coaches.length}</span></button>
    </div>
    <div className="admin-filters"><label>Buscar por correo<input type="search" value={query} placeholder="Escribe un correo…" onChange={event => setQuery(event.target.value)} /></label>
      <label>Estado<select value={status} onChange={event => setStatus(event.target.value)}><option value="all">Todos</option><option value="active">Activos</option><option value="inactive">Inactivos</option></select></label></div>
    {loading ? <p role="status">Cargando cuentas…</p> : error ? <p role="alert">{error} Usa Actualizar para reintentar.</p> : <>
      <p className="admin-result-count" aria-live="polite">{filtered.length} de {users.length} {view === "clients" ? "clientes" : "entrenadores"}</p>
      {filtered.length ? <ul className="admin-account-list">{filtered.map(user => <li key={user.id}>
        <span className="admin-avatar" aria-hidden="true">{user.email.slice(0, 2).toUpperCase()}</span>
        <div className="admin-account-info"><strong>{user.email}</strong><span>{view === "clients" ? "Cliente" : "Entrenador"} · #{user.id}</span></div>
        <span className={`admin-status ${user.is_active ? "is-active" : ""}`}>{user.is_active ? "Activo" : "Inactivo"}</span>
        {view === "clients" && <button type="button" disabled={!user.is_active} aria-label={`Asignar entrenador a ${user.email}`} onClick={() => setSelectedClient(user)}>Asignar entrenador</button>}
      </li>)}</ul> : <div className="admin-empty"><h3>{users.length ? "No hay coincidencias" : view === "clients" ? "Tu próximo cliente empieza aquí" : "Forma tu equipo de entrenadores"}</h3>
        <p>{users.length ? "Prueba con otro correo o cambia el filtro de estado." : view === "clients" ? "Las personas aparecerán aquí cuando se registren como clientes en la aplicación. Después podrás asignarles un entrenador." : "Crea la primera cuenta desde Nuevo entrenador. Luego podrás asignarle clientes."}</p>
        {users.length > 0 && <button type="button" onClick={() => { setQuery(""); setStatus("all"); }}>Limpiar filtros</button>}
      </div>}
    </>}
    {creating && <CreateCoachForm token={token} onClose={() => setCreating(false)} onSaved={coach => {
      setCoaches(previous => [...previous, coach]); setCreating(false); setView("coaches"); setQuery(""); setStatus("all"); setNotice(`Entrenador creado: ${coach.email}`);
    }} />}
    {selectedClient && <AssignmentForm token={token} client={selectedClient} coaches={coaches} onClose={() => setSelectedClient(null)} onSaved={text => { setSelectedClient(null); setNotice(text); }} />}
  </section>;
}
