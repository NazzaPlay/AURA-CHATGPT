# Mapa Contextual Hextech

## Propósito

Este mapa sirve para ahorrar tokens y navegar eficientemente el proyecto AURA. Proporciona referencias rápidas sobre qué archivos leer según el tipo de tarea, evitando exploraciones innecesarias y manteniendo contexto mínimo.

## Cómo Usar Este Mapa

1. **Identificar tipo de tarea**: Usar la tabla de áreas abajo
2. **Consultar archivos principales**: Leer solo los archivos listados para esa área
3. **Seguir reglas de lectura**: Respetar "cuándo leer" y "cuándo NO leer"
4. **Minimizar tokens**: No explorar fuera de lo necesario

## Áreas del Proyecto

### 1. Arranque/Chat Principal
**Archivos principales**:
- `main.py` - Punto de entrada principal
- `aura.py` - Cliente AURA
- `agents/chat_agent.py` - Agente de chat principal

**Cuándo leerlos**:
- Tareas relacionadas con flujo principal de conversación
- Modificación de comportamiento de chat
- Depuración de interacción usuario-IA

**Cuándo NO leerlos**:
- Tareas de configuración o infraestructura
- Modificaciones a agentes especializados
- Cambios en routing o memoria

**Riesgo de contexto**: Medio

### 2. Configuración/Modelos
**Archivos principales**:
- `config.py` - Configuración del sistema
- `model_runner.py` - Ejecutor de modelos
- `providers/base_provider.py` - Clase base de proveedores
- `agents/model_registry.py` - Registro de modelos

**Cuándo leerlos**:
- Cambios en configuración de modelos
- Integración de nuevos proveedores
- Optimización de ejecución de modelos

**Cuándo NO leerlos**:
- Tareas de UI o frontend
- Modificaciones a lógica de negocio
- Cambios en documentación

**Riesgo de contexto**: Bajo

### 3. Memoria
**Archivos principales**:
- `memory_store.py` - Almacenamiento de memoria
- `agents/memory_agent.py` - Agente de gestión de memoria
- `memory.json` - Estado persistente (solo lectura)

**Cuándo leerlos**:
- Tareas relacionadas con persistencia de estado
- Optimización de almacenamiento de memoria
- Depuración de pérdida de contexto

**Cuándo NO leerlos**:
- `memory.json` nunca debe modificarse
- Tareas de chat en tiempo real
- Configuración de modelos

**Riesgo de contexto**: Alto (especialmente memory.json)

### 4. Agentes
**Archivos principales**:
- `agents/core_agent.py` - Agente central
- `agents/` - Carpeta con todos los agentes
- `agents/internal_*.py` - Agentes de herramientas internas

**Cuándo leerlos**:
- Solo con permiso explícito para modificar agentes
- Auditoría de seguridad de agentes
- Análisis de dependencias entre agentes

**Cuándo NO leerlos**:
- Tareas de documentación o infraestructura
- Modificaciones sin permiso explícito
- Exploración general del proyecto

**Riesgo de contexto**: Alto (zona protegida)

### 5. Herramientas Internas
**Archivos principales**:
- `agents/internal_tools_agent.py` - Agente de herramientas
- `agents/internal_tools_registry.py` - Registro de herramientas
- `agents/internal_actions_agent.py` - Agente de acciones internas

**Cuándo leerlos**:
- Extensión de herramientas disponibles
- Depuración de ejecución de herramientas
- Auditoría de seguridad de acciones internas

**Cuándo NO leerlos**:
- Tareas de chat general
- Configuración de modelos
- Modificaciones a memoria

**Riesgo de contexto**: Medio

### 6. Operaciones
**Archivos principales**:
- `ops/` - Carpeta de operaciones
- `ops/assistant_ops_registry.json` - Registro de operaciones
- `ops/execution_log.md` - Log de ejecución
- `ops/task_queue.md` - Cola de tareas

**Cuándo leerlos**:
- Monitoreo de ejecución de tareas
- Auditoría de operaciones realizadas
- Depuración de problemas en colas

**Cuándo NO leerlos**:
- Tareas de chat en tiempo real
- Modificaciones a agentes
- Cambios en configuración de modelos

**Riesgo de contexto**: Bajo

### 7. RN/Routing
**Archivos principales**:
- `backend/app/routing_neuron/` - Implementación de RN
- `agents/routing_*.py` - Agentes de routing
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de referencia

**Cuándo leerlos**:
- Solo lectura para auditoría
- Análisis de imports y dependencias
- Reporte de riesgos de seguridad

