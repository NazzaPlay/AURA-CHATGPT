# RN Graph System Design — H3.4

## 1. Propósito

Diseñar conceptualmente el **RN Graph System**: un sistema de grafos futuro para registrar y relacionar decisiones, tareas, modelos, commits, tests, fallos, archivos, providers, neuronas RN Family y resultados de AURA Self-Work.

Este documento establece las bases conceptuales para que, en fases futuras (H3.5+), se pueda implementar un grafo que complemente a Git como sistema de trazabilidad semántica, sin reemplazarlo.

**Fase**: H3.4 — Diseño conceptual del RN Graph System  
**Estado**: Documentación de diseño (no implementación)  
**Fecha**: 27/4/2026  

---

## 2. Alcance

- **Solo diseño conceptual**: No se implementa código, no se crea base de datos, no se generan archivos JSON/JSONL.
- Define: nodos, aristas, metadata, eventos, relación con RN Family, almacenamiento futuro.
- No define: implementación de RN Graph Keeper (será H3.7), integración con Git hooks, visualizaciones automáticas.
- **Relación con H3.0**: Concreta la sección 10 de `RN_SELF_WORK_PLAN.md` (RN Graph System).
- **Relación con H3.3**: Consume la sección 18 de `MULTIMODEL_ROUTING_DESIGN.md` (relación con RN-GK).

---

## 3. Estado actual

- **No existe grafo implementado** en el proyecto AURA.
- No hay archivos JSON/JSONL de nodos ni aristas.
- No hay base de datos de grafos (SQLite, networkx, Neo4j).
- **RN Graph Keeper (RN-GK)** está en fase conceptual, con implementación estimada para H3.7.
- `RN_SELF_WORK_PLAN.md` (sección 10) ya introduce el concepto de RN Graph System.
- `MULTIMODEL_ROUTING_DESIGN.md` (sección 18) ya discute la relación entre routing y RN-GK.

---

## 4. Definición de RN Graph System

El **RN Graph System** es un sistema de registro basado en grafos que modela las relaciones entre todos los elementos que participan en el ciclo de vida de AURA Self-Work:

- **Tareas** que Cline ejecuta
- **Decisiones** que se toman durante una tarea
- **Modelos** de IA que se utilizan
- **Providers** que ejecutan los modelos
- **Archivos** que se crean, modifican o leen
- **Commits** de Git que se generan
- **Tests** que se ejecutan (pasados o fallados)
- **Fallos** que ocurren (runtime, test, conexión)
- **Riesgos** que RN identifica
- **Neuronas RN Family** que participan
- **Aprobaciones del usuario**
- **Artefactos** generados (documentos, planes, propuestas)
- **Eventos de memoria** relevantes

El grafo es **dirigido** (aristas con dirección), **etiquetado** (tipos de nodos y aristas), **ponderado** (peso opcional en aristas) y **temporal** (cada nodo y arista tiene timestamp).

---

## 5. Qué NO hará la primera versión (H3.4)

| Exclusión | Motivo |
|-----------|--------|
| ❌ No implementar código de grafo | H3.4 es solo diseño conceptual |
| ❌ No crear base de datos | Requiere plan de implementación aprobado (H3.5+) |
| ❌ No modificar RN Core | RN tiene su propio protocolo (RN_WRITE_ALLOWED) |
| ❌ No crear RN Graph Keeper todavía | RN-GK es neurona futura H3.7 |
| ❌ No integrar con Git hooks | Requiere RN Commit Auditor (H3.7) |
| ❌ No generar visualizaciones automáticas | Depende de fase 3 (grafo real) |
| ❌ No reemplazar Git como sistema de registro | El grafo complementa, no sustituye |
| ❌ No tocar memory.json, logs/, .venv/, __pycache__/ | Reglas absolutas de .clinerules |
| ❌ No instalar dependencias (networkx, Neo4j, SQLite) | Solo se mencionan como opciones futuras |

