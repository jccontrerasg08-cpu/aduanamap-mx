# ai/ — capa de IA (deliberadamente estrecha)

**Alcance permitido:** sugerencia de clasificación (HS/fracción con `confidence` + "por qué") y
búsqueda en lenguaje natural sobre el corpus indexado.

**Prohibido:** calcular tasas, aranceles, DTA, IVA o reglas de origen. Eso es consulta determinista
contra tablas versionadas (ver [ADR 0002](../docs/decisions/0002-ai-boundary.md)).

Un solo agente + tools + prompts en Fase 1. Se especializa solo cuando un planner único falle de forma
demostrable — no antes.

```
ai/
├── agent.py        # un agente; orquesta tools
├── llm.py          # UN abstractor de proveedor (default: Claude)
├── tools/          # conectores de solo-lectura al dominio
└── prompts/
    └── system.md
```
