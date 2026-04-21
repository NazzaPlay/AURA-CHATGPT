# Routing Neuron V1 Checkpoint

Documento legacy de compatibilidad.
La referencia canonica vive en `backend/app/routing_neuron/blueprint/`.

## Estado resumido

Routing Neuron esta en V1.8:

- subsistema canonico ya sellado
- runtime limitado ya operativo
- ventana liviana de historial reciente
- primer camino `applied` seguro ya demostrable
- mejor lectura visible de weak signal, baseline-only, blocked y applied
- traza visible de sesion/log cuando el proceso actual no conserva runtime en memoria
- replay visible mas estable cuando la sesion nueva ya escribio un log propio sin huella RN
- helper canonico para lectura observable y replay
- helper canonico de rendering admin/runtime
- separacion mas limpia entre `provider_trace`, `routing_neuron_trace`, `system_state` y checkpoint visible
- lectura compacta mas consistente entre estado general y checkpoint RN
- `skip_critic` mas alcanzable tras verificaciones limpias repetidas en sesiones tecnicas compatibles
- prompts tecnicos explicativos menos propensos a caer por error en troubleshooting

## Lectura correcta

No confundir:

- sellado estructural
- historial reciente en memoria
- validacion operativa
- traza visible de sesion
- replay desde la ultima sesion util
- actividad aplicada

Hoy el sistema puede mostrar de forma honesta:

- runtime preparado, todavia sin historial reciente
- sin historial runtime en memoria, con traza visible recuperada de la ultima sesion registrada
- senal debil observada
- actividad sin aplicacion
- actividad aplicada observada con muestra baja
- actividad aplicada observada
- y sigue distinguiendo que parte viene de memoria viva y que parte viene de replay visible

## Semantica runtime

Decisiones:

- `no_signal`
- `suggested_only`
- `blocked_by_barrier`
- `paused`
- `cooldown`
- `applied`

Trayectorias cortas:

- `no_candidate_match`
- `candidate_seen_no_active_match`
- `selected_paused`
- `selected_cooldown`
- `selected_blocked`
- `selected_not_applied`
- `selected_and_applied`

Caso importante:

- `routing_neuron_considered=true` con `routing_neuron_considered_ids=[]` significa que RN fue consultada aunque no encontro candidatas coincidentes
- la salida visible puede explicarlo como "considerada globalmente sin candidata coincidente"

## Sendero applied

V1.8 mantiene como sendero `applied` seguro:

- `skip_critic`

Sigue siendo:

- reversible
- auditable
- separado de `provider_trace`
- y ahora puede emerger tambien desde verificaciones limpias repetidas, no solo desde semilla manual

## Compatibilidad

Se mantiene:

- namespace canonico en `backend/app/routing_neuron`
- wrappers legacy en `agents/routing_*`
- `provider_trace` limpio
- `system_state` mas claro respecto del banco de modelos y del estado runtime observado
- AURA actual sin ruptura de compatibilidad

## Pendiente V1.x

- adelgazar mas `routing_maintenance` y `routing_neuron_registry`
- terminar de extraer mas rendering admin desde `system_state_agent`
- decidir si la ventana liviana necesita snapshot o persistencia ligera
- acumular mas historial `applied` fuera de escenarios controlados
- seguir haciendo mas probable un applied visible en sesiones reales sin meter teatro
- reforzar validacion viva del chat para confirmar que la mejora observable tambien aparece fuera del repo
- seguir acumulando evidencia real para decidir cuando un modelo del banco pasa de laboratorio a candidata inmediata

## Fuera de alcance

- V2
- panel UI
- persistencia pesada
- training real
