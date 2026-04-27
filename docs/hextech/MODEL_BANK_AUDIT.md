# Model Bank Audit — Banco externo de modelos AURA

## 1. Propósito

Este documento constituye el inventario técnico del banco externo de modelos detectado por el runtime de AURA en `A:\AURA\models`. Su objetivo es clasificar, documentar y evaluar los artefactos disponibles para fundamentar decisiones de uso y conversión futura en las fases H3.x del plan de Self-Work.

**Fase**: H3.1 — Model Bank Audit  
**Estado**: Auditoría completada (solo lectura)  
**Fecha**: 27/4/2026  

---

## 2. Alcance

- **Solo lectura**: No se modifican, mueven, convierten ni eliminan archivos.
- **Cobertura**: 15 artefactos detectados en el directorio raíz de `A:\AURA\models`.
- **No incluye**: Verificación de licencias, cálculo de hashes, análisis de integridad binaria, ni evaluación de rendimiento.
- **Limitación**: Los tamaños reportados son aproximados (según metadata del sistema de archivos).

---

## 3. Reglas de solo lectura

| Regla | Descripción |
|-------|-------------|
| 🔒 No mover modelos | Los artefactos permanecen en `A:\AURA\models` |
| 🔒 No borrar modelos | No se elimina ningún archivo |
| 🔒 No convertir modelos | No se transforman formatos (GGUF, safetensors, etc.) |
| 🔒 No modificar modelos | No se altera contenido binario ni metadata |
| 🔒 No leer binarios | No se abre contenido interno de modelos |
| 🔒 No calcular hashes | Los checksums quedan para fase futura (H3.6+) |

---

## 4. Ubicación externa del banco

```
Ruta:      A:\AURA\models
Relación:  Fuera del repositorio (A:\AURA\project)
Espacio:   38.26 GB ocupados · 114.70 GB libres (en unidad A:\)
```

> **Nota**: El banco es externo al repo. No hay carpeta `models/` dentro de `A:\AURA\project`.

---

## 5. Tabla de artefactos detectados

| # | Archivo | Ext | Tamaño (bytes) | Tamaño aprox. | Fecha modificación | Tipo |
|---|---------|:---:|----------------:|:-------------:|:------------------:|:----:|
| 1 | `350m_test.gguf` | .gguf | 709,295,424 | 676 MB | 05/04/2026 | Archivo |
| 2 | `ai21labs_AI21-Jamba-Reasoning-3B-Q8_0.gguf` | .gguf | 3,407,952,352 | 3.17 GB | 05/04/2026 | Archivo |
| 3 | `DeepSeek-R1-Distill-Qwen-1.5B-Q3_K_M.gguf` | .gguf | 924,456,288 | 882 MB | 05/04/2026 | Archivo |
| 4 | `facebookMobileLLM-R1-950M-base-model.safetensors` | .safetensors | 3,798,766,568 | 3.54 GB | 05/04/2026 | Archivo |
| 5 | `gemma-3-1b-it-q4_k_m.gguf` | .gguf | 806,058,240 | 769 MB | 04/04/2026 | Archivo |
| 6 | `googlegemma-4-E2B-it-model.safetensors` | .safetensors | 10,246,621,918 | 9.54 GB | 08/04/2026 | Archivo |
| 7 | `googlegemma-4-E2B-model.safetensors` | .safetensors | 10,246,621,918 | 9.54 GB | 08/04/2026 | Archivo |
| 8 | `google_gemma-3-270m-it-Q4_1.gguf` | .gguf | 247,677,728 | 236 MB | 04/04/2026 | Archivo |
| 9 | `granite-3.0-1b-a400m-instruct-Q4_K_M.gguf` | .gguf | 821,845,024 | 784 MB | 29/03/2026 | Archivo |
| 10 | `granite-4.0-350m-Q4_K_M.gguf` | .gguf | 236,985,760 | 226 MB | 05/04/2026 | Archivo |
| 11 | `OLMo-2-0425-1B-Instruct-Q4_K_M.gguf` | .gguf | 935,515,296 | 892 MB | 29/03/2026 | Archivo |
| 12 | `Phi-4-mini-instruct-GGUF-Q3_K_M.gguf` | .gguf | 2,117,532,992 | 1.97 GB | 05/04/2026 | Archivo |
| 13 | `Pleias-RAG-1B.gguf` | .gguf | 2,393,458,272 | 2.23 GB | 05/04/2026 | Archivo |
| 14 | `qwen2-1_5b-instruct-q4_k_m.gguf` | .gguf | 986,045,824 | 940 MB | 22/03/2026 | Archivo |
| 15 | `smollm2-360m-instruct-q8_0.gguf` | .gguf | 386,404,992 | 368 MB | 29/03/2026 | Archivo |

