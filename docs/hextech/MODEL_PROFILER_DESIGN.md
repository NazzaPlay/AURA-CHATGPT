# Model Profiler / Benchmark Design — H3.5

## 1. Propósito

Diseñar conceptualmente un sistema de profiling/benchmark de modelos para AURA, que permita medir y comparar modelos locales GGUF antes de asignarlos a roles en el routing multimodelo. Este diseño establece las bases para que, en fases futuras (H3.5.x), se pueda ejecutar profiling real sobre el banco de modelos externo (`A:\AURA\models`) y alimentar la matriz de decisión del sistema de routing multimodelo.

**Fase**: H3.5 — Diseño conceptual del Model Profiler  
**Estado**: Documentación de diseño (no implementación)  
**Fecha**: 27/4/2026  

---

## 2. Alcance

- **Solo diseño conceptual**: No se implementa código, no se ejecutan benchmarks, no se abren modelos, no se crean scripts de profiling.
- Define: métricas, set de prompts, categorías de benchmark, salida esperada, formato de resultados futuros, relación con otros componentes H3.
- No define: implementación de RN Model Profiler (RN-MP), scripts de benchmark reales, integración con runtime.
- **Relación con H3.0**: Concreta la sección 11 de `RN_SELF_WORK_PLAN.md` (RN-MP como neurona candidata).
- **Relación con H3.1**: Agrega la dimensión de rendimiento faltante en el inventario de modelos.
- **Relación con H3.3**: Alimenta la matriz de decisión del routing multimodelo con datos reales.
- **Relación con H3.4**: Los resultados de benchmark se registrarán como nodos `Model` con aristas `USED_MODEL` en el grafo futuro.

---

## 3. Estado actual

### 3.1 No existe profiler/benchmark automático

- **`agents/model_benchmark.py`** existe pero **no ejecuta benchmarks reales**. Contiene dataclasses (`BenchmarkSnapshot`, `BenchmarkTarget`, `BenchmarkAssessment`, `BenchmarkPreparationSnapshot`) con campos como `latency_ms`, `memory_mb`, `stability_score`, etc., pero **todos son `float | None` defaulting a None**. La función `assess_benchmark_snapshot()` contiene lógica de evaluación pero nunca se llama con datos reales. `build_benchmark_targets()` itera las políticas del registry pero no ejecuta nada.
- **`model_runner.py`** invoca `llama-cli` vía `subprocess.run()` con el flag **`--no-show-timings`**, lo que suprime activamente las métricas de tiempo de ejecución (tokens/segundo, tiempo total, etc.). No captura latencia, RAM ni ninguna métrica de rendimiento.
- **`local_llama_provider.py`** llama a `run_model()` y retorna solo texto plano. `check_availability()` solo verifica existencia de archivos. No hay timing, medición de RAM ni métricas de calidad.
- **`model_registry.py`** tiene campos `benchmark_readiness` y `benchmark_priority` en `ModelPolicyEntry`, pero son metadatos de planificación, no resultados de medición real.

### 3.2 Infraestructura existente aprovechable

| Componente | Estado | Aprovechable para |
|------------|--------|-------------------|
| `model_runner.py` | Funcional, suprime timings | Base para invocar modelos; requiere wrapper de medición |
| `local_llama_provider.py` | Funcional | Patrón de invocación; requiere wrapper de profiling |
| `model_registry.py` | Funcional | Catálogo de modelos con readiness y prioridad |
| `model_benchmark.py` | Dataclasses sin implementación | Schema de datos para resultados |
| `config.py` | Define rutas y nombres de modelos | Configuración de targets de benchmark |

---

## 4. Definición de Model Profiler

El **Model Profiler** es un sistema que:

1. Toma un modelo GGUF del banco externo (`A:\AURA\models`)
2. Ejecuta un set estandarizado de prompts de prueba sobre él
3. Captura métricas de rendimiento (latencia, throughput, RAM)
4. Evalúa calidad básica de respuestas (adherencia, español, razonamiento)
5. Produce un reporte estructurado con score recomendado y rol sugerido
6. Almacena resultados en formato append-only para trazabilidad

