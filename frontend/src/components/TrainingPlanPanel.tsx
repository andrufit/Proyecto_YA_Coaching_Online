import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  getTrainingPlan,
  saveTrainingPlan,
} from "../services/trainingPlan";

import type {
  TrainingDayWrite,
  TrainingExerciseWrite,
  TrainingPlanRead,
  TrainingPlanWrite,
} from "../services/trainingPlan";

import "./TrainingPlanPanel.css";

type Props = {
  token: string;
  clientId?: number;
};

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "No fue posible completar la operación.";
}

function newExercise(position: number): TrainingExerciseWrite {
  return {
    position,
    name: "",
    sets: 3,
    repetitions: "",
    rest_seconds: 60,
    notes: null,
  };
}

function newDay(position: number): TrainingDayWrite {
  return {
    position,
    name: `Día ${position}`,
    exercises: [newExercise(1)],
  };
}

function emptyPlan(): TrainingPlanWrite {
  return {
    title: "",
    instructions: null,
    days: [newDay(1)],
  };
}

// Extrae solo los campos que acepta el backend al guardar.
function editablePlan(plan: TrainingPlanRead): TrainingPlanWrite {
  return {
    title: plan.title,
    instructions: plan.instructions,
    days: plan.days.map((day) => ({
      position: day.position,
      name: day.name,
      exercises: day.exercises.map((exercise) => ({
        position: exercise.position,
        name: exercise.name,
        sets: exercise.sets,
        repetitions: exercise.repetitions,
        rest_seconds: exercise.rest_seconds,
        notes: exercise.notes,
      })),
    })),
  };
}

