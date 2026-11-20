import { useEffect, useRef, useState } from "react";
import type { User } from "../types/auth";
import ClientProfilePanel from "./ClientProfilePanel";
import ManagementPanel from "./ManagementPanel";
import TrainingPlanPanel from "./TrainingPlanPanel";
import NutritionPlanPanel from "./NutritionPlanPanel";
import { getProfile, getAssessments } from "../services/clientProfile";
import { getTrainingPlan } from "../services/trainingPlan";
import { getNutritionPlan } from "../services/nutritionPlan";
import { getUsers } from "../services/management";

type Page = "home" | "profile" | "training" | "nutrition" | "management";
const labels: Record<Page, string> = { home: "Resumen", profile: "Mi perfil y progreso", training: "Entrenamientos", nutrition: "Nutrición", management: "Clientes" };
const paths: Record<Page, string> = {
  home: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  profile: "M3 17l6-6 4 3 8-10 M15 4h6v6",
  training: "M6 4v16 M3 8v8 M18 4v16 M21 8v8 M6 12h12",
  nutrition: "M12 7c-8-6-12 4-7 11 3 5 5 1 7 2 2-1 4 3 7-2 5-7 1-17-7-11z M12 7c0-4 2-5 5-5",
  management: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M17 4a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-4",
};
function Icon({ page }: { page: Page }) { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[page]} /></svg>; }

