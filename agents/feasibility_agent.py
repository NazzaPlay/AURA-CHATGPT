from __future__ import annotations

import re
from dataclasses import dataclass

from .text_matching import (
    build_normalized_command_family,
    matches_normalized_command_family,
    normalize_internal_text,
)


FEASIBILITY_STATUS_POSSIBLE = "possible"
FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS = "possible_with_conditions"
FEASIBILITY_STATUS_UNCERTAIN = "uncertain"
FEASIBILITY_STATUS_UNLIKELY = "unlikely"
FEASIBILITY_STATUS_CONTRADICTORY = "contradictory"
FEASIBILITY_STATUS_NOT_FEASIBLE = "not_feasible"

FEASIBILITY_FRAME_GENERAL = "feasibility_check"
FEASIBILITY_FRAME_CONTRADICTION = "contradiction_check"
FEASIBILITY_FRAME_REALISM = "realism_check"
FEASIBILITY_FRAME_LIMITS = "limits_check"

FEASIBILITY_GENERAL_QUERY_COMMANDS = build_normalized_command_family(
    {
        "esto es posible",
        "esto de verdad se puede hacer",
        "ves viable esta idea",
        "esto tiene sentido",
        "esto no te parece imposible",
        "esto esta bien planteado",
        "esto es humo o tiene sentido",
        "esto se puede hacer asi como lo digo",
        "esto es razonable",
        "esto te parece posible en la practica",
    }
)
FEASIBILITY_CONTRADICTION_QUERY_COMMANDS = build_normalized_command_family(
    {
        "ves alguna contradiccion",
        "ves algo que no cierre",
        "esto se contradice con algo",
    }
)
FEASIBILITY_REALISM_QUERY_COMMANDS = build_normalized_command_family(
    {
        "te parece realista",
        "esto seria viable con mi pc",
    }
)
FEASIBILITY_LIMITS_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que problema ves en esta idea",
        "esto tiene algun limite importante",
    }
)

GENERIC_REFERENCE_PATTERNS = (
    "esto",
    "esta idea",
    "asi como lo digo",
    "asi planteado",
)


@dataclass(frozen=True)
class FeasibilityQuery:
    frame: str = FEASIBILITY_FRAME_GENERAL


@dataclass(frozen=True)
class FeasibilityEvaluation:
    status: str
    reason: str
    scope: str
    contradiction_detected: bool
    uncertainty_level: str
    realism_level: str
    conditions_required: tuple[str, ...]
    frame: str
    viability_basis: str
    primary_constraint: str | None = None
    plausibility_mode: str = "feasibility_scan"
    subject: str = ""
    reformulation: str | None = None


def _dedupe_items(items: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned = " ".join(item.split()).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)

    return tuple(unique)


