# Routing Neuron Roadmap

## Cerrado en V1.7

Queda cerrado hoy:

- subsistema canonico en `backend/app/routing_neuron`
- wrappers legacy razonablemente finos para runtime y observer
- score axes visibles
- runtime limitado y reversible
- `routing_neuron_trace` separado de `provider_trace`
- ventana liviana de `runtime_records`
- `session_summaries` con actividad runtime real
- checkpoint, admin, `system_state` y actividad reciente alineados mejor
- primer sendero `applied` seguro y demostrable
- traza visible desde sesion/log cuando falta historial runtime en memoria
- replay visible mas estable cuando la sesion nueva ya escribio un log propio sin huella RN
- semantica mas clara para weak signal, blocked, baseline-only y applied
- helper canonico para lectura observable y replay fuera de `system_state_agent.py`
- helper canonico de rendering admin/runtime fuera de `system_state_agent.py`
- activacion liviana de candidatas runtime-ready para el sendero `skip_critic`
- primer sendero `applied` visible tambien desde una progresion organica de verificaciones limpias, no solo desde semilla manual
- mejor clasificacion de prompts tecnicos explicativos para no perder actividad util por falsos troubleshooting
- resumenes visibles que priorizan el tramo mas nuevo del historial reciente

## Pendiente en V1.x

Siguiente nivel conservador:

1. seguir adelgazando `agents/routing_neuron_registry.py` y `agents/routing_maintenance.py`
2. mover mas renderers admin fuera de `agents/system_state_agent.py`
3. endurecer la lectura de outcomes recientes sin inflar el schema
4. decidir si la ventana liviana de `runtime_records` necesita snapshot o persistencia ligera
5. acumular mas historial `applied` real para salir de low-sample en mas escenarios
6. revisar si conviene una segunda influencia segura dentro del marco V1.x

## Pendiente para V1.7.x

Solo si sigue siendo conservador:

- breakdown mas fino de blocked por barrera en surfaces cortas
- mejor resumen de mezcla de outcomes recientes
- mejor diferenciacion entre traza visible recuperada y runtime en memoria cuando la sesion actual mezcla logs con y sin RN
- un segundo camino `applied` igualmente reversible y de bajo riesgo
- decidir con mas evidencia si hace falta snapshot ligero o si el replay actual alcanza
- validar mas duro el chat real para acumular `applied` fuera de secuencias tecnicas repetidas

## Fuera de V1.x

No meter todavia:

- V2
- panel UI
- persistencia pesada
- judge hub
- route families
- synthesis proposals
- LoRA real
- distillation
- micro-model propio
- composicion multi-neurona rica

## Relacion con V0.39

`shortlist`, `bridge`, `rehearsal`, `cutover` y `launch_dossier` siguen existiendo.

Regla de lectura:

- son extensiones tacticas utiles
- no identidad central de RN
- no definen la identidad de Routing Neuron V1
- RN V1.7 sigue siendo una capa transversal reusable aunque cambie el stack operativo principal

## Norte observable

La meta de V1.x ya no es solo packaging:

- historial operativo observado mas consistente entre repo y runtime visible
- applied visible en smokes razonables
- surfaces honestas cuando la actividad proviene de la sesion actual o de la ultima sesion registrada
- menos drift entre memoria viva, log actual y ultima sesion util
