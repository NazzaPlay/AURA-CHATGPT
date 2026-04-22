# Inventario Técnico Hextech - AURA H2.0

## Resumen ejecutivo

**Objetivo**: Este documento sirve como inventario técnico de AURA y mapa de riesgo operativo para la fase H2.0. Proporciona una visión completa de la estructura del proyecto, identifica zonas de riesgo y establece reglas de seguridad para trabajo con Auto-approve Edit activado.

**Fase actual**: H2.0 - Inventario técnico (post H1.5)
**Fecha de creación**: 22/4/2026
**Nota**: Este inventario fue creado durante H2.0. Los estados Git mencionados reflejan el momento de creación y pueden quedar obsoletos con commits posteriores.

## Estado del repositorio (al momento de creación)

- **Rama actual**: main (al momento de creación)
- **Último commit**: b3704c8 - H1.5 verificar consistencia de jaula Hextech (commit base para H2.0)
- **Estado**: Nothing to commit, working tree clean (al momento de creación)
- **Nota**: Esta información refleja el estado Git durante la creación del inventario H2.0 y puede quedar obsoleta con commits posteriores.

## Mapa de zonas de riesgo

### Zonas seguras (modificables con Auto-approve Edit)
- `docs/hextech/` - Documentación de infraestructura Hextech
- `.gitignore` - Reglas de exclusión de Git
- `.clinerules` - Reglas de seguridad para Cline
- `README.md` - Documentación principal (solo agregar enlaces Hextech)

### Zonas protegidas (NO modificar sin permiso explícito)
- `agents/` - Agentes de IA (39 archivos Python)
- `backend/` - Backend del sistema
- `providers/` - Proveedores de modelos
- `ops/` - Operaciones y registros
- `tests/` - Tests automatizados

### Zonas críticas (protección absoluta - RN)
- `backend/app/routing_neuron/` - Implementación canónica de Routing Neuron
- `agents/routing_*.py` - Agentes especializados en routing
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de referencia (solo lectura)

### Zonas prohibidas (NUNCA modificar)
- `memory.json` - Estado persistente del sistema
- `logs/` - Logs de sesión
- `.venv/` - Entorno virtual Python
- `__pycache__/` - Cachés de Python
- Archivos `.py` funcionales (main.py, config.py, aura.py, memory_store.py, model_runner.py, etc.)

## Inventario de módulos

### Agentes (39 archivos - zona protegida)
- **Agentes de routing**: routing_maintenance.py, routing_neuron_registry.py, routing_observer.py, routing_policy.py, routing_runtime.py, routing_scorer.py
- **Agentes core**: core_agent.py, chat_agent.py, memory_agent.py, system_state_agent.py
- **Agentes de herramientas**: internal_tools_agent.py, internal_tools_registry.py, internal_actions_agent.py, internal_actions_registry.py
- **Agentes especializados**: behavior_agent.py, capabilities_agent.py, consistency_agent.py, feasibility_agent.py, maintenance_agent.py, operations_agent.py, profile_agent.py, response_agent.py, router_agent.py, task_classifier.py
- **Registros**: capabilities_registry.py, model_registry.py, tools_registry.py, internal_sequences_registry.py
- **Utilidades**: capability_dispatcher.py, critic_layer.py, fallback_manager.py, model_benchmark.py, model_gateway.py, response_composer.py, runtime_quality.py, text_matching.py

### Backend (zona protegida)
- `backend/app/` - Aplicación backend
  - `routing_neuron/` - Implementación canónica de RN (zona crítica)
  - `blueprint/` - Referencia canónica interna

### Providers (zona protegida)
- `base_provider.py` - Clase base para proveedores
- `local_llama_provider.py` - Proveedor local Llama

### Ops (zona protegida)
- `assistant_ops_registry.json` - Registro de operaciones
- `execution_log.md` - Log de ejecución
- `task_queue.md` - Cola de tareas

### Tests (zona protegida)
- `test_operational_supervisor.py` - Tests de supervisión operacional
- `test_routing_neuron_subsystem.py` - Tests del subsistema RN
- `test_v030_internal_tools.py` - Tests de herramientas internas v0.3.0

