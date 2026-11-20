import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";
import "./FormDialog.css";

type Props = {
  wide?: boolean;
  title: string;
  description: string;
  dirty: boolean;
  busy: boolean;
  onClose: () => void;
  children: ReactNode;
};

// Mount only while editing. Native modal behavior keeps the background inert.
export default function FormDialog({ title, description, dirty, busy, onClose, children, wide = false }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const element = dialog.current;
    const trigger = document.activeElement;
    const overflow = document.body.style.overflow;
    element?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      element?.close();
      document.body.style.overflow = overflow;
      if (trigger instanceof HTMLElement && trigger.isConnected) trigger.focus();
    };
  }, []);

  useEffect(() => {
    if (!dirty && !busy) return;
    function warn(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, busy]);

  function requestClose() {
    if (busy) return;
    if (dirty && !window.confirm("Tienes cambios sin guardar. ¿Quieres descartarlos y cerrar?")) return;
    onClose();
  }

  return <dialog ref={dialog} className={`form-dialog ${wide ? "form-dialog-wide" : ""}`} aria-labelledby={titleId}
    aria-describedby={descriptionId} aria-busy={busy}
    onCancel={event => { event.preventDefault(); requestClose(); }}>
    <header className="form-dialog-heading">
      <div><h2 id={titleId}>{title}</h2><p id={descriptionId}>{description}</p></div>
      <button type="button" className="form-dialog-close" disabled={busy} onClick={requestClose} aria-label="Cerrar formulario">×</button>
    </header>
    {children}
    <div className="form-dialog-footer">
      <button type="button" disabled={busy} onClick={requestClose}>Cancelar</button>
      <small>{busy ? "Espera mientras se guarda la información." : "Los cambios se aplican al guardar."}</small>
    </div>
  </dialog>;
}
