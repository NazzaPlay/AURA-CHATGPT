import re
from dataclasses import dataclass
from typing import Any

from .capabilities_agent import (
    analyze_capabilities_query,
    build_capabilities_response,
)
from .internal_commands_agent import analyze_internal_command
from .internal_tools_agent import analyze_internal_tools_query
from .maintenance_agent import analyze_maintenance_command
from .memory_agent import analyze_memory_question, extract_memory_update
from .feasibility_agent import (
    build_direct_feasibility_response,
    looks_like_feasibility_statement,
)
from .profile_agent import (
    UserProfile,
    build_profile_planning_hints,
    build_profile_prompt_context,
    build_profile_style_hints,
    build_user_profile,
)
from .system_state_agent import analyze_system_state_command
from .text_matching import normalize_command_variants, normalize_internal_text
from .operations_agent import analyze_internal_operations_query


INTENT_CAPABILITY = "capabilities_command"
INTENT_CAPABILITIES_COMMAND = INTENT_CAPABILITY
INTENT_OPERATIONS_COMMAND = "operations_command"
INTENT_TOOLS_COMMAND = "tools_command"
INTENT_MEMORY_QUERY = "memory_query"
INTENT_MEMORY_COMMAND = "memory_command"
INTENT_SYSTEM_COMMAND = "system_command"
INTENT_MAINTENANCE_COMMAND = "maintenance_command"
INTENT_FEASIBILITY = "feasibility_evaluation"
INTENT_CONSISTENCY = "consistency_evaluation"
INTENT_TECHNICAL_TROUBLESHOOT = "technical_troubleshoot"
INTENT_TECHNICAL_EXPLAIN = "technical_explain"
INTENT_OPEN = "open"
INTENT_GENERAL = "general"

OPEN_QUESTION_PATTERN = re.compile(
    r"^\s*(que|como|por\s+que|cual|cuales|cuando|donde|quien)\b"
)
TECHNICAL_KEYWORDS = {
    "401",
    "403",
    "404",
    "500",
    "api",
    "arquitectura",
    "auth",
    "autenticacion",
    "autorizacion",
    "archivo",
    "bash",
    "backend",
    "bug",
    "cache",
    "cli",
    "codigo",
    "comando",
    "cola",
    "colas",
    "config",
    "concurrencia",
    "debug",
    "depurar",
    "docker",
    "error",
    "exception",
    "funcion",
    "git",
    "integracion",
    "integraciones",
    "instalar",
    "idempotencia",
    "idempotente",
    "json",
    "latencia",
    "libreria",
    "linux",
    "llama",
    "modelo",
    "modulo",
    "microservicio",
    "microservicios",
    "observabilidad",
    "paquete",
    "pip",
    "programa",
    "programacion",
    "prompt",
    "p95",
    "p99",
    "python",
    "regex",
    "rollback",
    "router",
    "ruta",
    "script",
    "servicio",
    "servicios",
    "stateful",
    "estado",
    "estados",
    "stateless",
    "terminal",
    "trafico",
    "token",
    "traceback",
    "oauth",
    "oauth2",
    "jwt",
}
TECHNICAL_TROUBLESHOOT_HINTS = {
    "401",
    "403",
    "404",
    "500",
    "arreglo",
    "arreglar",
    "auth",
    "configuro",
    "configurar",
    "crash",
    "crashea",
    "debug",
    "depurar",
    "devuelve",
    "error",
    "falla",
    "fallando",
    "fix",
    "instalar",
    "lanza",
    "no funciona",
    "problema",
    "rompe",
    "rompio",
    "rompió",
    "sale",
    "solucion",
    "solucionar",
    "tirando",
    "traceback",
    "rollback",
    "unauthorized",
    "forbidden",
}
TECHNICAL_FAILURE_HINTS = {
    "401",
    "403",
    "404",
    "500",
    "arreglo",
    "arreglar",
    "crash",
    "crashea",
    "debug",
    "depurar",
    "devuelve",
    "error",
    "exception",
    "falla",
    "fallando",
    "fix",
    "forbidden",
    "lanza",
    "no funciona",
    "problema",
    "rompe",
    "rompio",
    "rompió",
    "sale",
    "solucion",
    "solucionar",
    "tirando",
    "traceback",
    "unauthorized",
}
TECHNICAL_EXPLAIN_HINTS = {
    "como funciona",
    "diferencia",
    "explica",
    "para que sirve",
    "que es",
    "que significa",
}
EXTENDED_TECHNICAL_EXPLAIN_HINTS = TECHNICAL_EXPLAIN_HINTS | {
    "explicame",
    "explicar",
    "tradeoff",
    "tradeoffs",
    "balance",
    "balancearias",
    "equilibrar",
    "equilibrarias",
}
SPECIFIC_TROUBLESHOOT_HINTS = {
    "401",
    "403",
    "404",
    "500",
    "attributeerror",
    "archivo",
    "codigo",
    "importerror",
    "line ",
    "linea",
    "modulo",
    "nameerror",
    "syntaxerror",
    "traceback",
    "typeerror",
    "valueerror",
}
MINIMAL_GREETING_COMMANDS = normalize_command_variants(
    {
        "hola",
        "buen dia",
        "buenas",
        "que tal",
    }
)
MINIMAL_GRATITUDE_COMMANDS = normalize_command_variants(
    {
        "gracias",
        "muchas gracias",
    }
)