function TrainingPlanContent({ token, clientId }: Props) {
  const [plan, setPlan] = useState<TrainingPlanRead | null>(null);
  const [draft, setDraft] = useState<TrainingPlanWrite>(emptyPlan);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);

  const canEdit = clientId !== undefined;

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await getTrainingPlan(token, clientId);

        if (!active) return;

        setPlan(result);
        setDraft(result ? editablePlan(result) : emptyPlan());
      } catch (error) {
        if (active) setLoadError(errorMessage(error));
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token, clientId, retry]);

  function updateDay(
    dayIndex: number,
    changes: Partial<TrainingDayWrite>,
  ) {
    setNotice("");
    setDraft((previous) => ({
      ...previous,
      days: previous.days.map((day, index) =>
        index === dayIndex ? { ...day, ...changes } : day,
      ),
    }));
  }

  function updateExercise(
    dayIndex: number,
    exerciseIndex: number,
    changes: Partial<TrainingExerciseWrite>,
  ) {
    setNotice("");
    setDraft((previous) => ({
      ...previous,
      days: previous.days.map((day, index) =>
        index === dayIndex
          ? {
              ...day,
              exercises: day.exercises.map((exercise, position) =>
                position === exerciseIndex
                  ? { ...exercise, ...changes }
                  : exercise,
              ),
            }
          : day,
      ),
    }));
  }

  function addDay() {
    setNotice("");
    setDraft((previous) => {
      if (previous.days.length >= 7) return previous;

      return {
        ...previous,
        days: [
          ...previous.days,
          newDay(previous.days.length + 1),
        ],
      };
    });
  }

  function removeDay(dayIndex: number) {
    setNotice("");
    setDraft((previous) => ({
      ...previous,
      days: previous.days
        .filter((_, index) => index !== dayIndex)
        .map((day, index) => ({
          ...day,
          position: index + 1,
        })),
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (clientId === undefined) return;

    setBusy(true);
    setSaveError("");
    setNotice("");

    const payload: TrainingPlanWrite = {
      title: draft.title.trim(),
      instructions: draft.instructions?.trim() || null,
      days: draft.days.map((day, dayIndex) => ({
        position: dayIndex + 1,
        name: day.name.trim(),
        exercises: day.exercises.map((exercise, exerciseIndex) => ({
          position: exerciseIndex + 1,
          name: exercise.name.trim(),
          sets: exercise.sets,
          repetitions: exercise.repetitions.trim(),
          rest_seconds: exercise.rest_seconds,
          notes: exercise.notes?.trim() || null,
        })),
      })),
    };

    try {
      const saved = await saveTrainingPlan(token, clientId, payload);
      setPlan(saved);
      setDraft(editablePlan(saved));
      setNotice("Plan guardado correctamente.");
    } catch (error) {
      setSaveError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="training-panel">
      <h2>Plan de entrenamiento</h2>

      {loading ? (
        <p role="status">Consultando plan...</p>
      ) : loadError ? (
        <div>
          <p role="alert">{loadError}</p>
          <button
            type="button"
            onClick={() => {
              setLoadError("");
              setLoading(true);
              setRetry((value) => value + 1);
            }}
          >
            Reintentar
          </button>
        </div>
      ) : canEdit ? (
        <form onSubmit={submit}>
          <p>
            {plan
              ? "Edita el plan actual del cliente."
              : "Este cliente todavía no tiene un plan. Crea el primero."}
          </p>

          <fieldset disabled={busy}>
            <label>
              Nombre del plan
              <input
                value={draft.title}
                required
                minLength={2}
                maxLength={150}
                onChange={(event) => {
                  setNotice("");
                  setDraft({
                    ...draft,
                    title: event.target.value,
                  });
                }}
              />
            </label>

            <label>
              Indicaciones generales
              <textarea
                value={draft.instructions ?? ""}
                maxLength={5000}
                rows={3}
                onChange={(event) => {
                  setNotice("");
                  setDraft({
                    ...draft,
                    instructions: event.target.value,
                  });
                }}
              />
            </label>

            {draft.days.map((day, dayIndex) => (
              <div className="training-day" key={day.position}>
                <div className="training-actions">
                  <h3>Día {dayIndex + 1}</h3>
                  <button
                    type="button"
                    disabled={draft.days.length === 1}
                    onClick={() => removeDay(dayIndex)}
                  >
                    Quitar día
                  </button>
                </div>

                <label>
                  Nombre del día
                  <input
                    value={day.name}
                    required
                    minLength={2}
                    maxLength={100}
                    onChange={(event) =>
                      updateDay(dayIndex, { name: event.target.value })
                    }
                  />
                </label>

                {day.exercises.map((exercise, exerciseIndex) => (
                  <div
                    className="training-exercise"
                    key={exercise.position}
                  >
                    <h4>Ejercicio {exerciseIndex + 1}</h4>

                    <label>
                      Nombre del ejercicio
                      <input
                        value={exercise.name}
                        required
                        minLength={2}
                        maxLength={150}
                        onChange={(event) =>
                          updateExercise(dayIndex, exerciseIndex, {
                            name: event.target.value,
                          })
                        }
                      />
                    </label>

                    <div className="training-grid">
                      <label>
                        Series
                        <input
                          type="number"
                          min={1}
                          max={20}
                          step={1}
                          required
                          value={exercise.sets || ""}
                          onChange={(event) =>
                            updateExercise(dayIndex, exerciseIndex, {
                              sets: Number(event.target.value),
                            })
                          }
                        />
                      </label>

                      <label>
                        Repeticiones o duración
                        <input
                          placeholder="Ej. 8-10 o 30 segundos"
                          value={exercise.repetitions}
                          required
                          maxLength={50}
                          onChange={(event) =>
                            updateExercise(dayIndex, exerciseIndex, {
                              repetitions: event.target.value,
                            })
                          }
                        />
                      </label>

                      <label>
                        Descanso en segundos
                        <input
                          type="number"
                          min={0}
                          max={1800}
                          step={1}
                          required
                          value={exercise.rest_seconds}
                          onChange={(event) =>
                            updateExercise(dayIndex, exerciseIndex, {
                              rest_seconds: Number(event.target.value),
                            })
                          }
                        />
                      </label>
                    </div>

                    <label>
                      Indicaciones del ejercicio
                      <textarea
                        value={exercise.notes ?? ""}
                        maxLength={2000}
                        rows={2}
                        onChange={(event) =>
                          updateExercise(dayIndex, exerciseIndex, {
                            notes: event.target.value,
                          })
                        }
                      />
                    </label>

                    <button
                      type="button"
                      disabled={day.exercises.length === 1}
                      onClick={() =>
                        updateDay(dayIndex, {
                          exercises: day.exercises
                            .filter((_, index) => index !== exerciseIndex)
                            .map((item, index) => ({
                              ...item,
                              position: index + 1,
                            })),
                        })
                      }
                    >
                      Quitar ejercicio
                    </button>
                  </div>
                ))}

                <button
                  type="button"
                  disabled={day.exercises.length >= 30}
                  onClick={() =>
                    updateDay(dayIndex, {
                      exercises: [
                        ...day.exercises,
                        newExercise(day.exercises.length + 1),
                      ],
                    })
                  }
                >
                  Añadir ejercicio
                </button>
              </div>
            ))}

            <div className="training-actions">
              <button
                type="button"
                disabled={draft.days.length >= 7}
                onClick={addDay}
              >
                Añadir día
              </button>

              <button type="submit">
                {busy ? "Guardando..." : "Guardar plan"}
              </button>
            </div>
          </fieldset>

          <p>Los cambios se guardan al pulsar Guardar plan.</p>
          {saveError && <p role="alert">{saveError}</p>}
          {notice && <p role="status">{notice}</p>}
        </form>
      ) : plan ? (
        <div>
          <h3>{plan.title}</h3>

          {plan.instructions && (
            <p className="training-text">{plan.instructions}</p>
          )}

          {plan.days.map((day) => (
            <article className="training-day" key={day.id}>
              <h3>{day.name}</h3>

              {day.exercises.map((exercise) => (
                <div className="training-exercise" key={exercise.id}>
                  <h4>
                    {exercise.position}. {exercise.name}
                  </h4>

                  <p>
                    <strong>Series:</strong> {exercise.sets}
                    {" · "}
                    <strong>Repeticiones o duración:</strong>{" "}
                    {exercise.repetitions}
                    {" · "}
                    <strong>Descanso:</strong>{" "}
                    {exercise.rest_seconds} segundos
                  </p>

                  {exercise.notes && (
                    <p className="training-text">{exercise.notes}</p>
                  )}
                </div>
              ))}
            </article>
          ))}

          <p>
            Última actualización:{" "}
            {new Intl.DateTimeFormat("es-CO", {
              dateStyle: "medium",
              timeStyle: "short",
            }).format(new Date(plan.updated_at))}
          </p>
        </div>
      ) : (
        <p>Tu entrenador todavía no ha registrado un plan para ti.</p>
      )}
    </section>
  );
}

export default function TrainingPlanPanel(props: Props) {
  // Cambiar de sesión o cliente reinicia el formulario y su consulta.
  return (
    <TrainingPlanContent
      key={`${props.token}-${props.clientId ?? "me"}`}
      {...props}
    />
  );
}