El profiler **no modifica** el modelo, **no lo convierte**, **no lo mueve** y **no altera** la configuración actual de AURA.

---

## 5. Qué NO hará la primera versión (H3.5)

| Exclusión | Motivo |
|-----------|--------|
| ❌ No implementar código de profiling | H3.5 es solo diseño conceptual |
| ❌ No ejecutar benchmarks reales | Requiere plan H3.5.x aprobado |
| ❌ No abrir, modificar, mover ni convertir modelos | Los modelos están fuera del repo, solo lectura |
| ❌ No modificar `model_runner.py` | Zona protegida; requiere permiso explícito |
| ❌ No modificar `model_benchmark.py` | Zona protegida; requiere permiso explícito |
| ❌ No modificar `local_llama_provider.py` | Zona protegida |
| ❌ No crear `ops/model_profiler/` todavía | Se creará en H3.5.1 |
| ❌ No crear scripts de benchmark | Se crearán en H3.5.2+ |
| ❌ No conectar DeepSeek API | El profiler es local-only |
| ❌ No instalar dependencias | Solo Python estándar + llama.cpp existente |
| ❌ No tocar RN Core | RN tiene su propio protocolo (RN_WRITE_ALLOWED) |
| ❌ No tocar `agents/routing_*.py` | Zona protegida |
| ❌ No tocar `agents/`, `providers/`, `backend/` | Zonas protegidas |
| ❌ No modificar `config.py` | Archivo funcional protegido |
| ❌ No tocar `memory.json`, `logs/`, `.venv/`, `__pycache__/` | Reglas absolutas de .clinerules |

---

## 6. Principios de diseño

### 6.1 Solo lectura sobre modelos
El profiler **nunca modifica** los archivos de modelo. Solo los abre para inferencia y lee su metadata (nombre, tamaño, cuantización).

### 6.2 Bajo costo
Benchmarks secuenciales (no paralelos), tiempo máximo por modelo configurable, priorización de modelos livianos primero.

### 6.3 Reproducibilidad
Cada benchmark registra: timestamp, temperatura de CPU (si disponible), versión de llama.cpp, argumentos exactos usados, y resultados crudos. Múltiples corridas (3+) con promedio y desviación estándar.

### 6.4 No tocar modelos
Los modelos GGUF se leen pero no se modifican, convierten, mueven ni renombran. El profiler opera sobre copias de referencia o rutas existentes.

### 6.5 Local-only
Sin conexión externa. Sin DeepSeek API. Sin servicios remotos. Todos los datos residen localmente.

### 6.6 Sin DeepSeek
El profiler mide exclusivamente modelos locales GGUF. DeepSeek API (H3.2) tiene su propio mecanismo de monitoreo.

### 6.7 Resultados append-only
Los resultados de benchmark se agregan a un archivo JSONL. Nunca se modifican ni eliminan entradas existentes. Esto garantiza auditabilidad total.

### 6.8 No reemplaza Model Bank Audit
El Model Bank Audit (H3.1) es el inventario estático de modelos (formato, tamaño, licencia). El Model Profiler agrega la dimensión dinámica de rendimiento. Ambos se complementan.

---

## 7. Métricas propuestas

### 7.1 Métricas de rendimiento

| Métrica | Unidad | Descripción | Cómo se mide |
|---------|--------|-------------|--------------|
| **Tiempo de carga (cold start)** | segundos | Tiempo desde que se invoca llama-cli hasta que el modelo está listo para generar | `time` antes/después de subprocess; parsear stderr si no hay flag de timing |
| **Tiempo hasta primer token (TTFT)** | milisegundos | Tiempo desde que el modelo recibe el prompt hasta que genera el primer token | Medición con `time.perf_counter()` alrededor de `subprocess.run()`; estimación si `--no-show-timings` está activo |
| **Tokens/segundo (throughput)** | tokens/s | Velocidad de generación de tokens | `len(output_tokens) / (tiempo_total - ttft)` |
| **RAM aproximada** | MB | Uso de memoria del proceso llama-cli durante la inferencia | `psutil` o lectura de `/proc` en Windows (tasklist/Get-Process) |
| **Estabilidad** | % (0-100) | Proporción de ejecuciones exitosas vs. total de intentos | `éxitos / (éxitos + fallos) * 100` sobre múltiples corridas |
| **Tasa de fallos** | % (0-100) | Proporción de ejecuciones que terminan en error o timeout | `fallos / total * 100` |