**Cuándo NO leerlos**:
- Nunca modificar sin `RN_WRITE_ALLOWED`
- Tareas de documentación general
- Exploración casual del proyecto

**Riesgo de contexto**: Muy Alto (zona críticamente protegida)

### 8. Tests
**Archivos principales**:
- `tests/` - Carpeta de tests
- `tests/test_routing_neuron_subsystem.py` - Tests de RN
- `tests/test_operational_supervisor.py` - Tests de supervisión

**Cuándo leerlos**:
- Validación de cambios en código funcional
- Ejecución de tests después de modificaciones
- Depuración de fallos en tests

**Cuándo NO leerlos**:
- Tareas de documentación o infraestructura
- Sin permiso para modificar código funcional
- Exploración general del proyecto

**Riesgo de contexto**: Medio

### 9. Documentación
**Archivos principales**:
- `docs/` - Carpeta de documentación
- `docs/hextech/` - Infraestructura Hextech
- `README.md` - Documentación principal
- `docs/hextech/PROJECT_INVENTORY.md` - Inventario técnico y mapa de riesgo

**Cuándo leerlos**:
- Cualquier tarea de documentación
- Actualización de guías y protocolos
- Verificación de reglas de seguridad
- Análisis de estructura del proyecto y zonas de riesgo

**Cuándo NO leerlos**:
- Nunca (siempre es seguro leer documentación)
- **Nota**: Modificar solo con Auto-approve Edit activado

**Riesgo de contexto**: Bajo (zona segura)

### 10. Git/Checkpoints
**Archivos principales**:
- `.gitignore` - Reglas de exclusión de Git
- `.clinerules` - Reglas de seguridad para Cline
- `docs/hextech/` - Documentación de infraestructura
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de RN

**Comandos esenciales**:
- `git status` - Estado del repositorio (siempre al inicio)
- `git log --oneline -5` - Últimos 5 commits
- `git diff --stat` - Resumen de cambios (siempre al final)

**Cuándo leerlos**:
- Inicio de cualquier tarea (git status)
- Verificación de cambios (git diff --stat)
- Auditoría de reglas de seguridad (.clinerules)
- Referencia de checkpoint de RN (solo lectura)

**Cuándo NO leerlos**:
- `.clinerules` no debe modificarse sin razón de seguridad
- `docs/routing_neuron_v1_checkpoint.md` nunca modificar
- Exploración recursiva de .git/

**Riesgo de contexto**: Bajo

## Reglas de Navegación

### Regla 1: Contexto Mínimo
- Leer solo archivos necesarios para la tarea actual
- Usar `search_files` con patrones específicos en lugar de explorar
- Especificar `start_line` y `end_line` en `read_file` para archivos largos

### Regla 2: Zonas Protegidas
- **Agentes/**: Solo lectura con permiso explícito
- **RN/**: Solo lectura, nunca modificar sin `RN_WRITE_ALLOWED`
- **Tests/**: Solo lectura cuando corresponda ejecutar tests

### Regla 3: Zonas Seguras
- **docs/hextech/**: Siempre modificable con Auto-approve Edit
- **README.md**: Solo agregar enlaces a documentación Hextech
- **.gitignore, .clinerules**: Modificables para infraestructura

### Regla 4: Evitar @workspace
- Nunca usar `@workspace` para cargar todo el proyecto
- Usar rutas específicas: `read_file("main.py")`
- Usar `list_files` sin `recursive=true` para directorios específicos

## Ejemplos de Uso

### Ejemplo 1: Tarea de Documentación
1. Consultar "Documentación" en este mapa
2. Leer `README.md` y `docs/hextech/`
3. No leer `agents/` o `backend/`
4. Usar `git status` y `git diff --stat`

### Ejemplo 2: Auditoría de Seguridad
1. Consultar "RN/Routing" y "Agentes"
2. Leer `docs/routing_neuron_v1_checkpoint.md` (solo lectura)
3. Analizar imports en `agents/routing_*.py`
4. Reportar hallazgos sin modificar

### Ejemplo 3: Actualización de Configuración
1. Consultar "Configuración/Modelos"
2. Leer `config.py` y `model_runner.py`
3. No leer `memory.json` o `agents/`
4. Verificar cambios con `git diff --stat`

## Actualización de Este Mapa

Si descubres nueva información relevante:
1. Actualizar las secciones afectadas
2. Mantener formato consistente
3. No agregar contenido innecesario
4. Commit con mensaje descriptivo

---

**Nota**: Este mapa es parte de la infraestructura Hextech. Su propósito es ahorrar tokens y guiar navegación eficiente, manteniendo seguridad y contexto mínimo.