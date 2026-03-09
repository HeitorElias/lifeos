import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

VISION_PROMPT = """Você é um especialista em nutrição. Analise esta foto de um prato de comida.
Identifique TODOS os alimentos visíveis e estime a porção de cada um em gramas.

Retorne SOMENTE um JSON válido no seguinte formato (sem markdown, sem texto extra):
{
  "items": [
    {
      "name": "nome do alimento em português",
      "name_en": "food name in english",
      "estimated_grams": 150,
      "confidence": 0.85
    }
  ],
  "meal_type": "almoço|jantar|café da manhã|lanche",
  "notes": "observações breves se necessário"
}
"""

MEAL_TEXT_PROMPT = """Você é um especialista em nutrição. O usuário vai descrever o que comeu em texto livre.
Extraia os alimentos e porções mencionados.

Retorne SOMENTE um JSON válido no seguinte formato (sem markdown, sem texto extra):
{
  "items": [
    {
      "name": "nome do alimento em português",
      "name_en": "food name in english",
      "estimated_grams": 150,
      "confidence": 0.9
    }
  ],
  "meal_type": "almoço|jantar|café da manhã|lanche",
  "notes": "observações breves se necessário"
}
"""

AGENDA_PROMPT = """Você é um assistente de agenda inteligente. O usuário vai falar sobre compromissos.
Interprete a intenção e extraia os dados relevantes.

Retorne SOMENTE JSON válido com:
{
  "intent": "list_events|create_event|update_event|cancel_event|general_query",
  "payload": {},
  "response_text": "resposta amigável"
}

Use a data atual como referência: hoje é {today}."""

FINANCE_INSIGHT_PROMPT = """Você é um consultor financeiro comercial orientado a insights.

INSTRUÇÕES DE SEGURANÇA:
- Somente leitura: NÃO crie, altere ou delete dados.
- Não solicite nem exponha dados sensíveis.
- Baseie-se apenas no contexto agregado fornecido.
- Entregue relatório completo com resumo executivo, riscos, oportunidades e plano de economia.

Contexto financeiro agregado:
{finance_context}

Pergunta do usuário:
{user_message}

Retorne SOMENTE JSON válido no formato:
{
  "intent": "financial_insight",
  "analysis": {
    "summary": "resumo executivo curto",
    "full_report": "relatório detalhado em português BR",
    "top_cuts": ["..."],
    "alerts": ["..."],
    "opportunities": ["..."],
    "simple_actions": ["..."],
    "potential_savings": 0.0
  },
  "response_text": "resposta amigável, objetiva e comercial"
}
"""

MEAL_PLAN_PROMPT = """Você é um nutricionista profissional. Crie um plano alimentar personalizado.

Perfil do usuário:
- Idade: {age} anos
- Peso: {weight} kg
- Altura: {height} cm
- Objetivo: {goal}
- Nível de atividade: {activity_level}
- Restrições: {restrictions}
- Meta calórica diária: {calorie_target} kcal

Retorne SOMENTE JSON válido."""


def _parse_json_response(response: str) -> dict[str, Any]:
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        text = "\n".join(lines[1:end])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        logger.error("Failed to parse JSON from AI response")
        return {"error": "Falha ao processar resposta da IA"}


async def _send_json_prompt(system_message: str, user_message: str, session_prefix: str) -> dict[str, Any]:
    from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage

    provider = os.environ.get("AI_PROVIDER", "gemini")
    model = os.environ.get("AI_MODEL", "gemini-3-flash-preview")
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")

    chat = LlmChat(
        api_key=api_key,
        session_id=f"{session_prefix}-{os.urandom(8).hex()}",
        system_message=system_message,
    )
    chat.with_model(provider, model)

    if session_prefix == "food-photo":
        response = await chat.send_message(UserMessage(text=VISION_PROMPT, file_contents=[ImageContent(image_base64=user_message)]))
    else:
        response = await chat.send_message(UserMessage(text=user_message))
    return _parse_json_response(response)


async def analyze_food_photo(image_base64: str) -> dict[str, Any]:
    return await _send_json_prompt(
        "Você é um especialista em identificação de alimentos. Responda SOMENTE com JSON válido.",
        image_base64,
        "food-photo",
    )


async def analyze_food_text(text: str) -> dict[str, Any]:
    return await _send_json_prompt(
        "Você é um especialista em nutrição. Responda SOMENTE com JSON válido.",
        f"{MEAL_TEXT_PROMPT}\n\nTexto do usuário: {text}",
        "food-text",
    )


async def process_agenda_message(text: str, today: str) -> dict[str, Any]:
    return await _send_json_prompt(AGENDA_PROMPT.replace("{today}", today), text, "agenda")


async def process_finance_message(text: str, finance_context: str) -> dict[str, Any]:
    response = await _send_json_prompt(
        "Você é um consultor financeiro para insights. Responda SOMENTE com JSON válido.",
        FINANCE_INSIGHT_PROMPT.format(finance_context=finance_context, user_message=text),
        "finance",
    )
    return _normalize_finance_response(response)


async def generate_meal_plan(profile: dict[str, Any]) -> dict[str, Any]:
    return await _send_json_prompt(
        "Você é um nutricionista profissional. Responda SOMENTE com JSON válido.",
        MEAL_PLAN_PROMPT.format(**profile),
        "mealplan",
    )


def _normalize_finance_response(payload: dict[str, Any]) -> dict[str, Any]:
    analysis = payload.get("analysis") or {}
    normalized = {
        "intent": "financial_insight",
        "analysis": {
            "summary": str(analysis.get("summary", "Resumo indisponível"))[:300],
            "full_report": str(analysis.get("full_report", "Relatório detalhado indisponível."))[:4000],
            "top_cuts": [str(item)[:200] for item in (analysis.get("top_cuts") or [])][:5],
            "alerts": [str(item)[:200] for item in (analysis.get("alerts") or [])][:5],
            "opportunities": [str(item)[:200] for item in (analysis.get("opportunities") or [])][:5],
            "simple_actions": [str(item)[:200] for item in (analysis.get("simple_actions") or [])][:5],
            "potential_savings": float(analysis.get("potential_savings") or 0.0),
        },
        "response_text": str(payload.get("response_text", "Aqui está sua análise financeira."))[:1000],
    }
    return normalized
