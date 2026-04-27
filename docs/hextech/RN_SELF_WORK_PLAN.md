# RN Self-Work Plan — Integración RN Core & RN Family para AURA Self-Work

## 1. Propósito

Este documento define el plan maestro para que AURA pueda **auto-trabajarse de forma segura**, utilizando:
- **RN Core** como núcleo operativo protegido (V1.8 sellado)
- **RN Family** como ecosistema de neuronas futuras
- **DeepSeek API** como proveedor externo inicial (futuro)
- **Sistema multimodelo** local/remoto
- **Banco de modelos local** (externo al repo)
- **Conversión futura de modelos a GGUF**
- **Sistema de grafos para RN** (RN Graph)
- **Registro de metadata, pruebas, decisiones, commits, fallos y dependencias**

**Fase actual**: H3.0 — Documento maestro de integración RN/Self-Work
**Estado**: Documentación conceptual (no implementación)
**Protección**: Este documento NO modifica RN Core. NO requiere `RN_WRITE_ALLOWED`.

---

## 2. Definición de AURA Self-Work

**AURA Self-Work** es la capacidad de AURA de analizar, planificar y modificar su propio código, documentación y configuración bajo un flujo controlado que garantiza:

- **Seguridad**: Ninguna operación se ejecuta sin validación múltiple
- **Trazabilidad**: Todo cambio queda registrado en Git y metadata
- **Supervisión**: El usuario siempre tiene la última palabra en cambios críticos
- **Reversibilidad**: Todo cambio debe ser reversible

### 2.1 Principios fundamentales

1. **RN Core observa y mide**, pero no se auto-modifica
2. **RN Family ejecuta** bajo contratos definidos y supervisión
3. **El usuario aprueba** antes de cualquier cambio crítico
4. **Cline ejecuta** bajo las reglas de `.clinerules`
5. **Git registra** todo cambio con trazabilidad completa

---

## 3. Qué puede hacer AURA sola

Sin requerir aprobación del usuario (autonomía controlada):

| Acción | Descripción | Límite |
|--------|-------------|--------|
| Leer y analizar su propio código | Diagnóstico de estructura, imports, dependencias | Solo lectura |
| Ejecutar diagnósticos internos | Tests de diagnóstico, verificación de estado | No modificar |
| Proponer mejoras documentadas | Generar propuestas en `docs/` | Solo escritura en `docs/hextech/` |
| Registrar metadata de operaciones | Logs de diagnóstico, reportes | No modificar `logs/` existentes |
| Actualizar documentación propia | `docs/hextech/`, `README.md` (enlaces) | Solo zona segura |
| Ejecutar tests de diagnóstico | Tests en `tests/` que no modifiquen el sistema | Solo ejecución |
| Inventariar recursos | Listar archivos, contar líneas, analizar estructura | Solo lectura |

---

## 4. Qué requiere aprobación del usuario

| Acción | Riesgo | Requisito |
|--------|--------|-----------|
| Modificar código funcional (`.py`) | Alto | Permiso explícito + plan aprobado |
| Modificar RN Core | Crítico | `RN_WRITE_ALLOWED` + plan + supervisión |
| Crear nuevas neuronas RN Family | Alto | Plan aprobado + fase H3.x correspondiente |
| Conectar APIs externas (DeepSeek) | Alto | Plan H3.2 aprobado |
| Convertir modelos de formato | Medio | Plan H3.6+ aprobado |
| Modificar configuraciones críticas | Alto | Permiso explícito |
| Mover/renombrar carpetas | Alto | Plan aprobado (regla 9 de `.clinerules`) |
| Instalar dependencias | Medio | Permiso explícito (regla 7 de `.clinerules`) |
| Modificar más de 10 archivos por tarea | Medio | Permiso explícito (regla 8 de `.clinerules`) |

---

## 5. Qué está prohibido (incluso con aprobación parcial)

| Acción | Motivo |
|--------|--------|
| Auto-modificarse sin supervisión humana | Riesgo de daño irreversible al sistema |
| Tocar RN Core sin `RN_WRITE_ALLOWED` | Regla absoluta de `.clinerules` (regla 4) |
| Modificar `memory.json` | Estado persistente del sistema, solo lectura |
| Modificar `logs/` | Integridad del registro de actividad |
| Modificar `.venv/` | Entorno virtual, requiere reinstalación |
| Ejecutar código no verificado | Riesgo de seguridad y estabilidad |
| Auto-aprobarse cambios críticos | Violación del principio de supervisión humana |
| Ejecutar comandos destructivos | `git clean`, `git reset --hard`, `rm -rf` (regla 6) |