### 7.2 Métricas de calidad

| Métrica | Rango | Descripción |
|---------|-------|-------------|
| **Calidad percibida** | 0.0 - 1.0 | Evaluación subjetiva de la respuesta del modelo ante prompts estandarizados |
| **Adherencia a instrucciones** | 0.0 - 1.0 | Qué tan bien sigue las instrucciones del prompt (formato, contenido, restricciones) |
| **Español básico** | 0.0 - 1.0 | Calidad del español: gramática, coherencia, naturalidad |
| **Razonamiento simple** | 0.0 - 1.0 | Capacidad de razonar paso a paso sobre problemas simples |
| **Utilidad técnica** | 0.0 - 1.0 | Utilidad práctica de la respuesta para tareas técnicas (troubleshooting, explicaciones) |

### 7.3 Métrica compuesta

| Métrica | Fórmula | Descripción |
|---------|---------|-------------|
| **Costo local estimado** | `(RAM_MB / 1000) * (1 / tokens_por_segundo)` | Índice compuesto que relaciona consumo de recursos con velocidad. Menor = mejor |
| **Score recomendado** | `promedio(calidad_percibida, adherencia, español, razonamiento, utilidad) * (estabilidad / 100)` | Puntaje general para comparar modelos. 0.0 - 1.0 |

---

## 8. Set de prompts benchmark propuesto

| ID | Prompt | Categoría | Propósito |
|:--:|--------|-----------|-----------|
| P1 | "Hola, ¿cómo estás?" | Smoke test / Español básico | Verificar que el modelo responde, mide latencia mínima |
| P2 | "Explica qué es una variable en programación en una frase." | Quality sanity / Utilidad técnica | Evaluar claridad y precisión técnica |
| P3 | "Mi PC no enciende. ¿Qué puedo revisar?" | Troubleshooting / Utilidad técnica | Evaluar capacidad de troubleshooting estructurado |
| P4 | "¿Qué es un agujero negro? Explícalo en 3 oraciones." | Quality sanity / Razonamiento simple | Evaluar capacidad de explicación conceptual breve |
| P5 | "Resume este texto en una oración: 'El aprendizaje automático es una rama de la inteligencia artificial que permite a los sistemas aprender y mejorar a partir de la experiencia sin ser programados explícitamente.'" | Instruction following / Resumen | Evaluar capacidad de seguir instrucciones de formato |
| P6 | "Clasifica esta frase como 'positiva', 'negativa' o 'neutral': 'El servicio fue excelente, pero la espera fue muy larga.'" | Instruction following / Clasificación | Evaluar adherencia a formato de salida específico |
| P7 | "Haz un plan de 3 pasos para organizar una mudanza pequeña." | Routing suitability / Generación de plan | Evaluar capacidad de generar planes estructurados |
| P8 | "Responde en español: What is the capital of France?" | Español básico / Instruction following | Evaluar capacidad de cambiar de idioma y mantener coherencia |

### 8.1 Criterios de evaluación por prompt

| Prompt | Criterio de éxito | Peso en score |
|:------:|-------------------|:-------------:|
| P1 | Respuesta no vacía, coherente, en español | 5% |
| P2 | Definición correcta, una frase, sin errores técnicos | 15% |
| P3 | Pasos lógicos, causa probable identificada, solución accionable | 20% |
| P4 | Explicación correcta, 3 oraciones, sin divagaciones | 15% |
| P5 | Resumen correcto, una oración, captura la idea principal | 15% |
| P6 | Clasificación correcta, formato exacto solicitado | 10% |
| P7 | 3 pasos claros, orden lógico, accionables | 15% |
| P8 | Respuesta en español, correcta, sin mezcla de idiomas | 5% |

