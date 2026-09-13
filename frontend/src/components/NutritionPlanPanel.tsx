import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  getNutritionPlan,
  saveNutritionPlan,
} from "../services/nutritionPlan";
import type {
  NutritionFoodWrite,
  NutritionMealWrite,
  NutritionPlanRead,
  NutritionPlanWrite,
} from "../services/nutritionPlan";

import "./NutritionPlanPanel.css";

type Props = {
  token: string;
  clientId?: number;
};

function newFood(position: number): NutritionFoodWrite {
  return {
    position,
    name: "",
    quantity: "",
    notes: null,
  };
}

function newMeal(position: number): NutritionMealWrite {
  return {
    position,
    name: "",
    notes: null,
    foods: [newFood(1)],
  };
}

function emptyPlan(): NutritionPlanWrite {
  return {
    title: "",
    instructions: null,
    meals: [newMeal(1)],
  };
}

function editablePlan(plan: NutritionPlanRead): NutritionPlanWrite {
  return {
    title: plan.title,
    instructions: plan.instructions,
    meals: plan.meals.map((meal) => ({
      position: meal.position,
      name: meal.name,
      notes: meal.notes,
      foods: meal.foods.map((food) => ({
        position: food.position,
        name: food.name,
        quantity: food.quantity,
        notes: food.notes,
      })),
    })),
  };
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "No fue posible completar la operación.";
}

function optionalText(value: string | null): string | null {
  return value?.trim() || null;
}

export default function NutritionPlanPanel(props: Props) {
  return (
    <NutritionPlanContent
      key={`${props.token}-${props.clientId ?? "me"}`}
      {...props}
    />
  );
}