---

## 6. Flujo seguro AURA / RN / Cline

### 6.1 Diagrama de flujo

```
┌──────────────────────────────────────────────────────────────────┐
│                    AURA Self-Work Loop Seguro                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Usuario plantea objetivo                                      │
│     │                                                             │
│     ▼                                                             │
│  2. AURA analiza con modelo actual (local/remoto)                 │
│     │                                                             │
│     ▼                                                             │
│  3. RN Core valida contexto y nivel de riesgo                     │
│     │                                                             │
│     ▼                                                             │
│  4. RN Plan Validator (futuro) evalúa viabilidad del plan         │
│     │                                                             │
│     ▼                                                             │
│  5. Decision Engine selecciona modelo/herramienta adecuada        │
│     │                                                             │
│     ▼                                                             │
│  6. RN Test Guardian (futuro) verifica seguridad                  │
│     │                                                             │
│     ▼                                                             │
│  7. [USUARIO APRUEBA EXPLÍCITAMENTE]                              │
│     │                                                             │
│     ▼                                                             │
│  8. Cline/AURA ejecuta bajo supervisión                           │
│     │                                                             │
│     ▼                                                             │
│  9. RN Commit Auditor (futuro) registra metadata                  │
│     │                                                             │
│     ▼                                                             │
│ 10. RN Graph Keeper (futuro) actualiza relaciones                 │
│     │                                                             │
│     ▼                                                             │
│ 11. Feedback → RN Core (aprendizaje sin auto-modificación)        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Descripción de pasos

| Paso | Actor | Acción | ¿Requiere aprobación? |
|------|-------|--------|----------------------|
| 1 | Usuario | Plantea objetivo o tarea | — |
| 2 | AURA | Analiza con modelo activo | No |
| 3 | RN Core | Valida contexto y riesgo | No (solo lectura) |
| 4 | RN Plan Validator | Evalúa viabilidad del plan | No (futuro) |
| 5 | Decision Engine | Selecciona modelo/herramienta | No |
| 6 | RN Test Guardian | Verifica seguridad | No (futuro) |
| 7 | **Usuario** | **Aprueba o rechaza** | **Sí** |
| 8 | Cline/AURA | Ejecuta cambios | Sí (supervisado) |
| 9 | RN Commit Auditor | Registra metadata | No (futuro) |
| 10 | RN Graph Keeper | Actualiza relaciones | No (futuro) |
| 11 | RN Core | Recibe feedback (solo lectura) | No |

### 6.3 Garantías de seguridad del flujo

1. **Ningún componente puede auto-modificarse**
2. **Todo cambio requiere validación múltiple** (al menos 2 verificaciones)
3. **El usuario siempre tiene la última palabra** en cambios críticos
4. **Fallback automático** ante problemas detectados
5. **Trazabilidad completa** de decisiones en Git
6. **Reversibilidad**: todo cambio debe poder revertirse con `git checkout`

---

## 7. DeepSeek API como proveedor externo futuro

### 7.1 Estado actual
- **No implementado**: No hay conexión a DeepSeek API
- **Provider actual**: Solo `local_llama_provider.py`
- **Plan**: Diseñar e implementar en H3.2

### 7.2 Diseño conceptual del provider

```
providers/deepseek_provider.py (futuro)
├── Clase DeepSeekProvider(BaseProvider)
│   ├── __init__(api_key, base_url, model)
│   ├── generate(prompt, context) → Response
│   ├── stream_generate(prompt, context) → Stream
│   ├── validate_api_key() → bool
│   └── get_available_models() → List[str]
├── Rate limiting
│   ├── max_requests_per_minute: 60
│   └── fallback_on_limit: True → local_llama_provider
└── Configuración en config.py
    ├── DEEPSEEK_API_KEY (desde variable de entorno)
    ├── DEEPSEEK_BASE_URL
    └── DEEPSEEK_MODEL (default: deepseek-chat)
