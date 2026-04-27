# RN Family / Routing Neuron Mesh

## 1. Introducción

RN Family / Routing Neuron Mesh es la evolución conceptual del Routing Neuron (RN) hacia una arquitectura modular de subsistemas especializados. Este documento describe la visión arquitectónica futura, **no una implementación actual**.

**⚠️ IMPORTANTE**: Este documento es **documentación conceptual** sobre arquitectura futura. No modifica RN Core V1.8 ni requiere `RN_WRITE_ALLOWED`. Para reglas de seguridad RN, consulta [RN_BOUNDARY.md](RN_BOUNDARY.md) (única fuente de verdad).

**Principios fundamentales:**
- **RN Core V1.8** sigue siendo el núcleo sellado y protegido por `RN_WRITE_ALLOWED`
- **RN Family** es la arquitectura modular conceptual construida alrededor del núcleo
- **Propósito**: Documentar diseño futuro, no modificar implementación actual
- **RN Core no es una nueva implementación**: RN Core es el nombre conceptual del RN actual V1.8 sellado

## 2. Principios de diseño (Raspberry Pi mentality)

La filosofía Raspberry Pi guía el diseño de RN Family:

- **Eficiencia**: Uso óptimo de recursos
- **Bajo consumo**: Mínimo overhead operativo
- **Modularidad**: Componentes independientes con interfaces claras
- **Baja latencia**: Respuesta rápida en decisiones críticas
- **Trazabilidad**: Todo cambio es rastreable y verificable
- **Mejora progresiva**: Evolución incremental sin rupturas

**Principios operativos críticos:**
- **RN Core observa y mide**, pero no se auto-modifica
- **Todo aprendizaje** produce propuestas, reportes o candidatos; no cambios automáticos en producción
- **RN Foundry fabrica** propuestas, datasets o artefactos experimentales, pero no aplica cambios al RN real
- **RN Registry valida conceptualmente**, pero no se modifica registry.json en esta fase
- **RN Registry es un concepto futuro/documental en esta fase**: Esta tarea no crea, modifica ni valida registry.json

## 3. Arquitectura modular - Diagrama conceptual