---

## 9. Categorías de benchmark

### 9.1 Smoke test
- **Propósito**: Verificar que el modelo carga, responde y no falla inmediatamente
- **Prompts**: P1
- **Corridas**: 1
- **Duración estimada**: < 30 segundos
- **Criterio de éxito**: Respuesta no vacía, sin errores de subprocess

### 9.2 Latency test
- **Propósito**: Medir rendimiento puro (carga, TTFT, tokens/s, RAM)
- **Prompts**: P1, P2 (prompts cortos para minimizar variación por contenido)
- **Corridas**: 3 (promedio + desviación estándar)
- **Duración estimada**: 2-5 minutos por modelo
- **Criterio de éxito**: Métricas estables con desviación < 20%

### 9.3 Quality sanity test
- **Propósito**: Evaluar calidad básica de respuestas
- **Prompts**: P2, P3, P4, P5
- **Corridas**: 1 (evaluación cualitativa)
- **Duración estimada**: 3-8 minutos por modelo
- **Criterio de éxito**: Score de calidad > 0.5

### 9.4 Instruction following test
- **Propósito**: Evaluar capacidad de seguir instrucciones de formato y contenido
- **Prompts**: P5, P6, P8
- **Corridas**: 1
- **Duración estimada**: 2-5 minutos por modelo
- **Criterio de éxito**: Adherencia > 0.6

### 9.5 Routing suitability test
- **Propósito**: Determinar para qué rol es adecuado el modelo en el sistema multimodelo
- **Prompts**: P2, P3, P7 (todos los tipos de tarea)
- **Corridas**: 1
- **Duración estimada**: 3-6 minutos por modelo
- **Criterio de éxito**: Score compuesto que determina rol sugerido

---

## 10. Salida esperada del profiler

### 10.1 Campos por modelo benchmarkeado

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `modelo` | string | Nombre del modelo (ej: "Granite 3.0 1B-A400M-Instruct") |
| `archivo` | string | Nombre del archivo GGUF (ej: "granite-3.0-1b-a400m-instruct-Q4_K_M.gguf") |
| `tamaño_mb` | int | Tamaño del archivo en MB |
| `cuantización` | string | Tipo de cuantización (ej: "Q4_K_M", "Q8_0") |
| `familia` | string | Familia del modelo (ej: "granite", "smollm2") |
| `fecha_benchmark` | string (ISO 8601) | Fecha y hora del benchmark |
| `smoke_pass` | bool | Resultado del smoke test |
| `latency_avg_ms` | float | Latencia promedio en ms (TTFT) |
| `latency_std_ms` | float | Desviación estándar de latencia |
| `tokens_por_segundo` | float | Throughput en tokens/s |
| `ram_mb` | float | Uso de RAM aproximado |
| `estabilidad` | float | 0.0 - 1.0 |
| `tasa_fallos` | float | 0.0 - 1.0 |
| `calidad_percibida` | float | 0.0 - 1.0 |
| `adherencia_instrucciones` | float | 0.0 - 1.0 |
| `espanol` | float | 0.0 - 1.0 |
| `razonamiento` | float | 0.0 - 1.0 |
| `utilidad_tecnica` | float | 0.0 - 1.0 |
| `score_recomendado` | float | 0.0 - 1.0 (métrica compuesta) |
| `rol_sugerido` | string | Rol recomendado: "primary", "critic", "router", "fallback", "lab", "none" |
| `notas` | string | Observaciones adicionales |

### 10.2 Ejemplo de salida (formato JSONL futuro)

