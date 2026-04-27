# DeepSeek API Provider Design — H3.2

## 1. Propósito

Diseñar la integración futura de **DeepSeek API** como proveedor remoto seguro en AURA, permitiendo tareas de razonamiento y planificación que requieran mayor capacidad que los modelos locales GGUF.

**Fase**: H3.2 — Diseño DeepSeek API Provider  
**Estado**: Documentación de diseño (no implementación)  
**Fecha**: 27/4/2026  

---

## 2. Alcance

- **Solo diseño**: No implementación, no conexión API, no API key
- **Provider futuro**: `providers/deepseek_provider.py`
- **Roles iniciales**: `reasoning_planner` (planificación/razonamiento complejo)
- **Paradigma**: Remote-first con fallback local obligatorio
- **Relación con H3.0**: Este diseño concreta la sección 7.2 de `RN_SELF_WORK_PLAN.md`
- **Relación con H3.1**: Los modelos GGUF locales (12 disponibles) sirven como fallback

---

## 3. Estado actual de providers

| Provider | Tipo | `is_local` | Estado |
|----------|------|:----------:|--------|
| `local_primary` (Granite 1B) | Local GGUF | ✅ `True` | Activo |
| `local_critic` (OLMo 1B) | Local GGUF | ✅ `True` | Activo |
| `local_router` (SmolLM2 360M) | Local GGUF | ✅ `True` | Activo |
| `transitional_fallback` (Qwen 1.5B) | Local GGUF | ✅ `True` | Activo |
| **`deepseek_api`** (futuro) | **API remota** | **❌ `False`** | **Diseño** |

### 3.1 Arquitectura actual de providers

```
BaseProvider (ABC)
  └── LocalLlamaProvider
        ├── local_primary      (Granite, rol: primary_conversational)
        ├── local_critic       (OLMo,   rol: critic_verifier)
        ├── local_router       (SmolLM2, rol: micro_expert_router)
        └── transitional_fallback (Qwen, rol: transitional_fallback)

ModelRegistry
  └── providers: dict[str, BaseProvider]
  └── default_roles: dict[str, str]
  └── fallback_provider_id: str

ModelGateway
  └── invoke_model_gateway(prompt, routing_decision, registry)
```

### 3.2 Puntos de extensión identificados

| Componente | Extensión necesaria | Dificultad |
|------------|--------------------|:----------:|
| `BaseProvider` | Ya es abstracta — `DeepSeekProvider` implementa la interfaz | Baja |
| `ProviderDescriptor` | `is_local=False` para DeepSeek | Baja |
| `ModelRegistry` | Agregar `deepseek_api` al dict `providers` | Baja |
| `ModelGateway` | Ya selecciona por rol — funciona sin cambios | Ninguna |
| `config.py` | Nuevas env vars para DeepSeek | Media |
| `providers/__init__.py` | Exportar `DeepSeekProvider` | Baja |

---

## 4. Objetivos del provider DeepSeek

1. **Razonamiento complejo**: Planificación, análisis profundo, generación de propuestas
2. **Complemento local**: No reemplaza modelos locales, los complementa
3. **Modo offline completo**: Si DeepSeek no está disponible, el sistema funciona igual
4. **Seguro por defecto**: Deshabilitado, sin exponer API key, con rate limiting y budget
5. **Preparar RN-PS**: Proveer métricas para el futuro RN Provider Supervisor (H3.8+)
6. **Validación cruzada futura**: DeepSeek + local para tareas críticas (H3.3)

---

## 5. Qué NO hará en la primera implementación

| Acción | Motivo |
|--------|--------|
| ❌ Reemplazar el provider local primario | DeepSeek es complemento, no sustituto |
| ❌ Usarse para tareas simples (chat, diagnóstico) | Los modelos locales son suficientes |
| ❌ Tener acceso a memoria persistente | Riesgo de seguridad |
| ❌ Modificar código ni archivos funcionales | Solo generación de texto |
| ❌ Conectarse automáticamente al inicio | `AURA_DEEPSEEK_ENABLED=false` por defecto |
| ❌ Almacenar API key en disco ni en `config.py` | Solo variable de entorno |
| ❌ Ejecutarse sin rate limiting | Protección contra costos |
| ❌ Ejecutarse sin budget diario | Protección contra costos |

---

## 6. Variables de entorno propuestas