```

### 7.3 Requisitos para activación

1. Obtener API key de DeepSeek
2. Crear `providers/deepseek_provider.py`
3. Agregar configuración en `config.py`
4. Implementar rate limiting y fallback
5. Registrar en `model_registry.py`
6. Probar con tareas no críticas primero
7. Documentar uso y límites

### 7.4 Restricciones de seguridad

- **No activar sin plan H3.2 aprobado**
- **API key debe ir en variable de entorno**, nunca en código
- **Rate limiting obligatorio** para evitar costos inesperados
- **Fallback a local** ante fallos de conexión
- **Modo solo lectura** inicial para validar funcionamiento

---

## 8. Multimodelo local/remoto

### 8.1 Visión conceptual

```
┌─────────────────────────────────────────────┐
│           Sistema Multimodelo AURA           │
├─────────────────────────────────────────────┤
│                                             │
│  Tarea entrante                             │
│       │                                     │
│       ▼                                     │
│  Clasificador de tareas                     │
│  (task_classifier.py)                       │
│       │                                     │
│       ├── Tarea simple → Modelo local GGUF  │
│       │   (bajo costo, rápida)              │
│       │                                     │
│       ├── Tarea compleja → DeepSeek API     │
│       │   (alto razonamiento)               │
│       │                                     │
│       └── Tarea crítica → Ambos +          │
│           validación cruzada                │
│                                             │
└─────────────────────────────────────────────┘
```

### 8.2 Criterios de routing

> **Nota**: H3.3 (Multimodel Routing Design) refina y expande estos criterios. Ver `docs/hextech/MULTIMODEL_ROUTING_DESIGN.md` para la matriz de decisión completa.

| Tipo de tarea | Modelo recomendado | Justificación |
|---------------|-------------------|---------------|
| Diagnóstico simple | Local GGUF | Bajo costo, respuesta rápida |
| Documentación | Local GGUF | Suficiente capacidad |
| Análisis de código | Local GGUF o DeepSeek | Según complejidad |
| Planificación | DeepSeek API | Mayor razonamiento |
| Generación de propuestas | DeepSeek API | Calidad de salida |
| Validación cruzada | Ambos | Consistencia y seguridad |
| Tareas críticas | Ambos + verificación | Máxima seguridad |

### 8.3 Estado actual del Model Bank

**Dentro del repo (`A:\AURA\project\models/`)**:
- No existe la carpeta `models/` dentro del repositorio actual
- No hay modelos GGUF ni de ningún formato en el repo

**Banco externo detectado (`A:\AURA\models/`)**:
- El runtime de AURA detecta un banco de modelos externo en `A:\AURA\models`
- Contiene **15 artefactos** (12 GGUF + 3 Safetensors), totalizando **38.26 GB**
- **H3.1 (Model Bank Audit)** completado — ver `docs/hextech/MODEL_BANK_AUDIT.md`
- La auditoría clasificó: formato, tamaño, fecha, estado y prioridad de uso
- Los 12 GGUF son utilizables directamente por `local_llama_provider`
- Los 3 Safetensors (22.62 GB) son candidatos a conversión futura en H3.6+

**Nota importante**: H3.1 se limitó a **lectura e inventario**. No se convirtieron modelos ni se modificaron archivos en `A:\AURA\models`.

---

## 9. Model Bank Audit y conversión GGUF futura

### 9.1 Fases del Model Bank

| Fase | Acción | Estado |
|------|--------|--------|
| H3.1 | Inventariar modelos en `A:\AURA\models` (solo lectura) | Pendiente |
| H3.6+ | Evaluar conversión de modelos no-GGUF a GGUF | Futuro |
| H3.7+ | Poblar `models/` en repo con GGUF seleccionados | Futuro |

### 9.2 Metadata por modelo (formato propuesto para H3.1)

```json
{
  "modelo_id": "mistral-7b-v0.1",
  "formato": "gguf",
  "ruta": "A:\\AURA\\models\\mistral-7b-v0.1.Q4_K_M.gguf",
  "tamaño_mb": 4096,
  "fuente": "Hugging Face / TheBloke",
  "licencia": "Apache 2.0",
  "estado": "no_verificado",
  "rendimiento": null,
  "notas": "Requiere verificación de integridad"
}
```

### 9.3 Criterios para conversión GGUF futura

- Modelos en formato Tensor, Ckpt o Safetensors son candidatos
- La conversión solo se hará con plan aprobado (H3.6+)
- Se requiere espacio en disco suficiente
- Se documentará el proceso y resultado
- No se eliminarán los originales hasta verificar el GGUF resultante

---

## 10. RN Graph System

### 10.1 Concepto

RN Graph es un sistema de grafos que modela las relaciones entre todas las neuronas de RN Family, permitiendo:

- Visualizar dependencias entre componentes
- Identificar caminos críticos
- Detectar acoplamientos no deseados
- Planificar cambios con impacto controlado
- Registrar metadata evolutiva del sistema

### 10.2 Estructura del grafo

```
Nodo: Cada neurona RN Family (RNC, RNR, RNPV, RNTG, etc.)
  ├── id: Identificador único
  ├── nombre: Nombre descriptivo
  ├── version: Versión actual
  ├── estado: conceptual | diseño | implementado | probado | sellado
  ├── riesgo: bajo | medio | alto | crítico
  └── metadata: { creado, modificado, autor, notas }

