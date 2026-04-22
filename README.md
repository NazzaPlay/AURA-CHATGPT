# AURA - Autonomous Unified Reasoning Assistant

AURA es una IA/app personal modular en Python, diseñada con filosofía Hextech + Raspberry Pi:
- **Poco contexto**: Módulos claros, cambios pequeños.
- **Trazabilidad con Git**: Commits atómicos, diffs verificables.
- **RN protegido**: Routing Neuron solo modificable con permiso explícito.
- **Autonomía controlada**: Auto-approve Edit activado para infraestructura segura.

## Documentación Hextech

La infraestructura Hextech proporciona una jaula de seguridad para trabajar con Auto-approve Edit:

- [Protocolo de Autonomía](docs/hextech/AUTONOMY_PROTOCOL.md) - Guía de seguridad con Auto-approve Edit activado.
- [Flujo de Trabajo Cline](docs/hextech/CLINE_WORKFLOW.md) - Metodología para tareas (Plan Mode vs Act Mode).
- [Presupuesto de Tokens](docs/hextech/TOKEN_BUDGET.md) - Optimización de contexto y uso eficiente de tokens.
- [Blueprint de Arquitectura](docs/hextech/HEXTECH_BLUEPRINT.md) - Principios, fases y zonas del proyecto.
- [Mapa Contextual](docs/hextech/CONTEXT_MAP.md) - Guía para navegar eficientemente y ahorrar tokens.
- [Límites del Routing Neuron](docs/hextech/RN_BOUNDARY.md) - Reglas de protección para el subsistema crítico.
- [Inventario Técnico](docs/hextech/PROJECT_INVENTORY.md) - Inventario técnico y mapa de riesgo operativo (H2.0).

## Estructura del proyecto

```
AURA/
├── agents/           # Agentes de IA (protegido)
├── backend/          # Backend (protegido)
├── docs/             # Documentación
│   └── hextech/      # Infraestructura Hextech
├── providers/        # Proveedores de modelos (protegido)
├── ops/              # Operaciones (protegido)
├── tests/            # Tests (protegido)
├── main.py           # Punto de entrada principal
├── config.py         # Configuración
├── aura.py           # Cliente AURA
├── memory_store.py   # Almacenamiento de memoria
├── model_runner.py   # Ejecutor de modelos
└── .clinerules       # Reglas de seguridad para Cline
```

## Reglas de seguridad

1. **No modificar código funcional** sin permiso explícito:
   - `backend/`, `agents/`, `providers/`, `ops/`, `tests/`
   - Archivos `.py` funcionales (main.py, config.py, aura.py, etc.)
   - `memory.json`, `logs/`, `.venv/`, `__pycache__/`
2. **No tocar RN** (Routing Neuron) salvo que el prompt incluya exactamente: `RN_WRITE_ALLOWED`.
3. **Siempre** iniciar tareas con `git status`.
4. **Siempre** terminar con `git diff --stat`.
5. **Minimizar tokens**: usar archivos concretos, evitar @workspace, resumir hallazgos.
6. **Zonas seguras** (modificables con Auto-approve Edit):
   - `.gitignore`, `.clinerules`, `README.md`, `docs/hextech/`

## Inicio rápido

```bash
# Clonar repositorio
git clone <url>

# Ejecutar AURA
python main.py
```

## Licencia

[Información de licencia...]

---

**Nota**: Este proyecto sigue la filosofía Hextech + Raspberry Pi: modular, simple, trazable y seguro.