| Variable | Tipo | Default | Propósito |
|----------|:----:|:-------:|-----------|
| `AURA_DEEPSEEK_ENABLED` | `bool` | `"false"` | Habilita/deshabilita el provider. **Deshabilitado por defecto** |
| `AURA_DEEPSEEK_API_KEY` | `str` | `""` | API key de DeepSeek. **Nunca en código, solo env var** |
| `AURA_DEEPSEEK_BASE_URL` | `str` | `"https://api.deepseek.com"` | URL base de la API |
| `AURA_DEEPSEEK_MODEL` | `str` | `"deepseek-chat"` | Modelo a usar en la API |
| `AURA_DEEPSEEK_MAX_REQUESTS_PER_MINUTE` | `int` | `60` | Rate limiting |
| `AURA_DEEPSEEK_DAILY_BUDGET_USD` | `float` | `"0.50"` | Presupuesto diario máximo en USD |

### 6.1 Reglas de seguridad para las variables

- `AURA_DEEPSEEK_API_KEY` **nunca** debe estar en código fuente, logs, ni archivos de configuración
- `AURA_DEEPSEEK_ENABLED` debe ser explícitamente `"true"` para activar el provider
- Todas las variables deben tener valores por defecto seguros (disabled, empty, zero)

---

## 7. Arquitectura propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    AURA Provider Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │  LocalLlamaProvider  │    │  DeepSeekProvider        │    │
│  │  (local_primary)     │    │  (deepseek_api)          │    │
│  │  (local_critic)      │    │  - is_local=False        │    │
│  │  (local_router)      │    │  - HTTP requests         │    │
│  │  (fallback)          │    │  - Rate limiter          │    │
│  └─────────┬───────────┘    │  - Budget controller      │    │
│            │                └──────────┬───────────────┘    │
│            │                           │                    │
│            └──────────┬────────────────┘                    │
│                       │                                     │
│              ┌────────▼────────┐                            │
│              │  ModelRegistry  │                            │
│              │  (central)      │                            │
│              └────────┬────────┘                            │
│                       │                                     │
│              ┌────────▼────────┐                            │
│              │  ModelGateway   │                            │
│              │  (routing)      │                            │
│              └─────────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 Flujo de decisión

```
Tarea entrante
  │
  ▼
TaskClassifier
  │
  ├── Tarea simple (chat, diagnóstico) → LocalLlamaProvider
  │
  ├── Tarea compleja (planificación, razonamiento)
  │     │
  │     ▼
  │   DeepSeekProvider.check_availability()
  │     │
  │     ├── Disponible → DeepSeekProvider.generate()
  │     │
  │     └── No disponible (disabled, no key, rate limit, budget, error)
  │           │
  │           ▼
  │         Fallback → LocalLlamaProvider (transitional_fallback)
  │
  └── Tarea crítica (validación cruzada) → Ambos + comparación (H3.3+)
```

---

## 8. Interfaz propuesta del provider

```python
class DeepSeekProvider(BaseProvider):
    """Proveedor remoto para DeepSeek API."""

    def __init__(
        self,
        enabled: bool = False,
        api_key: str = "",
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        max_requests_per_minute: int = 60,
        daily_budget_usd: float = 0.50,
        provider_id: str = "deepseek_api",
        display_name: str = "DeepSeek API remote provider",
        roles_supported: tuple[str, ...] = ("reasoning_planner",),
        notes: str = "Provider remoto para razonamiento/planificación vía DeepSeek API.",
    ) -> None:
        # api_key solo en memoria, nunca persistida
        # Rate limiter y budget controller se inicializan aquí
        ...

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="deepseek_api",
            display_name="DeepSeek API remote provider",
            backend_type="deepseek_http_api",
            roles_supported=("reasoning_planner",),
            is_local=False,                    # ← Clave: es remoto
            family="deepseek",
            model_id="deepseek-chat",
            role="reasoning_planner",
            runtime_backend="http_api",
            artifact_format="api_endpoint",
            license_tier="api_service",
            openness_tier="api_closed_source",
            commercial_ok=True,
            device_tier="cloud_api",
            policy_status="remote_api",
            availability=self._availability,
            availability_reason=self._availability_reason,
            notes="Provider remoto para razonamiento/planificación vía DeepSeek API.",
        )

    def check_availability(self) -> tuple[bool, str | None]:
        if not self._enabled:
            return False, "disabled"
        if not self._api_key:
            return False, "no_api_key"
        if self._rate_limiter.is_limited():
            return False, "rate_limited"
        if self._budget_controller.is_exceeded():
            return False, "daily_budget_exceeded"
        # En implementación real: ping ligero a la API
        # En tests: mock
        return True, None

    def generate(self, request: ProviderRequest) -> ProviderResult:
        available, reason = self.check_availability()
        if not available:
            return ProviderResult(
                provider_id=self._provider_id,
                role=request.role,
                status=PROVIDER_RESULT_UNAVAILABLE,
                error=reason,
                availability=False,
                runtime_info=(f"deepseek:unavailable:{reason}",),
            )

        # En implementación real:
        # 1. Construir payload HTTP
        # 2. Aplicar rate limiter
        # 3. Hacer request a DeepSeek API
        # 4. Calcular costo estimado
        # 5. Actualizar budget controller
        # 6. Loguear sin exponer API key
        # 7. Retornar ProviderResult

        # En tests: mock de httpx.post / requests.post
        ...
```