### Documentación (zona segura)
- `docs/hextech/` - Infraestructura Hextech
  - `AUTONOMY_PROTOCOL.md` - Protocolo de autonomía
  - `CONTEXT_MAP.md` - Mapa contextual para navegación eficiente
  - `HEXTECH_BLUEPRINT.md` - Blueprint de arquitectura
  - `RN_BOUNDARY.md` - Límites del Routing Neuron
  - `PROJECT_INVENTORY.md` - Este documento
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de RN (solo lectura)

## RN (Routing Neuron) - Análisis de riesgo

### Estado actual
- **Versión**: V1.8 (subsistema canónico ya sellado)
- **Ubicación canónica**: `backend/app/routing_neuron/`
- **Documentación de referencia**: `docs/routing_neuron_v1_checkpoint.md` (legacy, solo lectura)

### Archivos relacionados
- `backend/app/routing_neuron/` - Implementación principal
- `agents/routing_maintenance.py` - Mantenimiento de RN
- `agents/routing_neuron_registry.py` - Registro de RN
- `agents/routing_observer.py` - Observador de RN
- `agents/routing_policy.py` - Políticas de routing
- `agents/routing_runtime.py` - Runtime de RN
- `agents/routing_scorer.py` - Puntuación de routing

### Reglas de protección absoluta
1. **NO MODIFICAR RN** salvo que el prompt incluya exactamente: `RN_WRITE_ALLOWED`
2. **Solo lectura permitida** para auditoría y análisis
3. **Nunca modificar** schemas, registry, control o runtime de RN sin permiso
4. **Referencia sensible**: `docs/routing_neuron_v1_checkpoint.md` es solo lectura

### Protocolo para modificaciones
1. Incluir `RN_WRITE_ALLOWED` en el prompt
2. Crear plan detallado en Plan Mode
3. Implementar cambios en Act Mode con supervisión
4. Validar con tests relacionados si existen
5. Commit con mensaje que incluya `[RN]`

## Relaciones inferidas por estructura y documentación

### Nota metodológica importante
**Este inventario NO realizó análisis de imports internos ni lectura de código funcional.** Las relaciones mencionadas a continuación son inferencias basadas únicamente en:
- Nombres de archivos y carpetas
- Rutas de directorio
- Documentación Hextech existente (CONTEXT_MAP.md, RN_BOUNDARY.md, HEXTECH_BLUEPRINT.md)
- Convenciones de nomenclatura observables

