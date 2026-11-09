function escapeCell(value: string): string {
  // Mitiga inyección de fórmulas en hojas de cálculo.
  const guarded = /^[=+\-@\t\r]/.test(value) ? `'${value}` : value;
  return `"${guarded.replaceAll('"', '""')}"`;
}

/** Serializa filas a CSV escapando comillas e inyección de fórmulas. */
export function toCsv(rows: ReadonlyArray<ReadonlyArray<string>>): string {
  const csv = rows.map((row) => row.map(escapeCell).join(",")).join("\r\n");
  return `\uFEFF${csv}`;
}

/** Genera y descarga un CSV escapando comillas e inyección de fórmulas. */
export function downloadCsv(filename: string, rows: ReadonlyArray<ReadonlyArray<string>>): void {
  const blob = new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