---

## 9. Modo disabled por defecto

- `AURA_DEEPSEEK_ENABLED` debe ser explícitamente `"true"` para activarse
- Si está disabled, `check_availability()` retorna `(False, "disabled")`
- `descriptor.availability` será `False`
- El sistema opera normalmente solo con providers locales
- No hay intentos de conexión ni consumo de recursos de red

---

## 10. Fallback obligatorio a modelo local

- Si DeepSeek falla (timeout, error HTTP, rate limit, budget excedido), se redirige al fallback local
- El fallback actual (`LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID` con Qwen 1.5B) maneja la respuesta
- El gateway registra en traces que ocurrió un fallback

```python
# Comportamiento esperado en ModelGateway o routing_policy:
result = deepseek_provider.generate(request)
if result.status != PROVIDER_RESULT_SUCCESS:
    fallback_provider = registry.get_fallback_provider()
    if fallback_provider:
        result = fallback_provider.generate(request)
        # Trace incluye: "deepseek:fallback:local"
```

---

## 11. Rate limiting

| Parámetro | Valor | Configurable |
|-----------|:-----:|:------------:|
| Máximo de requests por minuto | 60 | `AURA_DEEPSEEK_MAX_REQUESTS_PER_MINUTE` |
| Algoritmo | Token bucket o sliding window | — |
| Al alcanzar el límite | Fallback automático a local | — |
| Warning al 80% del límite | Log de warning | — |

### 11.1 Comportamiento

1. Cada request consume un token del bucket
2. Los tokens se regeneran a razón de `max_requests_per_minute / 60` por segundo
3. Si no hay tokens disponibles → `check_availability()` retorna `(False, "rate_limited")`
4. El rate limit se resetea al cambiar el minuto

---

## 12. Control de presupuesto

| Parámetro | Valor | Configurable |
|-----------|:-----:|:------------:|
| Presupuesto diario máximo | $0.50 USD | `AURA_DEEPSEEK_DAILY_BUDGET_USD` |
| Costo estimado input | ~$0.14/M tokens | Fijo (deepseek-chat) |
| Costo estimado output | ~$0.28/M tokens | Fijo (deepseek-chat) |
| Al exceder presupuesto | Provider desactivado hasta próximo día | — |

### 12.1 Cálculo de costo estimado

```python
def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * 0.14
    output_cost = (output_tokens / 1_000_000) * 0.28
    return input_cost + output_cost
```

### 12.2 Persistencia del contador

- El contador de presupuesto se resetea diariamente
- Se puede implementar con un archivo de metadatos en `ops/` (sin tocar `memory.json`)
- Alternativa: contador en memoria que se resetea al reiniciar AURA

---

## 13. Manejo de errores

| Situación | Comportamiento | Código de error |
|-----------|---------------|:---------------:|
| Provider disabled | No intentar conectar | `disabled` |
| Sin API key | No intentar conectar | `no_api_key` |
| Timeout de conexión | Fallback + log warning | `connection_timeout` |
| HTTP 401 (unauthorized) | Deshabilitar provider por seguridad | `auth_failed` |
| HTTP 429 (rate limit) | Esperar + fallback | `rate_limited` |
| HTTP 500+ (server error) | Fallback inmediato | `server_error` |
| Budget excedido | Provider deshabilitado temporalmente | `daily_budget_exceeded` |
| Error de red general | Fallback | `network_error` |
| Respuesta vacía | Reintentar 1 vez, luego fallback | `empty_response` |
| Respuesta malformada | Fallback | `malformed_response` |

---

## 14. Logging seguro sin exponer API key

| Elemento | Qué loguear | Qué NO loguear |
|----------|-------------|----------------|
| API key | Solo `key_prefix:{key[:4]}...` | La API key completa |
| Request | Modelo, tokens estimados, timestamp | Payload completo |
| Response | Status code, tokens usados, costo | Body de la respuesta |
| Error | Tipo de error, status code HTTP | Detalles sensibles |
| Rate limit | Límite actual, requests en el minuto | — |
| Budget | Gasto acumulado, límite diario | — |

