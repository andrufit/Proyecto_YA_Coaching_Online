import type { FormEvent } from "react";

// Reveal collapsed groups before the browser focuses an invalid required field.
export function revealInvalidField(event: FormEvent<HTMLFormElement>) {
  if (!(event.target instanceof HTMLElement)) return;
  let parent = event.target.parentElement;
  while (parent && parent !== event.currentTarget) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
    parent = parent.parentElement;
  }
}