**Totales**: 15 archivos · **38,265,238,596 bytes** (~38.26 GB)

---

## 6. Clasificación por formato

| Formato | Cantidad | Peso total | % del banco | Usable por `local_llama_provider` |
|---------|:--------:|-----------:|:-----------:|:---------------------------------:|
| **GGUF** ✅ | **12** | 13.56 GB | 35.4% | ✅ Sí, directamente |
| **Safetensors** 🔶 | **3** | 22.62 GB | 59.1% | ❌ No, requiere conversión |
| CKPT | 0 | — | — | — |
| BIN | 0 | — | — | — |
| JSON/config/tokenizer | 0 | — | — | — |
| Carpetas de modelo | 0 | — | — | — |
| Otros/desconocidos | 0 | — | — | — |

> **Nota**: Los safetensors NO son utilizables directamente por `local_llama_provider.py`. Quedan como candidatos a conversión futura GGUF en H3.6+.

---

## 7. Candidatos a uso inmediato (GGUF)

### 7.1 Prioridad muy alta — Livianos (< 1 GB, instruct)

| Modelo | Tamaño | Cuantización | Notas |
|--------|:------:|:------------:|-------|
| `granite-4.0-350m-Q4_K_M` | 226 MB | Q4_K_M | El más liviano, instruct |
| `google_gemma-3-270m-it-Q4_1` | 236 MB | Q4_1 | Muy liviano, instruct |
| `smollm2-360m-instruct-q8_0` | 368 MB | Q8_0 | Alta calidad, instruct |
| `350m_test` | 676 MB | — | Nombre sugiere testing |
| `gemma-3-1b-it-q4_k_m` | 769 MB | Q4_K_M | 1B params, instruct |
| `granite-3.0-1b-a400m-instruct-Q4_K_M` | 784 MB | Q4_K_M | IBM Granite instruct |

### 7.2 Prioridad alta — Medios (~1 GB, instruct)

| Modelo | Tamaño | Cuantización | Notas |
|--------|:------:|:------------:|-------|
| `DeepSeek-R1-Distill-Qwen-1.5B-Q3_K_M` | 882 MB | Q3_K_M | DeepSeek distillado |
| `OLMo-2-0425-1B-Instruct-Q4_K_M` | 892 MB | Q4_K_M | OLMo instruct |
| `qwen2-1_5b-instruct-q4_k_m` | 940 MB | Q4_K_M | Qwen2 instruct |

### 7.3 Prioridad media — Pesados (1-3 GB)

| Modelo | Tamaño | Cuantización | Notas |
|--------|:------:|:------------:|-------|
| `Phi-4-mini-instruct-Q3_K_M` | 1.97 GB | Q3_K_M | Baja precisión (Q3) |
| `Pleias-RAG-1B` | 2.23 GB | — | Especializado RAG |

### 7.4 Prioridad baja / Precaución

| Modelo | Tamaño | Cuantización | Notas |
|--------|:------:|:------------:|-------|
| `ai21labs_AI21-Jamba-Reasoning-3B-Q8_0` | 3.17 GB | Q8_0 | Pesado pero alta calidad. Evaluar si el hardware lo soporta. |

---

## 8. Candidatos a conversión futura GGUF (Safetensors)

| Modelo | Tamaño | Tipo | Riesgo de conversión | Prioridad |
|--------|:------:|:----:|:--------------------:|:---------:|
| `facebookMobileLLM-R1-950M-base-model` | 3.54 GB | Base (no instruct) | Medio | 🟡 Baja (es base, no instruct) |
| `googlegemma-4-E2B-it-model` | 9.54 GB | Instruct | Alto (muy pesado) | 🟠 Media |
| `googlegemma-4-E2B-model` | 9.54 GB | Base | Alto (muy pesado) | 🔴 Baja (preferir instruct) |

> **Requisitos para conversión** (H3.6+):
> - Espacio libre mínimo: 2x el tamaño del modelo original
> - Herramienta: `llama.cpp` o equivalente
> - Verificación de integridad post-conversión
> - No eliminar el original hasta verificar el GGUF resultante

---

## 9. Artefactos que NO deben tocarse

