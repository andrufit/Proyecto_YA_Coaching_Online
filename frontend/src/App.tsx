import { useEffect, useState } from "react";

import "./App.css";

type HealthResponse = {
  status: string;
  message: string;
};

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const response = await fetch(`${API_URL}/health`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Error HTTP ${response.status}`);
        }

        const data: HealthResponse = await response.json();
        setHealth(data);
      } catch (requestError) {
        if (
          requestError instanceof DOMException &&
          requestError.name === "AbortError"
        ) {
          return;
        }

        setError("No se pudo conectar con el backend.");
      }
    }

    checkBackend();

    return () => controller.abort();
  }, []);

  return (
    <main>
      <h1>Y&A Coaching Online</h1>
      <p>Frontend React funcionando correctamente.</p>

      <section>
        <h2>Estado del sistema</h2>

        {!health && !error && <p>Comprobando conexión...</p>}

        {health && (
          <>
            <p>Backend conectado correctamente.</p>
            <p>Estado: {health.status}</p>
            <p>{health.message}</p>
          </>
        )}

        {error && <p>{error}</p>}
      </section>
    </main>
  );
}

export default App;