Arista: Relación entre dos neuronas
  ├── tipo: depende_de | activa_a | supervisa_a | reporta_a | valida_a
  ├── peso: 1-10 (intensidad de la relación)
  └── metadata: { creado, justificación }
```

### 10.3 Tipos de aristas

| Tipo | Significado | Ejemplo |
|------|-------------|---------|
| `depende_de` | A necesita a B para funcionar | RNPV depende_de RNC |
| `activa_a` | A activa a B cuando se ejecuta | RNC activa_a RNR |
| `supervisa_a` | A supervisa las operaciones de B | RNCS supervisa_a RNFD |
| `reporta_a` | A envía reportes a B | RNTG reporta_a RNCA |
| `valida_a` | A valida las salidas de B | RNPV valida_a RNR |

### 10.4 Formato de almacenamiento (conceptual)

```json
{
  "rn_graph": {
    "version": "1.0",
    "ultima_actualizacion": "2026-04-27",
    "nodos": [
      {
        "id": "RNC",
        "nombre": "Routing Neuron Core",
        "version": "V1.8",
        "estado": "sellado",
        "riesgo": "crítico"
      }
    ],
    "aristas": [
      {
        "origen": "RNC",
        "destino": "RNR",
        "tipo": "activa_a",
        "peso": 8
      }
    ]
  }
}
```

### 10.5 Implementación futura

- **H3.4**: Diseño conceptual completo del RN Graph System
- **H3.5**: Implementación del grafo como archivo JSON en `docs/hextech/`
- **H3.7**: Integración con RN Graph Keeper (neurona dedicada)

---

## 11. Neuronas RN Family candidatas para Self-Work

### 11.1 Tabla de neuronas candidatas

| ID | Nombre | Familia | Propósito | Prioridad | Dependencias |
|----|--------|---------|-----------|-----------|--------------|
| RN-PV | RN Plan Validator | Governance | Valida planes antes de ejecución | 🔴 Alta | RNC |
| RN-TG | RN Test Guardian | Governance | Verifica tests antes/después de cambios | 🔴 Alta | RNC |
| RN-CA | RN Commit Auditor | Governance | Audita y registra commits con metadata | 🔴 Alta | RNC, RN-PV |
| RN-GK | RN Graph Keeper | Kernel | Mantiene grafo de relaciones RN | 🔴 Alta | RNC |
| RN-MR | RN Memory Repair | Memory & Context | Repara corrupción en memoria | 🟡 Media | RNC, RN-DV |
| RN-DV | RN Data Validator | Memory & Context | Valida integridad de datos persistidos | 🟡 Media | RNC |
| RN-PS | RN Provider Supervisor | Runtime | Supervisa proveedores externos | 🟡 Media | RNC, RN-TG |
| RN-CC | RN Context Curator | Memory & Context | Gestiona contexto eficientemente | 🟡 Media | RNC |
| RN-MP | RN Model Profiler | Evolution | Perfila rendimiento de modelos | 🟢 Baja | RNC, RN-PS |

### 11.2 Descripción de cada neurona candidata

#### RN Plan Validator (RN-PV)
- **Propósito**: Validar planes de ejecución antes de que se apliquen
- **Inputs**: Plan propuesto, contexto actual, reglas de seguridad
- **Outputs**: Aprobación/rechazo, riesgos identificados, sugerencias
- **Riesgo**: Alto (valida cambios críticos)
- **Fase estimada**: H3.7

#### RN Test Guardian (RN-TG)
- **Propósito**: Ejecutar y verificar tests antes y después de cambios
- **Inputs**: Tests a ejecutar, código modificado
- **Outputs**: Reporte de tests, cobertura, regresiones
- **Riesgo**: Alto (protege contra regresiones)
- **Fase estimada**: H3.7

#### RN Commit Auditor (RN-CA)
- **Propósito**: Auditar y registrar metadata de cada commit
- **Inputs**: Diff del commit, mensaje, archivos modificados
- **Outputs**: Metadata estructurada, reporte de auditoría
- **Riesgo**: Medio (solo lectura de metadata)
- **Fase estimada**: H3.7

#### RN Graph Keeper (RN-GK)
- **Propósito**: Mantener actualizado el grafo de relaciones RN
- **Inputs**: Cambios en componentes RN Family
- **Outputs**: Grafo actualizado, detección de ciclos
- **Riesgo**: Medio (solo metadata)
- **Fase estimada**: H3.7

#### RN Memory Repair (RN-MR)
- **Propósito**: Detectar y reparar corrupción en `memory.json`
- **Inputs**: `memory.json` dañado, backup disponible
- **Outputs**: Memoria reparada o rechazada
- **Riesgo**: Alto (opera sobre memoria persistente)
- **Fase estimada**: H3.8+

#### RN Data Validator (RN-DV)
- **Propósito**: Validar integridad de datos antes de cargarlos
- **Inputs**: Datos a validar, schema esperado
- **Outputs**: Validación exitosa/fallida, errores encontrados
- **Riesgo**: Medio (solo validación)
- **Fase estimada**: H3.8+

#### RN Provider Supervisor (RN-PS)
- **Propósito**: Supervisar estado y rendimiento de proveedores
- **Inputs**: Métricas de proveedores, estado de conexión
- **Outputs**: Reporte de salud, alertas, sugerencias de failover
- **Riesgo**: Medio (monitoreo)
- **Fase estimada**: H3.8+

#### RN Context Curator (RN-CC)
- **Propósito**: Gestionar y optimizar el contexto disponible
- **Inputs**: Contexto actual, límites de tokens
- **Outputs**: Contexto optimizado, resúmenes
- **Riesgo**: Bajo (solo gestión de contexto)
- **Fase estimada**: H3.8+

#### RN Model Profiler (RN-MP)
- **Propósito**: Perfilar rendimiento de modelos locales y remotos
- **Inputs**: Modelos a evaluar, cargas de prueba
- **Outputs**: Métricas de rendimiento, recomendaciones
- **Riesgo**: Bajo (solo medición)
- **Fase estimada**: H3.8+

---

## 12. Riesgos identificados

### 12.1 Tabla de riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|-------------|---------|------------|
| R1 | Auto-modificación sin control | Baja | Crítico | Flujo seguro con aprobación humana obligatoria |
| R2 | Dependencia externa (DeepSeek API) | Media | Alto | Fallback a local, rate limiting, modo offline |
| R3 | Model Bank vacío | Alta | Medio | Auditoría H3.1, identificar modelos disponibles |
| R4 | RN Core frágil por cambios no autorizados | Baja | Crítico | `RN_WRITE_ALLOWED`, checklist pre-RN Core |
| R5 | Ciclos infinitos de auto-modificación | Baja | Alto | Límite de iteraciones, supervisión humana |
| R6 | Contaminación de memoria por datos viejos | Media | Medio | DEV-CLEANUP protocol, RN Memory Repair futura |
| R7 | Acoplamiento excesivo entre neuronas RN Family | Media | Medio | RN Graph System para detectar ciclos |
| R8 | Pérdida de trazabilidad por commits masivos | Baja | Medio | Commits atómicos, RN Commit Auditor |

### 12.2 Riesgos específicos de H3

| Riesgo | Descripción | Acción |
|--------|-------------|--------|
| Documentación desactualizada | Los planes pueden quedar obsoletos | Revisión periódica de documentos H3 |
| Scope creep | Agregar funcionalidades no planificadas | Respetar fases H3.x estrictamente |
| Dependencias no documentadas | Componentes que dependen de RN no identificados | Auditoría de imports en H3.5 |

---

## 13. Fases recomendadas H3

### 13.1 Mapa de fases

```
H3.0 → H3.1 → H3.2 → H3.3 → H3.4 → H3.5 → H3.6 → H3.7 → H3.8
 │       │       │       │       │       │       │       │       │
 │       │       │       │       │       │       │       │       └── Conversión GGUF
 │       │       │       │       │       │       │       │           Población Model Bank
 │       │       │       │       │       │       │       │
 │       │       │       │       │       │       │       └── RN Family primeras neuronas
 │       │       │       │       │       │       │           (PV, TG, CA, GK)
 │       │       │       │       │       │       │
 │       │       │       │       │       │       └── Pruebas y criterios de seguridad
 │       │       │       │       │       │
 │       │       │       │       │       └── AURA Self-Work Loop controlado
 │       │       │       │       │
 │       │       │       │       └── RN Graph System conceptual
 │       │       │       │
 │       │       │       └── Diseño multimodel routing seguro
 │       │       │
 │       │       └── Diseño DeepSeek API Provider (solo diseño)
 │       │
 │       └── Inventario de modelos / Model Bank Audit
 │
 └── Documento maestro (esta tarea)
