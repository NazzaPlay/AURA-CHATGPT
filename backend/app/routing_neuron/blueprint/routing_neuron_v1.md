# Routing Neuron V1

## 1. Identidad

Routing Neuron V1 es el subsistema de:

- observacion de regularidades de routing
- evidencia reusable por sesion
- score con ejes visibles
- runtime limitado, reversible y auditable
- maintenance y lectura admin del repertorio

V1.7 sigue siendo V1:

- sin V2
- sin persistencia pesada
- sin panel UI
- sin judge hub
- sin route families
- sin training real

## 2. Estado actual de V1.7

V1.7 consolida lo que V1.6 ya sabia hacer y agrega una lectura visible mas limpia y una entrada mas realista al primer `applied` seguro:

- sellado estructural del subsistema sin mezclarlo con madurez runtime
- runtime canonico en `backend/app/routing_neuron/core/runtime.py`
- wrappers legacy todavia finos en `agents/routing_*`
- ventana liviana de `runtime_records` para seguimiento reciente
- `session_summaries` refrescados con actividad runtime real
- `routing_neuron_trace` separado de `provider_trace`
- primer sendero `applied` seguro y demostrable
- helper canonico para lectura observable y replay en `backend/app/routing_neuron/admin/observable.py`
- helper canonico de rendering admin/runtime en `backend/app/routing_neuron/admin/rendering.py`
- lectura visible capaz de reutilizar metadatos/logs de sesion cuando el registro runtime en memoria esta vacio
- replay desde logs que ya no se pierde cuando la sesion nueva escribe un log propio sin actividad RN
- semilla observacional para `skip_critic` a partir de verificaciones limpias repetidas en tareas tecnicas
- activacion liviana de candidatas runtime-ready sin esperar siempre una pasada completa de maintenance
- actividad reciente visible priorizando el tramo mas nuevo de la ventana
- prompts tecnicos explicativos sobre auth/oauth/rollback menos propensos a caer por error en troubleshooting
- resumenes visibles de runtime que priorizan tambien las rutas y outcomes mas nuevos

Ese sendero `applied` hoy es:

- `skip_critic` en escenarios compatibles y de bajo riesgo

Tambien siguen permitidas:

- transformaciones de prompt livianas

## 3. Runtime y semantica

Decisiones runtime vigentes:

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

Regla importante:

- `routing_neuron_considered=true` significa que el runtime de RN fue consultado
- `routing_neuron_considered_ids=[]` ya no queda ambiguo si aparece junto con `decision_path=no_candidate_match`
- `routing_neuron_selected=true` distingue cuando hubo una neurona elegida aunque no se haya aplicado

## 4. Trazabilidad minima obligatoria

V1.7 debe dejar, como minimo:

- `routing_neuron_considered`
- `routing_neuron_considered_ids`
- `routing_neuron_selected`
- `routing_neuron_decision`
- `routing_neuron_decision_path`
- `routing_neuron_influence`
- `routing_neuron_barriers_checked`
- `routing_neuron_barriers_blocked`
- `routing_neuron_conflict`
- `routing_neuron_conflict_resolution`
- `routing_neuron_fallback_reason`
- `routing_neuron_outcome_label`

La traza de RN vive fuera de `provider_trace`.

## 5. Lectura operativa

Los estados de observabilidad que usan admin, checkpoint y `system_state` siguen siendo:

- `runtime_ready_but_no_history`
- `only_no_signal_seen`
- `blocked_or_baseline_only`
- `healthy_but_low_sample`
- `applied_activity_observed`

Pero en V1.7 su lectura visible ya debe separar mejor:

- falta de historial runtime en memoria
- replay visible recuperado desde logs
- replay visible recuperado desde el log actual o desde la ultima sesion util
- origen del estado visible entre memoria viva y replay util
- señal debil
- baseline-only
- bloqueo por barrera
- actividad aplicada
- traza visible de sesion/log cuando existe historial operativo observado fuera del proceso actual
- ausencia de snapshot ligero canonico extra por ahora

La validacion operativa se sigue leyendo aparte:

- `runtime_validation_in_progress`
- `baseline_only_validation`
- `runtime_validation_low_sample`
- `runtime_behavior_observed`

## 6. Score y lifecycle

Ejes madre:

- `efficiency_score`
- `stability_score`
- `quality_score`
- `reusability_score`
- `global_routing_score`

Lifecycle visible:

- `observed_pattern`
- `candidate`
- `active`
- `stabilized`
- `promotion_ready`
- `promoted`
- `paused`
- `retired`

Regla de lectura:

- runtime persiste estados base cortos
- admin deriva estados extendidos
- no se confunde lifecycle derivado con estado runtime first-class

## 7. Maintenance, admin y superficie observable

Maintenance debe sostener:

- repertorio
- alertas
- watch y review
- recomendaciones
- summaries de sesion
- activity reciente
- launch dossier tactico cuando aplique

Admin y la lectura visible deben poder diferenciar:

- RN observo
- RN considero sin candidata coincidente
- RN selecciono pero no aplico
- RN fue bloqueada
- RN influyo y aplico
- RN cayo en degraded/fallback
- RN se esta leyendo desde memoria viva o desde replay visible
- RN viene de runtime vivo o de superficie observable reconstruida

## 8. Relacion con V0.39

`shortlist`, `bridge`, `rehearsal`, `cutover` y `launch_dossier` siguen existiendo.

No definen la identidad de Routing Neuron V1.

Regla de lectura:

- son extensiones tacticas utiles
- no identidad central de RN
- RN V1.7 sigue siendo una capa transversal reusable aunque cambie el stack operativo principal

## 9. Deuda V1.x

Sigue pendiente en V1.x:

- adelgazar aun mas `agents/routing_maintenance.py` y `agents/routing_neuron_registry.py`
- terminar de extraer rendering admin compartido desde `agents/system_state_agent.py`
- decidir si la ventana liviana de `runtime_records` alcanza o necesita snapshot o persistencia ligera
- acumular mas historial aplicado real fuera de escenarios tecnicos compatibles
- seguir estabilizando la lectura entre memoria viva y replay desde logs sin inflar arquitectura
- reforzar validacion viva del chat para confirmar que el `applied` util aparece fuera de smokes controlados

No pertenece todavia a V1.x:

- promotions estructurales pesadas
- persistencia especializada grande
- UI dedicada
- composicion multi-neurona rica
- entrenamiento o distillation real