```json
{
  "modelo": "Granite 3.0 1B-A400M-Instruct",
  "archivo": "granite-3.0-1b-a400m-instruct-Q4_K_M.gguf",
  "tamaño_mb": 780,
  "cuantizacion": "Q4_K_M",
  "familia": "granite",
  "fecha_benchmark": "2026-05-01T14:30:00-03:00",
  "smoke_pass": true,
  "latency_avg_ms": 2450.5,
  "latency_std_ms": 180.3,
  "tokens_por_segundo": 15.2,
  "ram_mb": 1200.0,
  "estabilidad": 1.0,
  "tasa_fallos": 0.0,
  "calidad_percibida": 0.85,
  "adherencia_instrucciones": 0.90,
  "espanol": 0.88,
  "razonamiento": 0.82,
  "utilidad_tecnica": 0.87,
  "score_recomendado": 0.86,
  "rol_sugerido": "primary",
  "notas": "Modelo actual en producción. Benchmark de referencia para comparación."
}
```

---

## 11. Formato futuro de resultados

### 11.1 Ubicación de artefactos

```
ops/model_profiler/                    # Artefactos del profiler (futuro)
├── results.jsonl                      # Resultados append-only (Fase 1)
├── reports.md                         # Reporte legible generado a partir de results.jsonl
└── .gitkeep                           # Para mantener la carpeta en el repo

docs/hextech/
└── MODEL_PROFILER_DESIGN.md           # Este documento (H3.5)
```

**Nota**: En H3.5 no se crea `ops/model_profiler/`. Es solo una ubicación propuesta para fases futuras.

### 11.2 Formato results.jsonl (Fase 1)

- Cada línea es un JSON independiente con los campos de la sección 10.1
- Append-only: nunca se modifican ni eliminan líneas existentes
- Un modelo puede tener múltiples entradas (benchmarks repetidos para tracking de cambios)
- La entrada más reciente por modelo es la que se considera activa

### 11.3 Formato reports.md (Fase 1+)

- Reporte generado automáticamente a partir de `results.jsonl`
- Tabla comparativa de todos los modelos benchmarkeados
- Ranking por score recomendado
- Recomendaciones de asignación de roles
- Sección de notas y observaciones

---

## 12. Relación con Model Bank Audit (H3.1)

| Aspecto | Model Bank Audit (H3.1) | Model Profiler (H3.5) |
|---------|------------------------|----------------------|
| **Propósito** | Inventario estático | Evaluación dinámica |
| **Qué mide** | Formato, tamaño, fecha, licencia | Rendimiento, calidad, estabilidad |
| **Formato** | Documento Markdown | JSONL + reportes |
| **Frecuencia** | Una vez (inventario inicial) | Periódica (cada benchmark) |
| **Estado** | ✅ Completado | 🔵 Diseño (esta tarea) |
| **Output** | 12 GGUF clasificados, 3 safetensors identificados | Scores, roles sugeridos, métricas |

El profiler **consume** el inventario de H3.1 para saber qué modelos están disponibles y cuáles tienen prioridad de benchmark. H3.1 identificó que los 12 GGUF son utilizables directamente; el profiler determinará cuáles son realmente útiles para cada rol.

---

## 13. Relación con Multimodel Routing (H3.3)

| Componente H3.3 | Relación con H3.5 |
|-----------------|-------------------|
| **Matriz de decisión** (sección 5) | El profiler alimenta la matriz con datos reales de rendimiento por modelo |
| **Categorías de modelos** (local_micro, local_liviano, local_mediano, local_pesado) | El profiler asigna `rol_sugerido` basado en métricas |
| **Política de fallback** | El profiler identifica qué modelos son estables para fallback |
| **Criterios de selección** | Las métricas del profiler (latencia, calidad, RAM) son inputs directos |
| **H3.5+ benchmark automático** (sección 5 de H3.3) | Esta tarea (H3.5) es el diseño que H3.3 referenciaba como futuro |

**Ver también**: `MULTIMODEL_ROUTING_DESIGN.md` sección 5 (exclusión de benchmark automático) y sección 18 (relación con profiling).

---

## 14. Relación con RN Graph System (H3.4)

| Elemento del grafo | Relación con H3.5 |
|--------------------|-------------------|
| **Nodo `Model`** | Los modelos benchmarkeados se registran como nodos con atributos del profiler |
| **Arista `USED_MODEL`** | Cuando un modelo benchmarkeado se usa en una tarea, se crea la arista |
| **Arista `OBSERVED_BY`** | El profiler (o RN-MP futuro) observa y registra los resultados |
| **Metadata de nodo `Model`** | Incluye `size_mb`, `quant`, `family` del profiler |
| **Fase 1 de almacenamiento** | `results.jsonl` del profiler puede ser consumido por el grafo |