### 14.1 Ejemplo de log seguro

```
[DeepSeekProvider] auth:key_prefix:sk-d8...
[DeepSeekProvider] request:model=deepseek-chat, est_input_tokens=450, est_output_tokens=120
[DeepSeekProvider] response:status=200, tokens_in=432, tokens_out=98, cost=$0.00009
[DeepSeekProvider] error:connection_timeout (timeout=30s)
[DeepSeekProvider] rate_limit:current=58/60, limited=True
[DeepSeekProvider] budget:daily_spent=$0.42, limit=$0.50, exceeded=False
```

---

## 15. Tests sin llamar API real

### 15.1 Estrategia de testing

- Usar `unittest.mock.patch` para simular `httpx.post` o `requests.post`
- No se requiere conexión real a DeepSeek API
- Todos los tests deben pasar en modo offline

### 15.2 Casos de test

| Test | Descripción |
|------|-------------|
| `test_disabled_by_default` | `check_availability()` retorna `(False, "disabled")` sin env var |
| `test_no_api_key` | `check_availability()` retorna `(False, "no_api_key")` con key vacía |
| `test_enabled_with_key` | `check_availability()` retorna `(True, None)` con key válida simulada |
| `test_rate_limiting` | Después de N requests, el rate limiter bloquea |
| `test_rate_limit_reset` | El rate limiter se resetea después del intervalo |
| `test_budget_exceeded` | Después de gastar el presupuesto, el provider se desactiva |
| `test_budget_daily_reset` | El contador de budget se resetea al nuevo día |
| `test_fallback_on_timeout` | Timeout simulado → fallback a local |
| `test_fallback_on_http_401` | HTTP 401 simulado → fallback + provider deshabilitado |
| `test_fallback_on_http_429` | HTTP 429 simulado → fallback |
| `test_fallback_on_http_500` | HTTP 500 simulado → fallback |
| `test_logging_no_api_key` | Verificar que logs no contienen API key completa |
| `test_descriptor_is_local_false` | `descriptor.is_local` es `False` |
| `test_descriptor_roles` | `roles_supported` contiene `"reasoning_planner"` |
| `test_generate_success` | Mock de respuesta exitosa → `PROVIDER_RESULT_SUCCESS` |
| `test_generate_empty_response` | Mock de respuesta vacía → `PROVIDER_RESULT_EMPTY` |

---

## 16. Plan de implementación futura H3.2.x

| Sub-fase | Acción | Dependencias | Archivos afectados |
|----------|--------|:------------:|--------------------|
| **H3.2.0** | ✅ Diseño y documentación (esta tarea) | Ninguna | `docs/hextech/DEEPSEEK_PROVIDER_DESIGN.md` |
| **H3.2.1** | Crear `providers/deepseek_provider.py` (clase base) | H3.2.0 | `providers/deepseek_provider.py` |
| H3.2.2 | Agregar env vars a `config.py` | H3.2.1 | `config.py` |
| H3.2.3 | Exportar en `providers/__init__.py` | H3.2.1 | `providers/__init__.py` |
| H3.2.4 | Registrar en `ModelRegistry.build_default_model_registry()` | H3.2.1 | `agents/model_registry.py` |
| H3.2.5 | Implementar rate limiting y budget controller | H3.2.1 | `providers/deepseek_provider.py` |
| H3.2.6 | Tests simulados (sin API real) | H3.2.5 | `tests/test_deepseek_provider.py` |
| H3.2.7 | Prueba real con API key (supervisado) | H3.2.6 + aprobación | — |
| H3.2.8 | Documentación de uso y límites | H3.2.7 | `docs/hextech/DEEPSEEK_PROVIDER_DESIGN.md` |

---

## 17. Relación con H3.3 (multimodel routing)

- **H3.2** provee el provider remoto (`DeepSeekProvider`)
- **H3.3** (ver `docs/hextech/MULTIMODEL_ROUTING_DESIGN.md`) define **cuándo** usar DeepSeek vs local:
  - Tareas de planificación → DeepSeek
  - Tareas de chat simple → Local
  - Validación cruzada → Ambos
- El `task_classifier.py` existente puede extender sus criterios para clasificar tareas
- Posible integración con `routing_policy.py` para decisiones de routing automáticas

### 17.1 Criterios de routing propuestos para H3.3

> **Nota**: H3.3 refina estos criterios en una matriz de decisión completa. Ver `docs/hextech/MULTIMODEL_ROUTING_DESIGN.md` sección 7.

