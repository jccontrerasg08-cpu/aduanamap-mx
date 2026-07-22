# ADR 0002 — Frontera de la capa de IA

- **Estado:** aceptado
- **Fecha:** 2026-07-20

## Contexto

La regla no negociable del producto: *si una preferencia o tasa no puede confirmarse con fuente
estructurada, marcar como `no confirmable` y mostrar la fuente primaria*. Una arquitectura centrada en
"agentes que responden" tienta a generar respuestas donde el dominio exige búsquedas deterministas.

## Decisión

`ai/` puede: **sugerir clasificación** y **buscar en lenguaje natural** sobre el corpus indexado.
`ai/` **no puede**: calcular tasas, aranceles, DTA, IVA ni resolver reglas de origen.

Refuerzo estructural: `ai/` no importa la lógica de tarifas de la calculadora. La calculadora consulta
`tariff_rate` / `rule_of_origin` directamente y devuelve `not_confirmable` cuando falta fuente.

## Consecuencias

- (+) La confianza del usuario se basa en trazabilidad, no en fluidez del modelo.
- (+) Escala aunque cambien las páginas de ANAM/SNICE/VUCEM/DOF.
- (−) La UX de clasificación es "sugerencia + validación humana", no respuesta definitiva. Es intencional.