export default function Dashboard({ user, token, onLogout }: { user: User; token: string; onLogout: () => void }) {
  const [page, setPage] = useState<Page>("home");
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const menuButton = useRef<HTMLButtonElement>(null);
  const nav = useRef<HTMLElement>(null);
  const pages: Page[] = user.role === "client" ? ["home", "training", "nutrition", "profile"] : ["home", "management"];
  const role = { client: "Cliente", coach: "Entrenador", admin: "Administrador" }[user.role];
  function title(item: Page) { return item === "management" && user.role === "admin" ? "Administración" : labels[item]; }
  function navigate(item: Page) { setPage(item); setOpen(false); setQuery(""); }
  useEffect(() => {
    if (!open) return;
    nav.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function key(event: KeyboardEvent) {
      if (event.key === "Escape") { setOpen(false); menuButton.current?.focus(); }
      if (event.key === "Tab") {
        const items = nav.current?.querySelectorAll<HTMLButtonElement>("button");
        if (!items?.length) return;
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    }
    document.addEventListener("keydown", key);
    return () => { document.body.style.overflow = previous; document.removeEventListener("keydown", key); };
  }, [open]);
  return <div className={`workspace ${open ? "menu-open" : ""}`}>
    <a className="skip-link" href="#main-content">Ir al contenido</a>
    {open && <button className="nav-overlay" aria-label="Cerrar menú" onClick={() => { setOpen(false); menuButton.current?.focus(); }} />}
    <aside ref={nav} className="sidebar" id="main-menu" aria-label="Menú principal">
      <button className="mobile-close" onClick={() => { setOpen(false); menuButton.current?.focus(); }}>Cerrar menú ×</button>
      <div className="sidebar-logo"><img src="/logo-ya.png" alt="Y&A Fitness Coaching" /></div>
      <p className="nav-caption">TU ESPACIO PERSONAL</p>
      <nav>{pages.map(item => <button key={item} className={`nav-item ${page === item ? "selected" : ""}`} aria-current={page === item ? "page" : undefined} onClick={() => navigate(item)}><Icon page={item} />{title(item)}</button>)}</nav>
      <div className="sidebar-bottom"><div className="brand-note"><strong>Disciplina. Constancia.</strong><p>Cada paso cuenta para alcanzar tus objetivos.</p><span>Y&A COACHING ONLINE</span></div>
      <div className="sidebar-account"><span className="avatar">{user.email.slice(0,2).toUpperCase()}</span><div><strong>{user.email}</strong><small>{role}</small></div></div>
      <button className="sign-out" onClick={onLogout}>Cerrar sesión ↗</button></div>
    </aside>
    <div className="workspace-main">
      <header className="topbar"><button ref={menuButton} className="mobile-toggle" aria-label="Abrir menú" aria-expanded={open} aria-controls="main-menu" onClick={() => setOpen(true)}>☰</button>
        <div className="section-search"><label><span aria-hidden="true">⌕</span><input aria-label="Buscar sección" placeholder="Buscar una sección…" value={query} onChange={e => setQuery(e.target.value)} /></label>
        {query && <div className="search-results">{pages.filter(item => title(item).toLowerCase().includes(query.toLowerCase())).map(item => <button key={item} onClick={() => navigate(item)}>{title(item)} →</button>)}{!pages.some(item => title(item).toLowerCase().includes(query.toLowerCase())) && <p>No hay secciones con ese nombre.</p>}</div>}</div>
        <div className="top-account"><span className="avatar">{user.email.slice(0,2).toUpperCase()}</span><div><strong>{user.email}</strong><small>{role}</small></div></div>
      </header>
      <main id="main-content" className="main-content">
        <div className="page-heading"><div><p className="eyebrow">{new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" }).format(new Date())}</p><h1>{page === "home" ? (user.role === "admin" ? "Tu equipo y tus clientes" : user.role === "coach" ? "Acompaña el progreso de tus clientes" : "Tu progreso empieza aquí") : title(page)}</h1><p>{user.role === "admin" ? "Organiza las cuentas y asigna el acompañamiento de cada cliente." : user.role === "coach" ? "Consulta el progreso y prepara los planes de tus clientes asignados." : "Tu entrenamiento, alimentación y seguimiento. Todo en un lugar."}</p></div><span className="role-badge">{role}</span></div>
        {page === "home" && <Overview user={user} token={token} navigate={navigate} />}
        <div hidden={page !== "profile"}>{user.role === "client" && page === "profile" && <ClientProfilePanel token={token} onSessionExpired={onLogout} />}</div>
        {page === "training" && user.role === "client" && <TrainingPlanPanel token={token} />}
        {page === "nutrition" && user.role === "client" && <NutritionPlanPanel token={token} />}
        {page === "management" && user.role !== "client" && <ManagementPanel token={token} role={user.role} />}
        <footer className="workspace-footer">Y&A Fitness Coaching <span>Disciplina · Constancia · Resultados</span></footer>
      </main>
    </div>
  </div>;
}

function Overview({ user, token, navigate }: { user: User; token: string; navigate: (page: Page) => void }) {
  const [data, setData] = useState<{ stats: [string,string][]; training: string; nutrition: string; exercises: string[]; meals: string[]; clients: User[] } | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    async function load() {
      if (user.role === "client") {
        const [profile, training, nutrition] = await Promise.all([getProfile(token), getTrainingPlan(token), getNutritionPlan(token)]);
        const history = profile ? await getAssessments(token) : [];
        if (active) setData({ stats: [["Último peso", history.length ? `${history[0].weight_kg} kg` : "Sin registro"], ["Días en tu plan", String(training?.days.length ?? 0)], ["Comidas en tu plan", String(nutrition?.meals.length ?? 0)], ["Perfil personal", profile ? "Completado" : "Pendiente"]], training: training?.title ?? "Tu próximo entrenamiento", nutrition: nutrition?.title ?? "Tu alimentación", exercises: training?.days[0]?.exercises.map(e => `${e.name} · ${e.sets} series · ${e.repetitions}`) ?? [], meals: nutrition?.meals.map(m => `${m.name} · ${m.foods.length} ${m.foods.length === 1 ? "alimento" : "alimentos"}`) ?? [], clients: [] });
      } else {
        const clients = await getUsers(token, user.role === "admin" ? "/admin/clients" : "/coach/clients");
        const coaches = user.role === "admin" ? await getUsers(token, "/admin/coaches") : [];
        if (active) setData({ stats: [[user.role === "coach" ? "Clientes asignados" : "Clientes registrados", String(clients.length)], ["Clientes activos", String(clients.filter(c => c.is_active).length)], ["Tu rol", user.role === "admin" ? "Administrador" : "Entrenador"], [user.role === "admin" ? "Entrenadores" : "Estado de cuenta", user.role === "admin" ? String(coaches.length) : "Activa"]], training: "Acompaña cada objetivo", nutrition: "Un seguimiento cercano", exercises: [], meals: [], clients });
      }
    }
    void load().catch(err => { if (active) setError(err instanceof Error ? err.message : "No se pudo cargar el resumen."); });
    return () => { active = false; };
  }, [token, user.role, retry]);
  if (error) return <div className="overview-card"><p role="alert">{error}</p><button onClick={() => {setError(""); setRetry(v=>v+1);}}>Reintentar</button></div>;
  if (!data) return <p role="status">Preparando tu resumen…</p>;
  return <>
    <div className="stats-grid">{data.stats.map(([label,value],i) => <article className="stat-card" key={label}><span className={`stat-icon tone-${i}`}><Icon page={(["profile","training","nutrition","management"] as Page[])[i]} /></span><div><p>{label}</p><strong>{value}</strong><small>Información de tu cuenta</small></div></article>)}</div>
    {user.role === "client" ? <div className="overview-grid">
      <article className="overview-card"><p className="eyebrow">TU PLAN DE ENTRENAMIENTO</p><h2>{data.training}</h2>{data.exercises.length ? <ol className="overview-list">{data.exercises.slice(0,4).map((e,i)=><li key={i}><span>{String(i+1).padStart(2,"0")}</span>{e}</li>)}</ol> : <p className="empty-copy">Cuando tu entrenador prepare un plan, podrás consultarlo aquí.</p>}<button className="gold-button" onClick={()=>navigate("training")}>Ver entrenamiento →</button></article>
      <article className="overview-card"><p className="eyebrow">TU PLAN NUTRICIONAL</p><h2>{data.nutrition}</h2>{data.meals.length ? <ul className="overview-list">{data.meals.slice(0,4).map((m,i)=><li key={i}><span>◦</span>{m}</li>)}</ul> : <p className="empty-copy">Tus comidas y cantidades aparecerán cuando tengas un plan asignado.</p>}<button className="outline-button" onClick={()=>navigate("nutrition")}>Consultar alimentación →</button></article>
      <article className="overview-card full-width"><p className="eyebrow">CADA PASO CUENTA</p><h2>Haz visible tu progreso</h2><p>Actualiza tus medidas y comparte tu evolución con tu entrenador.</p><button className="outline-button" onClick={()=>navigate("profile")}>Mi perfil y valoraciones →</button></article>
    </div> : <div className="overview-grid"><article className="overview-card full-width"><div className="card-heading"><div><p className="eyebrow">SEGUIMIENTO PERSONALIZADO</p><h2>Tus clientes, en un solo lugar</h2></div><button className="gold-button" onClick={()=>navigate("management")}>Gestionar clientes →</button></div>{data.clients.length ? <div className="client-preview">{data.clients.slice(0,6).map(c=><div key={c.id}><span className="avatar">{c.email.slice(0,2).toUpperCase()}</span><strong>{c.email}</strong><span className="role-badge">{c.is_active ? "Activo" : "Inactivo"}</span></div>)}</div> : <p className="empty-copy">Todavía no hay clientes disponibles en tu cuenta.</p>}</article></div>}
  </>;
}
