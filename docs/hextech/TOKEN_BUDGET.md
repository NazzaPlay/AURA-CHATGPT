# Presupuesto de Tokens Hextech

## ¿Por qué importa el presupuesto de tokens?

Los modelos de lenguaje tienen límites de contexto. Usar tokens eficientemente permite:
- **Tareas más largas**: Más espacio para razonamiento y ejecución.
- **Respuestas más rápidas**: Menos tokens = menos tiempo de procesamiento.
- **Costos reducidos**: En servicios de pago por token.
- **Contexto enfocado**: Solo información relevante en el contexto.

## Cómo ahorrar tokens

### 1. Leer solo archivos necesarios
- **✅ Correcto**: `read_file("main.py", start_line=1, end_line=50)` para leer solo las primeras 50 líneas.
- **❌ Incorrecto**: Leer archivos completos de 1000+ líneas sin necesidad.
- **✅ Correcto**: `search_files("agents/", "class.*Agent")` para encontrar patrones específicos.
- **❌ Incorrecto**: Listar carpetas completas con `list_files(recursive=true)` sin propósito claro.

### 2. Usar resúmenes en lugar de contenido completo
- En lugar de pegar 200 líneas de código en la respuesta, resumir:
  - "El archivo main.py tiene 182 líneas, importa módulos de backend y agents, y define la función principal `save_log`."
- Incluir solo las líneas relevantes cuando sea necesario para el contexto.

### 3. Evitar @workspace
- `@workspace` incluye TODO el contenido del workspace, consumiendo miles de tokens.
- En su lugar, usar rutas específicas: `read_file("config.py")`, `list_files("docs/")`.

### 4. Limitar búsquedas recursivas
- `search_files` con `file_pattern="*.py"` para limitar a archivos Python.
- Especificar directorios concretos en lugar de buscar en todo el proyecto.

## deepseek-reasoner para planificación compleja

**Cuándo usarlo**:
- Tareas que requieren razonamiento profundo.
- Análisis de arquitectura.
- Diseño de soluciones complejas.
- Planificación de refactorizaciones.

**Ejemplos**:
- "Diseñar un sistema de caching para agents/"
- "Planificar migración de Python 3.9 a 3.11"
- "Analizar dependencias y proponer optimizaciones"

**Ventajas**:
- Mayor capacidad de razonamiento.
- Mejor comprensión de relaciones complejas.
- Planes más robustos.

## deepseek-chat para ejecución simple

**Cuándo usarlo**:
- Tareas directas y bien definidas.
- Ejecución de cambios concretos.
- Modificaciones simples en archivos.
- Comandos CLI específicos.

**Ejemplos**:
- "Crear .gitignore con estas reglas"
- "Actualizar README.md para agregar enlaces"
- "Ejecutar `git status` y `git diff --stat`"

**Ventajas**:
- Respuestas más rápidas.
- Menor consumo de tokens.
- Ideal para tareas rutinarias.

## No leer carpetas completas salvo auditoría

**Regla**: Solo leer carpetas completas cuando:
1. **Auditoría de seguridad**: Verificar estructura completa del proyecto.
2. **Búsqueda de problemas**: Encontrar archivos específicos en todo el proyecto.
3. **Análisis inicial**: Primer contacto con un proyecto desconocido.

**En tareas normales**:
- Saber qué archivos necesitas (ej: "modificar config.py").
- Leer solo esos archivos.
- Usar `list_files` sin `recursive=true` para ver contenido de un directorio específico.

## Usar CONTEXT_MAP.md como mapa

Si existe `docs/hextech/CONTEXT_MAP.md`:
1. **Consultarlo primero**: Antes de explorar el proyecto.
2. **Seguir referencias**: Usar las rutas y descripciones proporcionadas.
3. **Actualizarlo**: Si descubres nueva información relevante, actualizar el mapa.

El CONTEXT_MAP.md debe contener:
- Estructura de directorios clave.
- Archivos importantes y su propósito.
- Dependencias entre módulos.
- Reglas de seguridad y zonas prohibidas.

## Dividir tareas grandes

Técnica para manejar tareas complejas:

1. **Dividir en subtareas**:
   - Subtarea 1: Analizar estructura actual.
   - Subtarea 2: Diseñar solución.
   - Subtarea 3: Implementar cambios.
   - Subtarea 4: Verificar y commit.

2. **Cada subtarea independiente**:
   - Objetivo claro.
   - Archivos específicos.
   - Criterio de éxito.

3. **Mantener contexto manejable**:
   - No cargar todo el proyecto en cada subtarea.
   - Solo información relevante para la subtarea actual.

## Ejemplo práctico

**Tarea grande**: "Refactorizar sistema de logging"

**Subtareas**:
1. Analizar logging actual (`read_file("main.py")`, `search_files("", "log")`).
2. Diseñar nuevo sistema (deepseek-reasoner).
3. Implementar cambios en archivos específicos (deepseek-chat).
4. Ejecutar tests y commit.

Cada subtarea usa solo los tokens necesarios para su objetivo.

---

**Conclusión**: El presupuesto de tokens es un recurso limitado. Usarlo eficientemente permite trabajar en proyectos más grandes y complejos sin alcanzar límites de contexto.