---

## 6. Principios de diseño

### 6.1 Append-only
Los eventos solo se agregan al grafo. Nunca se modifican ni eliminan entradas existentes. Esto garantiza auditabilidad total.

### 6.2 Auditabilidad
Cada nodo y arista tiene timestamp y origen. Es posible reconstruir el estado del sistema en cualquier punto del tiempo.

### 6.3 Bajo costo
El almacenamiento inicial es texto plano (JSONL). Overhead mínimo de CPU/RAM. Sin servidores ni procesos en background.

### 6.4 Local-first
El grafo funciona completamente sin conexión externa. Todos los datos residen localmente en `ops/rn_graph/`.

### 6.5 Privacidad
No se guardan prompts completos, API keys, contenido completo de archivos ni `memory.json` completo. Los datos sensibles se truncan o excluyen antes de persistir.

### 6.6 No modifica RN Core
El grafo **observa y registra**, pero no interviene en las operaciones de RN Core ni de ningún componente protegido.

### 6.7 No reemplaza Git
Git sigue siendo el sistema de control de versiones y trazabilidad de cambios. El grafo complementa con relaciones semánticas que Git no modela (qué modelo se usó, qué riesgo se detectó, qué decisión se tomó).

---

## 7. Nodos propuestos (13 tipos)

| Tipo | Descripción | Atributos base |
|------|-------------|----------------|
| **Task** | Una tarea o subtarea ejecutada por Cline/AURA | `id`, `description`, `type`, `status`, `timestamp`, `duration_ms` |
| **Decision** | Decisión tomada durante una tarea | `id`, `rationale`, `option_chosen`, `alternatives`, `timestamp` |
| **Model** | Modelo de IA utilizado | `id`, `name`, `format`, `size_mb`, `source`, `quant`, `family` |
| **Provider** | Proveedor que ejecutó el modelo | `id`, `name`, `is_local`, `backend_type`, `family` |
| **File** | Archivo creado/modificado/leído | `id`, `path`, `extension`, `action`, `size_before`, `size_after` |
| **Commit** | Commit de Git generado | `id`, `hash`, `message`, `files_changed`, `author`, `timestamp` |
| **Test** | Test ejecutado | `id`, `test_name`, `test_file`, `duration_ms`, `result` |
| **Failure** | Fallo detectado (test, runtime, conexión, etc.) | `id`, `type`, `severity`, `component`, `summary` |
| **Risk** | Riesgo identificado por RN | `id`, `risk_id` (R1..Rn), `probability`, `impact`, `mitigation` |
| **RNNeuron** | Neurona RN Family involucrada | `id`, `neuron_id`, `name`, `family`, `version`, `risk_level` |
| **UserApproval** | Aprobación o rechazo del usuario | `id`, `approved` (bool), `context`, `timestamp` |
| **Artifact** | Artefacto generado (documento, plan, propuesta) | `id`, `type`, `path`, `description`, `format` |
| **MemoryEvent** | Evento de memoria relevante | `id`, `component`, `event_type`, `summary` |

### 7.1 Estructura JSON de ejemplo (nodo Task)

```json
{
  "node_type": "Task",
  "id": "task-h3-4-001",
  "description": "Diseñar RN Graph System conceptual",
  "type": "documentation",
  "status": "completed",
  "timestamp": "2026-04-27T20:30:00-03:00",
  "duration_ms": 450000,
  "metadata": {
    "phase": "H3.4",
    "mode": "plan",
    "risk_level": "bajo"
  }
}
```

---

## 8. Aristas propuestas (13 tipos)

