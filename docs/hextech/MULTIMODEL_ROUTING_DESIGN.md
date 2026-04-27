# H3.3 — Diseño Multimodel Routing para AURA

> **Estado:** Diseño / Plan (sin implementación)
> **Versión:** 1.0
> **Dependencias:** H3.0 (RN Self-Work), H3.1 (Model Bank Audit), H3.2 (DeepSeek Provider Design)
> **Próxima fase:** H3.3.1 (extender task_classifier.py)
> **Regla:** Este documento es diseño. No implementa código. No modifica RN. No conecta APIs.

---

## 1. Propósito

Definir una política de routing multimodelo que permita a AURA seleccionar inteligentemente entre:

- **Respuestas directas** (behavior_agent, sin modelo)
- **Modelos locales livianos** (350M–1B)
- **Modelos locales medianos** (1B–2B)
- **Modelos locales pesados** (3B+, si HW lo soporta)
- **DeepSeek API** (futuro, condicionado por H3.2)

La selección debe basarse en tipo de tarea, complejidad, costo, privacidad, disponibilidad y modo offline.

---

## 2. Alcance

- **Solo diseño documental.** No se implementa código en esta fase.
- Cubre el routing entre: `direct_response` → modelos locales (3 rangos) → DeepSeek API (futuro).
- No cubre: implementación de DeepSeek (H3.2), conversión de Safetensors a GGUF (H3.6+), RN Graph Keeper (H3.7+), RN Provider Supervisor (H3.8+).

---

## 3. Estado actual del routing de modelos

| Aspecto | Estado actual |
|---------|---------------|
| **Providers activos** | 4 instancias de `LocalLlamaProvider`: local_primary (Granite 1B), local_critic (OLMo 1B), local_router (SmolLM2 360M), local_fallback (Qwen 1.5B) |
| **Routing de modelo** | Basado en **rol** (role-based), NO en tipo de tarea. `TaskClassification` determina `requested_role` (primary/critic/none) y `routing_policy.decide_routing()` selecciona el provider para ese rol |
| **Criterios de selección** | Solo 3 caminos: (1) `no_model_needed` → skip, (2) `requested_role=primary` → local_primary, (3) `requested_role=critic` → local_critic |
| **No existe** | Clasificador de tarea→tamaño de modelo, matriz de decisión por complejidad, selección inteligente entre modelos livianos/medianos/pesados |
| **Fallback** | Si primary falla → transitional_fallback (Qwen 1.5B). Si critic falla → primary_only sin critic |
| **Capa direct_response** | `BehaviorAgent` puede responder sin modelo (saludos, troubleshooting práctico, explicaciones técnicas predefinidas) |
| **Router helper** | SmolLM2 360M se usa como helper de routing para inputs cortos, pero solo para hints, no para decidir modelo |
| **DeepSeek** | No implementado. Provider diseñado en H3.2, sin código ni conexión |
| **Banco disponible** | 12 GGUF en `A:\AURA\models` (13.56 GB). Actualmente solo se usan 4. Hay 8 GGUF "durmientes" |

### Brecha identificada

AURA actualmente **no distingue** entre una pregunta técnica simple (que podría responder un modelo de 350M) y una planificación compleja (que requeriría DeepSeek o un modelo más pesado). **Todo** lo que no es `direct_response` va a `local_primary` (Granite 1B) con eventual critic.

---

## 4. Objetivos del routing multimodelo

1. **Usar el modelo mínimo suficiente** para cada tarea, preservando recursos locales.
2. **Preservar recursos** (CPU/RAM) para tareas que realmente los necesiten.
3. **Preparar el terreno** para DeepSeek API sin depender de él.
4. **Garantizar modo offline completo**: todo debe funcionar sin API.
5. **Proteger privacidad**: datos sensibles nunca van a remoto.
6. **Auto-trabajo**: AURA debe poder auto-trabajarse sin gastar API (local-only por defecto).
7. **No degradar** la experiencia del usuario vs. el routing actual.

---

## 5. Qué NO hará la primera versión (H3.3.x)

