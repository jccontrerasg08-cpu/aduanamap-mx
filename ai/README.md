# ai/ — capa de IA (deliberadamente estrecha y *fundamentada*)

Asistente especializado en comercio exterior de México. Sigue la decisión final del
informe: **"producto de datos verificables, no una app de IA que adivina"**.

**Alcance permitido:** responder y buscar en lenguaje natural sobre el **corpus canónico
del repo** (TLC, países), citando la fuente; y sugerir clasificación con `confidence`.

**Prohibido:** afirmar tasas, aranceles, DTA, IVA o reglas de origen. Eso es consulta
determinista contra tablas versionadas (ver [ADR 0002](../docs/decisions/0002-ai-boundary.md)).
El asistente responde `no confirmable` y remite a `/arancel` y `/calculadora`.

## Cómo está fundamentado

```
data/seed/agreements.json  ─┐
                            ├─▶ knowledge.py  (carga; resuelve país por nombre/ISO/alias)
countries-50m.geojson ──────┘        │
                                     ▼
                              assistant.py  (intención → recupera → responde + cita)
                                     │
                        apps/api/app/routers/assistant.py
                                     │
                            POST /api/assistant/ask  →  web /asistente
```

- **Sin base de datos y sin LLM**: lee los seeds del repo, así que funciona (y se prueba)
  incluso con la infraestructura caída. La degradación elegante es requisito, no extra.
- **No puede inventar**: solo afirma lo que existe en `knowledge.py`. Si el país no está en
  el catálogo, lo dice; si piden una tasa, la rechaza explícitamente.
- **Un LLM es opcional y nunca es la fuente de verdad**: si se configura, solo reformula los
  mismos hechos ya recuperados. `llm.py` mantiene un único abstractor (Claude por defecto).
- **Frontera estructural**: `ai/` vive en la raíz del monorepo y **no importa** nada de
  `apps/api/app/services/` — no puede alcanzar la lógica de la calculadora.

## Qué sabe responder hoy

| Pregunta | Comportamiento |
|---|---|
| "¿México tiene TLC con Japón?" | Lista el AAE bilateral **y** el CPTPP, con fecha de vigencia |
| "¿TLC con Alemania?" | Resuelve vía los 27 miembros del TLCUEM |
| "¿Cuántos TLC tiene México?" | 13 vigentes / 52 países socios **+ el desacuerdo SE 14 vs ANAM 12** |
| "Háblame del T-MEC" | Miembros, firma, vigencia, notas |
| "¿México tiene TLC con Rusia?" | "No tiene TLC vigente" + advertencia de cobertura |
| "¿Cuánto arancel pago…?" | **Se niega**: `no confirmable` + remite a las herramientas deterministas |

```
ai/
├── knowledge.py    # base de conocimiento canónica (sin DB/LLM)
├── assistant.py    # Q&A fundamentado es/en
├── llm.py          # UN abstractor de proveedor (opcional)
└── prompts/system.md
```

Pruebas: `tests/ai/test_assistant.py` (21 casos, incluidos los de "nunca inventa").