**Ver también**: `RN_GRAPH_SYSTEM_DESIGN.md` sección 7 (nodo `Model`), sección 8 (arista `USED_MODEL`), sección 16 (RN-MP).

---

## 15. Relación con RN Model Profiler (RN-MP) futuro

| Aspecto | H3.5 (Model Profiler Design) | RN-MP (futuro, H3.8+) |
|---------|------------------------------|----------------------|
| **Naturaleza** | Diseño conceptual | Neurona RN Family |
| **Implementación** | No se implementa | Se implementa como neurona |
| **Autonomía** | Manual (Cline ejecuta) | Automática (RN-MP ejecuta) |
| **Integración** | Independiente | Integrada con RN Core, RN-PS, RN-GK |
| **Fase** | H3.5 | H3.8+ |
| **Riesgo** | Bajo (solo diseño) | Bajo (solo medición, ver RN_SELF_WORK_PLAN.md sección 11) |

RN-MP (RN Model Profiler) es la neurona candidata de RN Family que automatizará el profiling en fases futuras. H3.5 establece el diseño conceptual que RN-MP implementará. RN-MP sigue siendo prioridad baja y fase estimada H3.8+ según `RN_SELF_WORK_PLAN.md` (sección 11.1) y `RN_FAMILY.md` (sección 10.5).

---

## 16. Relación con RN Provider Supervisor (RN-PS) futuro

| Aspecto | H3.5 (Model Profiler) | RN-PS (futuro, H3.8+) |
|---------|----------------------|----------------------|
| **Qué mide** | Rendimiento de modelos (benchmark) | Salud de providers en runtime |
| **Cuándo mide** | Fuera de línea (sesión de benchmark) | En línea (durante operación) |
| **Output** | Score recomendado, rol sugerido | Alertas, failover, reportes de salud |
| **Dependencia** | Independiente | Consume métricas del profiler |

RN-PS consumirá las métricas de profiling para establecer líneas de base de rendimiento y detectar degradación en runtime. Por ejemplo, si un modelo que en benchmark daba 15 tokens/s ahora da 5 tokens/s, RN-PS puede alertar o activar failover.

---

## 17. Riesgos y mitigaciones

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|:-----------:|:-------:|------------|
| MP-R1 | Contaminación de caché del sistema al ejecutar benchmarks (archivos temporales de llama.cpp) | Alta | Bajo | Definir limpieza post-benchmark en el diseño; incluir paso de cleanup |
| MP-R2 | Consumo de RAM durante benchmark interfiere con otros procesos | Media | Medio | Benchmarks secuenciales, no paralelos; medir RAM antes/después; priorizar modelos livianos |
| MP-R3 | Benchmarks no reproducibles por variación de carga del sistema | Alta | Medio | Incluir timestamp, temperatura de CPU, procesos en background en metadata; múltiples corridas |
| MP-R4 | Benchmarks largos (modelos de 3GB+) consumen tiempo sin valor inmediato | Media | Bajo | Priorizar modelos livianos/medios primero; smoke test rápido antes de full benchmark |
| MP-R5 | Falsa sensación de precisión en métricas (una sola corrida no es estadísticamente significativa) | Alta | Medio | Diseñar múltiples corridas (3+) con promedio y desviación estándar |
| MP-R6 | Duplicación con `model_benchmark.py` existente | Media | Bajo | El diseño debe integrarse, no reemplazar, la infraestructura de dataclasses existente |
| MP-R7 | Benchmarks que modifican accidentalmente la configuración actual de AURA | Baja | Alto | El profiler debe operar en modo solo lectura; no debe cambiar config.py ni registry |
| MP-R8 | Evaluación de calidad subjetiva (diferentes evaluadores pueden dar diferentes scores) | Alta | Medio | Definir criterios de evaluación explícitos por prompt (sección 8.1); usar rúbricas |

