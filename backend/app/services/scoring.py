"""Experimental, explicit evidence policy; never scores raw cosine similarity."""
POLICY_VERSION = "evidence-v2-automatic"
CONTRIBUTION = {"evidenced": 1.0, "partial": 0.5, "not_evidenced": 0.0, "contradictory": 0.0}


def calculate_score(requirements, evidence):
    total = sum(requirement["weight"] for requirement in requirements)
    if not requirements or total <= 0:
        raise ValueError("A soma dos pesos deve ser superior a zero")
    states = {item["requirement_id"]: item["state"] for item in evidence}
    if set(states) != {r["id"] for r in requirements} or len(states) != len(evidence):
        raise ValueError("Evidências incompletas ou repetidas")
    score = round(sum(r["weight"] * CONTRIBUTION[states[r["id"]]] for r in requirements) / total * 100, 2)
    missing = [r["name"] for r in requirements if r["is_mandatory"] and states[r["id"]] != "evidenced"]
    if missing:
        recommendation = "Requisito obrigatório ausente"
        summary = "Adequação não comprovada: faltam evidências completas para os requisitos obrigatórios: " + ", ".join(missing) + "."
    elif score >= 80:
        recommendation = "Recomendado"
        summary = "Adequado segundo o CV: todos os requisitos obrigatórios estão comprovados e a compatibilidade é de pelo menos 80%."
    elif score >= 50:
        recommendation = "Compatibilidade parcial"
        summary = "Parcialmente adequado segundo o CV: compatibilidade entre 50% e 80%, sem requisitos obrigatórios em falta."
    else:
        recommendation = "Baixa compatibilidade"
        summary = "Baixa adequação aos requisitos: o CV comprova menos de 50% do peso dos critérios."
    return {"score": score, "mandatory_missing": missing, "policy_version": POLICY_VERSION,
            "policy_status": "automatic", "recommendation": recommendation, "summary": summary}


def known_experience_days(experiences):
    intervals = sorted((e.start, e.end) for e in experiences if e.start and e.end)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return sum((end - start).days for start, end in merged)
