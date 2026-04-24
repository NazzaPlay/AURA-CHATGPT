# Protocolo DEV-CLEANUP — Limpieza de estado vivo en desarrollo

## Propósito

Este protocolo define un procedimiento seguro para limpiar el estado vivo de AURA durante la fase de desarrollo activo. Su objetivo es evitar que datos viejos (caches, logs, memoria persistente) contaminen pruebas y sesiones de desarrollo, incluso cuando el código nuevo es correcto.

**Problema detectado:** Un bug previo dañó preferencias guardadas en `memory.json`. Luego el código fue corregido, pero los datos viejos seguían contaminando las pruebas. Este protocolo previene esa situación.

---

## ¿Cuándo usar limpieza?

1. **Antes de cada actualización importante de código** — para asegurar que los tests reflejen el código nuevo, no datos viejos.
2. **Cuando se sospeche contaminación por datos previos** — si AURA falla sin causa clara en código.
3. **Antes de iniciar una nueva sesión de pruebas** — para partir de estado limpio.
4. **Periódicamente durante desarrollo activo** — para evitar acumulación de caches.

---

## ¿Qué se puede borrar?

| Elemento | ¿Borrable? | Descripción |
|----------|-----------|-------------|
| `memory.json` | ✅ Sí | Estado persistente del sistema. Se regenera al iniciar AURA. |
| `logs/` (contenido) | ✅ Sí | Archivos de sesión (`session_*.json`). Se regeneran al ejecutar AURA. |
| `__pycache__/` (todo) | ✅ Sí | Cachés de bytecode Python. Se regeneran al importar módulos. |
| `*.pyc`, `*.pyo`, `*.pyd` | ✅ Sí | Archivos compilados de Python. Se regeneran automáticamente. |

---

## ¿Qué NO se debe borrar NUNCA?

| Elemento | Motivo |
|----------|--------|
| `.venv/` | Entorno virtual con dependencias instaladas. Requiere reinstalación. |
| `.git/` | Repositorio Git. Contiene todo el historial del proyecto. |
| `models/` o `AURA/models/` | Modelos GGUF. Archivos grandes que requieren descarga. |
| `backend/app/routing_neuron/` | RN — zona críticamente protegida. |
| `agents/` | Código funcional de agentes de IA. |
| `memory_store.py` | Código funcional de memoria (no confundir con `memory.json`). |
| `main.py`, `aura.py`, `config.py`, `model_runner.py` | Código funcional del sistema. |
| `docs/` | Documentación del proyecto. |
| `ops/` | Operaciones y registros de ejecución. |
| `tests/` | Tests automatizados. |

---

## Comandos PowerShell recomendados

### Limpieza completa (todo en uno)

```powershell
# DEV-CLEANUP: Resetea estado vivo para desarrollo
# Ejecutar desde la raíz del proyecto (A:\AURA\project)

Write-Host "=== DEV-CLEANUP ===" -ForegroundColor Cyan

# 1. memory.json
if (Test-Path memory.json) {
    Remove-Item memory.json -Verbose
    Write-Host "  ✓ memory.json eliminado" -ForegroundColor Green
} else {
    Write-Host "  - memory.json no existe, saltando" -ForegroundColor Yellow
}

# 2. logs/
if (Test-Path logs) {
    Remove-Item logs\* -Recurse -Force -Verbose
    Write-Host "  ✓ logs/ limpiado" -ForegroundColor Green
} else {
    Write-Host "  - logs/ no existe, saltando" -ForegroundColor Yellow
}

# 3. __pycache__/ recursivo
$pycacheCount = (Get-ChildItem -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue).Count
if ($pycacheCount -gt 0) {
    Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -Verbose
    Write-Host "  ✓ __pycache__/ eliminado ($pycacheCount carpetas)" -ForegroundColor Green
} else {
    Write-Host "  - __pycache__/ no existe, saltando" -ForegroundColor Yellow
}

# 4. *.pyc sueltos
$pycCount = (Get-ChildItem -Recurse -Filter *.pyc -ErrorAction SilentlyContinue).Count
if ($pycCount -gt 0) {
    Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force -Verbose
    Write-Host "  ✓ *.pyc eliminados ($pycCount archivos)" -ForegroundColor Green
} else {
    Write-Host "  - *.pyc no existen, saltando" -ForegroundColor Yellow
}

Write-Host "=== DEV-CLEANUP COMPLETADO ===" -ForegroundColor Cyan
Write-Host "Ejecuta 'git status' para verificar el estado."
```

### Limpieza selectiva (por componente)

```powershell
# Solo memory.json
if (Test-Path memory.json) { Remove-Item memory.json -Verbose }

# Solo logs/
if (Test-Path logs) { Remove-Item logs\* -Recurse -Force -Verbose }

# Solo __pycache__/
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -Verbose

# Solo *.pyc
Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force -Verbose
```

---

## Checklist pre-limpieza

- [ ] `git status` — confirmar working tree clean
- [ ] No hay cambios sin commit que se puedan perder
- [ ] No hay sesiones activas de AURA ejecutándose
- [ ] No se está en medio de una prueba importante

## Checklist post-limpieza

- [ ] `git status` — debe mostrar "nothing to commit, working tree clean"
- [ ] `memory.json` ya no existe
- [ ] `logs/` está vacío o no existe
- [ ] `__pycache__/` ya no existe en ningún subdirectorio

---

## Relación con la fase de desarrollo

Este protocolo está diseñado para la **fase de desarrollo activo** de AURA. No debe confundirse con un procedimiento de producción.

- **Desarrollo**: Se permite borrar estado vivo libremente para mantener entornos de prueba limpios.
- **Producción**: No aplica. En producción el estado vivo debe persistir y gestionarse con otros mecanismos.

---

## Nota futura: RN Memory Repair / RN Data Validator

En una fase futura, una neurona de la **RN Family** podría encargarse de validar y reparar memoria automáticamente. Posibles candidatos conceptuales:

- **RN Memory Repair**: Detecta y corrige corrupción en `memory.json` antes de cargarlo.
- **RN Data Validator**: Valida integridad de datos persistidos y rechaza cargas dañadas.

> **Esto NO se implementa ahora.** Queda como nota conceptual para arquitectura futura. Mientras tanto, este protocolo manual es la solución recomendada.

---

## Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 24/4/2026 | v1.0 | Creación inicial del protocolo DEV-CLEANUP |

**Ubicación:** `docs/hextech/DEV_CLEANUP_PROTOCOL.md`
