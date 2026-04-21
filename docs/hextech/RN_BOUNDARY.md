# Límites del Routing Neuron (RN)

## ¿Qué es el Routing Neuron en AURA?

El Routing Neuron (RN) es el subsistema central de enrutamiento y toma de decisiones de AURA. Es un componente crítico que:

1. **Gestiona el flujo** entre diferentes agentes y módulos
2. **Toma decisiones** basadas en señales y contexto
3. **Mantiene traza** de sesiones y actividad aplicada
4. **Proporciona runtime** limitado para operaciones seguras

RN está actualmente en **V1.8** y se considera un subsistema canónico ya sellado.

## Carpetas y Archivos Relacionados

### Implementación Principal
- `backend/app/routing_neuron/` - Implementación canónica de RN
- `backend/app/routing_neuron/blueprint/` - Referencia canónica (documentación interna)

### Agentes de Routing
- `agents/routing_*.py` - Agentes especializados en routing:
  - `agents/routing_maintenance.py` - Mantenimiento de RN
  - `agents/routing_neuron_registry.py` - Registro de RN
  - `agents/routing_observer.py` - Observador de RN
  - `agents/routing_policy.py` - Políticas de routing
  - `agents/routing_runtime.py` - Runtime de RN
  - `agents/routing_scorer.py` - Puntuación de routing

### Documentación de Referencia
- `docs/routing_neuron_v1_checkpoint.md` - Checkpoint de referencia (documento legacy de compatibilidad)

## Regla Absoluta de Protección

### ❌ **NO MODIFICAR RN** salvo que el prompt incluya exactamente:
```
RN_WRITE_ALLOWED
```

Esta regla es **absoluta** y se aplica a:
- Cualquier archivo en `backend/app/routing_neuron/`
- Cualquier archivo `agents/routing_*.py`
- Cualquier referencia o import relacionado con RN
- Cualquier cambio en schemas, registry, control o runtime de RN

## docs/routing_neuron_v1_checkpoint.md - Referencia Sensible

### Estado del Documento
- **Tipo**: Documento legacy de compatibilidad
- **Propósito**: Proporcionar checkpoint de referencia para V1.8
- **Ubicación canónica**: La referencia canónica vive en `backend/app/routing_neuron/blueprint/`

### Reglas de Uso
1. **Solo lectura**: Nunca modificar este documento
2. **Referencia**: Usar solo para entender estado actual de RN
3. **Auditoría**: Permitido leer para análisis de seguridad
4. **No dependencia**: No basar implementaciones en este documento legacy

### Contenido Clave (según checkpoint)
- RN está en V1.8 con subsistema canónico ya sellado
- Runtime limitado ya operativo
- Ventana liviana de historial reciente
- Primer camino `applied` seguro ya demostrable
- Separación limpia entre `provider_trace`, `routing_neuron_trace`, `system_state` y checkpoint visible

## Qué SÍ se Puede Hacer sin RN_WRITE_ALLOWED

### 1. Leer Documentación
- Leer `docs/routing_neuron_v1_checkpoint.md` para entender estado actual
- Leer referencias en documentación Hextech sobre RN
- Consultar `CONTEXT_MAP.md` para ubicación de archivos RN

### 2. Auditar Imports
- Analizar imports de archivos RN para entender dependencias
- Identificar qué módulos dependen de RN
- Reportar dependencias críticas

### 3. Reportar Riesgos
- Identificar posibles problemas de seguridad relacionados con RN
- Reportar dependencias obsoletas o vulnerables
- Sugerir mejoras de seguridad (sin implementarlas)

### 4. Entender Arquitectura
- Estudiar cómo RN interactúa con otros componentes
- Comprender flujo de decisiones del sistema
- Documentar relaciones entre módulos

## Qué NO se Puede Hacer sin RN_WRITE_ALLOWED

### 1. Mover RN
- ❌ No mover archivos de `backend/app/routing_neuron/`
- ❌ No reorganizar estructura de carpetas de RN
- ❌ No renombrar archivos o módulos de RN

