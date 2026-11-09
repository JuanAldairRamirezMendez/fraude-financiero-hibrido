---
name: Engineering Practices
description: Guia transversal para Git, documentacion, testing, codigo limpio, deuda tecnica y privacidad en este proyecto.
---

# Engineering Practices

Usa esta skill en cualquier cambio transversal o antes de cerrar una fase.

## Reglas obligatorias
- Commits atomicos con Conventional Commits; PR con contexto, pruebas y riesgos.
- Documenta decisiones relevantes como ADR y mantén README/comandos actualizados.
- Aplica piramide de pruebas y agrega regresion por cada bug.
- Prefiere nombres claros y funciones pequenas; no uses `any` ni `@ts-ignore`.
- Registra deuda tecnica con impacto y prioridad, no como lista infinita.
- Minimiza datos; no agregues PII y trata `customer_id` como seudonimizado.
- Revisa GDPR y Ley 29733 para retencion, acceso y eliminacion.

## Checklist de PR
- [ ] CI verde y commit describe una sola intencion.
- [ ] Documentacion y ADR actualizados si aplica.
- [ ] Tests cubren happy path, limites y errores.
- [ ] No hay secretos, PII nueva ni cambios sin migracion.
- [ ] Accesibilidad y seguridad revisadas.

## Comandos
`git diff --check`, `git status`, tests del area y la verificacion completa del proyecto.
