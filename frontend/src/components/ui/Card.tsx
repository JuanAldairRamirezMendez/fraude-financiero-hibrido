import type { HTMLAttributes } from "react";

export function Card({ className = "", ...rest }: HTMLAttributes<HTMLElement>) {
  return <section className={`card ${className}`.trim()} {...rest} />;
}
