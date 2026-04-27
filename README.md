# AURA - Autonomous Unified Reasoning Assistant

AURA es una IA/app personal modular en Python, diseñada con filosofía Hextech + Raspberry Pi:
- **Poco contexto**: Módulos claros, cambios pequeños.
- **Trazabilidad con Git**: Commits atómicos, diffs verificables.
- **RN protegido**: Routing Neuron solo modificable con permiso explícito.
- **Autonomía controlada**: Auto-approve Edit activado para infraestructura segura.

## Documentación Hextech

La infraestructura Hextech proporciona una jaula de seguridad para trabajar con Auto-approve Edit:

- [Protocolo de Autonomía](docs/hextech/AUTONOMY_PROTOCOL.md) - Guía de seguridad con Auto-approve Edit activado.
- [Plan de Self-Work / Integración RN](docs/hextech/RN_SELF_WORK_PLAN.md) - Plan maestro para que AURA pueda auto-trabajarse de forma segura (H3.0).
- [Flujo de Trabajo Cline](docs/hextech/CLINE_WORKFLOW.md) - Metodología para tareas (Plan Mode vs Act Mode) *(no implementado aún)*
- [Presupuesto de Tokens](docs/hextech/TOKEN_BUDGET.md) - Optimización de contexto y uso eficiente de tokens *(no implementado aún)*
- [Blueprint de Arquitectura](docs/hextech/HEXTECH_BLUEPRINT.md) - Principios, fases y zonas del proyecto.
- [Mapa Contextual](docs/hextech/CONTEXT_MAP.md) - Guía para navegar eficientemente y ahorrar tokens.
- [Límites del Routing Neuron](docs/hextech/RN_BOUNDARY.md) - Reglas de protección para el subsistema crítico **(única fuente de verdad para seguridad RN)**.
- [Inventario Técnico](docs/hextech/PROJECT_INVENTORY.md) - Inventario técnico y mapa de riesgo operativo (H2.0).
- [RN Family / Routing Neuron Mesh](docs/hextech/RN_FAMILY.md) - Arquitectura modular conceptual alrededor de RN Core.
- [Protocolo DEV-CLEANUP](docs/hextech/DEV_CLEANUP_PROTOCOL.md) - Limpieza de estado vivo durante desarrollo activo.

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

Para las reglas de seguridad completas y ejecutables, consulta:
- [`.clinerules`](.clinerules) - Reglas operativas para Cline
- [`AUTONOMY_PROTOCOL.md`](docs/hextech/AUTONOMY_PROTOCOL.md) - Filosofía de autonomía controlada
- [`RN_BOUNDARY.md`](docs/hextech/RN_BOUNDARY.md) - Reglas absolutas de protección RN (única fuente de verdad)

**Principios clave:**
1. **No tocar RN** sin `RN_WRITE_ALLOWED` en el prompt
2. **Siempre** iniciar tareas con `git status`
3. **Siempre** terminar con `git diff --stat`
4. **Minimizar tokens**: usar archivos concretos, evitar @workspace, resumir hallazgos

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