```
┌─────────────────────────────────────────────────────────┐
│                    RN Family / Routing Neuron Mesh      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │RN Kernel│  │RN Memory│  │RN Runtime│  │RN Gov. │   │
│  │         │  │ & Context│ │         │  │         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│         │           │           │           │          │
│  ┌──────┴───────────┴───────────┴───────────┴──────┐  │
│  │              RN Core V1.8 (sellado)              │  │
│  │        (Observación y medición central)          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Relaciones clave:**
- **RN Core V1.8**: Núcleo central sellado que observa y mide
- **Componentes RN Family**: Subsistemas especializados que interactúan a través de interfaces definidas
- **Separación clara**: Observación (RN Core) vs. Acción (componentes RN Family)
- **Comunicación**: A través de contratos y APIs bien definidas

## 4. Clasificación por familias

### 4.1 RN Kernel
Componentes centrales de routing y toma de decisiones:
- **Routing Neuron Core** (RN Core V1.8)
- **Routing Neuron Router / RNR**
- **Routing Neuron Registry** (conceptual)

### 4.2 RN Memory & Context
Gestión de memoria, contexto y estado:
- **Routing Neuron Memory**
- **Routing Neuron Context Guard**
- **Routing Neuron KV** (Key-Value)
- **Routing Neuron Cache**

### 4.3 RN Runtime
Ejecución, scheduling y performance:
- **Routing Neuron Scheduler**
- **Routing Neuron Loader**
- **Routing Neuron Batcher**
- **Routing Neuron GPU**
- **Routing Neuron Sync**

### 4.4 RN Governance
Validación, seguridad y supervisión:
- **Routing Neuron Cline Supervisor**
- **Routing Neuron Plan Validator**
- **Routing Neuron Test Guardian**
- **Routing Neuron Autonomy Rules**
- **Routing Neuron Critic**

### 4.5 RN Evolution
Aprendizaje, optimización y fabricación:
- **Routing Neuron Profiler**
- **Routing Neuron Foundry**
- **Routing Neuron Merger**
- **Routing Neuron Quant**
- **Routing Neuron Allocator**

### 4.6 RN Hardware & Performance
Optimización hardware y rendimiento:
- **Routing Neuron Spec**
- **Routing Neuron Token**
- **Routing Neuron Fallback**

## 5. Tabla de componentes RN Family (25 componentes)

| ID | Nombre | Familia | Propósito | Estado |
|----|--------|---------|-----------|--------|
| RNC | Routing Neuron Core | Kernel | Núcleo central de observación y medición | V1.8 sellado |
| RNR | Routing Neuron Router / RNR | Kernel | Enrutamiento inteligente entre componentes | Conceptual |
| RNM | Routing Neuron Memory | Memory & Context | Gestión de memoria de corto/largo plazo | Conceptual |
| RNS | Routing Neuron Scheduler | Runtime | Programación y priorización de tareas | Conceptual |
| RNP | Routing Neuron Profiler | Evolution | Perfilado y análisis de performance | Conceptual |
| RNL | Routing Neuron Loader | Runtime | Carga y descarga dinámica de componentes | Conceptual |
| RNF | Routing Neuron Fallback | Hardware & Performance | Mecanismos de fallback y recuperación | Conceptual |
| RNRG | Routing Neuron Registry | Kernel | Registro y descubrimiento de componentes | Conceptual |
| RNCS | Routing Neuron Cline Supervisor | Governance | Supervisión de interacciones con Cline | Conceptual |
| RNCG | Routing Neuron Context Guard | Memory & Context | Protección y gestión de contexto | Conceptual |
| RNAR | Routing Neuron Autonomy Rules | Governance | Reglas de autonomía controlada | Conceptual |
| RNTG | Routing Neuron Test Guardian | Governance | Validación y testing de componentes | Conceptual |
| RNCA | Routing Neuron Cache | Memory & Context | Caché de datos frecuentes | Conceptual |
| RNB | Routing Neuron Batcher | Runtime | Procesamiento por lotes | Conceptual |
| RNCR | Routing Neuron Critic | Governance | Evaluación crítica de decisiones | Conceptual |
| RNFD | Routing Neuron Foundry | Evolution | Fabricación de propuestas experimentales | Conceptual |
| RNMR | Routing Neuron Merger | Evolution | Fusión y consolidación de resultados | Conceptual |
| RNQ | Routing Neuron Quant | Evolution | Cuantificación y optimización numérica | Conceptual |
| RNA | Routing Neuron Allocator | Evolution | Asignación de recursos | Conceptual |
| RNPV | Routing Neuron Plan Validator | Governance | Validación de planes de ejecución | Conceptual |
| RNSP | Routing Neuron Spec | Hardware & Performance | Especificaciones de hardware | Conceptual |
| RNKV | Routing Neuron KV | Memory & Context | Almacenamiento clave-valor | Conceptual |
| RNT | Routing Neuron Token | Hardware & Performance | Gestión de tokens y límites | Conceptual |
| RNSY | Routing Neuron Sync | Runtime | Sincronización entre componentes | Conceptual |
| RNG | Routing Neuron GPU | Runtime | Optimización GPU y aceleración | Conceptual |

## 6. Contrato mínimo por componente

Para cada componente de RN Family se define un contrato mínimo:

### 6.1 Estructura del contrato
```
id: Identificador único (ej: RNC)
name: Nombre descriptivo (ej: Routing Neuron Core)
purpose: Propósito específico del componente
inputs: Qué recibe (señales, datos, eventos)
outputs: Qué produce (decisiones, reportes, propuestas)
reads: Qué lee (archivos, memoria, registros)
writes: Qué escribe (archivos, memoria, registros)
risk_level: Bajo/Medio/Alto/Crítico
activation_policy: Manual/Automático/Condicional
dependencies: Componentes de los que depende
metrics: Métricas de desempeño (latencia, throughput, etc.)
fallback: Mecanismo de fallback y recuperación
```

### 6.2 Ejemplo: Routing Neuron Core (RNC)
```
id: RNC
name: Routing Neuron Core
purpose: Núcleo central de observación y medición del sistema
inputs: Señales de todos los componentes, estado del sistema
outputs: Métricas, observaciones, alertas tempranas
reads: Estado de componentes, logs de actividad, métricas históricas
writes: Logs de observación, reportes de métricas
risk_level: Crítico
activation_policy: Siempre activo
dependencies: Ninguna (es el núcleo base)
metrics: Latencia de observación, precisión de medición
fallback: Modo degradado con observación básica
```

### 6.3 Ejemplo: Routing Neuron Foundry (RNFD)
```
id: RNFD
name: Routing Neuron Foundry
purpose: Fabricación de propuestas, datasets o artefactos experimentales
inputs: Datos de observación, métricas, patrones identificados
outputs: Propuestas experimentales, datasets sintéticos, artefactos de prueba
reads: Datos de RN Core, patrones históricos, configuraciones experimentales
writes: Propuestas (archivos temporales), datasets experimentales
risk_level: Medio
activation_policy: Condicional (solo con supervisión)
dependencies: RNC (observación), RNCR (crítica)
metrics: Calidad de propuestas, utilidad experimental
fallback: Desactivación automática si no hay supervisión
```

## 7. Cadena segura de decisiones

Flujo conceptual seguro para cualquier cambio o propuesta:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ RN Core │ →  │RN Registry│ → │RN Router│ → │RN Cline │
│(Observa)│    │ (Valida) │    │(Decide) │    │Supervisor│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
      ↓              ↓              ↓              ↓
┌─────────┐    ┌─────────┐    ┌─────────┐
│RN Plan  │ →  │RN Test  │ →  │Aplicación│
│Validator│    │Guardian │    │Controlada│
└─────────┘    └─────────┘    └─────────┘
```

