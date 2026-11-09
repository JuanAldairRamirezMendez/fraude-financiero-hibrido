import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "outline" | "warning";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({
  variant = "primary",
  type = "button",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button type={type} className={`button button-${variant} ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
