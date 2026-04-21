# Routing Neuron Changelog

## 2026-04-02

- Cambio: se consolido Routing Neuron V1.7 como evolucion conservadora de V1.6.
  Motivo: bajar deuda de mantenibilidad y hacer mas visible el comportamiento util de RN en chats tecnicos compatibles, no solo en smokes sembrados.
  Impacto: el backplane observable queda un poco mas ordenado, el sendero `applied` seguro aparece antes tras verificaciones limpias repetidas y la superficie visible sigue mas de cerca al core canonico.
  Compatibilidad o riesgo: riesgo bajo; no mete snapshot ni persistencia pesada y mantiene contratos del runtime.

- Cambio: se extrajeron helpers canonicos de rendering admin hacia `backend/app/routing_neuron/admin/rendering.py`.
  Motivo: `system_state_agent.py` seguia concentrando demasiado wording y formateo compartido de RN.
  Impacto: estado, checkpoint y actividad reciente reutilizan mejor labels canonicos de observabilidad, validacion e historial vivo/replay.
  Compatibilidad o riesgo: riesgo bajo; cambia ubicacion de rendering compartido, no la semantica persistida.

- Cambio: se ajusto la clasificacion tecnica para no mandar a troubleshoot preguntas explicativas sobre auth/oauth/rollback si no hay marcadores reales de falla.
  Motivo: varios prompts tecnicos normales quedaban fuera del sendero seguro `skip_critic` por una heuristica demasiado agresiva.
  Impacto: preguntas explicativas repetidas y verificadas pueden llegar antes a weak signal y `applied` honesto sin relajar seguridad en casos con error/falla real.
  Compatibilidad o riesgo: riesgo bajo; los casos con `401`, errores, fallas o rollback roto siguen yendo por troubleshooting.

- Cambio: se corrigio el rendering de runtime reciente para priorizar el tramo mas nuevo tambien en resumenes largos.
  Motivo: `muestra actividad reciente` ya miraba lo ultimo, pero `state` y checkpoint todavia podian arrastrar primero rutas/outcomes mas viejos.
  Impacto: `recent_paths`, `recent_outcomes` y `recent_applied_influences` reflejan mejor el ultimo `selected_and_applied` cuando acaba de ocurrir.
  Compatibilidad o riesgo: riesgo bajo; cambia presentation order, no el historial canonico.

- Cambio: se consolidó Routing Neuron V1.6 como evolución conservadora de V1.5.
  Motivo: bajar deuda de mantenibilidad y hacer más visible el primer sendero `applied` fuera de escenarios sembrados a mano.
  Impacto: parte de la lectura observable ahora vive en `backend/app/routing_neuron/admin/observable.py` y las surfaces visibles siguen más de cerca al core canónico.
  Compatibilidad o riesgo: riesgo bajo; no mete persistencia pesada ni cambia contratos públicos del runtime.

- Cambio: se agregó una semilla observacional segura para `skip_critic`.
  Motivo: V1.5 podía demostrar `applied`, pero seguía dependiendo demasiado de candidatas activadas manualmente en tests o smokes controlados.
  Impacto: verificaciones limpias repetidas en tareas técnicas pueden preparar una candidata `prefer_primary_only_when_verified`, activarla de forma liviana y habilitar un `selected_and_applied` honesto en una sesión real compatible.
  Compatibilidad o riesgo: riesgo bajo; la heurística queda acotada a contextos técnicos, repetidos, verificados y sin fallbacks recientes.

- Cambio: se ajustó la barrera de estabilidad para el sendero verificado `skip_critic`.
  Motivo: la señal nueva nacía de forma legítima pero no cruzaba el score general pensado para rutas más maduras.
  Impacto: RN puede aplicar antes en ese sendero puntual sin relajar el resto de barreras de budget, context, composition o fallback.
  Compatibilidad o riesgo: riesgo bajo; es una excepción específica y auditable, no una relajación global.

- Cambio: se corrigió la actividad reciente para priorizar el tramo más nuevo de la ventana.
  Motivo: la surface podía ocultar el último `applied` si mostraba solo el inicio de la ventana reciente.
  Impacto: `muestra actividad reciente de routing neuron` refleja mejor el evento más nuevo, incluyendo `selected_and_applied` cuando acaba de ocurrir.
  Compatibilidad o riesgo: riesgo bajo; cambia el rendering, no el historial canónico.

## 2026-04-01

- Cambio: se consolido Routing Neuron V1.5 como evolucion conservadora de V1.4.
  Motivo: cerrar el drift residual entre memoria viva, replay desde logs y superficie observable.
  Impacto: la lectura visible ahora sigue buscando la ultima sesion util aunque el log actual ya exista pero todavia no tenga huella RN.
  Compatibilidad o riesgo: riesgo bajo; no agrega persistencia pesada ni toca la semantica canonica del runtime.