**Pasos detallados:**
1. **RN Core observa y mide**: Recoge datos del sistema sin modificar
2. **RN Registry valida conceptualmente**: Verifica que la propuesta cumple con contratos
3. **RN Router decide**: Selecciona el mejor camino basado en políticas
4. **RN Cline Supervisor propone**: Presenta la propuesta para consideración
5. **RN Plan Validator autoriza**: Valida que el plan es seguro y reversible
6. **RN Test Guardian comprueba**: Ejecuta pruebas de validación antes de aplicación

**Garantías de seguridad:**
- Ningún componente puede auto-modificarse
- Todo cambio requiere validación múltiple
- Fallback automático ante problemas
- Trazabilidad completa de decisiones

## 8. Fases RNF internas

### RNF-0: Concepto documental (fase actual)
- **Objetivo**: Documentar arquitectura conceptual RN Family
- **Entregables**: Este documento (RN_FAMILY.md)
- **Restricciones**: Solo documentación, sin implementación
- **Criterio de éxito**: Documentación completa y clara

### RNF-1: Contratos y especificaciones
- **Objetivo**: Definir contratos detallados para cada componente
- **Entregables**: Especificaciones técnicas por componente
- **Restricciones**: Solo especificaciones, sin código
- **Criterio de éxito**: Contratos verificables y completos

### RNF-2: Observatorio y medición
- **Objetivo**: Implementar sistema de observación (sin modificar RN Core)
- **Entregables**: Herramientas de monitoreo y métricas
- **Restricciones**: Solo lectura, sin escritura a RN
- **Criterio de éxito**: Observación completa sin afectar producción

### RNF-3: Runtime experimental
- **Objetivo**: Implementar componentes RN Family en entorno aislado
- **Entregables**: Runtime experimental con componentes seleccionados
- **Restricciones**: Entorno aislado, sin afectar producción
- **Criterio de éxito**: Funcionamiento básico en sandbox

### RNF-4: Autonomía controlada
- **Objetivo**: Integración gradual con supervisión humana
- **Entregables**: Sistema operativo con autonomía limitada
- **Restricciones**: Supervisión humana requerida para cambios críticos
- **Criterio de éxito**: Autonomía controlada y verificable

## 9. Relación con RN Core V1.8

### 9.1 RN Core sigue siendo núcleo sellado
- **Versión**: V1.8 (subsistema canónico ya sellado)
- **Ubicación**: `backend/app/routing_neuron/`
- **Protección**: Requiere `RN_WRITE_ALLOWED` para modificaciones
- **Documentación**: `docs/routing_neuron_v1_checkpoint.md` (solo lectura)

### 9.2 RN Family se construye alrededor, no reemplaza
- **Arquitectura**: RN Family es modular alrededor de RN Core
- **Interacción**: Componentes RN Family observan a RN Core, no lo modifican
- **Evolución**: Migración gradual mediante fases RNF
- **Compatibilidad**: Hacia atrás garantizada en todas las fases

