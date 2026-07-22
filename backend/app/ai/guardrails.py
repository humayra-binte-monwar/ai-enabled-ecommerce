SENSITIVE_HEALTH_TERMS = {
    "allergy",
    "allergic",
    "baby formula",
    "diabetes",
    "diabetic",
    "doctor",
    "medicine",
    "pregnancy",
    "pregnant",
    "prescribe",
    "supplement",
}

HEALTH_TERMS = {
    "balanced",
    "calorie",
    "diabetic",
    "diet",
    "healthy",
    "nutrition",
    "protein",
    "sugar",
}


def is_health_question(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in HEALTH_TERMS | SENSITIVE_HEALTH_TERMS)


def health_disclaimer(message: str) -> str:
    message_lower = message.lower()

    if any(term in message_lower for term in SENSITIVE_HEALTH_TERMS):
        return (
            "General information only: I can help compare grocery choices, but this is "
            "not medical advice. Please check with a qualified professional for medical "
            "conditions, allergies, pregnancy, baby formula, or supplements."
        )

    return "General information only: I can suggest grocery tradeoffs, but this is not medical advice."