- Cambio: se volvio mas explicita la diferencia entre historial runtime en memoria y traza visible recuperada.
  Motivo: evitar salidas donde unas sesiones hablaban de replay y otras volvían a "sin historial" por detalles del log actual.
  Impacto: `system_state`, checkpoint y actividad reciente describen mejor si la lectura viene de memoria viva, de la sesion actual o de la ultima sesion registrada.
  Compatibilidad o riesgo: riesgo bajo; cambia rendering y wording, no contratos de core.

- Cambio: se mejoro el naming visible de `decision_path` en surfaces cortas.
  Motivo: los nombres canonicos son utiles para precision, pero solos se leen toscos en sesiones visibles.
  Impacto: rutas como `no_candidate_match`, `selected_not_applied` y `selected_and_applied` ahora se muestran con texto mas legible sin perder el identificador canonico.
  Compatibilidad o riesgo: riesgo bajo; no cambia los valores persistidos.

- Cambio: se extendio la bateria de pruebas hacia replay entre sesiones y applied visible en smoke real.
  Motivo: V1.5 necesitaba demostrar que el cierre de brecha observable no era solo documental.
  Impacto: hay smokes que cubren replay tras escribir un log no-RN y secuencias reales con `skip_critic` visible.
  Compatibilidad o riesgo: sin riesgo funcional.

- Cambio: se consolido Routing Neuron V1.4 como evolucion conservadora de V1.3.
  Motivo: cerrar la brecha entre runtime canonico, tests y superficie observable de AURA.
  Impacto: `system_state`, checkpoint y actividad reciente ahora pueden reutilizar metadatos y logs de sesion cuando el runtime en memoria esta vacio.
  Compatibilidad o riesgo: riesgo bajo; no agrega persistencia pesada ni altera el runtime canonico.

- Cambio: se mantuvo el primer sendero `applied` seguro y se lo aterrizo mejor en smokes reales de AURA.
  Motivo: V1.4 debia verse viva no solo en tests unitarios.
  Impacto: `skip_critic` queda visible en una secuencia real de turnos y sigue separado de `provider_trace`.
  Compatibilidad o riesgo: riesgo bajo; usa una intervencion ya existente y solo mejora su exposicion observable.

- Cambio: se reforzo la lectura humana del caso `considered=true` con `considered_ids=[]`.
  Motivo: evitar ambiguedad silenciosa en sesiones degradadas o sin candidatas.
  Impacto: la salida visible ahora puede explicar "considerada globalmente sin candidata coincidente" usando `decision_path=no_candidate_match`.
  Compatibilidad o riesgo: riesgo bajo; semantica compatible con V1.3.

- Cambio: se alineo mejor el tracking de blueprint, checkpoint, roadmap y doc legacy con el estado post-pulido.
  Motivo: el repo ya habia avanzado mas rapido que algunas superficies y textos.
  Impacto: V1.4 queda documentada como consolidacion operativa visible dentro de V1.x, sin mezclar V2.
  Compatibilidad o riesgo: sin riesgo funcional.

## 2026-03-31

- Cambio: se consolido Routing Neuron V1.3 como evolucion conservadora de V1.2.
  Motivo: pasar de observabilidad util pero ambigua a una lectura mas nitida entre observar, seleccionar, bloquear y aplicar.
  Impacto: el runtime mantiene compatibilidad, pero ahora expone `decision_path` para distinguir `no_candidate_match`, `candidate_seen_no_active_match`, `selected_not_applied`, `selected_blocked`, `selected_and_applied` y variantes pausadas/cooldown.
  Compatibilidad o riesgo: riesgo bajo; no rompe contratos previos y solo agrega semantica explicita.

- Cambio: se formalizo el primer sendero `applied` seguro de V1.x.
  Motivo: V1.3 debia demostrar una influencia real, reversible y auditable.
  Impacto: `skip_critic` queda reconocido como camino `applied` valido y se muestra mejor en runtime, admin, checkpoint y estado.
  Compatibilidad o riesgo: riesgo bajo; usa una intervencion ya existente y la vuelve mas visible, sin contaminar `provider_trace`.

- Cambio: se alineo `system_state`, `checkpoint routing neuron` y `muestra actividad reciente de routing neuron`.
  Motivo: evitar que una vista diga "sin historial real" mientras otra ya muestra senal debil o actividad aplicada.
  Impacto: las tres superficies ahora comparten mejor la lectura de ventana reciente, senal debil, baseline-only, bloqueos, degraded y actividad aplicada.
  Compatibilidad o riesgo: riesgo bajo; cambia wording y agregados, no el runtime principal.