| Tipo | Origen → Destino | Significado |
|------|-----------------|-------------|
| **CREATED_BY** | Artifact → Task | El artefacto fue creado por la tarea |
| **USED_MODEL** | Task → Model | La tarea usó este modelo |
| **USED_PROVIDER** | Task → Provider | La tarea usó este proveedor |
| **MODIFIED_FILE** | Task → File | La tarea modificó este archivo |
| **GENERATED_COMMIT** | Task → Commit | La tarea generó este commit |
| **VALIDATED_BY_TEST** | Commit/File → Test | El elemento fue validado por este test |
| **FAILED_WITH** | Task → Failure | La tarea falló con este error |
| **MITIGATED_BY** | Risk → Decision/RNNeuron | El riesgo fue mitigado por esta acción |
| **APPROVED_BY** | Task/Decision → UserApproval | El elemento fue aprobado/rechazado por el usuario |
| **BLOCKED_BY** | Task → Risk/RNNeuron | La tarea fue bloqueada por este riesgo o neurona |
| **DEPENDS_ON** | Task/RNNeuron → Task/RNNeuron | Dependencia entre elementos |
| **SUPERSEDED_BY** | Artifact/Decision → Artifact/Decision | El elemento fue reemplazado por otro |
| **OBSERVED_BY** | Cualquier nodo → RNNeuron | El evento fue observado por esta neurona |

### 8.1 Estructura JSON de ejemplo (arista)

```json
{
  "edge_type": "USED_MODEL",
  "source_id": "task-h3-4-001",
  "target_id": "model-granite-4-0-350m",
  "weight": 1.0,
  "confidence": 1.0,
  "timestamp": "2026-04-27T20:30:00-03:00",
  "metadata": {
    "context": "Modelo local para tarea de documentación",
    "role": "primary_conversational"
  }
}
```

---

## 9. Metadata mínima por nodo

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|:-----------:|-------------|
| `node_type` | string | ✅ | Tipo de nodo (Task, Decision, Model, etc.) |
| `id` | string | ✅ | Identificador único |
| `timestamp` | string (ISO 8601) | ✅ | Cuándo se creó el nodo |
| `metadata` | dict | ❌ | Datos adicionales específicos del tipo |
| `source` | string | ❌ | Origen del dato (Cline, RN, usuario) |

Cada tipo de nodo tiene además sus atributos específicos (ver sección 7).

---

## 10. Metadata mínima por arista

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|:-----------:|-------------|
| `edge_type` | string | ✅ | Tipo de arista (USED_MODEL, CREATED_BY, etc.) |
| `source_id` | string | ✅ | ID del nodo origen |
| `target_id` | string | ✅ | ID del nodo destino |
| `weight` | float | ❌ | Peso de la relación (0.0 a 1.0, default 1.0) |
| `confidence` | float | ❌ | Confianza en la relación (0.0 a 1.0) |
| `timestamp` | string (ISO 8601) | ✅ | Cuándo se registró la arista |
| `metadata` | dict | ❌ | Datos adicionales |

---

## 11. Eventos a registrar (10 tipos)

| Evento | Nodo(s) generado(s) | Arista(s) generada(s) |
|--------|---------------------|----------------------|
| **Plan generado** | Artifact(plan), Task | CREATED_BY(Artifact → Task) |
| **ACT ejecutado** | Task(status=completed) | MODIFIED_FILE(Task → File) por cada archivo |
| **Test pasado/fallado** | Test, Failure(si falla) | VALIDATED_BY_TEST(Commit/File → Test), FAILED_WITH(Task → Failure) |
| **Commit creado** | Commit | GENERATED_COMMIT(Task → Commit) |
| **Provider seleccionado** | Provider, Decision | USED_PROVIDER(Task → Provider) |
| **Fallback ejecutado** | Decision, Provider(fallback) | USED_PROVIDER(Task → Provider), DEPENDS_ON(Decision → Risk) |
| **RN risk detected** | Risk | BLOCKED_BY(Task → Risk), OBSERVED_BY(Risk → RNNeuron) |
| **Usuario aprueba/rechaza** | UserApproval | APPROVED_BY(Task/Decision → UserApproval) |
| **Limpieza DEV-CLEANUP** | Task(cleanup), MemoryEvent | CREATED_BY(MemoryEvent → Task) |
| **Neurona RN Family activada** | RNNeuron | OBSERVED_BY(nodo observado → RNNeuron) |