@dataclass(frozen=True)
class BehaviorPlan:
    intent: str
    direct_response: str | None = None
    style_instructions: str = ""
    planning_instructions: str = ""
    profile_context: str = ""


def _normalize_text(text: str) -> str:
    return normalize_internal_text(text)


def _contains_any(text: str, options: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(option in text for option in options)


def _pick_variant(seed_text: str, variants: list[str]) -> str:
    if not variants:
        return ""

    index = sum(ord(char) for char in seed_text) % len(variants)
    return variants[index]


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _build_memory_facts(user_input: str, memory: dict[str, Any]) -> list[str]:
    memory_update = extract_memory_update(user_input)
    facts = []

    if "name" in memory_update and memory.get("name"):
        facts.append(f"Te llamas {memory['name']}.")

    if "work" in memory_update and memory.get("work"):
        facts.append(f"Trabajas {memory['work']}.")

    if "interests" in memory_update:
        facts.append(f"Te gusta {_format_items(memory_update['interests'])}.")

    if "preferences" in memory_update:
        facts.append(f"Prefieres {_format_items(memory_update['preferences'])}.")

    return facts


def build_memory_update_response(user_input: str, memory: dict[str, Any]) -> str:
    facts = _build_memory_facts(user_input, memory)
    if not facts:
        return "Anotado."

    intro = _pick_variant(
        user_input,
        [
            "Anotado.",
            "Listo, lo guardé.",
            "Perfecto, queda registrado.",
        ],
    )

    return f"{intro} {' '.join(facts)}"


def build_repetition_response(user_input: str, memory: dict[str, Any]) -> str:
    facts = _build_memory_facts(user_input, memory)
    if not facts:
        return "Eso ya lo tenía guardado."

    intro = _pick_variant(
        user_input,
        [
            "Eso ya lo tenía guardado.",
            "Sí, eso ya me había quedado anotado.",
            "Sí, eso sigue guardado.",
        ],
    )

    return f"{intro} {' '.join(facts)}"


def _build_capability_response() -> str:
    return build_capabilities_response()


def _build_generic_troubleshoot_response(
    user_input: str,
    profile: UserProfile | None = None,
) -> str | None:
    normalized_input = _normalize_text(user_input)

    if "python" not in normalized_input and "error" not in normalized_input:
        return None

    if any(hint in normalized_input for hint in SPECIFIC_TROUBLESHOOT_HINTS):
        return None

    if len(normalized_input.split()) > 10:
        return None

    response = (
        "Idea breve: me falta el error exacto para decirte la causa. "
        "Explicación: la última línea del traceback suele mostrar qué falló, en qué archivo y en qué línea. "
        "Qué hacer: 1. copia esa última línea, 2. ubica el archivo y la línea, "
        "3. revisa nombres, indentación e imports, 4. vuelve a ejecutar. "
        "Cómo verificar: el script debe correr sin traceback. "
        "Si me pegas el mensaje exacto, te digo la causa probable."
    )

    if profile and (profile.prefers_practical or profile.works_in_workshop):
        response += " Ve una variable por vez para aislar la falla más rápido."

    return response


def build_stable_technical_explain_response(
    user_input: str,
    profile: UserProfile | None = None,
) -> str | None:
    normalized_input = _normalize_text(user_input)
    asks_for_explanation = _contains_any(
        normalized_input,
        EXTENDED_TECHNICAL_EXPLAIN_HINTS,
    ) or normalized_input.startswith("como ")

    if (
        "api" in normalized_input
        and "auth" in normalized_input
        and "rollback" in normalized_input
        and ("produccion" in normalized_input or "production" in normalized_input)
        and not _contains_any(
            normalized_input,
            {
                "riesgo",
                "riesgos",
                "scope",
                "scopes",
                "redirect",
                "refresh",
                "latencia",
                "concurrencia",
                "migracion",
                "migraciones",
                "cola",
                "colas",
            },
        )
    ):
        response = (
            "Una API con auth y rollback en produccion necesita tres piezas: autenticacion "
            "estable, operaciones trazables y un plan de reversion probado. Usa tokens o "
            "sesiones bien delimitadas, deja los cambios criticos como idempotentes o "
            "transaccionales, y separa rollback de base de datos, colas y efectos externos "
            "con compensaciones claras. Antes de desplegar, valida auth, expiracion, auditoria "
            "y rollback en un entorno igual al real."
        )
        if profile and (profile.prefers_practical or profile.works_in_workshop):
            response += (
                " El punto fino es no prometer rollback total si hay efectos externos "
                "sin compensacion."
            )
        return response

    if "api" in normalized_input and "rest" in normalized_input:
        response = (
            "Una API REST expone recursos por HTTP usando rutas y metodos como GET, POST, "
            "PUT y DELETE. Suele ser stateless: cada request lleva su contexto y la respuesta "
            "normalmente viaja en JSON. Ejemplo: `GET /users` lista recursos y `POST /users` crea uno."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += " Si la estas disenando, define bien recursos, codigos HTTP e idempotencia."
        return response

    if "jwt" in normalized_input or "json web token" in normalized_input:
        response = (
            "JWT es un token firmado que suele llevar claims como identidad, expiracion y roles. "
            "Sirve para transportar contexto verificable entre servicios sin guardar sesion en el "
            "server. Ojo: un JWT firmado no cifra por si solo; si lleva datos sensibles, no deberia "
            "exponerlos en claro."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += " En practica, revisa firma, expiracion corta y rotacion de claves."
        return response

    if (
        "oauth2" in normalized_input
        or "oauth 2" in normalized_input
        or "oauth" in normalized_input
    ):
        response = (
            "OAuth2 sirve para delegar autorizacion: una app obtiene permisos limitados para "
            "actuar sobre recursos de un usuario sin manejar su password. Lo normal es trabajar "
            "con access token, scopes y expiracion. Si quieres login de identidad, suele "
            "complementarse con OpenID Connect."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += (
                " Si lo implementas, define bien redirect URI, scopes y renovacion de tokens."
            )
        return response

    if (
        ("auth" in normalized_input or "autenticacion" in normalized_input)
        and "autorizacion" in normalized_input
        and _contains_any(
            normalized_input,
            {"diferencia", "diferencias", "vs", "versus", "compar"},
        )
    ):
        response = (
            "Autenticacion responde quien eres; autorizacion responde que puedes hacer. "
            "Primero verificas identidad con password, token o SSO, y despues aplicas roles, "
            "permisos o scopes sobre recursos concretos."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += (
                " En una API, auth suele terminar en un token valido y autorizacion en "
                "checks por rol o scope."
            )
        return response

    if "idempotencia" in normalized_input or "idempotente" in normalized_input:
        response = (
            "Idempotencia significa que repetir la misma operacion produce el mismo efecto final "
            "que ejecutarla una sola vez. Es clave en APIs y colas para tolerar reintentos sin "
            "duplicar cobros, ordenes o cambios de estado."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += (
                " Ejemplo: repetir `PUT /users/42` con el mismo payload no deberia crear "
                "dos usuarios."
            )
        return response

    if "rollback" in normalized_input and (
        "produccion" in normalized_input or "production" in normalized_input
    ) and not _contains_any(
        normalized_input,
        {
            "api",
            "auth",
            "oauth",
            "jwt",
            "scope",
            "scopes",
            "riesgo",
            "riesgos",
            "redirect",
            "refresh",
        },
    ):
        response = (
            "Rollback en produccion es volver rapido a una version estable cuando un deploy rompe "
            "comportamiento, rendimiento o datos. Lo sano es tener una version previa lista, "
            "migraciones reversibles o compensables, y checks claros para decidir revertir sin "
            "improvisar."
        )
        if profile and (profile.prefers_practical or profile.works_in_workshop):
            response += (
                " El riesgo real suele estar en base de datos, colas y efectos externos "
                "que no revierten solos."
            )
        return response

    if "api" in normalized_input and "stateless" in normalized_input:
        response = (
            "Una API stateless no guarda estado de sesion del cliente entre requests. Cada llamada "
            "debe traer todo lo necesario para procesarse, por ejemplo token, parametros y contexto. "
            "Eso simplifica escalado y balanceo, porque cualquier instancia puede atender la request."
        )
        if profile and (profile.prefers_practical or profile.prefers_clear):
            response += (
                " Si necesitas estado, suele quedar en el cliente, cache compartida o base externa."
            )
        return response

    if (
        asks_for_explanation
        and "api" in normalized_input
        and _contains_any(normalized_input, {"versionado", "version", "compatibilidad", "backward"})
        and _contains_any(normalized_input, {"rollout", "despliegue", "release", "canary", "canario"})
    ):
        response = (
            "En una API con clientes externos, versionado, compatibilidad y rollout se ordenan por contrato. "
            "Primero evita cambios breaking en caliente: agrega campos y rutas nuevas antes de quitar viejas, marca deprecaciones y define ventana de convivencia. "
            "Despues usa rollout gradual, canary o feature flags para medir errores y clientes afectados antes del corte total. "
            "Si no puedes mantener compatibilidad, versiona de forma explicita y comunica fecha, alcance y plan de retiro."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"multi tenant", "multitenant", "tenant", "tenants"})
        and _contains_any(normalized_input, {"observabilidad", "limite", "limites", "quota", "rate limit", "cliente"})
        and _contains_any(normalized_input, {"backend", "api", "servicio", "servicios"})
    ):
        response = (
            "En un backend multi-tenant, lo primero es aislar contexto por tenant en auth, datos y observabilidad. "
            "Cada request deberia cargar tenant_id verificable, aplicar limites por cliente o plan, y medir errores, latencia y consumo por tenant para detectar abuso o vecinos ruidosos. "
            "Lo sano es combinar cuotas, rate limits, particion logica de datos y dashboards por tenant antes de optimizar throughput global."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"monolito", "monolitico", "monolitica", "migrar", "migrarias", "strangler"})
        and _contains_any(normalized_input, {"servicio", "servicios", "microservicio", "microservicios"})
        and _contains_any(normalized_input, {"auth", "autenticacion", "contrato", "contratos"})
    ):
        response = (
            "Para migrar un monolito a servicios sin romper auth ni contratos, conviene cortar primero por limites de negocio y no por capas tecnicas. "
            "Mantén auth y autorizacion coherentes en un borde comun, saca un primer servicio detras del mismo contrato externo o con un adapter, y mueve trafico de forma gradual con estrategia tipo strangler. "
            "Si cambias contratos, hazlo por version o compatibilidad progresiva; si cambias auth, prueba claims, scopes y auditoria antes de repartir la logica."
        )
        return response

    if (
        asks_for_explanation
        and "api" in normalized_input
        and _contains_any(
            normalized_input,
            {"backend", "servicio", "servicios", "arquitectura", "integracion", "integraciones"},
        )
    ):
        response = (
            "En backend, una API conviene verla como contrato de entrada y salida entre clientes y servicios. "
            "La parte sana es separar contrato HTTP, logica de dominio y adaptadores a base de datos o integraciones. "
            "Asi puedes cambiar internals sin romper clientes, y controlar auth, validacion, idempotencia y errores en un borde claro."
        )
        if "rollback" in normalized_input:
            response += " Si ademas hay cambios criticos, define rollback y compensaciones antes del deploy."
        return response

    if asks_for_explanation and _contains_any(
        normalized_input,
        {"arquitectura", "backend", "servicio", "servicios", "microservicio", "microservicios"},
    ) and not _contains_any(
        normalized_input,
        {"estado", "estados", "state", "stateful"},
    ):
        response = (
            "En arquitectura backend, un servicio sano tiene una responsabilidad clara, contratos estables "
            "y dependencias explicitas. Lo util suele ser separar API, dominio, persistencia e integraciones, "
            "y dejar observabilidad, timeouts y reintentos como preocupaciones de plataforma, no mezcladas con la logica de negocio."
        )
        if profile and (profile.prefers_practical or profile.works_in_workshop):
            response += " Si el sistema crece, primero corta por limites de negocio antes que por moda de microservicios."
        return response

    if (
        asks_for_explanation
        and "api" in normalized_input
        and _contains_any(normalized_input, {"cache", "cola", "colas"})
        and _contains_any(normalized_input, {"auth", "autenticacion", "autorizacion"})
        and _contains_any(
            normalized_input,
            {"trafico", "alto trafico", "mucho trafico", "picos", "concurrencia", "throughput"},
        )
    ):
        response = (
            "En una API con mucho trafico, auth, cache y colas cumplen trabajos distintos. "
            "Auth debe quedarse en el camino sincrono minimo y cachear solo artefactos seguros, "
            "como claves, metadata o permisos derivables; la cache sirve para bajar lectura y latencia, "
            "mientras las colas absorben trabajo asincrono, reintentos y efectos no criticos fuera del request. "
            "La regla sana es no mandar autenticacion ni cambios de estado criticos a la cola, "
            "mantener idempotencia en consumidores, y usar backpressure, TTL e invalidacion clara para no mezclar rendimiento con perdida de control."
        )
        if profile and (profile.prefers_practical or profile.works_in_workshop):
            response += " Si algo falla, primero protege auth y consistencia, y despues optimiza cache y throughput."
        return response

    if asks_for_explanation and _contains_any(
        normalized_input,
        {"integracion", "integraciones", "externa", "externas", "webhook", "cola", "colas"},
    ):
        response = (
            "Una integracion backend confiable trata al sistema externo como frontera inestable: valida entradas, "
            "usa timeouts, reintentos controlados y trazabilidad, y evita acoplar toda la transaccion local al estado remoto. "
            "Si el efecto externo no es reversible, conviene usar compensaciones e idempotencia en vez de prometer rollback total."
        )
        return response

    if asks_for_explanation and _contains_any(
        normalized_input,
        {"observabilidad", "tracing", "trace", "metricas", "metrics", "logs", "logging"},
    ) and _contains_any(
        normalized_input,
        {"api", "backend", "servicio", "servicios", "integracion", "integraciones"},
    ):
        response = (
            "Observabilidad util en backend significa poder seguir una request completa y explicar por que fue lenta, fallo o se desvio. "
            "Lo minimo sano es logs estructurados con request id, metricas de error y latencia p95/p99, trazas entre servicios e integraciones, "
            "y alertas sobre timeouts, retries y colas acumuladas. Sin eso, auth, cache o integraciones pueden fallar bien en superficie y mal en produccion."
        )
        return response

    if asks_for_explanation and _contains_any(
        normalized_input,
        {"estado", "estados", "state", "stateful"},
    ):
        response = (
            "En backend, manejar estado significa definir transiciones validas y quien puede cambiarlas. "
            "Lo estable es modelar estados explicitos, reglas de transicion y efectos colaterales separados, "
            "para que reintentos, auditoria y rollback no dependan de suposiciones ocultas."
        )
        if "api" in normalized_input:
            response += " En una API eso suele verse en codigos HTTP claros y cambios de estado idempotentes cuando aplica."
        return response

    if (
        asks_for_explanation
        and "cache" in normalized_input
        and "write through" in normalized_input
        and "write back" in normalized_input
    ):
        response = (
            "Write-through escribe primero en cache y almacenamiento final, asi que da consistencia simple pero mas latencia por operacion. "
            "Write-back confirma rapido en cache y difiere la persistencia, lo que mejora rendimiento pero agrega riesgo si cae el proceso o falla la sincronizacion. "
            "En una API con auth conviene usar write-through para datos criticos y write-back solo donde toleras cola, replay e invalidez controlada."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"latencia", "p95", "p99", "percentil", "percentiles"})
        and "api" in normalized_input
    ):
        response = (
            "P95 y P99 no miden lo mismo que el promedio: muestran la cola lenta de tu API. "
            "P95 te dice como rinde casi todo el trafico, mientras P99 revela los peores casos que suelen venir de locks, cache miss, colas o dependencias externas. "
            "Si P95 esta bien pero P99 explota, la experiencia general puede parecer correcta y aun asi fallar justo en picos o rutas pesadas."
        )
        return response

    if (
        asks_for_explanation
        and "api" in normalized_input
        and _contains_any(normalized_input, {"versionado", "version", "compatibilidad", "backward"})
        and _contains_any(normalized_input, {"rollout", "despliegue", "release", "canary", "canario"})
    ):
        response = (
            "En una API con clientes externos, versionado, compatibilidad y rollout se ordenan por contrato. "
            "Primero evita cambios breaking en caliente: agrega campos y rutas nuevas antes de quitar viejas, marca deprecaciones y define ventana de convivencia. "
            "Despues usa rollout gradual, canary o feature flags para medir errores y clientes afectados antes del corte total. "
            "Si no puedes mantener compatibilidad, versiona de forma explicita y comunica fecha, alcance y plan de retiro."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"multi tenant", "multitenant", "tenant", "tenants"})
        and _contains_any(normalized_input, {"observabilidad", "limite", "limites", "quota", "rate limit", "cliente"})
        and _contains_any(normalized_input, {"backend", "api", "servicio", "servicios"})
    ):
        response = (
            "En un backend multi-tenant, lo primero es aislar contexto por tenant en auth, datos y observabilidad. "
            "Cada request deberia cargar tenant_id verificable, aplicar limites por cliente o plan, y medir errores, latencia y consumo por tenant para detectar abuso o vecinos ruidosos. "
            "Lo sano es combinar cuotas, rate limits, particion logica de datos y dashboards por tenant antes de optimizar throughput global."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"monolito", "monolitico", "monolitica", "migrar", "migrarias", "strangler"})
        and _contains_any(normalized_input, {"servicio", "servicios", "microservicio", "microservicios"})
        and _contains_any(normalized_input, {"auth", "autenticacion", "contrato", "contratos"})
    ):
        response = (
            "Para migrar un monolito a servicios sin romper auth ni contratos, conviene cortar primero por limites de negocio y no por capas tecnicas. "
            "Mantén auth y autorizacion coherentes en un borde comun, saca un primer servicio detras del mismo contrato externo o con un adapter, y mueve trafico de forma gradual con estrategia tipo strangler. "
            "Si cambias contratos, hazlo por version o compatibilidad progresiva; si cambias auth, prueba claims, scopes y auditoria antes de repartir la logica."
        )
        return response

    if (
        asks_for_explanation
        and _contains_any(normalized_input, {"balance", "balancearias", "equilibrar", "tradeoff", "tradeoffs"})
        and _contains_any(normalized_input, {"api", "backend", "servicio", "servicios"})
        and _contains_any(
            normalized_input,
            {"cache", "cola", "colas", "auth", "autenticacion", "latencia", "integracion", "observabilidad"},
        )
    ):
        response = (
            "En backend, balancear tradeoffs no es repartir todo parejo sino proteger primero el camino critico. "
            "Deja auth, validacion y cambios de estado sensibles en el request sincrono; usa cache para lecturas o contexto derivable; "
            "mueve a cola lo que tolera retraso o compensacion; y apoya la decision con observabilidad, timeouts e idempotencia. "
            "Si mezclas esos limites, ganas throughput a costa de perder trazabilidad o control operativo."
        )
        return response

    if "router" in normalized_input and "python" in normalized_input:
        response = (
            "Idea breve: en Python, un router suele ser la pieza que decide qué función o handler "
            "se ejecuta según la ruta o el tipo de petición. "
            "Explicación: es común en frameworks web como FastAPI o Flask, donde una URL como "
            "`/users` se deriva al código correcto. "
            "Ejemplo: una petición `GET /users` puede terminar en una función como `get_users()`."
        )
        if profile and (profile.prefers_practical or profile.works_in_workshop):
            response += (
                " En la práctica, piensa en el router como la pieza que manda cada pedido "
                "al lugar correcto sin mezclar tareas."
            )
        return response

    if "prompt" in normalized_input:
        response = (
            "Idea breve: un prompt es la instrucción o contexto que se le pasa al modelo. "
            "Explicación: incluye lo que quieres pedir, restricciones de estilo y, a veces, "
            "contexto previo para guiar la respuesta. "
            "Ejemplo: si le das un prompt más claro y específico, la respuesta suele salir más útil y estable."
        )
        if profile and (profile.prefers_clear or profile.prefers_practical):
            response += (
                " En lo práctico, cuanto mejor defines qué quieres y en qué formato, "
                "más útil suele salir la respuesta."
            )
        return response

    return None