| Exclusión | Motivo |
|-----------|--------|
| ❌ No implementar DeepSeek real | Depende de H3.2, que está en diseño |
| ❌ No cambiar el provider primario actual | El stack actual funciona; cambios son futuros |
| ❌ No modificar RN ni `agents/routing_*.py` | RN tiene su propio protocolo (RN_WRITE_ALLOWED) |
| ❌ No hacer hot-swap de modelos en runtime | Riesgo de estabilidad; requiere benchmark previo |
| ❌ No benchmark automático de modelos | Será H3.5+ |
| ❌ No auto-descubrimiento de modelos del banco | Será H3.6+ |
| ❌ No modificar `config.py` ni `model_gateway.py` ni `model_registry.py` | Solo diseño en esta fase |

---

## 6. Clasificación de modelos locales por tamaño/costo/capacidad

Basado en el Model Bank Audit (H3.1) y los artefactos en `A:\AURA\models`:

| Categoría | Rango peso | Modelos disponibles | Uso propuesto |
|-----------|------------|-------------------|---------------|
| **Micro** (< 400MB) | 226–368 MB | granite-4.0-350m, gemma-3-270m-it, smollm2-360m-instruct | Routing hints, clasificación rápida, respuestas ultra-livianas |
| **Liviano** (700–900 MB) | 676–940 MB | granite-3.0-1b-a400m, gemma-3-1b-it, DeepSeek-R1-Distill-1.5B, OLMo-2-1B, qwen2-1.5b | Chat general, troubleshooting práctico, análisis simple |
| **Mediano** (1–2 GB) | 1.97–2.23 GB | Phi-4-mini-instruct, Pleias-RAG-1B | Análisis técnico medio, generación de propuestas |
| **Pesado** (3 GB+) | 3.17 GB | AI21-Jamba-Reasoning-3B | Tareas complejas (si HW lo soporta; default disabled) |
| **Remoto** (futuro) | API | DeepSeek API | Planificación compleja, razonamiento profundo |
| **Safetensors** (futuro) | 3.54–9.54 GB | MobileLLM-950M-Base, Gemma-4-E2B-it/base | H3.6+ conversión a GGUF |

### Stack actual en producción

| Provider | Modelo | Familia | Rol | Peso |
|----------|--------|---------|:---:|:----:|
| local_primary | Granite 3.0 1B-A400M-Instruct | granite | primary_conversational | ~700 MB |
| local_critic | OLMo-2-0425-1B-Instruct | olmo2 | critic_verifier | ~700 MB |
| local_router | SmolLM2-360M-Instruct | smollm2 | micro_expert_router | ~226 MB |
| local_fallback | Qwen2-1.5B-Instruct | qwen2 | transitional_fallback | ~940 MB |

---

## 7. Matriz de decisión por tipo de tarea

| Tipo de tarea | Proveedor actual | Proveedor propuesto | Modelo sugerido | ¿DeepSeek? |
|---------------|:----------------:|:-------------------:|:---------------:|:----------:|
| Saludo / charla simple | direct_response | direct_response | — | No |
| Troubleshooting práctico conocido | direct_response | direct_response | — | No |
| Consulta memoria | direct_response | direct_response | — | No |
| Diagnóstico interno | direct_response | direct_response | — | No |
| Pregunta técnica simple (< 10 palabras) | local_primary | **local_liviano** | gemma-3-1b-it / granite-3.0-1b | No |
| "¿Qué es X?" / Explicación técnica breve | local_primary | **local_liviano** | granite-3.0-1b (actual) | No |
| Análisis técnico medio (> 15 palabras) | local_primary | **local_mediano** o primary | Phi-4-mini / Granite 1B | No |
| Troubleshooting con traceback/código | local_primary + critic | **local_liviano + critic** | Granite 1B + OLMo 1B | No |
| Planificación arquitectura compleja | — | **DeepSeek o local_pesado** | Jamba 3B o DeepSeek API | ✅ Si budget OK |
| Generación prompt para Cline | — | **DeepSeek o local_mediano** | Phi-4-mini o DeepSeek | ✅ Solo si justificado |
| Revisión cambios críticos (git diff) | — | **DeepSeek + local critic** | Ambos | ✅ Validación cruzada |
| Tarea con datos sensibles | local_primary | **local_only** | local_liviano | **BLOQUEAR** |
| Modo offline | local_primary | **local_only** | todos locales | **BLOQUEAR** |
| Presupuesto agotado | — | **local_only** | el mejor local disponible | **BLOQUEAR** |
| RN Core touch request | — | **BLOQUEAR** | — | **BLOQUEAR** |