def _contains_any(text: str, options: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(option in text for option in options)


def _format_reformulation(reformulation: str | None, prefix: str) -> str:
    if not reformulation:
        return ""

    cleaned = " ".join(reformulation.split()).strip()
    if not cleaned:
        return ""

    if cleaned[-1] not in ".!?":
        cleaned = f"{cleaned}."

    lower = normalize_internal_text(cleaned)
    if lower.startswith(("una version", "una reformulacion", "hay que", "si quieres", "tiene mas sentido")):
        return f" {cleaned[0].upper()}{cleaned[1:]}" if cleaned else ""

    return f" {prefix} {cleaned}"


def analyze_feasibility_query(user_input: str) -> FeasibilityQuery | None:
    if matches_normalized_command_family(user_input, FEASIBILITY_CONTRADICTION_QUERY_COMMANDS):
        return FeasibilityQuery(frame=FEASIBILITY_FRAME_CONTRADICTION)

    if matches_normalized_command_family(user_input, FEASIBILITY_REALISM_QUERY_COMMANDS):
        return FeasibilityQuery(frame=FEASIBILITY_FRAME_REALISM)

    if matches_normalized_command_family(user_input, FEASIBILITY_LIMITS_QUERY_COMMANDS):
        return FeasibilityQuery(frame=FEASIBILITY_FRAME_LIMITS)

    if matches_normalized_command_family(user_input, FEASIBILITY_GENERAL_QUERY_COMMANDS):
        return FeasibilityQuery(frame=FEASIBILITY_FRAME_GENERAL)

    return None


def looks_like_feasibility_statement(user_input: str) -> bool:
    normalized = normalize_internal_text(user_input)

    if analyze_feasibility_query(user_input):
        return True

    resource_pressure = (
        bool(re.search(r"\b([4-9]|[1-9]\d+)\s+modelos\b", normalized))
        or "varios modelos grandes" in normalized
        or "modelos grandes" in normalized
    )
    extreme_expectation = _contains_any(
        normalized,
        {
            "instantaneo",
            "ultrarapido",
            "cero recursos",
            "sin hardware potente",
            "siempre lo ultimo que paso en internet",
            "seguro funcionaria",
            "no falle nunca",
            "resolveria todo de una vez",
            "mejor arquitectura posible",
            "mejor que cualquier otra opcion",
            "sin decirme que no",
        },
    )
    planning_conditions = _contains_any(
        normalized,
        {
            "mas adelante",
            "con mejores recursos",
            "si primero",
            "si primero mejoramos la arquitectura",
            "si mejoramos la arquitectura",
            "encapsulamos providers",
            "otro modelo solo cuando haga falta",
            "modelo principal y otro verificador",
            "podriamos hacerlo en v0 36",
            "podriamos hacerlo en v0.36",
        },
    )

    return resource_pressure or extreme_expectation or planning_conditions


def _extract_subject_text(
    user_input: str,
    conversation: list[dict[str, str]] | None = None,
) -> str:
    normalized = normalize_internal_text(user_input)
    conversation = conversation or []

    if analyze_feasibility_query(user_input) and any(
        pattern in normalized for pattern in GENERIC_REFERENCE_PATTERNS
    ):
        for message in reversed(conversation):
            if message.get("role") != "user":
                continue

            content = str(message.get("content", "")).strip()
            if not content:
                continue

            if normalize_internal_text(content) == normalized:
                continue

            return content

    return user_input.strip()


def _build_missing_subject_evaluation(frame: str) -> FeasibilityEvaluation:
    reason = "me falta la idea concreta para evaluarla con honestidad"
    if frame == FEASIBILITY_FRAME_CONTRADICTION:
        reason = "me falta el planteo concreto para ver si realmente hay un choque"
    elif frame == FEASIBILITY_FRAME_REALISM:
        reason = "me falta el escenario concreto para juzgar si eso es realista"

    return FeasibilityEvaluation(
        status=FEASIBILITY_STATUS_UNCERTAIN,
        reason=reason,
        scope="information_gap",
        contradiction_detected=False,
        uncertainty_level="high",
        realism_level="unknown",
        conditions_required=(),
        frame=frame,
        viability_basis="information_gap",
        primary_constraint="missing_context",
        plausibility_mode="insufficient_context",
        subject="",
    )


def evaluate_feasibility(
    user_input: str,
    conversation: list[dict[str, str]] | None = None,
    preferred_frame: str | None = None,
) -> FeasibilityEvaluation:
    frame = preferred_frame or FEASIBILITY_FRAME_GENERAL
    subject = _extract_subject_text(user_input, conversation=conversation)
    normalized = normalize_internal_text(subject)

    if not subject or analyze_feasibility_query(subject):
        return _build_missing_subject_evaluation(frame)

    conditions: list[str] = []
    contradiction_detected = False
    reformulation: str | None = None

    asks_latest_internet = _contains_any(
        normalized,
        {
            "siempre lo ultimo que paso en internet",
            "siempre lo ultimo",
            "lo ultimo que paso en internet",
        },
    )
    requires_offline = _contains_any(
        normalized,
        {
            "offline",
            "todo offline",
            "local",
            "sin internet",
        },
    )
    wants_zero_resources = "cero recursos" in normalized
    wants_huge_reasoning = _contains_any(
        normalized,
        {
            "servidor enorme",
            "7 modelos grandes",
            "varios modelos grandes",
            "modelos grandes activos",
            "instantaneo",
            "ultrarapido",
        },
    )
    asks_many_large_models = bool(re.search(r"\b([4-9]|[1-9]\d+)\s+modelos\b", normalized)) or _contains_any(
        normalized,
        {
            "varios modelos grandes",
            "modelos grandes activos",
        },
    )
    asks_low_hardware = _contains_any(
        normalized,
        {
            "mi pc",
            "sin hardware potente",
            "gratis",
            "cero recursos",
        },
    )
    asks_absolute_guarantee = _contains_any(
        normalized,
        {
            "seguro funcionaria",
            "mejor que cualquier otra opcion",
            "mejor arquitectura posible",
            "garantiza que no falle nunca",
            "resolveria todo de una vez",
        },
    )
    is_future_architecture = _contains_any(
        normalized,
        {
            "multimodelo mas adelante",
            "modelo principal y otro verificador",
            "otro modelo solo cuando haga falta",
            "si primero mejoramos la arquitectura",
            "si mejoramos la arquitectura",
            "con mejores recursos",
            "si primero encapsulamos providers",
            "podriamos hacerlo en v0 36",
            "podriamos hacerlo en v0.36",
        },
    )
    asks_realism_with_pc = "viable con mi pc" in normalized
    asks_impossible_without_pushback = _contains_any(
        normalized,
        {
            "algo imposible",
            "sin decirme que no",
        },
    )

    if requires_offline and asks_latest_internet:
        contradiction_detected = True
        conditions.extend(
            [
                "permitir una capa online opcional",
                "o aceptar que lo offline no siempre estará al día",
            ]
        )
        reformulation = (
            "una versión más realista es mantenerlo local y aceptar datos no siempre al día, "
            "o abrir una sincronización online opcional"
        )
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_CONTRADICTORY,
            reason="pides que sea totalmente offline y, al mismo tiempo, que siempre sepa lo último de internet",
            scope="requirements",
            contradiction_detected=True,
            uncertainty_level="low",
            realism_level="low",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="requirement_conflict",
            primary_constraint="offline_vs_live_internet",
            plausibility_mode="contradiction_check",
            subject=subject,
            reformulation=reformulation,
        )

    if wants_zero_resources and wants_huge_reasoning:
        contradiction_detected = True
        conditions.extend(
            [
                "subir recursos disponibles",
                "o bajar de forma clara la ambición del sistema",
            ]
        )
        reformulation = "hay que elegir entre más capacidad o una meta bastante más modesta"
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_CONTRADICTORY,
            reason="pides cero recursos y, a la vez, un nivel de cómputo que empuja en la dirección opuesta",
            scope="resources",
            contradiction_detected=True,
            uncertainty_level="low",
            realism_level="low",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="resource_conflict",
            primary_constraint="resource_budget",
            plausibility_mode="contradiction_check",
            subject=subject,
            reformulation=reformulation,
        )

    if asks_impossible_without_pushback:
        contradiction_detected = True
        reformulation = "si algo no cierra, lo útil es reformularlo hacia una versión más realista"
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_CONTRADICTORY,
            reason="pides algo imposible y, al mismo tiempo, que no se marque el límite real",
            scope="requirements",
            contradiction_detected=True,
            uncertainty_level="low",
            realism_level="low",
            conditions_required=("aceptar límites explícitos",),
            frame=frame,
            viability_basis="requirement_conflict",
            primary_constraint="explicit_impossibility",
            plausibility_mode="contradiction_check",
            subject=subject,
            reformulation=reformulation,
        )

    if _contains_any(
        normalized,
        {
            "ultrarapido",
            "gratis",
            "local",
            "sin hardware potente",
            "varios modelos grandes activos",
            "modelos grandes activos",
        },
    ) and sum(
        [
            "ultrarapido" in normalized,
            "gratis" in normalized,
            "local" in normalized,
            "sin hardware potente" in normalized,
            "varios modelos grandes activos" in normalized
            or "modelos grandes activos" in normalized,
        ]
    ) >= 4:
        conditions.extend(
            [
                "ceder en velocidad, costo o cantidad de modelos",
                "o subir claramente el hardware disponible",
            ]
        )
        reformulation = "si quieres que cierre, hay que elegir qué restricción pesa menos"
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_CONTRADICTORY,
            reason="la combinación de requisitos empuja en direcciones que no cierran bien entre sí",
            scope="requirements",
            contradiction_detected=True,
            uncertainty_level="low",
            realism_level="low",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="requirement_conflict",
            primary_constraint="competing_requirements",
            plausibility_mode="constraint_bundle_check",
            subject=subject,
            reformulation=reformulation,
        )

    if asks_many_large_models and asks_low_hardware and _contains_any(
        normalized,
        {"instantaneo", "ultrarapido"},
    ):
        conditions.extend(
            [
                "reducir la cantidad de modelos activos",
                "aceptar más latencia",
                "o usar hardware bastante más fuerte",
            ]
        )
        reformulation = "una versión más realista es un modelo principal y otro apoyo ocasional, no varios grandes a la vez"
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_NOT_FEASIBLE,
            reason="mezclas paralelismo pesado, latencia casi instantánea y un presupuesto de hardware demasiado bajo",
            scope="resources",
            contradiction_detected=False,
            uncertainty_level="low",
            realism_level="low",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="resource_constraints",
            primary_constraint="hardware_and_latency",
            plausibility_mode="resource_check",
            subject=subject,
            reformulation=reformulation,
        )

    if is_future_architecture:
        if "modelo principal y otro verificador" in normalized:
            conditions.extend(
                [
                    "definir cuándo entra el verificador",
                    "aceptar más costo y algo más de latencia",
                    "mantener providers bien encapsulados",
                ]
            )
        elif "otro modelo solo cuando haga falta" in normalized:
            conditions.extend(
                [
                    "definir un criterio claro de activación",
                    "aislar bien la capa de providers",
                ]
            )
        else:
            conditions.extend(
                [
                    "cerrar antes la arquitectura base",
                    "encapsular providers",
                    "medir costo, latencia y complejidad antes de abrir esa capa",
                ]
            )

        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS,
            reason="la idea puede cerrar, pero depende de ordenar primero la base técnica y el costo operativo",
            scope="architecture",
            contradiction_detected=False,
            uncertainty_level="medium",
            realism_level="medium",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="architectural_dependencies",
            primary_constraint="architecture_maturity",
            plausibility_mode="conditional_roadmap",
            subject=subject,
            reformulation="tiene más sentido como evolución posterior que como salto inmediato",
        )

    if asks_realism_with_pc:
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_UNCERTAIN,
            reason="sin saber RAM, VRAM, CPU y tamaño real de los modelos no lo daría por realista ni por inviable",
            scope="hardware",
            contradiction_detected=False,
            uncertainty_level="high",
            realism_level="medium",
            conditions_required=(
                "mirar RAM o VRAM disponibles",
                "definir cuántos modelos y de qué tamaño hablas",
            ),
            frame=frame,
            viability_basis="information_gap",
            primary_constraint="missing_hardware_data",
            plausibility_mode="hardware_check",
            subject=subject,
        )

    if asks_absolute_guarantee:
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_UNCERTAIN,
            reason="estás pidiendo una certeza demasiado fuerte para algo que siempre depende de contexto, trade-offs y validación real",
            scope="claims",
            contradiction_detected=False,
            uncertainty_level="high",
            realism_level="medium",
            conditions_required=("probarlo contra objetivos y límites concretos",),
            frame=frame,
            viability_basis="overclaim_detection",
            primary_constraint="overconfidence",
            plausibility_mode="uncertainty_check",
            subject=subject,
        )

    if "viable" in normalized or "posible" in normalized or "razonable" in normalized or "sentido" in normalized:
        conditions.extend(
            [
                "mantener el alcance acotado",
                "validarlo con una prueba concreta antes de darlo por cerrado",
            ]
        )
        return FeasibilityEvaluation(
            status=FEASIBILITY_STATUS_POSSIBLE,
            reason="no veo un choque fuerte en la idea tal como está planteada",
            scope="general",
            contradiction_detected=False,
            uncertainty_level="medium",
            realism_level="medium",
            conditions_required=_dedupe_items(conditions),
            frame=frame,
            viability_basis="scope_alignment",
            primary_constraint=None,
            plausibility_mode="feasibility_scan",
            subject=subject,
        )

    return FeasibilityEvaluation(
        status=FEASIBILITY_STATUS_UNCERTAIN,
        reason="no hay suficiente base en el planteo para afirmarlo con seguridad",
        scope="general",
        contradiction_detected=False,
        uncertainty_level="high",
        realism_level="medium",
        conditions_required=(),
        frame=frame,
        viability_basis="information_gap",
        primary_constraint="insufficient_detail",
        plausibility_mode="uncertainty_check",
        subject=subject,
    )