---

## 12. Relación con AURA Self-Work

El RN Graph System es un componente clave del **AURA Self-Work Loop** (definido en `RN_SELF_WORK_PLAN.md` sección 6):

1. **Self-Work genera datos**: Cada paso del loop (plan, act, test, commit) produce nodos y aristas.
2. **El grafo alimenta decisiones futuras**: Consultando el grafo, AURA puede:
   - Saber qué modelo funcionó mejor para cierto tipo de tarea
   - Detectar patrones de fallo recurrentes
   - Identificar dependencias entre componentes
   - Medir el impacto de cambios anteriores
3. **El grafo no interfiere**: Solo observa y registra. No bloquea ni modifica el flujo de Self-Work.

**Regla**: En modo Self-Work, el grafo opera en local-only. No envía datos a ningún servicio externo.

---

## 13. Relación con Multimodel Routing (H3.3)

El RN Graph System consume los datos generados por el sistema de routing multimodelo:

- Cada vez que se selecciona un provider → se crea un nodo `Provider` + arista `USED_PROVIDER`
- Cada vez que se usa un modelo → se crea un nodo `Model` + arista `USED_MODEL`
- Cada fallback ejecutado → se crea un nodo `Decision` + arista `USED_PROVIDER` al fallback
- Cada validación cruzada → se crean aristas `VALIDATED_BY_TEST` y `OBSERVED_BY`

**Ver también**: `MULTIMODEL_ROUTING_DESIGN.md` sección 18 (relación con RN-GK).

---

## 14. Relación con DeepSeek Provider (H3.2)

El RN Graph System registrará eventos relacionados con DeepSeek API cuando esté activo:

- Disponibilidad del provider → nodo `Provider` con atributos de estado
- Rate limiting → nodo `Failure` con tipo `rate_limited`
- Budget excedido → nodo `Failure` con tipo `budget_exceeded`
- Fallback a local → arista `USED_PROVIDER` al provider local + nodo `Decision`
- Costo estimado → metadata en arista `USED_PROVIDER`

**Regla de seguridad**: No se registra la API key ni prompts completos enviados a DeepSeek.

---

## 15. Relación con Model Bank (H3.1)

El RN Graph System referencia los modelos del Model Bank:

- Cada modelo GGUF utilizado se registra como nodo `Model` con metadata del inventario H3.1
- Los safetensors no utilizados no se registran hasta su conversión (H3.6+)
- La metadata incluye: nombre, tamaño, cuantización, familia, prioridad

**Ver también**: `MODEL_BANK_AUDIT.md` para el inventario completo de 12 GGUF y 3 safetensors.

---

## 16. Relación con RN Family

| Neurona | ID | Rol en RN Graph System | Fase estimada |
|---------|:--:|------------------------|:-------------:|
| **RN Graph Keeper** | RN-GK | Neurona responsable de mantener y auditar el grafo. Valida consistencia, detecta ciclos, responde consultas. | H3.7 |
| **RN Commit Auditor** | RN-CA | Alimenta nodos `Commit` + aristas `GENERATED_COMMIT` | H3.7 |
| **RN Test Guardian** | RN-TG | Alimenta nodos `Test` + aristas `VALIDATED_BY_TEST` | H3.7 |
| **RN Plan Validator** | RN-PV | Alimenta nodos `Decision` + aristas `BLOCKED_BY` | H3.7 |
| **RN Provider Supervisor** | RN-PS | Alimenta nodos `Provider` + aristas `USED_PROVIDER` | H3.8+ |
| **RN Memory Repair** | RN-MR | Alimenta nodos `MemoryEvent` | H3.8+ |
| **RN Data Validator** | RN-DV | Valida metadata de nodos antes de insertar en el grafo | H3.8+ |

