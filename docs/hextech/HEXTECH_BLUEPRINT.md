# Blueprint de Arquitectura Hextech

## Propósito

La arquitectura Hextech proporciona una jaula de seguridad y metodología para trabajar con Auto-approve Edit activado en AURA. Combina filosofía Raspberry Pi (módulos claros, cambios pequeños) con trazabilidad Git para permitir autonomía controlada.

## Principios Fundamentales

### 1. Mentalidad Raspberry Pi
- **Módulos claros**: Cada componente tiene responsabilidad única y bien definida
- **Cambios pequeños**: Modificaciones atómicas y verificables
- **Interfaces simples**: Comunicación entre módulos a través de APIs claras

### 2. Mínimo Contexto
- Leer solo archivos necesarios para la tarea actual
- Evitar `@workspace` y exploraciones recursivas innecesarias
- Usar `CONTEXT_MAP.md` como guía para navegar el proyecto

### 3. Git como Caja Negra
- **Antes de cada tarea**: `git status` para conocer estado inicial
- **Durante la tarea**: Cambios pequeños y enfocados
- **Después de cada tarea**: `git diff --stat` para ver resumen de cambios
- **Commit condicional**: Solo si cambios son correctos y limitados a zonas seguras

### 4. RN Protegido
- **Regla absoluta**: Consulta [RN_BOUNDARY.md](RN_BOUNDARY.md) para las reglas completas de protección RN
- **Referencia sensible**: `docs/routing_neuron_v1_checkpoint.md` es solo lectura
- **Auditoría permitida**: Leer, analizar imports, reportar riesgos
- **⚠️ NOTA**: Este documento NO define reglas de seguridad RN. La única fuente de verdad para seguridad RN es [RN_BOUNDARY.md](RN_BOUNDARY.md).

### 5. Cambios Pequeños y Verificables
- Una tarea = un objetivo claro
- Scope definido: archivos específicos a modificar
- Criterio de éxito explícito

## Fases Actuales del Proyecto

### H0: Auditoría
- Análisis inicial de estructura del proyecto
- Identificación de zonas seguras y peligrosas
- Establecimiento de reglas base (.clinerules)

### H1: Jaula/Documentación
- Creación de documentación Hextech
- Definición de protocolos de seguridad
- Establecimiento de flujos de trabajo controlados
- **Esta fase incluye**: AUTONOMY_PROTOCOL.md, CLINE_WORKFLOW.md *(no implementado aún)*, TOKEN_BUDGET.md *(no implementado aún)*, HEXTECH_BLUEPRINT.md, CONTEXT_MAP.md, RN_BOUNDARY.md

### H2: Reorganización Controlada
- Reestructuración de carpetas solo con plan aprobado
- Migraciones controladas con validación paso a paso
- Mantenimiento de compatibilidad hacia atrás

## Zonas del Proyecto

### 1. Núcleo AURA
- `main.py` - Punto de entrada principal
- `aura.py` - Cliente AURA
- `config.py` - Configuración del sistema
- `memory_store.py` - Almacenamiento de memoria
- `model_runner.py` - Ejecutor de modelos

### 2. Agentes
- `agents/` - Todos los agentes de IA
- **Protegido**: No modificar sin permiso explícito

### 3. Runtime/Modelos
- `model_runner.py` - Ejecutor de modelos
- `providers/` - Proveedores de modelos
- `agents/model_*.py` - Agentes relacionados con modelos

### 4. Memoria
- `memory_store.py` - Almacenamiento de memoria
- `memory.json` - Estado persistente
- **Protegido**: No modificar memory.json

### 5. Ops
- `ops/` - Operaciones y registros
- `ops/assistant_ops_registry.json` - Registro de operaciones
- `validate_sync.py` - Herramienta de validación Ops (dev_tool) — solo lectura de archivos; ejecuta consultas RN

### 6. RN (Routing Neuron)
- `backend/app/routing_neuron/` - Implementación de RN
- `agents/routing_*.py` - Agentes de routing
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de referencia
- **Evolución conceptual**: RN evoluciona hacia RN Family / Routing Neuron Mesh, una arquitectura modular de subsistemas especializados documentada en RN_FAMILY.md. RN Core V1.8 permanece como núcleo sellado protegido por RN_WRITE_ALLOWED.

### 7. Documentación
- `docs/` - Documentación general
- `docs/hextech/` - Infraestructura Hextech
- **Zona segura**: Modificable con Auto-approve Edit

### 8. Tests
- `tests/` - Tests automatizados
- **Protegido**: No modificar sin permiso explícito

## Reglas de Seguridad

### Regla de Reorganización
- **No mover carpetas completas** sin plan aprobado
- **No renombrar módulos críticos** sin validación
- **Mantener compatibilidad** hacia atrás en cambios estructurales

### Regla de Contexto
- **Minimizar tokens**: usar archivos concretos, evitar @workspace
- **Resumir hallazgos**: no pegar contenido largo innecesariamente
- **Dividir tareas grandes** en subtareas manejables

### Regla de Auto-approve
- **Zonas seguras**: .gitignore, .clinerules, README.md, docs/hextech/
- **Zonas peligrosas**: backend/, agents/, providers/, ops/, tests/, logs/, .venv/, __pycache__/, memory.json, archivos .py funcionales (main.py, config.py, aura.py, etc.)
- **Verificación**: Siempre usar `git diff --stat` para confirmar cambios

## Flujo de Trabajo Hextech

1. **Plan Mode**: Explorar archivos, entender contexto, proponer plan
2. **Aprobación**: Usuario aprueba plan
3. **Act Mode**: Implementar cambios en zonas seguras
4. **Verificación**: `git diff --stat` para resumen de cambios
5. **Commit**: Si todo correcto, commit con mensaje descriptivo
6. **Reporte**: Resumen final con archivos modificados y estado Git

## Próximos Pasos

1. **Completar H1**: Terminar documentación Hextech faltante
2. **Validar jaula**: Asegurar que todas las reglas están documentadas
3. **Preparar H2**: Diseñar plan para reorganización controlada

---

**Nota**: Este blueprint es la base de la jaula de seguridad Hextech. Todas las tareas deben alinearse con estos principios para mantener autonomía controlada y seguridad.