---

## 18. Fases futuras H3.5.x

| Sub-fase | Acción | Dependencias | Archivos afectados |
|----------|--------|:-----------:|--------------------|
| **H3.5.0** | ✅ Diseño y documentación (esta tarea) | H3.0, H3.1, H3.2, H3.3, H3.4 | `docs/hextech/MODEL_PROFILER_DESIGN.md` |
| H3.5.1 | Crear `ops/model_profiler/` con estructura de directorios + `.gitkeep` | H3.5.0 | `ops/model_profiler/` |
| H3.5.2 | Script `smoke_test.py` — verifica que un modelo GGUF carga y responde | H3.5.1 | `ops/model_profiler/smoke_test.py` |
| H3.5.3 | Script `latency_test.py` — mide TTFT, tokens/s, RAM, estabilidad | H3.5.2 | `ops/model_profiler/latency_test.py` |
| H3.5.4 | Script `quality_test.py` — ejecuta set de prompts y evalúa calidad básica | H3.5.3 | `ops/model_profiler/quality_test.py` |
| H3.5.5 | Script `profiler_orchestrator.py` — orquesta las pruebas y produce `results.jsonl` | H3.5.4 | `ops/model_profiler/profiler_orchestrator.py` |
| H3.5.6 | Integrar con `model_registry.py` — actualizar `benchmark_readiness` post-benchmark | H3.5.5 + aprobación | `agents/model_registry.py` (zona protegida) |
| H3.5.7 | Tests de integración del profiler (sin modelos reales, con mocks) | H3.5.6 | `tests/test_model_profiler.py` |
| H3.5.8 | Primer benchmark real supervisado (solo modelos livianos, usuario presente) | H3.5.7 + aprobación | `ops/model_profiler/results.jsonl` |

---

## 19. Tests/verificaciones futuras (post-ACT)

Checklist que se verificará después de implementar en ACT MODE:

- [ ] Documento creado en `docs/hextech/MODEL_PROFILER_DESIGN.md`
- [ ] Enlaces agregados en `README.md` y `CONTEXT_MAP.md`
- [ ] Referencias a H3.5 actualizadas en `RN_SELF_WORK_PLAN.md`, `RN_FAMILY.md`, `MODEL_BANK_AUDIT.md`, `MULTIMODEL_ROUTING_DESIGN.md`, `RN_GRAPH_SYSTEM_DESIGN.md`
- [ ] No hay archivos de código modificados (solo documentación)
- [ ] No hay benchmarks ejecutados
- [ ] No hay modelos tocados
- [ ] No hay archivos creados en `ops/model_profiler/`
- [ ] `git diff --stat` muestra solo archivos de documentación modificados

---

## 20. Checklist antes de correr el primer benchmark real (H3.5.8)

- [ ] Este documento H3.5 aprobado por el usuario
- [ ] Plan H3.5.x detallado y aprobado
- [ ] Scripts de benchmark implementados y probados con mocks
- [ ] No hay cambios pendientes en Git
- [ ] Modo ACT MODE habilitado para implementación
- [ ] `ops/model_profiler/` creado con estructura completa
- [ ] Tests de integración pasando
- [ ] Modelo seleccionado para primer benchmark (prioridad: liviano < 1GB)
- [ ] Usuario presente durante ejecución
- [ ] Sin procesos pesados ejecutándose en segundo plano
- [ ] Rollback plan definido (restaurar `results.jsonl` si algo sale mal)
- [ ] Reglas de seguridad revisadas y comprendidas

---

## 21. Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 27/4/2026 | v1.0 | Creación inicial como parte de H3.5 — Diseño conceptual Model Profiler / Benchmark |

---

**Ubicación**: `docs/hextech/MODEL_PROFILER_DESIGN.md`  
**Responsable**: Cline bajo supervisión Hextech  
**Estado**: Documentación de diseño (H3.5)  
**Próxima fase**: H3.5.1 — Esqueleto `ops/model_profiler/` (requiere aprobación)
