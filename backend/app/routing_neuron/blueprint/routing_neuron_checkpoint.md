# Routing Neuron Checkpoint

Fecha: 2026-04-08
Estado: V1.8 sellado estructuralmente, operativo en runtime, con ventana liviana de historial reciente, helpers canonicos de lectura observable y rendering admin, separacion mas clara respecto de `provider_trace`/`system_state`, y sendero applied mas visible en chats tecnicos compatibles

## 1. Lectura correcta del estado

Routing Neuron V1.8 debe leerse en capas:

- sellado estructural
- runtime canonico disponible
- historial reciente liviano
- validacion operativa observable
- traza visible de sesion/log cuando el proceso actual no conserva runtime en memoria
- replay estable aun cuando la sesion nueva ya escribio un log propio sin decisiones RN
- sin snapshot canonico extra todavia: memoria viva + replay visible siguen siendo el modelo actual

Eso implica:

- estar sellada no significa tener historial largo
- haber observado senal debil no significa haber influido
- haber seleccionado una neurona no significa haber aplicado
- un `applied` real y seguro ya existe, pero la muestra puede seguir siendo baja

## 2. Lo que existe de verdad

Canonico:

- `backend/app/routing_neuron/core/observer.py`
- `backend/app/routing_neuron/core/runtime.py`
- `backend/app/routing_neuron/core/governor.py`
- `backend/app/routing_neuron/core/promoter.py`
- `backend/app/routing_neuron/core/registry.py`
- `backend/app/routing_neuron/core/maintenance.py`
- `backend/app/routing_neuron/schemas/*`
- `backend/app/routing_neuron/admin/*`

Compatibilidad legacy:

- `agents/routing_observer.py`
- `agents/routing_runtime.py`
- `agents/routing_scorer.py`
- `agents/routing_neuron_registry.py`
- `agents/routing_maintenance.py`
- `agents/system_state_agent.py`

La compatibilidad legacy se mantiene para no romper AURA actual.

Lectura honesta:

- `routing_runtime` y `routing_observer` son wrappers finos
- `routing_maintenance` y `routing_neuron_registry` siguen siendo backplane legacy
- `system_state_agent.py` sigue concentrando parte del rendering visible
- `system_state_agent.py` ya resume mejor el estado sin mezclar tanto provider/runtime/checkpoint
- el namespace canonico manda y la compatibilidad legacy no redefine la semantica central

## 3. Runtime V1.8

Decisiones reales:

- `no_signal`
- `suggested_only`
- `blocked_by_barrier`
- `paused`
- `cooldown`
- `applied`

Trayectorias semanticas de apoyo:

- `no_candidate_match`
- `candidate_seen_no_active_match`
- `selected_paused`
- `selected_cooldown`
- `selected_blocked`
- `selected_not_applied`
- `selected_and_applied`

Esto resuelve el caso que antes quedaba ruidoso:

- `routing_neuron_considered=true`
- `routing_neuron_considered_ids=[]`
- `routing_neuron_decision=no_signal`
- `routing_neuron_fallback_reason=no_match`

Ahora la lectura correcta es:

- RN fue consultada
- no hubo candidatas coincidentes
- `decision_path=no_candidate_match`

## 4. Sendero applied seguro ya disponible y mas visible

V1.8 mantiene un `applied` realista y reversible:

- `skip_critic` cuando la neurona activa lo sugiere y la barrera lo permite

Propiedades:

- bajo riesgo
- reversible
- auditable
- separado de `provider_trace`
- visible en runtime records, summary, admin state, `system_state`, checkpoint y actividad reciente
- ahora tambien puede emerger de forma mas organica tras verificaciones limpias repetidas de tareas tecnicas explicativas con critic, sin sembrar la candidata a mano
- la clasificacion visible evita mejor confundir prompts explicativos sobre auth/oauth/rollback con troubleshooting si no hay marcadores reales de falla

Tambien siguen existiendo:

- transformaciones de prompt livianas