| Artefacto | Motivo |
|-----------|--------|
| `googlegemma-4-E2B-model.safetensors` (9.54 GB) | Es modelo base (no instruct). Preferir la versión instruct si se convierte. |
| `facebookMobileLLM-R1-950M-base-model.safetensors` (3.54 GB) | Es modelo base, no instruct. Requeriría fine-tuning para uso en chat. |
| Cualquier archivo no identificado que aparezca en el futuro | Requiere nueva auditoría antes de cualquier operación. |

---

## 10. Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|:-----------:|:-------:|------------|
| MB-R1 | Espacio insuficiente en disco para conversiones | Baja | Alto | Verificar espacio libre antes de H3.6 (114.7 GB libres actualmente) |
| MB-R2 | Safetensors no utilizables por `local_llama_provider` | Alta | Medio | Priorizar uso de GGUF existentes; safetensors quedan para H3.6+ |
| MB-R3 | Licencias no verificadas | Alta | Alto | No redistribuir modelos sin verificar licencia de cada uno |
| MB-R4 | Modelos base (no instruct) no útiles para chat directo | Media | Bajo | Clasificar correctamente; no intentar usar sin fine-tuning |
| MB-R5 | Posible duplicado gemma-4 (instruct + base = 19 GB) | Media | Bajo | Ambos safetensors tienen exactamente el mismo tamaño (10,246,621,918 bytes). Verificar si son idénticos en H3.6. |
| MB-R6 | Modelos GGUF con cuantización muy baja (Q3_K_M) | Media | Medio | `Phi-4-mini` y `DeepSeek-R1-Distill` usan Q3, que puede afectar calidad. Evaluar antes de uso crítico. |

---

## 11. Recomendaciones para H3.2 / H3.3 / H3.6

### H3.2 — DeepSeek API Provider (diseño)
- Usar modelos GGUF livianos (< 1 GB) para pruebas locales del proveedor.
- **Recomendados**: `smollm2-360m-instruct-q8_0`, `google_gemma-3-270m-it-Q4_1`, `granite-4.0-350m-Q4_K_M`.
- Estos modelos permiten verificar el fallback local sin consumir recursos excesivos.

### H3.3 — Multimodel routing (diseño)
- Clasificar los 12 GGUF por capacidad para routing inteligente:
  - **270M-360M**: Tareas simples, diagnóstico, documentación
  - **1B-1.5B**: Tareas de análisis, generación de propuestas
  - **3B**: Tareas complejas (si el hardware lo soporta)
- Los safetensors no se consideran hasta H3.6+.

### H3.6 — Conversión GGUF
- Prioridad 1: `googlegemma-4-E2B-it-model.safetensors` (instruct, 9.54 GB)
- Prioridad 2: `facebookMobileLLM-R1-950M-base-model.safetensors` (si se necesita modelo base)
- No convertir `googlegemma-4-E2B-model.safetensors` a menos que se necesite específicamente el base.
- Espacio requerido estimado: ~45 GB libres adicionales para las conversiones.

---

## 12. Checklist de seguridad antes de cualquier conversión

- [ ] Espacio libre suficiente (mínimo 2x el tamaño del modelo original)
- [ ] Backup del safetensor original disponible
- [ ] `git status` limpio en el repo
- [ ] Herramienta de conversión verificada (`llama.cpp` o similar)
- [ ] Modo offline o sin consumo de API durante conversión
- [ ] Plan de rollback si la conversión falla
- [ ] Verificación de integridad del GGUF resultante
- [ ] No eliminar el original hasta verificar el GGUF
- [ ] Documentar el proceso y resultado

---

## 13. Nota sobre licencias

**Las licencias NO fueron verificadas en esta auditoría.**

Los nombres de archivo sugieren procedencia de:
- Hugging Face (TheBloke, Google, AI21 Labs, etc.)
- Repositorios oficiales de fabricantes (Google, IBM, AI21, Meta, Microsoft)

No existen archivos LICENSE, README ni metadata textual en `A:\AURA\models`.

**Recomendación**: Antes de cualquier uso en producción o redistribución, verificar la licencia de cada modelo consultando su página de Hugging Face o repositorio oficial. Los modelos más comunes tienen licencias como Apache 2.0, MIT, o licencias específicas del fabricante (ej. Gemma de Google tiene su propia licencia).

---

## 14. Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 27/4/2026 | v1.0 | Auditoría inicial H3.1 — inventario de 15 artefactos en `A:\AURA\models` |

---

**Ubicación**: `docs/hextech/MODEL_BANK_AUDIT.md`  
**Responsable**: Cline bajo supervisión Hextech  
**Estado**: Auditoría completada (solo lectura)  
**Próxima fase**: H3.2 — Diseño DeepSeek API Provider