### 9.3 Principio de no modificación
- **RN Core V1.8 no se modifica** por componentes RN Family
- **Componentes RN Family son conceptuales** en esta fase
- **Cualquier cambio futuro** requerirá planificación específica y `RN_WRITE_ALLOWED`

## 10. Gobernanza y seguridad

### 10.1 Documentos de referencia
- **`RN_BOUNDARY.md`**: Documento de seguridad prioritario para RN
- **`RN_FAMILY.md`**: Este documento, arquitectura conceptual
- **Regla de precedencia**: Si hay conflicto entre documentos, gana `RN_BOUNDARY.md`

### 10.2 Reglas de protección absoluta
1. **`RN_WRITE_ALLOWED`** sigue siendo requerido para modificar RN Core
2. **`backend/app/routing_neuron/`** es zona crítica protegida
3. **`agents/routing_*.py`** son agentes protegidos de routing
4. **`docs/routing_neuron_v1_checkpoint.md`** es solo lectura

### 10.3 Protocolo para futuras implementaciones
1. **Fase documental completa** (RNF-0 a RNF-1)
2. **Plan específico por componente** con `RN_WRITE_ALLOWED` si aplica
3. **Implementación en entorno aislado** (RNF-2 a RNF-3)
4. **Validación exhaustiva** antes de integración (RNF-4)
5. **Supervisión humana** para cambios críticos

## 10.5 Neuronas Self-Work candidatas (H3.0)

Como parte del plan H3.0 (RN Self-Work), se identificaron **9 neuronas candidatas** adicionales para RN Family, orientadas específicamente al ciclo de auto-trabajo de AURA:

| ID | Nombre | Familia | Prioridad | Fase estimada |
|----|--------|---------|-----------|---------------|
| RN-PV | RN Plan Validator | Governance | Alta | H3.7 |
| RN-TG | RN Test Guardian | Governance | Alta | H3.7 |
| RN-CA | RN Commit Auditor | Governance | Alta | H3.7 |
| RN-GK | RN Graph Keeper | Kernel | Alta | H3.7 |
| RN-MR | RN Memory Repair | Memory & Context | Media | H3.8+ |
| RN-DV | RN Data Validator | Memory & Context | Media | H3.8+ |
| RN-PS | RN Provider Supervisor | Runtime | Media | H3.8+ |
| RN-CC | RN Context Curator | Memory & Context | Media | H3.8+ |
| RN-MP | RN Model Profiler | Evolution | Baja | H3.8+ |

**Nota**: Estas neuronas están documentadas en detalle en `RN_SELF_WORK_PLAN.md` (sección 11). Son candidatas conceptuales para fases futuras y no implican implementación inmediata. No modifican RN Core V1.8 ni requieren `RN_WRITE_ALLOWED`.

---

## 11. Próximos pasos y consideraciones

### 11.1 Esta documentación es conceptual
- **No implica implementación inmediata**
- **No modifica código existente**
- **No requiere `RN_WRITE_ALLOWED`**
- **Es solo documentación de arquitectura futura**

### 11.2 Implementación futura requerirá
1. **Planes específicos** por componente
2. **Validación de seguridad** exhaustiva
3. **Entornos aislados** para pruebas
4. **Supervisión humana** en todas las fases

### 11.3 Consideraciones críticas
- **Mantener compatibilidad** con sistemas existentes
- **Preservar `RN_BOUNDARY.md`** como documento de seguridad prioritario
- **Respetar `RN_WRITE_ALLOWED`** para cualquier cambio a RN Core
- **Validar experimentalmente** antes de integración

### 11.4 Revisión periódica
Esta arquitectura debe revisarse periódicamente para:
- Ajustar a necesidades emergentes
- Incorporar lecciones aprendidas
- Mantener coherencia con evolución tecnológica
- Garantizar seguridad continua

---

**Nota final**: RN Family / Routing Neuron Mesh representa la visión arquitectónica modular para la evolución futura de AURA. Esta documentación establece los principios, componentes y flujos conceptuales, manteniendo la protección absoluta de RN Core V1.8 y respetando todas las reglas de seguridad Hextech.

**Última actualización**: 22/4/2026 - Creación inicial como parte de H2.1
**Responsable**: Cline bajo supervisión Hextech
**Ubicación**: `docs/hextech/RN_FAMILY.md`
**Estado**: Documentación conceptual (RNF-0)