---

## 8. Criterios para usar DeepSeek (futuro)

DeepSeek solo se usará si TODAS las siguientes condiciones se cumplen:

1. **Tarea clasificada** como `planning_complex` o `cross_validation`
2. **AURA_DEEPSEEK_ENABLED=true** (deshabilitado por defecto)
3. **API key presente** y válida (solo por variable de entorno)
4. **Rate limit** no excedido
5. **Budget diario** no agotado (default $0.50 USD)
6. **Modo online** (no offline)
7. **Sin datos sensibles** en el prompt
8. **No es tarea de RN Core**
9. **No es tarea de auto-trabajo** (Self-Work usa local-only por defecto)

---

## 9. Criterios para NO usar DeepSeek (bloqueo)

DeepSeek se bloquea automáticamente si ocurre CUALQUIERA de estas condiciones:

| Condición | Detección | Acción |
|-----------|-----------|--------|
| Modo offline | Env var `AURA_FORCE_OFFLINE=true` o fallo de conectividad | Forzar local_only |
| Datos sensibles en prompt | Palabras clave: password, token, api_key, secret, credentials, dni, cuil, tarjeta, cuenta bancaria | Forzar local_only |
| Tarea de alto riesgo con flag de privacidad | `risk_profile=high` + flag `privacy_sensitive` | Forzar local_only |
| Budget diario excedido | Budget controller reporta excedido | Fallback a local |
| Tarea de RN Core | Clasificación `rn_core_touch` | Bloquear + requerir RN_WRITE_ALLOWED |
| Tarea trivial | Input < 5 palabras sin contexto técnico | local_liviano |
| Auto-trabajo (Self-Work) | Modo self_work activo | local_only por defecto |

---

## 10. Política de fallback

La cadena de fallback completa, en orden descendente:

```
DeepSeek API → local_mediano → local_liviano → local_primary → transitional_fallback → error graceful
```

### Reglas de fallback

1. **DeepSeek falla** (no disponible, timeout, error) → local_mediano (Phi-4-mini o Granite 1B)
2. **local_mediano falla** (modelo no encontrado) → local_liviano (gemma-3-1b-it)
3. **local_liviano falla** → local_primary (Granite 1B, el actual)
4. **local_primary falla** → transitional_fallback (Qwen 1.5B, el actual)
5. **transitional_fallback falla** → error graceful con mensaje al usuario
6. **Máximo 1 re-intento por nivel** de fallback (evitar loops infinitos)
7. **Si el fallback es por datos sensibles u offline**, no se intenta DeepSeek en ningún caso

---

## 11. Política de privacidad

### Datos sensibles detectados

Palabras clave que activan bloqueo de remoto:

```
password, token, api_key, api-key, secret, credentials,
dni, cuil, cuil/cuit, tarjeta, numero de tarjeta,
cuenta bancaria, cbu, alias bancario, clave, pin,
tarjeta de credito, tarjeta de debito
```

### Reglas

1. Si se detectan datos sensibles → **forzar `local_only`**
2. DeepSeek nunca recibe prompts con datos sensibles
3. El logging debe truncar o excluir datos sensibles (nunca loguear el prompt completo si contiene datos sensibles)
4. La detección se hace en la capa de routing, antes de cualquier llamada a provider

---

## 12. Política de costo

| Aspecto | Regla |
|---------|-------|
| DeepSeek budget diario | Default $0.50 USD (configurable vía env var) |
| Budget excedido | Bloqueo automático hasta el día siguiente |
| Modelos locales | Sin costo monetario |
| Prioridad | Priorizar local para todo lo que local pueda resolver |
| Auto-trabajo | local-only por defecto (no gastar API en auto-análisis) |

---

## 13. Política offline

1. **Detección automática**: verificar conectividad antes de rutear a DeepSeek
2. **Modo forzado**: env var `AURA_FORCE_OFFLINE=true` → solo modelos locales
3. **En offline**: funcionalidad completa sin degradación
4. **Sin dependencia de API**: todo el stack local debe funcionar independientemente de DeepSeek

---

## 14. Validación cruzada local/remoto

Para tareas críticas donde se use DeepSeek:

| Tarea crítica | Provider primario | Provider verificador | Comportamiento |
|---------------|:-----------------:|:--------------------:|----------------|
| Revisión de cambios críticos (git diff) | DeepSeek | local_critic (OLMo 1B) | Si divergencia significativa → reportar + pedir revisión humana |
| Planificación arquitectura mayor | DeepSeek | local_critic (OLMo 1B) | Si divergencia → reportar + pedir revisión humana |
| Generación de prompt complejo | DeepSeek o local_mediano | local_critic (OLMo 1B) | Verificación de consistencia |

### Reglas de validación cruzada

1. El crítico local (OLMo 1B) siempre verifica respuestas de DeepSeek en tareas críticas
2. Si los resultados divergen significativamente → se reporta la divergencia y se pide revisión humana
3. La divergencia se mide por: contradicción factual, omisión grave, o recomendación opuesta

---

## 15. Relación con AURA Self-Work (H3.0)

| Aspecto | Regla |
|---------|-------|
| Modo auto-trabajo | **local-only por defecto** |
| DeepSeek en auto-trabajo | Solo para planificación arquitectura compleja, y solo si está justificado explícitamente |
| Auto-diagnóstico | local_only |
| Auto-análisis de código | local_only |
| Auto-documentación | local_only |
| Auto-benchmark | local_only |
| Excepción | Si el auto-trabajo requiere razonamiento profundo no disponible localmente → DeepSeek con aprobación |

---

## 16. Relación con DeepSeek Provider Design (H3.2)

Este documento **consume** la interfaz diseñada en H3.2:

- `DeepSeekProvider.check_availability()` → puerta de entrada para decidir si DeepSeek está disponible
- `DeepSeekProvider.generate()` → llamado si la matriz de decisión selecciona DeepSeek
- Rate limiting, budget controller → diseñados en H3.2, no se duplican aquí
- Fallback local obligatorio → diseñado en H3.2, se integra en la cadena de fallback de este documento

**No se duplica** el diseño de DeepSeek Provider. Este documento define **cuándo** usarlo; H3.2 define **cómo** implementarlo.

---

## 17. Relación con RN Provider Supervisor futuro (H3.8+)

RN-PS recibirá datos de:

- `provider_selected` — qué proveedor se usó
- `task_type` — qué tipo de tarea
- `fallback_chain` — qué cadena de fallback se ejecutó
- `cross_validation_result` — resultado de validación cruzada (si aplicó)

RN-PS podrá sugerir ajustes en la matriz de decisión basado en histórico de routing.

---

## 18. Relación con RN Graph Keeper futuro (H3.7)

RN-GK registrará las relaciones de routing como aristas en el grafo:

- **Nodos**: `local_micro`, `local_liviano`, `local_mediano`, `local_pesado`, `deepseek_api`
- **Aristas**: `activa_a` entre tipo de tarea y provider seleccionado
- **Pesos**: frecuencia de uso, tasa de éxito, latencia promedio

---

## 19. Riesgos y mitigaciones

| ID | Riesgo | Prob | Impacto | Mitigación |
|----|--------|:----:|:-------:|------------|
| MR-R1 | DeepSeek usado sin autorización | Baja | Alto | Deshabilitado por defecto; solo activación explícita vía env var |
| MR-R2 | Modelo local insuficiente para tarea compleja | Media | Medio | Fallback a modelo más grande dentro de lo disponible |
| MR-R3 | Datos sensibles enviados a API accidentalmente | Baja | Crítico | Filtro pre-routing de palabras clave sensibles |
| MR-R4 | Selección incorrecta de modelo degrada experiencia | Media | Medio | Matriz ajustable por configuración sin tocar código |
| MR-R5 | Confusión entre "complejo" y "largo" (tareas largas pero simples) | Media | Bajo | Clasificador por contenido, no solo por longitud |
| MR-R6 | Modelo pesado local (Jamba 3B) satura recursos | Media | Alto | Sondear hardware antes de activar; default disabled |
| MR-R7 | Ciclo de re-intento infinito entre fallbacks | Baja | Medio | Máximo 1 re-intento por fallback, luego error graceful |
| MR-R8 | Falso positivo en detección de datos sensibles bloquea DeepSeek innecesariamente | Media | Bajo | Lista explícita y acotada; revisable por configuración |