### Relaciones inferidas por nombres y rutas
1. **main.py** → **aura.py** → **agents/core_agent.py** (inferido por flujo principal documentado)
2. **agents/routing_*.py** → **backend/app/routing_neuron/** (inferido por documentación RN_BOUNDARY.md)
3. **model_runner.py** → **providers/** → **agents/model_registry.py** (inferido por nombres y propósito documentado)
4. **agents/memory_agent.py** → **memory_store.py** → **memory.json** (inferido por nombres y propósito)

### Dependencias documentadas explícitamente
- **RN (Routing Neuron)**: Documentado en RN_BOUNDARY.md como subsistema central
- **Agentes de routing**: Mencionados en RN_BOUNDARY.md como especializados en routing
- **Documentación Hextech**: Referencias cruzadas entre documentos de docs/hextech/

### Dependencias externas
- Python 3.x (asumido por archivos .py)
- Dependencias listadas en requirements.txt (no analizado en este inventario)

### Advertencia de verificación
Las relaciones inferidas requieren auditoría con permiso explícito para verificación mediante análisis de imports reales. Este inventario se limitó a documentación y estructura superficial, respetando las restricciones de H2.0.

## Reglas Hextech aplicables

### Resumen de .clinerules
1. Siempre iniciar tareas con `git status`
2. Siempre terminar con `git diff --stat`
3. Una tarea = un objetivo claro
4. No tocar RN sin `RN_WRITE_ALLOWED`
5. No modificar backend/, agents/, providers/, ops/, tests/ sin permiso explícito
6. No ejecutar comandos destructivos
7. No instalar dependencias sin permiso explícito
8. No modificar más de 10 archivos por tarea sin permiso explícito
9. No mover carpetas completas sin plan aprobado
10. Preferir cambios pequeños y verificables
11. Mantener compatibilidad hacia atrás
12. Ejecutar tests cuando corresponda
13. No usar navegador salvo permiso explícito
14. No tocar memory.json, logs, .venv/, __pycache__/
15. Minimizar tokens: usar archivos concretos, evitar @workspace, resumir hallazgos
16. Usar CONTEXT_MAP.md como mapa contextual cuando esté disponible
17. Dividir tareas grandes en subtareas

### Protocolo de autonomía
- Auto-approve Edit activado para zonas seguras
- Cambios limitados a documentación e infraestructura
- Trazabilidad completa con Git
- Reversión inmediata ante problemas

### Flujo de trabajo Cline
1. **Plan Mode**: Explorar, entender contexto, proponer plan
2. **Aprobación**: Usuario aprueba plan
3. **Act Mode**: Implementar cambios en zonas seguras
4. **Verificación**: `git diff --stat` para resumen de cambios
5. **Commit**: Si todo correcto, commit con mensaje descriptivo

## Riesgos operativos identificados

### Riesgos de seguridad
1. **Modificación accidental de RN**: Podría romper sistema de enrutamiento completo
2. **Cambios en agents/**: Podría afectar comportamiento de IA sin supervisión
3. **Corrupción de memory.json**: Pérdida de estado persistente del sistema

### Riesgos de compatibilidad
1. **Dependencias entre agentes**: Cambios en un agente podrían afectar otros
2. **Esquemas de datos RN**: Modificaciones podrían romper contratos existentes
3. **Interfaces públicas**: Cambios podrían afectar integraciones externas

### Riesgos de contexto
1. **Uso excesivo de tokens**: Exploración recursiva innecesaria
2. **Falta de referencia contextual**: No usar CONTEXT_MAP.md para navegación
3. **Cambios grandes**: Modificar muchos archivos en una sola tarea

### Riesgos de organización
1. **Estructura de carpetas**: Reorganización sin plan podría romper imports
2. **Renombrado de módulos**: Podría afectar referencias en múltiples archivos
3. **Distribución de responsabilidades**: Cambios podrían crear acoplamiento innecesario

## Recomendaciones para próximas fases

### Prioridades de reorganización controlada
1. **Documentación**: Completar documentación faltante en docs/hextech/
2. **Estructura de agents/**: Evaluar posibilidad de agrupar agentes por dominio
3. **Separación de concerns**: Identificar acoplamientos altos entre módulos
4. **Tests**: Expandir cobertura de tests para zonas críticas

### Mejoras de seguridad sugeridas
1. **Checkpoints automáticos**: Snapshots de RN antes de cambios autorizados
2. **Validación de imports**: Herramienta para verificar dependencias antes de cambios
3. **Auditoría de permisos**: Revisión periódica de .clinerules

### Documentación faltante
1. **API documentation**: Documentar interfaces públicas de agentes
2. **Setup guide**: Guía detallada de configuración inicial
3. **Troubleshooting**: Solución de problemas comunes

## Checklist de verificación para tareas H2.0

### Antes de cada tarea
- [ ] Ejecutar `git status` para conocer estado inicial
- [ ] Consultar CONTEXT_MAP.md para navegación eficiente
- [ ] Identificar zonas afectadas (seguras/protegidas/críticas)

### Durante la tarea
- [ ] Respetar reglas de .clinerules
- [ ] No tocar RN sin `RN_WRITE_ALLOWED`
- [ ] No modificar archivos .py funcionales
- [ ] Mantener cambios pequeños y verificables
- [ ] Minimizar uso de tokens

### Después de la tarea
- [ ] Ejecutar `git diff --stat` para ver resumen de cambios
- [ ] Verificar que solo se modificaron zonas seguras/autorizadas
- [ ] Commit con mensaje descriptivo si cambios son correctos
- [ ] Reportar hallazgos relevantes

### Protección RN (absoluta)
- [ ] NO se modificará backend/app/routing_neuron/
- [ ] NO se modificarán agents/routing_*.py
- [ ] NO se modificará docs/routing_neuron_v1_checkpoint.md
- [ ] Solo lectura para auditoría permitida

---

**Nota**: Este inventario es parte de la infraestructura Hextech y debe actualizarse periódicamente para reflejar cambios en el proyecto. Sirve como referencia central para entender la estructura de AURA y gestionar riesgos operativos durante el desarrollo con Auto-approve Edit activado.

**Última actualización**: 22/4/2026 - Creación inicial como parte de H2.0
**Responsable**: Cline bajo supervisión Hextech
**Ubicación**: `docs/hextech/PROJECT_INVENTORY.md`