### 2. Refactorizar RN
- ❌ No cambiar estructura de código de RN
- ❌ No modificar interfaces públicas de RN
- ❌ No reorganizar responsabilidades entre módulos RN

### 3. Cambiar Schemas
- ❌ No modificar schemas de datos de RN
- ❌ No cambiar formatos de entrada/salida
- ❌ No alterar contratos de API internos

### 4. Cambiar Registry/Control
- ❌ No modificar `agents/routing_neuron_registry.py`
- ❌ No alterar mecanismos de registro y descubrimiento
- ❌ No cambiar políticas de control de acceso

### 5. Cambiar Runtime/Core
- ❌ No modificar `agents/routing_runtime.py`
- ❌ No alterar núcleo de ejecución de RN
- ❌ No cambiar mecanismos de toma de decisiones

## Protocolo para Futuras Tareas RN

### Paso 1: Evaluación de Necesidad
1. ¿La tarea realmente requiere modificar RN?
2. ¿Existe alternativa que no toque RN?
3. ¿El beneficio justifica el riesgo?

### Paso 2: Obtención de Permiso
1. Incluir `RN_WRITE_ALLOWED` en el prompt
2. Esperar confirmación explícita del usuario
3. Documentar razón del cambio requerido

### Paso 3: Planificación Controlada
1. Crear plan detallado en Plan Mode
2. Especificar exactamente qué archivos se modificarán
3. Definir criterios de éxito y rollback

### Paso 4: Ejecución Supervisada
1. Implementar cambios en Act Mode
2. Verificar cada cambio con `git diff`
3. Ejecutar tests relacionados si existen

### Paso 5: Validación y Commit
1. Verificar que solo se modificaron archivos autorizados
2. Confirmar que no se rompió funcionalidad existente
3. Hacer commit con mensaje descriptivo que incluya `[RN]`

## Ejemplos de Tareas Permitidas/Prohibidas

### ✅ Permitido (sin RN_WRITE_ALLOWED)
- "Leer docs/routing_neuron_v1_checkpoint.md para entender estado de RN"
- "Auditar imports en agents/routing_*.py para reportar dependencias"
- "Documentar interacción entre RN y agents/core_agent.py"

### ❌ Prohibido (requiere RN_WRITE_ALLOWED)
- "Refactorizar agents/routing_runtime.py para mejorar performance"
- "Agregar nuevo método a backend/app/routing_neuron/"
- "Cambiar schema de datos en routing_neuron_registry.py"

### ⚠️ Caso Especial (consultar primero)
- "¿Necesito RN_WRITE_ALLOWED para leer agents/routing_policy.py?"
  - **Respuesta**: Solo lectura está permitida, modificación NO

## Integración con Hextech

### Protección en .clinerules
La regla 4 de `.clinerules` establece:
```
4. No tocar RN (Routing Neuron) salvo que el prompt incluya exactamente: `RN_WRITE_ALLOWED`
```

### Referencia en CONTEXT_MAP.md
El `CONTEXT_MAP.md` clasifica RN/Routing como:
- **Riesgo de contexto**: Muy Alto (zona críticamente protegida)
- **Cuándo leer**: Solo lectura para auditoría
- **Cuándo NO leer**: Nunca modificar sin `RN_WRITE_ALLOWED`

### Mención en HEXTECH_BLUEPRINT.md
El blueprint incluye RN como zona protegida con reglas específicas de modificación.

## Consecuencias de Violar la Regla

Si accidentalmente se modifica RN sin permiso:
1. **Detener inmediatamente** la tarea
2. **Revertir cambios** con `git checkout -- <archivo>`
3. **Reportar incidente** en documentación
4. **Revisar .clinerules** para fortalecer protección

---

**Nota**: RN es el corazón del sistema de enrutamiento de AURA. Su protección es crítica para mantener estabilidad y seguridad. Esta documentación establece límites claros para trabajar de manera segura con Auto-approve Edit activado.