### 16.1 RN Graph Keeper (RN-GK) — Detalle

RN-GK es la neurona que **gestiona el grafo**. Sus responsabilidades serán:

- Insertar nuevos nodos y aristas (append-only)
- Validar consistencia estructural (no ciclos inválidos, no nodos huérfanos)
- Detectar ciclos en dependencias entre componentes RN Family
- Responder consultas: "¿qué archivos modificó esta tarea?", "¿qué modelo se usó para X?"
- Generar reportes periódicos de salud del grafo
- No modificar RN Core ni componentes protegidos

**Importante**: RN-GK **no se implementa en H3.4**. Es una neurona candidata para H3.7.

---

## 17. Almacenamiento futuro recomendado

### Fase 1: JSONL append-only (H3.5+)

Formato más simple y auditable. Cada línea es un JSON independiente.

```
ops/rn_graph/
├── events.jsonl      # Eventos en orden cronológico (append-only)
├── nodes.jsonl       # Nodos deduplicados (clave primaria: id)
└── edges.jsonl       # Aristas deduplicadas (clave primaria: source_id+target_id+edge_type)
```

**Ventajas**:
- Sin base de datos, sin dependencias externas
- Append-only garantiza auditabilidad
- Fácil de inspeccionar con `cat`, `grep`, `head`
- Backup simple (copiar archivos)
- Tamaño estimado: ~1-5 KB por tarea típica

**Desventajas**:
- Consultas complejas requieren scan lineal
- Sin integridad referencial automática
- Sin índices

### Fase 2: SQLite local (H3.7+)

Schema relacional con tablas `nodes`, `edges`, `events`.

```
ops/rn_graph/
├── rn_graph.db       # Base de datos SQLite
├── schema.sql        # Schema de referencia
└── migrations/       # Migraciones futuras
```

**Ventajas**:
- Consultas eficientes con SQL
- Integridad referencial (claves foráneas)
- Backup simple (un solo archivo .db)
- Sin servidor, sin configuración

**Desventajas**:
- Dependencia de sqlite3 (biblioteca estándar de Python)
- No modela grafos nativamente (consultas recursivas con CTE)

### Fase 3: Grafo real opcional (H3.9+)

Solo si se justifica por tamaño o necesidad de análisis avanzado.

| Opción | Cuándo usarla |
|--------|---------------|
| **networkx** (Python, en memoria) | Análisis ad-hoc, visualización, detección de ciclos |
| **Neo4j** (base de datos de grafos) | Grafos muy grandes (>100K nodos), consultas frecuentes, visualización |

**Requisito**: Cualquier opción de fase 3 requiere plan aprobado y justificación de necesidad.

---

## 18. Ubicación futura sugerida para artefactos

```
ops/rn_graph/                          # Artefactos del grafo (futuro)
├── events.jsonl                       # Fase 1: eventos append-only
├── nodes.jsonl                        # Fase 1: nodos
├── edges.jsonl                        # Fase 1: aristas
├── rn_graph.db                        # Fase 2: SQLite (futuro)
├── schema.sql                         # Fase 2: schema de referencia
└── migrations/                        # Fase 2: migraciones (futuro)

docs/hextech/
└── RN_GRAPH_SYSTEM_DESIGN.md          # Este documento (H3.4)
```

**Nota**: En H3.4 no se crea `ops/rn_graph/`. Es solo una ubicación propuesta para fases futuras.

---

## 19. Reglas de seguridad

### 19.1 Prohibiciones absolutas

| Regla | Descripción |
|-------|-------------|
| 🔒 No guardar API keys | En ningún nodo, arista ni metadata |
| 🔒 No guardar prompts completos con datos sensibles | Truncar o excluir antes de persistir |
| 🔒 No guardar contenido completo de archivos | Solo path + stats (size, hash opcional) |
| 🔒 No registrar memory.json completo | Solo eventos relevantes resumidos |
| 🔒 No tocar modelos | Solo metadata de referencia (nombre, tamaño, formato) |
| 🔒 No guardar credenciales | Passwords, tokens, secrets, credentials |
| 🔒 No guardar datos personales | DNI, CUIL, tarjetas, cuentas bancarias |