def build_feasibility_response(evaluation: FeasibilityEvaluation) -> str:
    conditions = list(evaluation.conditions_required)
    conditions_text = ", ".join(conditions[:3])
    reformulation = evaluation.reformulation

    if evaluation.frame == FEASIBILITY_FRAME_CONTRADICTION:
        if evaluation.contradiction_detected:
            response = f"Sí, veo una contradicción clara: {evaluation.reason}."
            response += _format_reformulation(
                reformulation,
                "Una versión más realista sería",
            )
            return response

        if evaluation.status == FEASIBILITY_STATUS_UNCERTAIN:
            return f"No lo daría por contradictorio todavía: {evaluation.reason}."

        return f"No veo una contradicción fuerte, pero {evaluation.reason}."

    if evaluation.status == FEASIBILITY_STATUS_CONTRADICTORY:
        response = f"Eso no cierra bien: {evaluation.reason}."
        response += _format_reformulation(
            reformulation,
            "Una reformulación más realista sería",
        )
        return response

    if evaluation.status == FEASIBILITY_STATUS_NOT_FEASIBLE:
        response = f"Así como está, no lo veo viable: {evaluation.reason}."
        if conditions_text:
            response += f" Para acercarlo a algo realista, habría que {conditions_text}."
        response += _format_reformulation(reformulation, "En corto,")
        return response

    if evaluation.status == FEASIBILITY_STATUS_UNLIKELY:
        response = f"Lo veo difícil tal como está: {evaluation.reason}."
        if conditions_text:
            response += f" Solo lo intentaría si antes {conditions_text}."
        return response

    if evaluation.status == FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS:
        response = f"Sí, pero depende de condiciones claras: {evaluation.reason}."
        if conditions_text:
            response += f" Para que cierre, haría falta {conditions_text}."
        response += _format_reformulation(reformulation, "En ese encuadre,")
        return response

    if evaluation.status == FEASIBILITY_STATUS_POSSIBLE:
        response = f"Sí, puede cerrar: {evaluation.reason}."
        if conditions_text:
            response += f" Igual conviene {conditions_text}."
        return response

    response = f"No lo afirmaría fuerte: {evaluation.reason}."
    if conditions_text:
        response += f" Para afirmarlo mejor, me haría falta {conditions_text}."
    return response


def build_direct_feasibility_response(user_input: str) -> str | None:
    if not looks_like_feasibility_statement(user_input):
        return None

    evaluation = evaluate_feasibility(user_input)
    return build_feasibility_response(evaluation)
