export function SettingsPage() {
  return (
    <section className="info-page" aria-labelledby="settings-title">
      <p className="section-kicker">Administration</p>
      <h1 id="settings-title">Settings</h1>
      <p className="info-lead">Estado de la configuración activa del entorno.</p>
      <div className="card settings-list">
        <div><span>API</span><strong>Conectada</strong><em className="settings-ok">●</em></div>
        <div><span>Modelo</span><strong>XGBoost calibrado</strong><em>Producción</em></div>
        <div><span>Explicabilidad</span><strong>SHAP habilitado</strong><em>Activo</em></div>
        <div><span>Asistente</span><strong>Gemini</strong><em>Disponible con API key</em></div>
      </div>
    </section>
  );
}