```

### 13.2 Detalle de fases

#### H3.0 — Documento maestro (actual)
- **Objetivo**: Crear este documento (RN_SELF_WORK_PLAN.md)
- **Entregables**: Plan maestro de integración RN/Self-Work
- **Restricciones**: Solo documentación, sin implementación
- **Duración estimada**: 1 sesión

#### H3.1 — Model Bank Audit
- **Objetivo**: Inventariar modelos en `A:\AURA\models` (solo lectura)
- **Entregables**: Inventario detallado con metadata por modelo
- **Restricciones**: No mover, modificar ni convertir modelos
- **Duración estimada**: 1-2 sesiones

#### H3.2 — Diseño DeepSeek API Provider
- **Objetivo**: Diseñar el provider para DeepSeek API (sin implementar)
- **Entregables**: Especificación técnica de `deepseek_provider.py`
- **Restricciones**: No conectar API, no implementar código
- **Duración estimada**: 1 sesión

#### H3.3 — Diseño multimodel routing seguro
- **Objetivo**: Diseñar sistema de routing entre modelos locales y remotos
- **Entregables**: Especificación de routing, criterios de selección, matriz de decisión
- **Restricciones**: No implementar, solo diseño
- **Duración estimada**: 1 sesión
- **Documento**: `docs/hextech/MULTIMODEL_ROUTING_DESIGN.md`

#### H3.4 — RN Graph System conceptual ✅
- **Objetivo**: Diseñar el sistema de grafos para RN Family
- **Entregables**: Especificación del grafo, formato JSON, tipos de aristas, relación con RN Family
- **Restricciones**: No implementar, solo diseño
- **Duración estimada**: 1 sesión
- **Documento**: `docs/hextech/RN_GRAPH_SYSTEM_DESIGN.md`
- **Estado**: ✅ Completado

#### H3.5 — AURA Self-Work Loop controlado
- **Objetivo**: Implementar el bucle seguro de auto-trabajo
- **Entregables**: Scripts de diagnóstico, flujo de aprobación
- **Restricciones**: No tocar RN Core, solo componentes auxiliares
- **Duración estimada**: 2-3 sesiones

#### H3.6 — Pruebas y criterios de seguridad
- **Objetivo**: Definir y ejecutar pruebas de seguridad para Self-Work
- **Entregables**: Suite de tests, criterios de aceptación
- **Restricciones**: No modificar código funcional sin permiso
- **Duración estimada**: 2 sesiones

#### H3.7 — RN Family: primeras neuronas
- **Objetivo**: Implementar las primeras 4 neuronas RN Family
- **Neuronas**: RN Plan Validator, RN Test Guardian, RN Commit Auditor, RN Graph Keeper
- **Restricciones**: No modificar RN Core, implementar como módulos independientes
- **Duración estimada**: 3-4 sesiones

#### H3.8 — Conversión GGUF / Model Bank
- **Objetivo**: Convertir modelos seleccionados a GGUF y poblar Model Bank
- **Entregables**: Modelos GGUF en `models/`, documentación de conversión
- **Restricciones**: No eliminar originales, verificar cada conversión
- **Duración estimada**: 2-3 sesiones

---

## 14. Checklist antes de tocar RN Core

Este checklist debe completarse **antes de cualquier modificación a RN Core** (requiere `RN_WRITE_ALLOWED`):

- [ ] **Plan H3 completo aprobado** — Todas las fases H3.0 a H3.8 documentadas y aprobadas
- [ ] **RN Family al menos en RNF-1** — Contratos definidos para componentes que interactúan con RN Core
- [ ] **Tests de regresión para RN existentes** — Suite de tests que validen funcionamiento actual
- [ ] **Backup de RN Core** — Checkpoint Git del estado actual de `backend/app/routing_neuron/`
- [ ] **`RN_WRITE_ALLOWED` en prompt** — Incluir explícitamente en el prompt de la tarea
- [ ] **Usuario presente durante ejecución** — Supervisión humana en tiempo real
- [ ] **Rollback plan definido** — Procedimiento para revertir cambios si algo falla
- [ ] **Impacto analizado** — Documentar qué componentes dependen de RN Core y cómo les afectará el cambio
- [ ] **Criterio de éxito definido** — Qué debe pasar para considerar el cambio exitoso
- [ ] **Ventana de tiempo acordada** — Cuánto tiempo máximo puede durar la intervención

---

## 15. Archivos relacionados

### 15.1 Documentos Hextech

| Documento | Relación |
|-----------|----------|
| `HEXTECH_BLUEPRINT.md` | Blueprint de arquitectura, fases H0-H2 |
| `CONTEXT_MAP.md` | Mapa contextual para navegación eficiente |
| `RN_BOUNDARY.md` | Reglas absolutas de protección RN |
| `RN_FAMILY.md` | Arquitectura modular conceptual RN Family |
| `PROJECT_INVENTORY.md` | Inventario técnico y mapa de riesgo |
| `DEV_CLEANUP_PROTOCOL.md` | Protocolo de limpieza de estado vivo |
| `AUTONOMY_PROTOCOL.md` | Protocolo de autonomía controlada |
| `RN_SELF_WORK_PLAN.md` | **Este documento** |
| `DEEPSEEK_PROVIDER_DESIGN.md` | Diseño del provider remoto DeepSeek API (H3.2) |
| `MULTIMODEL_ROUTING_DESIGN.md` | Diseño de política de routing multimodelo (H3.3) |
| `RN_GRAPH_SYSTEM_DESIGN.md` | Diseño conceptual del sistema de grafos para RN Family (H3.4) |

### 15.2 Archivos de código relacionados (solo referencia)

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `agents/decision_engine.py` | Motor de decisiones | Protegido |
| `agents/task_classifier.py` | Clasificador de tareas | Protegido |
| `agents/model_registry.py` | Registro de modelos | Protegido |
| `agents/model_gateway.py` | Gateway de modelos | Protegido |
| `providers/base_provider.py` | Clase base de proveedores | Protegido |
| `providers/local_llama_provider.py` | Proveedor local | Protegido |
| `config.py` | Configuración del sistema | Protegido |

---

## 16. Reglas de protección para este plan

### 16.1 Reglas absolutas

1. **RN Core no se modifica** sin `RN_WRITE_ALLOWED` + checklist completo
2. **No se implementa nada** que no esté en una fase H3.x aprobada
3. **No se conecta DeepSeek API** sin plan H3.2 aprobado
4. **No se convierten modelos** sin plan H3.6+ aprobado
5. **No se modifican archivos protegidos** (`backend/`, `agents/`, `providers/`, etc.) sin permiso explícito

### 16.2 Reglas de documentación

1. Este documento es **solo planificación conceptual**
2. No implica autorización para implementar
3. Cada fase H3.x requiere su propio plan y aprobación
4. Las neuronas RN Family listadas son **candidatas conceptuales**, no compromiso de implementación

### 16.3 Reglas de prioridad

1. **Seguridad > Funcionalidad**: No sacrificar seguridad por velocidad
2. **Documentación > Implementación**: Primero documentar, luego implementar
3. **Validación > Ejecución**: Validar antes de ejecutar cualquier cambio
4. **Trazabilidad > Eficiencia**: Preferir cambios trazables sobre cambios rápidos

---

## 17. Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 27/4/2026 | v1.0 | Creación inicial como parte de H3.0 |

---

**Ubicación**: `docs/hextech/RN_SELF_WORK_PLAN.md`
**Responsable**: Cline bajo supervisión Hextech
**Estado**: Documentación conceptual (H3.0)
**Próxima fase**: H3.1 — Model Bank Audit