## 5. Ventana de historial y traza visible

`runtime_records` sigue siendo:

- ventana liviana
- reciente
- util para seguimiento inmediato
- no persistencia pesada

La lectura correcta de esa ventana:

- sirve para observar actividad reciente
- sirve para alinear estado/admin/checkpoint
- no pretende ser historico largo todavia

Cuando el registro runtime en memoria esta vacio pero la sesion ya dejo metadatos RN en conversacion o log:

- `system_state`
- `checkpoint routing neuron`
- `muestra actividad reciente de routing neuron`

pueden mostrar una traza visible de sesion/log sin inventar actividad canonica.

En V1.8 esa logica visible vive mas cerca del namespace canonico en:

- `backend/app/routing_neuron/admin/observable.py`
- `backend/app/routing_neuron/admin/rendering.py`

En lugar de quedar concentrada por completo en `system_state_agent.py`.

En V1.8 ademas:

- si el log actual todavia no trae actividad RN
- pero la ultima sesion registrada si la trae

la lectura visible no debe volver a "sin historial" por ese detalle de orden temporal.

No se agrego snapshot ligero canonico todavia:

- se evaluo
- se considero prematuro
- por ahora la politica sigue siendo memoria viva + replay visible desde sesion/log

## 6. Superficies alineadas en V1.8

Las siguientes vistas deben contar la misma historia:

- `que estado tienes`
- `checkpoint routing neuron`
- `muestra actividad reciente de routing neuron`

Escenarios cubiertos:

- sin historial reciente
- weak signal / `no_signal`
- baseline-only / selected-not-applied
- bloqueos por barrera
- degraded / fallback
- actividad `applied`
- lectura recuperada desde la ultima sesion registrada cuando corresponde
- lectura recuperada desde la ultima sesion registrada aunque la sesion nueva ya tenga un log propio sin huella RN
- actividad reciente priorizando el tramo mas nuevo de la ventana, para no esconder el ultimo `applied`
- summaries de runtime/admin que priorizan tambien el tramo mas nuevo de `recent_paths`, `recent_outcomes` y `recent_applied_influences`

## 7. Wording operativo recomendado

Formas de lectura preferidas:

- runtime preparado, todavia sin historial reciente
- sin historial runtime en memoria, con traza visible recuperada de la ultima sesion registrada
- senal debil observada, sin candidatas coincidentes recientes
- actividad baseline-only observada, sin aplicar cambios
- actividad bloqueada observada, sin aplicar cambios
- actividad aplicada observada con muestra baja
- actividad aplicada observada
- validacion operativa en progreso

Evitar:

- decir "sin historial real" cuando ya hubo weak signal, degraded o applied en la sesion visible
- mezclar baseline-only con blocked sin aclaracion
- tratar `considered` como si significara siempre `candidate ids` no vacios
- mezclar `provider_trace` con decisiones RN o usar el checkpoint como si fuera health directo del provider stack

## 8. Huecos aceptados

Siguen abiertos en V1.x:

- backplane legacy en `agents/routing_neuron_registry.py`
- backplane legacy en `agents/routing_maintenance.py`
- parte del rendering admin y de checkpoint sigue compartida con `agents/system_state_agent.py`, aunque menos que antes
- falta decidir si algun dia conviene snapshot o persistencia ligera si la ventana reciente queda corta
- muestra `applied` aun baja fuera de escenarios tecnicos compatibles
- el `applied` visible ya no depende solo de tests sembrados, pero sigue dependiendo de verificaciones limpias y contexto seguro
- la validacion viva del chat todavia necesita acumular mas evidencia fuera de secuencias tecnicas repetidas
- la alineacion futura con promotion/benchmark del banco ampliado de modelos sigue pendiente de evidencia real, no de activacion automatica

## 9. Lo que no pertenece todavia

No meter en este checkpoint:

- V2
- panel UI
- persistencia pesada
- judge hub
- route families
- synthesis
- training real
- promociones estructurales pesadas
