# Protocolo de Autonomía Hextech

## ¿Por qué Auto-approve Edit está activado?

Auto-approve Edit está activado intencionalmente para agilizar cambios seguros en infraestructura y documentación, permitiendo que Cline realice modificaciones controladas sin requerir aprobación explícita para cada archivo. Esto acelera el flujo de trabajo mientras mantenemos seguridad mediante:

1. **Restricciones estrictas**: Solo se permiten cambios en archivos específicos (.gitignore, .clinerules, README.md, docs/hextech/).
2. **Protección de código funcional**: No se puede modificar backend/, agents/, providers/, ops/, tests/, ni archivos críticos como main.py, config.py, memory.json.
3. **Trazabilidad con Git**: Todos los cambios son rastreables mediante commits.

## Autonomía controlada

Autonomía controlada significa que Cline tiene capacidad de modificar solo archivos de configuración y documentación, sin tocar código funcional. Esto permite:

- **Actualizar infraestructura**: Mejorar .gitignore, .clinerules, documentación.
- **Mantener consistencia**: Asegurar que las reglas de seguridad estén actualizadas.
- **Optimizar flujo de trabajo**: Crear guías y protocolos sin intervención humana.

La autonomía está limitada a "zonas seguras" definidas explícitamente.

**Nota importante**: Este documento es **explicativo** (filosofía de autonomía). Para las reglas ejecutables que Cline debe seguir, consulta [`.clinerules`](../.clinerules).

## Zonas seguras y zonas peligrosas

### Zonas seguras (modificables)
- `.gitignore` - Reglas de exclusión de Git.
- `.clinerules` - Reglas de seguridad para Cline.
- `README.md` - Documentación principal (solo agregar enlaces Hextech).
- `docs/hextech/` - Documentación de infraestructura Hextech.

### Zonas peligrosas (prohibidas)
- `backend/` - Código del backend.
- `agents/` - Agentes de IA.
- `providers/` - Proveedores de modelos.
- `ops/` - Operaciones.
- `tests/` - Tests.
- `logs/` - Logs de sesión.
- `.venv/` - Entorno virtual.
- `__pycache__/` - Cachés de Python.
- `memory.json` - Memoria de estado.
- Cualquier archivo `.py` funcional (main.py, config.py, aura.py, etc.).

## Cómo actuar ante riesgo alto

Si detectas comportamiento inesperado o riesgo alto:

1. **Detener inmediatamente**: No continuar con la tarea.
2. **Evaluar cambios**: Usar `git status` y `git diff` para ver qué se modificó.
3. **Revertir si es necesario**: Si los cambios son incorrectos, usar `git checkout -- <archivo>` para restaurar.
4. **Reportar**: Documentar el incidente y considerar ajustar .clinerules.

## Cómo usar Git como caja negra

Git proporciona trazabilidad completa:

- **Antes de cada tarea**: `git status` para conocer el estado inicial.
- **Durante la tarea**: Cambios pequeños y enfocados.
- **Después de cada tarea**: `git diff --stat` para ver un resumen de cambios.
- **Commit condicional**: Solo si los cambios son correctos y limitados a zonas seguras.

## Qué hacer antes y después de cada tarea

### Antes
1. Ejecutar `git status`.
2. Verificar que estás en la rama correcta.
3. Confirmar que no hay cambios no commitados que puedan interferir.

### Durante
1. Trabajar solo en archivos permitidos.
2. Mantener cambios pequeños y verificables.
3. No tocar zonas peligrosas.

### Después
1. Ejecutar `git diff --stat` para ver resumen de cambios.
2. Revisar que los cambios sean correctos.
3. Si todo está bien, hacer commit con mensaje descriptivo.
4. Si hay problemas, revertir antes de commit.

---

**Nota**: Este protocolo es parte de la jaula de seguridad Hextech para trabajar con Auto-approve Edit activado de manera segura y controlada.