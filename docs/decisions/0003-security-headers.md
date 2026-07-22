# ADR 0003 — Cabeceras de seguridad HTTP

- **Estado:** aceptado
- **Fecha:** 2026-07-21

## Contexto

El informe exige (Fase 4 / checklist de seguridad) CSP, HSTS, `X-Content-Type-Options`,
`Referrer-Policy`, `Permissions-Policy` y `frame-ancestors`. Es de las mejoras de mayor
relación valor/esfuerzo en seguridad web.

El patrón concreto se tomó del **catálogo de conocimiento** del autor
(`Obsidian Catalogue/Juca Projects → Wiki/Security & Cybersecurity → Security Headers`),
alineado con [OWASP Top Ten](https://owasp.org/www-project-top-ten/) y
[OWASP Secure Headers](https://owasp.org/www-project-secure-headers/). Ver
[docs/references.md](../references.md).

## Decisión

Un `SecurityHeadersMiddleware` ([apps/api/app/security.py](../../apps/api/app/security.py))
añade las cabeceras a **toda** respuesta (registrado como middleware más externo, por lo que
cubre también 429 y preflights CORS). Dos concesiones deliberadas:

1. **HSTS solo en producción** (`APP_ENV=production`). En localhost sobre http fijaría el
   navegador a https por error.
2. **CSP permite el CDN jsDelivr** que usa Swagger UI (`/docs`), para no romper la
   documentación interactiva. Las respuestas JSON no se ejecutan en el navegador, así que la
   CSP protege sobre todo la página de docs.

Las cabeceras usan `setdefault`: si una ruta necesita anular una, puede hacerlo sin pelear
con el middleware (degradación/override elegante).

## Consecuencias

- (+) Base de seguridad presente por defecto, sin tocar cada endpoint.
- (+) Cierra el ítem de Fase 4 "Headers CSP/HSTS".
- (−) Si en el futuro la web pública se sirviera desde el mismo origen que la API con scripts
  de terceros, habría que revisar la CSP. Hoy web y API están separadas.
