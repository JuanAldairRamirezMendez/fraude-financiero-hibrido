import { Link } from "react-router-dom";

export function ReportsPage() {
  return (
    <section className="info-page" aria-labelledby="reports-title">
      <p className="section-kicker">Analytics</p>
      <h1 id="reports-title">Reports</h1>
      <p className="info-lead">Una vista rápida para orientar la revisión operativa del periodo actual.</p>
      <div className="info-grid">
        <article className="card info-card"><span>Fuente</span><strong>Snapshot operativo</strong><p>Indicadores y alertas disponibles desde el dashboard.</p></article>
        <article className="card info-card"><span>Detalle</span><strong>Transacciones y riesgo</strong><p>Consulta los casos individuales en el analizador.</p><Link className="button button-outline" to="/analyzer">Abrir analyzer</Link></article>
        <article className="card info-card"><span>Explicación</span><strong>Factores SHAP</strong><p>Cada evaluación incluye los principales factores que influyeron en la decisión.</p></article>
      </div>
    </section>
  );
}