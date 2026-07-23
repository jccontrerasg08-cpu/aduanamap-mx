# apps/web — Frontend (Next.js App Router)

Web pública bilingüe (es/en) que consume la API y renderiza el envelope
`data / source_trace / warnings` (tipos en `packages/schemas/ts/envelope.ts`).

```bash
npm install
npm run dev      # http://localhost:3000  (requiere la API en :8000)
npm run build    # typecheck + lint + compila rutas (sin API: degrada con avisos)
```

## Rutas

| Ruta | Pantalla |
|---|---|
| `/` | Landing + estado de la API |
| `/mapa` | Mapa mundial como **lista accesible** de países (fallback sin WebGL; MapLibre es mejora progresiva futura) |
| `/pais/[iso3]` | Perfil de país + sus instrumentos |
| `/tratado/[slug]` | Ficha de tratado (miembros, fechas, documentos fuente) |
| `/arancel` | Explorador HS/Fracción/NICO: búsqueda (`?q=`) y detalle de código (`?code=`) |
| `/calculadora` | Estimador de costo aterrizado (valor en aduana determinista; IGI/IVA `no confirmable` sin tasa) |

## Principios aplicados en la UI

- **Trazabilidad visible:** `components/Trace.tsx` muestra `source_trace` + `warnings` en cada pantalla.
- **Nunca inventa:** si la API devuelve `null` o `no confirmable`, la UI lo muestra tal cual; no rellena huecos.
- **Falla segura:** `lib/api.ts` nunca lanza; ante error de red devuelve un envelope con aviso y la página se renderiza igual.
- **Accesibilidad:** skip-link, landmarks (`<main>`), foco visible, mapa alternativo en tabla, tema claro/oscuro.
- **Bilingüe:** `lib/i18n.ts` (es por defecto, `?lang=en`); `lang` se pasa también a la API.

## Estructura

```
app/            layout (shell) + globals.css + una carpeta por ruta
components/      Shell, Nav, Disclaimer, Trace (Sources + Warnings)
lib/             api (cliente tipado con fallback), i18n, format
```