| Tipo de tarea | Provider | Justificación |
|---------------|----------|---------------|
| Diagnóstico simple | Local GGUF | Bajo costo, respuesta rápida |
| Documentación | Local GGUF | Suficiente capacidad |
| Análisis de código | Local GGUF o DeepSeek | Según complejidad |
| Planificación | DeepSeek API | Mayor razonamiento |
| Generación de propuestas | DeepSeek API | Calidad de salida |
| Validación cruzada | Ambos | Consistencia y seguridad |
| Tareas críticas | Ambos + verificación | Máxima seguridad |

---

## 18. Relación con RN Provider Supervisor futuro (H3.8+)

- **RN-PS** (RN Provider Supervisor) supervisará salud de todos los providers
- `DeepSeekProvider` expondrá métricas vía `descriptor`:
  - `availability`: conectividad actual
  - Métricas de rate limiting y budget
- RN-PS podrá sugerir failover preventivo basado en métricas históricas
- `DeepSeekProvider` reportará a RN-PS sin modificar RN Core
- RN-PS es una neurona RN Family candidata (ver `RN_SELF_WORK_PLAN.md` sección 11.1)

---

## 19. Riesgos y mitigaciones

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|:-----------:|:-------:|------------|
| DSK-R1 | Exposición accidental de API key | Baja | Crítico | Solo env vars, nunca en logs/código, logging seguro |
| DSK-R2 | Costos inesperados por API | Media | Alto | Budget diario ($0.50 default) + rate limiting |
| DSK-R3 | Dependencia de conectividad | Alta | Medio | Fallback local obligatorio, modo offline completo |
| DSK-R4 | DeepSeek cambia su API | Baja | Alto | Abstracción vía BaseProvider, tests con mock |
| DSK-R5 | Latencia alta afecta experiencia | Media | Bajo | Timeout configurable + fallback automático |
| DSK-R6 | Modo offline no detectado | Media | Medio | `check_availability()` antes de cada request |
| DSK-R7 | Uso excesivo de tokens en tareas simples | Media | Medio | Routing inteligente (H3.3) para evitar DeepSeek en tareas simples |
| DSK-R8 | Dependencia de un solo proveedor externo | Baja | Medio | Diseño permite agregar más providers remotos (OpenAI, Anthropic, etc.) |

---

## 20. Checklist antes de activar API real

Este checklist debe completarse **antes de cualquier conexión real a DeepSeek API**:

- [ ] H3.2.0 a H3.2.6 completados (diseño + implementación base + tests simulados)
- [ ] `AURA_DEEPSEEK_ENABLED` en `"false"` por defecto en código
- [ ] Tests de rate limiting pasan en entorno simulado
- [ ] Tests de budget controller pasan
- [ ] Tests de fallback local pasan
- [ ] Logs verificados: no exponen API key
- [ ] `git status` limpio
- [ ] Plan H3.2.7 aprobado por usuario
- [ ] API key obtenida de DeepSeek (por el usuario, no por Cline)
- [ ] Usuario presente durante primera conexión
- [ ] Modo solo lectura para primera prueba (sin modificar nada)
- [ ] Rollback plan definido (desactivar env var, revertir a local)

---

## 21. Restricciones de diseño

### 21.1 Restricciones absolutas

1. **No almacenar API key** en código, archivos de configuración, logs ni memoria persistente
2. **No conectar API** sin plan H3.2.7 aprobado y usuario presente
3. **No reemplazar** providers locales como primary
4. **No modificar RN Core** ni componentes RN Family sin `RN_WRITE_ALLOWED`
5. **No instalar dependencias** sin permiso explícito (regla 7 de `.clinerules`)

### 21.2 Restricciones de implementación

1. `DeepSeekProvider` debe implementar `BaseProvider` (ABC)
2. `is_local` debe ser `False` en `ProviderDescriptor`
3. Rate limiting y budget controller son obligatorios, no opcionales
4. Fallback local es obligatorio ante cualquier error
5. Tests deben usar mocks, no llamadas reales a la API

---

## 22. Historial

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 27/4/2026 | v1.0 | Creación inicial como parte de H3.2 — Diseño DeepSeek API Provider |

---

**Ubicación**: `docs/hextech/DEEPSEEK_PROVIDER_DESIGN.md`  
**Responsable**: Cline bajo supervisión Hextech  
**Estado**: Documentación de diseño (H3.2)  
**Próxima fase**: H3.2.1 — Implementación de `providers/deepseek_provider.py` (requiere aprobación)
