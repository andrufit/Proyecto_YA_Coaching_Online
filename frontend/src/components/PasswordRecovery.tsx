import { useState } from "react";
import type { FormEvent } from "react";

export default function PasswordRecovery({ onBack }: { onBack: () => void }) {
  const [token] = useState(() => {
    const value = new URLSearchParams(window.location.hash.slice(1)).get("reset_token") ?? "";
    return value;
  });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    if (token && password !== confirmation) { setError("Las contraseñas no coinciden."); return; }
    setBusy(true);
    try {
      const base = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
      const response = await fetch(`${base}/api/v1/auth/${token ? "reset-password" : "forgot-password"}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(token ? { token, password } : { email }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Revisa los datos e inténtalo nuevamente.");
      setNotice(data.message); setPassword(""); setConfirmation("");
      if (token) window.history.replaceState(null, "", window.location.pathname);
    } catch (error) { setError(error instanceof Error ? error.message : "No fue posible conectar."); }
    finally { setBusy(false); }
  }
  return <main className="recovery-page"><section className="recovery-card">
    <img src="/logo-ya.png" alt="Y&A Fitness Coaching" className="recovery-logo" />
    <span className="eyebrow">VOLVAMOS A TU PROGRESO</span>
    <h1>{token ? "Tu nueva contraseña" : "Recupera tu acceso"}</h1>
    <p>{token ? "Elige una contraseña de al menos 8 caracteres." : "Te enviaremos un enlace para que puedas volver a tu cuenta."}</p>
    {notice ? <p role="status" className="recovery-notice">{notice}</p> : <form onSubmit={submit}>
      <fieldset disabled={busy}>
      {!token ? <label>Correo electrónico<input type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} /></label> : <>
        <label>Nueva contraseña<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={e => setPassword(e.target.value)} /></label>
        <label>Confirma tu contraseña<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={confirmation} onChange={e => setConfirmation(e.target.value)} /></label>
      </>}
      <button className="gold-button" type="submit">{busy ? "Procesando…" : token ? "Guardar contraseña" : "Enviar enlace"}</button>
      </fieldset>
    </form>}
    {error && <p role="alert" className="error-message">{error}</p>}
    <button className="forgot-link" onClick={onBack}>Volver a iniciar sesión</button>
  </section></main>;
}