function NutritionPlanContent({ token, clientId }: Props) {
  const [plan, setPlan] = useState<NutritionPlanRead | null>(null);
  const [draft, setDraft] = useState<NutritionPlanWrite>(emptyPlan);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState(0);

  const canEdit = clientId !== undefined;

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await getNutritionPlan(token, clientId);

        if (active) {
          setPlan(result);
          setDraft(result ? editablePlan(result) : emptyPlan());
        }
      } catch (error) {
        if (active) {
          setLoadError(errorMessage(error));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token, clientId, retry]);

  function changeDraft(next: NutritionPlanWrite) {
    setDraft(next);
    setNotice("");
    setSaveError("");
  }

  function updateMeal(
    mealIndex: number,
    changes: Partial<NutritionMealWrite>,
  ) {
    changeDraft({
      ...draft,
      meals: draft.meals.map((meal, index) =>
        index === mealIndex ? { ...meal, ...changes } : meal,
      ),
    });
  }

  function updateFood(
    mealIndex: number,
    foodIndex: number,
    changes: Partial<NutritionFoodWrite>,
  ) {
    const meal = draft.meals[mealIndex];

    updateMeal(mealIndex, {
      foods: meal.foods.map((food, index) =>
        index === foodIndex ? { ...food, ...changes } : food,
      ),
    });
  }

  function removeMeal(mealIndex: number) {
    changeDraft({
      ...draft,
      meals: draft.meals
        .filter((_, index) => index !== mealIndex)
        .map((meal, index) => ({
          ...meal,
          position: index + 1,
        })),
    });
  }

  function removeFood(mealIndex: number, foodIndex: number) {
    updateMeal(mealIndex, {
      foods: draft.meals[mealIndex].foods
        .filter((_, index) => index !== foodIndex)
        .map((food, index) => ({
          ...food,
          position: index + 1,
        })),
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (clientId === undefined || busy) return;

    setBusy(true);
    setSaveError("");
    setNotice("");

    const payload: NutritionPlanWrite = {
      title: draft.title.trim(),
      instructions: optionalText(draft.instructions),
      meals: draft.meals.map((meal, mealIndex) => ({
        position: mealIndex + 1,
        name: meal.name.trim(),
        notes: optionalText(meal.notes),
        foods: meal.foods.map((food, foodIndex) => ({
          position: foodIndex + 1,
          name: food.name.trim(),
          quantity: food.quantity.trim(),
          notes: optionalText(food.notes),
        })),
      })),
    };

    try {
      const saved = await saveNutritionPlan(token, clientId, payload);
      setPlan(saved);
      setDraft(editablePlan(saved));
      setNotice("Plan nutricional guardado correctamente.");
    } catch (error) {
      setSaveError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <section className="nutrition-panel">
        <h2>Plan nutricional</h2>
        <p role="status">Cargando plan nutricional...</p>
      </section>
    );
  }

  if (loadError) {
    return (
      <section className="nutrition-panel">
        <h2>Plan nutricional</h2>
        <p className="nutrition-error" role="alert">
          {loadError}
        </p>
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
      </section>
    );
  }

  if (!canEdit) {
    return (
      <section className="nutrition-panel">
        <h2>Mi plan nutricional</h2>

        {!plan ? (
          <p>Tu entrenador todavía no ha registrado tu plan nutricional.</p>
        ) : (
          <>
            <h3>{plan.title}</h3>

            {plan.instructions && (
              <p className="nutrition-text">{plan.instructions}</p>
            )}

            {plan.meals.map((meal) => (
              <article className="nutrition-meal" key={meal.id}>
                <h3>
                  {meal.position}. {meal.name}
                </h3>

                {meal.notes && (
                  <p className="nutrition-text">{meal.notes}</p>
                )}

                <ul className="nutrition-food-list">
                  {meal.foods.map((food) => (
                    <li key={food.id}>
                      <div className="nutrition-food-heading">
                        <strong>{food.name}</strong>
                        <span>{food.quantity}</span>
                      </div>

                      {food.notes && (
                        <p className="nutrition-text">{food.notes}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </article>
            ))}

            <p className="nutrition-updated">
              Última actualización:{" "}
              {new Intl.DateTimeFormat("es-CO", {
                dateStyle: "medium",
                timeStyle: "short",
              }).format(new Date(plan.updated_at))}
            </p>
          </>
        )}
      </section>
    );
  }

  return (
    <section className="nutrition-panel">
      <h2>{plan ? "Editar plan nutricional" : "Crear plan nutricional"}</h2>
      <p>Organiza las comidas, los alimentos y sus cantidades.</p>

      <form onSubmit={submit}>
        <fieldset disabled={busy} className="nutrition-fields">
          <label>
            Título del plan
            <input
              value={draft.title}
              minLength={2}
              maxLength={150}
              required
              placeholder="Ejemplo: Plan de alimentación semanal"
              onChange={(event) =>
                changeDraft({ ...draft, title: event.target.value })
              }
            />
          </label>

          <label>
            Indicaciones generales
            <textarea
              value={draft.instructions ?? ""}
              maxLength={5000}
              rows={3}
              onChange={(event) =>
                changeDraft({
                  ...draft,
                  instructions: event.target.value,
                })
              }
            />
          </label>

          {draft.meals.map((meal, mealIndex) => (
            <fieldset className="nutrition-meal" key={mealIndex}>
              <legend>Comida {mealIndex + 1}</legend>

              <label>
                Nombre de la comida
                <input
                  value={meal.name}
                  minLength={2}
                  maxLength={100}
                  required
                  placeholder="Ejemplo: Desayuno"
                  onChange={(event) =>
                    updateMeal(mealIndex, { name: event.target.value })
                  }
                />
              </label>

              <label>
                Notas de la comida
                <textarea
                  value={meal.notes ?? ""}
                  maxLength={2000}
                  rows={2}
                  onChange={(event) =>
                    updateMeal(mealIndex, { notes: event.target.value })
                  }
                />
              </label>

              {meal.foods.map((food, foodIndex) => (
                <div className="nutrition-food-editor" key={foodIndex}>
                  <h4>Alimento {foodIndex + 1}</h4>

                  <div className="nutrition-grid">
                    <label>
                      Alimento
                      <input
                        value={food.name}
                        minLength={2}
                        maxLength={150}
                        required
                        placeholder="Ejemplo: Arroz"
                        onChange={(event) =>
                          updateFood(mealIndex, foodIndex, {
                            name: event.target.value,
                          })
                        }
                      />
                    </label>

                    <label>
                      Cantidad
                      <input
                        value={food.quantity}
                        maxLength={100}
                        required
                        placeholder="Ejemplo: 120 g cocidos"
                        onChange={(event) =>
                          updateFood(mealIndex, foodIndex, {
                            quantity: event.target.value,
                          })
                        }
                      />
                    </label>
                  </div>

                  <label>
                    Notas del alimento
                    <textarea
                      value={food.notes ?? ""}
                      maxLength={2000}
                      rows={2}
                      onChange={(event) =>
                        updateFood(mealIndex, foodIndex, {
                          notes: event.target.value,
                        })
                      }
                    />
                  </label>

                  <button
                    className="nutrition-remove"
                    type="button"
                    disabled={meal.foods.length <= 1}
                    onClick={() => removeFood(mealIndex, foodIndex)}
                  >
                    Quitar alimento
                  </button>
                </div>
              ))}

              <div className="nutrition-actions">
                <button
                  type="button"
                  disabled={meal.foods.length >= 30}
                  onClick={() =>
                    updateMeal(mealIndex, {
                      foods: [
                        ...meal.foods,
                        newFood(meal.foods.length + 1),
                      ],
                    })
                  }
                >
                  Agregar alimento
                </button>

                <button
                  className="nutrition-remove"
                  type="button"
                  disabled={draft.meals.length <= 1}
                  onClick={() => removeMeal(mealIndex)}
                >
                  Quitar comida
                </button>
              </div>
            </fieldset>
          ))}

          <div className="nutrition-actions">
            <button
              type="button"
              disabled={draft.meals.length >= 10}
              onClick={() =>
                changeDraft({
                  ...draft,
                  meals: [
                    ...draft.meals,
                    newMeal(draft.meals.length + 1),
                  ],
                })
              }
            >
              Agregar comida
            </button>

            <button className="nutrition-save" type="submit">
              {busy ? "Guardando..." : "Guardar plan nutricional"}
            </button>
          </div>
        </fieldset>

        {saveError && (
          <p className="nutrition-error" role="alert">
            {saveError}
          </p>
        )}

        {notice && (
          <p className="nutrition-success" role="status">
            {notice}
          </p>
        )}
      </form>
    </section>
  );
}