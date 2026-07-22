# ADR 0001 — Scaffold lean (3 procesos, no microservicios)

- **Estado:** aceptado
- **Fecha:** 2026-07-20

## Contexto

Se propuso un monorepo con ~15 "services", 6 adaptadores LLM, RAG completo, Elastic + Meilisearch +
vector search, Kubernetes y Terraform desde el día 1. El deep research report, en cambio, recomienda un
MVP en 4 fases y explícitamente **no** intentar cobertura legal total al inicio.

## Decisión

Empezar con **tres procesos**: `web`, `api`, `workers`. Todo lo demás son *módulos* dentro de ellos, no
unidades de despliegue. Una carpeta se crea el día que el código llega, no antes.

Recortes deliberados para Fase 1:
- **Un** abstractor LLM + una implementación (Claude), no seis proveedores.
- Búsqueda: Postgres `tsvector` (default del report), no tres motores.
- RAG / k8s / terraform: diferidos.

## Consecuencias

- (+) Menos superficie que mantener; el MVP llega antes.
- (+) La estructura del report (`apps/web`, `apps/api`, `apps/workers`, `packages/schemas`) crece sin reestructurar.
- (−) Migrar a microservicios más tarde requerirá extraer módulos — aceptable y localizado.