def _build_direct_technical_explain_response(
    user_input: str,
    profile: UserProfile | None = None,
) -> str | None:
    return build_stable_technical_explain_response(user_input, profile)


def _recent_user_messages(
    conversation: list[dict[str, str]] | None,
    limit: int = 4,
) -> list[str]:
    conversation = conversation or []
    messages = [
        str(message.get("content", "")).strip()
        for message in conversation
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    return messages[-limit:]


def _build_direct_contextual_requirement_response(
    user_input: str,
    conversation: list[dict[str, str]] | None = None,
) -> str | None:
    normalized_input = _normalize_text(user_input)
    recent_messages = [_normalize_text(message) for message in _recent_user_messages(conversation)]

    offline_markers = (
        "quiero que todo sea offline",
        "quiero que sea offline",
        "quiero que todo siga offline",
        "quiero que todo sea local",
        "quiero que sea local",
    )
    live_markers = (
        "quiero que siempre sepa lo ultimo de internet",
        "quiero que siempre sepa lo ultimo que paso en internet",
        "quiero que siempre este al dia con internet",
        "quiero que sepa siempre lo ultimo de internet",
    )
    low_resource_markers = (
        "quiero cero recursos",
        "quiero que use cero recursos",
        "sin hardware potente",
        "quiero que sea gratis y local",
    )
    high_resource_markers = (
        "quiero calidad de servidor grande",
        "quiero que piense como un servidor enorme",
        "quiero varios modelos grandes activos",
        "quiero 7 modelos grandes",
    )

    has_recent_offline = any(_contains_any(message, offline_markers) for message in recent_messages)
    has_recent_live = any(_contains_any(message, live_markers) for message in recent_messages)
    has_recent_low_resource = any(
        _contains_any(message, low_resource_markers) for message in recent_messages
    )
    has_recent_high_resource = any(
        _contains_any(message, high_resource_markers) for message in recent_messages
    )

    if _contains_any(normalized_input, offline_markers):
        response = (
            "Tiene sentido si quieres priorizar un modo offline, autonomía local o privacidad."
        )
        if has_recent_live:
            response += (
                " Si además quieres que esté siempre al día con internet, ahí aparece una tensión real."
            )
        else:
            response += " El costo es aceptar que no estaría siempre al día con internet."
        return response

    if _contains_any(normalized_input, live_markers):
        response = "Eso pide alguna capa online o una sincronización periódica."
        if has_recent_offline:
            response += " Si además quieres mantenerlo totalmente offline, ahí sí aparece una tensión clara."
        else:
            response += " Por sí solo tiene sentido, pero ya no sería un planteo completamente offline."
        return response

    if _contains_any(normalized_input, low_resource_markers):
        response = "Entiendo la dirección: minimizar recursos es razonable si quieres algo más liviano."
        if has_recent_high_resource:
            response += " Si además quieres una exigencia de cómputo alta, conviene decidir qué restricción pesa más."
        return response

    if _contains_any(normalized_input, high_resource_markers):
        response = "Eso apunta a más capacidad real de cómputo, no a una versión especialmente liviana."
        if has_recent_low_resource:
            response += " Si además quieres casi cero recursos, ahí ya aparece una tensión práctica."
        return response

    return None


def _build_minimal_conversational_response(user_input: str) -> str | None:
    normalized_input = _normalize_text(user_input)

    if normalized_input in MINIMAL_GREETING_COMMANDS:
        if normalized_input == "buen dia":
            return "Buen dia."
        if normalized_input == "que tal":
            return "Todo bien."
        return "Hola."

    if normalized_input in MINIMAL_GRATITUDE_COMMANDS:
        return "De nada."

    return None


def _classify_technical_intent(normalized_input: str) -> str | None:
    has_technical_keyword = any(keyword in normalized_input for keyword in TECHNICAL_KEYWORDS)
    if not has_technical_keyword:
        return None

    has_troubleshoot_hint = any(
        hint in normalized_input for hint in TECHNICAL_TROUBLESHOOT_HINTS
    )
    has_specific_hint = any(
        hint in normalized_input for hint in SPECIFIC_TROUBLESHOOT_HINTS
    )
    asks_for_explanation = any(
        hint in normalized_input for hint in EXTENDED_TECHNICAL_EXPLAIN_HINTS
    ) or normalized_input.startswith("como ")
    compares_technical_concepts = any(
        marker in normalized_input
        for marker in (" vs ", " versus ", "diferencia", "diferencias", "compar")
    )
    has_failure_hint = any(
        hint in normalized_input for hint in TECHNICAL_FAILURE_HINTS
    )

    if asks_for_explanation and _contains_any(
        normalized_input,
        {
            "migrar",
            "migrarias",
            "monolito",
            "monolitico",
            "monolitica",
            "versionado",
            "compatibilidad",
            "rollout",
            "multi tenant",
            "multitenant",
            "tenant",
        },
    ) and not has_specific_hint:
        return INTENT_TECHNICAL_EXPLAIN

    # Keep explanatory prompts about auth/oauth/rollback on the explain path
    # unless the user is also describing a concrete failure surface.
    if asks_for_explanation and not has_specific_hint and not has_failure_hint:
        return INTENT_TECHNICAL_EXPLAIN

    if compares_technical_concepts and not has_specific_hint and not has_failure_hint:
        return INTENT_TECHNICAL_EXPLAIN

    if has_troubleshoot_hint or has_specific_hint:
        return INTENT_TECHNICAL_TROUBLESHOOT

    if asks_for_explanation:
        return INTENT_TECHNICAL_EXPLAIN

    return INTENT_TECHNICAL_EXPLAIN


def classify_user_intent(user_input: str) -> str:
    normalized_input = _normalize_text(user_input)

    if analyze_maintenance_command(user_input):
        return INTENT_MAINTENANCE_COMMAND

    if analyze_system_state_command(user_input):
        return INTENT_SYSTEM_COMMAND

    if analyze_internal_command(user_input):
        return INTENT_MEMORY_COMMAND

    tools_query = analyze_internal_tools_query(user_input)
    if tools_query:
        if tools_query.mode == "feasibility_evaluation":
            return INTENT_FEASIBILITY
        if tools_query.mode == "consistency_evaluation":
            return INTENT_CONSISTENCY
        return INTENT_TOOLS_COMMAND

    if analyze_internal_operations_query(user_input):
        return INTENT_OPERATIONS_COMMAND

    if analyze_capabilities_query(user_input):
        return INTENT_CAPABILITIES_COMMAND

    if analyze_memory_question(user_input):
        return INTENT_MEMORY_QUERY

    if looks_like_feasibility_statement(user_input):
        return INTENT_FEASIBILITY

    technical_intent = _classify_technical_intent(normalized_input)
    if technical_intent:
        return technical_intent

    if "?" in user_input or OPEN_QUESTION_PATTERN.search(normalized_input):
        return INTENT_OPEN

    return INTENT_GENERAL


def build_style_instructions(
    intent: str,
    profile: UserProfile | None = None,
    user_input: str = "",
) -> str:
    base_instructions = [
        "Responde siempre en español.",
        "Ve directo al punto y evita saludos, relleno y frases vacías.",
        'No escribas etiquetas como "Usuario:" o "AURA:".',
        "No cierres con preguntas genéricas salvo que aporten valor real.",
        "No repitas literalmente la pregunta del usuario.",
    ]

    if intent == INTENT_TECHNICAL_TROUBLESHOOT:
        extra_instructions = [
            "Haz la respuesta clara, estructurada y práctica.",
            "Sigue este orden si aplica: idea breve, explicación clara, qué hacer y cómo verificar.",
            "Prioriza una causa probable y una solución accionable.",
            "Si faltan datos, dilo en una sola frase y da igualmente el primer paso más útil.",
            "Evita explicaciones vagas o demasiado largas.",
        ]
    elif intent == INTENT_TECHNICAL_EXPLAIN:
        extra_instructions = [
            "Empieza con una idea breve.",
            "Explica el tema con claridad y orden.",
            "Incluye contexto útil y pasos o ejemplo breve si ayudan.",
            "Mantén la respuesta compacta y enfocada.",
        ]
    elif intent == INTENT_OPEN:
        extra_instructions = [
            "Da una respuesta útil, concreta y natural.",
            "Incluye una idea práctica, ejemplo o siguiente paso si suma valor.",
            "Evita sonar robótico o demasiado abstracto.",
        ]
    elif intent == INTENT_FEASIBILITY:
        extra_instructions = [
            "Evalúa viabilidad, límites y condiciones con honestidad intelectual.",
            "No sigas la corriente automáticamente.",
            "Si algo no cierra, dilo con calma y explica el límite concreto.",
            "Si algo podría hacerse, aclara las condiciones reales.",
            "Evita sonar agresivo, dogmático o complaciente.",
        ]
    elif intent == INTENT_CONSISTENCY:
        extra_instructions = [
            "Calibra certeza, evidencia y dependencia con honestidad intelectual.",
            "No llenes la respuesta de disclaimers ni rebajes un juicio fuerte sin motivo.",
            "Si el juicio es firme, dilo claro; si es tentativo, marca por qué.",
            "Si falta base o hay tensión con el contexto reciente, señálalo sin sobreactuar.",
            "Evita sonar agresivo, dogmático o complaciente.",
        ]
    elif intent in {
        INTENT_CAPABILITIES_COMMAND,
        INTENT_OPERATIONS_COMMAND,
        INTENT_TOOLS_COMMAND,
        INTENT_MEMORY_QUERY,
        INTENT_MEMORY_COMMAND,
        INTENT_SYSTEM_COMMAND,
        INTENT_MAINTENANCE_COMMAND,
    }:
        extra_instructions = [
            "Responde de forma breve, directa y operativa.",
        ]
    else:
        extra_instructions = [
            "Responde de forma natural, breve y útil.",
        ]

    profile_instructions = build_profile_style_hints(
        profile or UserProfile(),
        intent,
        user_input=user_input,
    )
    instructions = base_instructions + extra_instructions + profile_instructions
    return "\n".join(f"- {instruction}" for instruction in instructions)


def build_planning_instructions(
    intent: str,
    profile: UserProfile | None = None,
    user_input: str = "",
) -> str:
    if intent == INTENT_TECHNICAL_TROUBLESHOOT:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): responde en 4 bloques breves: "
            "Idea breve, Explicación clara, Qué hacer (2 o 3 pasos), Cómo verificar. "
            "Máximo 120 palabras."
        )
    elif intent == INTENT_TECHNICAL_EXPLAIN:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): responde en 3 bloques breves: "
            "Idea breve, Explicación clara y Pasos o ejemplo práctico. Máximo 120 palabras."
        )
    elif intent == INTENT_OPEN:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): responde directo; aporta una idea "
            "útil o ejemplo; cierra sin relleno. Máximo 90 palabras."
        )
    elif intent == INTENT_FEASIBILITY:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): clasifica la viabilidad; marca si es "
            "posible, posible con condiciones, incierto, poco realista, contradictorio o inviable; "
            "explica el límite principal y, si suma, sugiere una reformulación. Máximo 90 palabras."
        )
    elif intent == INTENT_CONSISTENCY:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): calibra certeza, evidencia, dependencia "
            "o tensión contextual del juicio actual; di si es firme, condicional o tentativo; "
            "explica brevemente qué falta o qué sostiene el juicio. Máximo 90 palabras."
        )
    elif intent in {
        INTENT_CAPABILITIES_COMMAND,
        INTENT_OPERATIONS_COMMAND,
        INTENT_TOOLS_COMMAND,
        INTENT_MEMORY_QUERY,
        INTENT_MEMORY_COMMAND,
        INTENT_SYSTEM_COMMAND,
        INTENT_MAINTENANCE_COMMAND,
    }:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): responde directo, breve y operativo. "
            "Máximo 70 palabras."
        )
    else:
        base_instruction = (
            "Plan interno de respuesta (no lo muestres): responde de forma breve, natural y útil. "
            "Máximo 70 palabras."
        )

    profile_hints = build_profile_planning_hints(
        profile or UserProfile(),
        intent,
        user_input=user_input,
    )
    if not profile_hints:
        return base_instruction

    return f"{base_instruction} {' '.join(profile_hints)}"