### 19.2 Reglas de logging seguro

| Elemento | Qué registrar | Qué NO registrar |
|----------|---------------|------------------|
| Provider | Nombre, tipo, is_local, familia | API key, tokens de autenticación |
| Modelo | Nombre, formato, tamaño, cuantización | Contenido del modelo |
| Archivo | Path, extensión, acción, tamaño | Contenido completo del archivo |
| Prompt | Solo metadata (tokens estimados, tipo) | Prompt completo si contiene datos sensibles |
| Error | Tipo, severidad, componente, resumen | Stack trace completo si contiene datos sensibles |

---

## 20. Ejemplos de flujo

### 20.1 Flujo completo: Cline genera plan → usuario aprueba → ACT modifica archivo → tests pasan → commit creado

```
Evento 1: Plan generado
  Nodo: Artifact(id="art-h3-4-plan", type="plan", path="docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md")
  Nodo: Task(id="task-h3-4", type="documentation", status="planned")
  Arista: CREATED_BY(source=art-h3-4-plan, target=task-h3-4)

Evento 2: Modelo usado
  Nodo: Model(id="model-granite-4-0-350m", name="granite-4.0-350m", format="gguf")
  Arista: USED_MODEL(source=task-h3-4, target=model-granite-4-0-350m)

Evento 3: Provider seleccionado
  Nodo: Provider(id="prov-local-primary", name="local_primary", is_local=true)
  Arista: USED_PROVIDER(source=task-h3-4, target=prov-local-primary)

Evento 4: Usuario aprueba
  Nodo: UserApproval(id="ua-h3-4-001", approved=true, context="plan_approval")
  Arista: APPROVED_BY(source=task-h3-4, target=ua-h3-4-001)

Evento 5: Archivo modificado
  Nodo: File(id="file-rn-graph-design", path="docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md", action="created")
  Arista: MODIFIED_FILE(source=task-h3-4, target=file-rn-graph-design)

Evento 6: Tests pasan
  Nodo: Test(id="test-diag-001", name="test_diagnostic_routing_fix", result="passed")
  Arista: VALIDATED_BY_TEST(source=file-rn-graph-design, target=test-diag-001)

Evento 7: Commit creado
  Nodo: Commit(id="commit-h3-4", hash="abc123def", message="H3.4 RN Graph System design")
  Arista: GENERATED_COMMIT(source=task-h3-4, target=commit-h3-4)

Evento 8: RN-GK observa
  Nodo: RNNeuron(id="rn-gk", name="RN Graph Keeper", family="Kernel")
  Arista: OBSERVED_BY(source=task-h3-4, target=rn-gk)
```

### 20.2 Flujo con fallback y riesgo

```
Evento: Provider remoto no disponible
  Nodo: Decision(id="dec-fallback-001", rationale="DeepSeek no disponible, fallback a local")
  Nodo: Provider(id="prov-local-fallback", name="transitional_fallback", is_local=true)
  Arista: USED_PROVIDER(source=task-complex-001, target=prov-local-fallback)
  Arista: DEPENDS_ON(source=dec-fallback-001, target=risk-conexion)

Evento: Riesgo detectado
  Nodo: Risk(id="risk-conexion", risk_id="DSK-R3", probability="alta", impact="medio")
  Arista: BLOCKED_BY(source=task-complex-001, target=risk-conexion)
```

---

