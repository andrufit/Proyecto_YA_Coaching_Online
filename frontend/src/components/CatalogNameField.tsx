import { useId, useRef, useState } from "react";
import type { CatalogGroup } from "./PlanCatalogs";
import "./CatalogNameField.css";

type Props = {
  groups: CatalogGroup[];
  categoryLabel: string;
  itemLabel: string;
  value: string;
  onChange: (name: string) => void;
};

export default function CatalogNameField({ groups, categoryLabel, itemLabel, value, onChange }: Props) {
  const initialGroup = groups.find(group => group.items.includes(value));
  const [category, setCategory] = useState(initialGroup?.id ?? "");
  const nameInput = useRef<HTMLInputElement>(null);
  const hintId = useId();
  const visibleGroups = category ? groups.filter(group => group.id === category) : groups;
  const visibleNames = visibleGroups.flatMap(group => group.items);
  const inCatalog = groups.some(group => group.items.includes(value));
  // Retain a saved/custom name when filtering. Category changes never erase a plan.
  const showCurrent = value !== "" && !visibleNames.includes(value);

  return <div className="catalog-name-field">
    <div className="catalog-selectors">
      <label>{categoryLabel}
        <select value={category} onChange={event => setCategory(event.target.value)}>
          <option value="">Todas las categorías</option>
          {groups.map(group => <option key={group.id} value={group.id}>{group.label}</option>)}
        </select>
      </label>
      <label>{itemLabel} del catálogo
        <select value={value || ""} onChange={event => {
          if (event.target.value === "__manual__") {
            // Preserve the current name so it can also be adapted manually.
            nameInput.current?.focus();
            nameInput.current?.select();
          } else {
            onChange(event.target.value);
          }
        }}>
          <option value="" disabled>Selecciona una opción</option>
          <option value="__manual__">Otro: escribir manualmente</option>
          {showCurrent && <optgroup label={inCatalog ? "Selección actual" : "Personalizado"}><option value={value}>{value}</option></optgroup>}
          {visibleGroups.map(group => <optgroup key={group.id} label={group.label}>
            {group.items.map(name => <option key={name} value={name}>{name}</option>)}
          </optgroup>)}
        </select>
      </label>
    </div>
    <label>Nombre del {itemLabel.toLowerCase()} (editable)
      <input ref={nameInput} value={value} required minLength={2} maxLength={150}
        aria-describedby={hintId} placeholder={`Selecciona o escribe un ${itemLabel.toLowerCase()}`}
        onChange={event => onChange(event.target.value)} />
    </label>
    <small id={hintId}>Puedes elegir del catálogo o escribir tu propia opción. Se guardará en este plan.</small>
  </div>;
}
