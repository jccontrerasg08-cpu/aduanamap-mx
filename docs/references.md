# Referencias y buenas prácticas aplicadas

Este documento traza **de dónde** vienen las decisiones de ingeniería del proyecto.
Las fuentes se curaron del catálogo de conocimiento del autor
(`Obsidian Catalogue/Juca Projects`: wikis de _Frameworks_, _Databases &
Infrastructure_, _Security & Cybersecurity_, _Learning/Awesome Lists_) y de dos
proyectos hermanos del mismo dominio aduanero (`cfe-bot`, `customs-dashboard`).

## Aplicado ya en el código

| Práctica | Fuente / repo | Dónde se usa |
|---|---|---|
| Cabeceras de seguridad HTTP (CSP, HSTS, nosniff, frame-ancestors…) | [OWASP Top Ten](https://github.com/OWASP/Top10) · [OWASP Secure Headers](https://owasp.org/www-project-secure-headers/) · Wiki/Security → "Security Headers" | [apps/api/app/security.py](../apps/api/app/security.py) · [ADR 0003](decisions/0003-security-headers.md) |
| Rate limiting 429 + `Retry-After` | OWASP (Availability & Abuse) · Wiki/Security → "API Security" | [apps/api/app/ratelimit.py](../apps/api/app/ratelimit.py) |
| Validación estricta de entrada (Pydantic + regex) | Wiki/Frameworks → FastAPI · Wiki/Security → "Input Validation" | routers `calculator`, `classify`, `countries`, `agreements`, `banxico`, `wiki` |
| Secrets solo por entorno; logs sin secretos | Wiki/Security → "Secrets Management" | [config.py](../apps/api/app/config.py) · [logging.py](../apps/api/app/logging.py) |
| Docstring/description en cada archivo | Convención del vault (cfe-bot, customs-dashboard: todos sus módulos abren con docstring) | todo el árbol de código |
| ETL con dato semilla y fallback a snapshot previo | Patrón de [`customs-dashboard/ingest.py`](../..) (seed CSV → SQLite; mapea INEGI real después) | [workers/common/source_job.py](../workers/common/source_job.py) |
| Caché con invalidación como fallback | Patrón de [`cfe-bot/account_pool.py`](../..) (caché RPU→email, se auto-limpia si queda inválido) | [apps/api/app/cache.py](../apps/api/app/cache.py) + fallbacks de Banxico |
| Reutilización de listas "awesome" para elección de stack | [awesome-python](https://github.com/vinta/awesome-python) · [awesome-docker](https://github.com/veggiemonk/awesome-docker) | stack `api`/`workers`/`infra` |

## Earmarked para fases siguientes (con repo de referencia)

| Necesidad futura | Repo / recurso de buenas prácticas |
|---|---|
| Parser de PDF del DOF (decretos) con fallback robusto | [opendataloader-project/opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) · idea del vault "AI PDF Parser" |
| Frontend Next.js (mapa, país, tratado, calculadora) | [unicodeveloper/awesome-nextjs](https://github.com/unicodeveloper/awesome-nextjs) · [vitejs/awesome-vite](https://github.com/vitejs/awesome-vite) |
| Dashboard operativo / freshness de fuentes | [obazoud/awesome-dashboard](https://github.com/obazoud/awesome-dashboard) · Wiki "Dashboards & Data Apps" |
| Escaneo de dependencias / contenedores (DevSecOps) | [sbilly/awesome-security](https://github.com/sbilly/awesome-security) · Trivy/Semgrep (Wiki/Databases → Security Scanning) |
| Sysadmin / observabilidad de despliegue | [awesome-foss/awesome-sysadmin](https://github.com/awesome-foss/awesome-sysadmin) · [wmariuss/awesome-devops](https://github.com/wmariuss/awesome-devops) |
| Fundamentos (por qué Redis/DB se comportan así) | [build-your-own.org/redis](https://build-your-own.org/redis) · [build-your-own.org/database](https://build-your-own.org/database/) |

## Principio de traza

Igual que cada respuesta de la API lleva su `source_trace`, cada práctica no trivial
del repo debería poder rastrearse hasta una fuente. Cuando adoptes un patrón nuevo,
añádelo aquí con su enlace.
