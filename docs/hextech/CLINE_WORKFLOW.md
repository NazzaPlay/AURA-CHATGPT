# Flujo de Trabajo Cline

## Plan Mode vs Act Mode

### Plan Mode (para diseño)
- **Propósito**: Explorar archivos, entender contexto, proponer plan.
- **Cuándo usarlo**: Al inicio de tareas complejas o cuando se necesita entender la estructura del proyecto.
- **Herramientas disponibles**: `read_file`, `list_files`, `search_files`, `ask_followup_question`.
- **Resultado esperado**: Un plan detallado que el usuario apruebe antes de pasar a Act Mode.

### Act Mode (para ejecución)
- **Propósito**: Implementar cambios, usar herramientas para modificar archivos.
- **Cuándo usarlo**: Una vez aprobado el plan, para ejecutar cambios concretos.
- **Herramientas disponibles**: `write_to_file`, `replace_in_file`, `execute_command`, etc.
- **Resultado esperado**: Cambios implementados y commit realizados.

## Una tarea = un objetivo

Cada tarea debe tener:
- **Objetivo claro**: Una sola cosa a lograr (ej: "crear .gitignore", "actualizar documentación").
- **Scope definido**: Archivos específicos a modificar.
- **Criterio de éxito**: Cómo verificar que la tarea se completó correctamente.

Ejemplos de tareas bien definidas:
- "Crear .gitignore con reglas mínimas para Python"
- "Actualizar README.md para agregar enlaces a docs/hextech/"
- "Crear protocolo de autonomía en docs/hextech/AUTONOMY_PROTOCOL.md"

## Usar @archivo en vez de @workspace

Para minimizar tokens y mantener contexto enfocado:

- **✅ Correcto**: `read_file("main.py")`, `search_files("agents/", "class.*Agent")`
- **❌ Incorrecto**: `@workspace`, leer carpetas completas sin necesidad.

Regla: Leer solo los archivos necesarios para la tarea actual, no explorar todo el proyecto.

## git status antes

**Siempre** ejecutar `git status` al inicio de cada tarea para:
1. Conocer el estado actual del repositorio.
2. Verificar que no hay cambios no commitados que puedan interferir.
3. Identificar archivos untracked que podrían ser relevantes.

## git diff --stat después

**Siempre** ejecutar `git diff --stat` al final de cada tarea para:
1. Ver un resumen de los cambios realizados.
2. Confirmar que solo se modificaron los archivos esperados.
3. Detectar cambios accidentales en zonas peligrosas.

## Tests cuando corresponda

Si la tarea involucra modificar código funcional (requiere permiso explícito):
1. Ejecutar tests existentes antes de modificar.
2. Ejecutar tests después de modificar.
3. Asegurar que no se rompe funcionalidad existente.

Para tareas de infraestructura (como esta), los tests no son necesarios ya que no se modifica código.

## Reporte final corto

Al completar la tarea, proporcionar un resumen que incluya:
1. Archivos creados/editados.
2. Reglas importantes agregadas.
3. Resultado de `git status`.
4. Resultado de `git diff --stat`.
5. Si hubo commit, mostrar hash corto.
6. Si no hubo commit, explicar por qué.
7. Próximo paso recomendado.

## Ejemplo de flujo completo

1. **Inicio**: `git status`
2. **Plan Mode**: Explorar archivos relevantes, proponer plan.
3. **Aprobación**: Usuario aprueba plan.
4. **Act Mode**: Implementar cambios.
5. **Verificación**: `git diff --stat`
6. **Commit**: Si todo está bien, `git add` y `git commit`
7. **Reporte**: Resumen final.

---

**Nota**: Este flujo asegura cambios controlados, trazables y seguros, especialmente importante cuando Auto-approve Edit está activado.