---

## 20. Fases futuras H3.3.x

| Sub-fase | Acción | Dependencia | Archivos a modificar |
|----------|--------|:-----------:|---------------------|
| **H3.3.0** | ✅ Diseño y documentación (esta tarea) | H3.0, H3.1, H3.2 | `docs/hextech/MULTIMODEL_ROUTING_DESIGN.md` |
| H3.3.1 | Extender `task_classifier.py` para clasificar por tamaño de modelo requerido | H3.3.0 | `agents/task_classifier.py` |
| H3.3.2 | Extender `routing_policy.py` para implementar matriz de decisión | H3.3.1 | `agents/routing_policy.py` |
| H3.3.3 | Crear suite de tests de routing sin API real | H3.3.2 | `tests/test_multimodel_routing.py` |
| H3.3.4 | Integrar detección offline y filtro de privacidad | H3.3.2 | `agents/routing_policy.py`, `config.py` |
| H3.3.5 | Tests de integración con mock de DeepSeek | H3.3.3, H3.2.x | `tests/test_multimodel_routing.py` |

---

## 21. Tests sin API real

| Test | Descripción | Cobertura |
|------|-------------|:---------:|
| `test_direct_response_never_uses_model` | Saludos, gratitud → no_model_needed | Matriz fila 1-4 |
| `test_simple_technical_uses_local_light` | Pregunta < 10 palabras técnica → local_liviano | Matriz fila 5-6 |
| `test_complex_planning_routes_to_deepseek_if_enabled` | Planificación → DeepSeek si enabled | Matriz fila 9 |
| `test_complex_planning_fallback_to_local` | Planificación → local_mediano si DeepSeek no disponible | Fallback |
| `test_sensitive_data_blocks_remote` | Prompt con "password" → local_only forzado | Privacidad |
| `test_offline_mode_blocks_remote` | Offline detectado → solo locales | Offline |
| `test_budget_exceeded_blocks_deepseek` | Budget agotado → fallback local | Costo |
| `test_budget_available_allows_deepseek` | Budget disponible → DeepSeek permitido | Costo |
| `test_cross_validation_uses_both_providers` | Tarea crítica → DeepSeek + critic local | Validación cruzada |
| `test_rn_core_request_blocked` | Consulta sobre modificar RN → bloqueado | RN protección |
| `test_fallback_chain_respects_order` | DeepSeek → mediano → liviano → primary → fallback | Fallback |
| `test_self_work_defaults_to_local` | Modo self_work activo → local_only | Self-Work |

---

## 22. Checklist antes de implementar código (H3.3.1+)

- [ ] Este documento aprobado por el usuario
- [ ] H3.2 implementado (`deepseek_provider.py` existe y tests con mock pasan)
- [ ] `config.py` tiene env vars de DeepSeek (`AURA_DEEPSEEK_ENABLED`, `AURA_DEEPSEEK_API_KEY`, `AURA_DEEPSEEK_DAILY_BUDGET`)
- [ ] Model Bank Audit (H3.1) completado y documentado
- [ ] No hay cambios pendientes en Git
- [ ] Plan H3.3.x detallado y aprobado
- [ ] Modo ACT MODE habilitado para implementación

---

## 23. Resumen de restricciones

| Restricción | Aplica a |
|-------------|:--------:|
| ✅ DeepSeek deshabilitado por defecto | Siempre |
| ✅ API key solo por variable de entorno | DeepSeek |
| ✅ Fallback local obligatorio | Siempre |
| ✅ Rate limiting obligatorio | DeepSeek |
| ✅ Daily budget obligatorio | DeepSeek |
| ✅ Tests con mocks | DeepSeek |
| ✅ Primera prueba real solo con aprobación humana | DeepSeek |
| ✅ Modo offline/local-only funciona completo | Siempre |
| ✅ Tareas sensibles bloquean remoto | Siempre |
| ✅ RN Core touch request bloqueado o requiere RN_WRITE_ALLOWED | Siempre |
| ✅ AURA Self-Work prioriza local-only por defecto | Self-Work |
| ❌ No se conecta API en esta fase | H3.3 |
| ❌ No se toca RN | H3.3 |
| ❌ No se modifica código funcional | H3.3 |
