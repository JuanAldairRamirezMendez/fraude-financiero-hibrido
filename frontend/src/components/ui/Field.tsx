interface FieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "number";
  suffix?: string;
  options?: readonly string[];
  error?: string;
  min?: number;
  max?: number;
  step?: number;
}

export function Field({
  id,
  label,
  value,
  onChange,
  type = "text",
  suffix,
  options,
  error,
  min,
  max,
  step,
}: FieldProps) {
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div className={`input-field ${error ? "field-invalid" : ""}`.trim()}>
      <label htmlFor={id}>{label}</label>
      <div className="input-wrap">
        {options ? (
          <select
            id={id}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            aria-invalid={Boolean(error)}
            aria-describedby={errorId}
          >
            {options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        ) : (
          <input
            id={id}
            type={type}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            min={min}
            max={max}
            step={step}
            inputMode={type === "number" ? "decimal" : undefined}
            aria-invalid={Boolean(error)}
            aria-describedby={errorId}
          />
        )}
        {suffix && (
          <span className="input-suffix" aria-hidden="true">
            {suffix}
          </span>
        )}
        {options && (
          <span className="select-chevron" aria-hidden="true">
            ⌄
          </span>
        )}
      </div>
      {error && (
        <span id={errorId} className="field-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