def plan_behavior_for_input(
    user_input: str,
    intent: str | None = None,
    memory: dict[str, Any] | None = None,
    conversation: list[dict[str, str]] | None = None,
) -> BehaviorPlan:
    resolved_intent = intent or classify_user_intent(user_input)
    profile = build_user_profile(memory or {})
    style_instructions = build_style_instructions(
        resolved_intent,
        profile,
        user_input=user_input,
    )
    planning_instructions = build_planning_instructions(
        resolved_intent,
        profile,
        user_input=user_input,
    )
    profile_context = build_profile_prompt_context(
        profile,
        resolved_intent,
        user_input=user_input,
    )

    if resolved_intent == INTENT_CAPABILITY:
        return BehaviorPlan(
            intent=resolved_intent,
            direct_response=_build_capability_response(),
            style_instructions=style_instructions,
            planning_instructions=planning_instructions,
            profile_context=profile_context,
        )

    if resolved_intent == INTENT_TECHNICAL_TROUBLESHOOT:
        direct_response = _build_generic_troubleshoot_response(user_input, profile)
        if direct_response:
            return BehaviorPlan(
                intent=resolved_intent,
                direct_response=direct_response,
                style_instructions=style_instructions,
                planning_instructions=planning_instructions,
                profile_context=profile_context,
            )

    if resolved_intent == INTENT_FEASIBILITY:
        direct_response = build_direct_feasibility_response(user_input)
        if direct_response:
            return BehaviorPlan(
                intent=resolved_intent,
                direct_response=direct_response,
                style_instructions=style_instructions,
                planning_instructions=planning_instructions,
                profile_context=profile_context,
            )

    if resolved_intent == INTENT_TECHNICAL_EXPLAIN:
        direct_response = _build_direct_technical_explain_response(user_input, profile)
        if direct_response:
            return BehaviorPlan(
                intent=resolved_intent,
                direct_response=direct_response,
                style_instructions=style_instructions,
                planning_instructions=planning_instructions,
                profile_context=profile_context,
            )

    if resolved_intent in {INTENT_GENERAL, INTENT_OPEN}:
        direct_response = _build_minimal_conversational_response(user_input)
        if direct_response:
            return BehaviorPlan(
                intent=resolved_intent,
                direct_response=direct_response,
                style_instructions=style_instructions,
                planning_instructions=planning_instructions,
                profile_context=profile_context,
            )

        direct_response = _build_direct_contextual_requirement_response(
            user_input,
            conversation=conversation,
        )
        if direct_response:
            return BehaviorPlan(
                intent=resolved_intent,
                direct_response=direct_response,
                style_instructions=style_instructions,
                planning_instructions=planning_instructions,
                profile_context=profile_context,
            )

    return BehaviorPlan(
        intent=resolved_intent,
        direct_response=None,
        style_instructions=style_instructions,
        planning_instructions=planning_instructions,
        profile_context=profile_context,
    )


def plan_behavior(
    conversation: list[dict[str, str]],
    memory: dict[str, Any],
) -> BehaviorPlan:
    latest_user_message = ""
    for message in reversed(conversation):
        if message.get("role") == "user":
            latest_user_message = str(message.get("content", ""))
            break

    return plan_behavior_for_input(
        latest_user_message,
        memory=memory,
        conversation=conversation,
    )