## 21. Riesgos y mitigaciones

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|:-----------:|:-------:|------------|
| GR-R1 | Grafo crece sin control (archivos enormes) | Alta | Medio | Rotación diaria de JSONL, límite de tamaño configurable, poda de eventos viejos |
| GR-R2 | Datos duplicados o inconsistentes | Media | Medio | RN Data Validator futuro, deduplicación por id, validación de unicidad |
| GR-R3 | Ruido excesivo (eventos irrelevantes) | Alta | Bajo | Filtros de eventos por severidad/tipo, umbral de registro configurable |
| GR-R4 | Carga cognitiva extra para Cline al registrar eventos | Media | Medio | Automatización futura vía RN Family (RN-GK, RN-CA, RN-TG) |
| GR-R5 | Ciclos en grafo detectados tarde | Baja | Bajo | RN Graph Keeper validará consistencia periódicamente |
| GR-R6 | Confusión entre grafo y Git como sistema de registro | Media | Bajo | Principio explícito: el grafo complementa, no reemplaza Git |
| GR-R7 | Fuga de datos sensibles en metadata del grafo | Baja | Crítico | Reglas de seguridad estrictas (sección 19), revisión de campos antes de persistir |
| GR-R8 | Dependencia de fase 3 (Neo4j/networkx) sin justificación | Baja | Medio | Fase 3 solo si se justifica; fases 1 y 2 cubren la mayoría de casos |

---

## 22. Fases futuras H3.4.x

| Sub-fase | Acción | Dependencias | Archivos afectados |
|----------|--------|:-----------:|--------------------|
| **H3.4.0** | ✅ Diseño y documentación (esta tarea) | H3.0, H3.1, H3.2, H3.3 | `docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md` |
| H3.4.1 | Crear esqueleto `ops/rn_graph/` con estructura vacía | H3.4.0 | `ops/rn_graph/` (carpetas + .gitkeep) |
| H3.4.2 | Script Python para append JSONL (nodo/arista/evento) | H3.4.1 | `ops/rn_graph/rn_graph_appender.py` |
| H3.4.3 | Script Python para consultas básicas (por id, tipo, fecha) | H3.4.2 | `ops/rn_graph/rn_graph_query.py` |
| H3.4.4 | Tests de funcionalidad básica del grafo | H3.4.3 | `tests/test_rn_graph.py` |
| H3.4.5 | Integración con flujo Cline/Self-Work | H3.4.4 | Hooks en plan/act/completado |
| H3.4.6 | Validación cruzada con RN Family (GK, CA, TG) | H3.4.5 + H3.7 | Integración con RN-GK futuro |

---

## 23. Tests/verificaciones futuras (post-ACT)

Checklist que se verificará después de implementar en ACT MODE:

- [ ] Documento creado en `docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md`
- [ ] Enlaces agregados en `README.md` y `CONTEXT_MAP.md`
- [ ] Referencias a H3.4 actualizadas en `RN_SELF_WORK_PLAN.md` y `RN_FAMILY.md`
- [ ] No hay archivos JSON/JSONL creados en `ops/rn_graph/`
- [ ] No hay código implementado
- [ ] No hay modificaciones a RN, agents, providers, backend
- [ ] `git diff --stat` muestra solo archivos de documentación modificados

---

## 24. Checklist antes de implementar grafo real (H3.4.1+)

- [ ] Este documento H3.4 aprobado por el usuario
- [ ] Plan H3.4.x detallado y aprobado
- [ ] No hay cambios pendientes en Git
- [ ] Modo ACT MODE habilitado para implementación
- [ ] Ubicaciones de artefactos creadas (`ops/rn_graph/`)
- [ ] Tests definidos y aprobados
- [ ] Reglas de seguridad revisadas y comprendidas
- [ ] Sin dependencias externas (solo Python estándar para fase 1)

---

## 25. Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 27/4/2026 | v1.0 | Creación inicial como parte de H3.4 — Diseño conceptual RN Graph System |

---

**Ubicación**: `docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md`  
**Responsable**: Cline bajo supervisión Hextech  
**Estado**: Documentación de diseño (H3.4)  
**Próxima fase**: H3.4.1 — Esqueleto `ops/rn_graph/` (requiere aprobación)
