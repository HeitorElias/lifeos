import os
import json
import logging
import base64
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

Regras:
- Use nomes comuns e simples (ex: "arroz branco", "feijão carioca", "frango grelhado")
- Estime porções em gramas de forma realista
- Confidence entre 0 e 1
- Se não conseguir identificar um item, coloque confidence < 0.5
- NÃO invente valores nutricionais, apenas identifique alimentos e porções"""

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

Regras:
- Se o usuário mencionar "um prato de arroz", estime ~200g
- Se mencionar "frango 150g", use exatamente 150g
- Use nomes normalizados e simples
- NÃO invente valores nutricionais"""

AGENDA_PROMPT = """Você é um assistente de agenda inteligente. O usuário vai falar sobre compromissos.
Interprete a intenção e extraia os dados relevantes.

Retorne SOMENTE um JSON válido no seguinte formato (sem markdown, sem texto extra):
{
  "intent": "list_events|create_event|update_event|cancel_event|general_query",
  "payload": {
    "title": "título do compromisso",
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "end_time": "HH:MM",
    "location": "local se mencionado",
    "notes": "notas adicionais",
    "event_id": "id do evento se mencionado para update/cancel"
  },
  "response_text": "resposta amigável para o usuário em português"
}

Regras:
- Use a data atual como referência: hoje é {today}
- "amanhã" = dia seguinte, "segunda" = próxima segunda, etc.
- Se a intenção não for clara, use "general_query"
- response_text deve ser natural e em português BR"""

FINANCE_PROMPT = """Você é um consultor financeiro pessoal inteligente. O usuário vai falar sobre suas finanças.
Interprete a intenção e forneça análises baseadas nos dados.

Contexto dos gastos do usuário:
{finance_context}

Retorne SOMENTE um JSON válido no seguinte formato (sem markdown, sem texto extra):
{{
  "intent": "add_bill|add_expense|list_bills|list_expenses|analyze_savings|general_query",
  "payload": {{
    "name": "nome da conta/gasto",
    "amount": 150.00,
    "due_date": "YYYY-MM-DD",
    "category": "categoria",
    "recurrence": "once|monthly|weekly",
    "description": "descrição"
  }},
  "analysis": {{
    "top_cuts": ["sugestão 1", "sugestão 2"],
    "suggested_goals": ["meta 1", "meta 2"],
    "simple_actions": ["ação 1", "ação 2"],
    "potential_savings": 0.0
  }},
  "response_text": "resposta amigável para o usuário em português"
}}

Regras:
- Baseie análises nos dados reais do usuário
- Sugestões devem ser práticas e específicas
- Valores em BRL (R$)
- response_text deve ser natural e em português BR"""

MEAL_PLAN_PROMPT = """Você é um nutricionista profissional. Crie um plano alimentar personalizado.

Perfil do usuário:
- Idade: {age} anos
- Peso: {weight} kg
- Altura: {height} cm
- Objetivo: {goal}
- Nível de atividade: {activity_level}
- Restrições: {restrictions}
- Meta calórica diária: {calorie_target} kcal

Retorne SOMENTE um JSON válido no seguinte formato (sem markdown, sem texto extra):
{{
  "plan_name": "Nome do plano",
  "daily_target": {{
    "calories": {calorie_target},
    "protein_g": 0,
    "carbs_g": 0,
    "fat_g": 0
  }},
  "days": [
    {{
      "day": 1,
      "day_name": "Segunda-feira",
      "meals": [
        {{
          "meal_type": "café da manhã",
          "time": "07:00",
          "items": [
            {{
              "name": "nome do alimento",
              "portion": "porção em texto",
              "grams": 150
            }}
          ]
        }}
      ]
    }}
  ],
  "shopping_list": [
    {{
      "item": "nome do item",
      "quantity": "quantidade",
      "category": "categoria"
    }}
  ],
  "tips": ["dica 1", "dica 2"]
}}

Regras:
- Crie plano para 7 dias
- 5-6 refeições por dia (café, lanche manhã, almoço, lanche tarde, jantar, ceia se necessário)
- Use alimentos comuns e acessíveis do Brasil
- Respeite as restrições alimentares
- Distribua macros adequadamente ao objetivo
- Lista de compras organizada por categoria"""


async def analyze_food_photo(image_base64: str) -> dict:
    """Analyze a food photo using AI vision."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        
        provider = os.environ.get('AI_PROVIDER', 'gemini')
        model = os.environ.get('AI_MODEL', 'gemini-3-flash-preview')
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')

        chat = LlmChat(
            api_key=api_key,
            session_id=f"food-photo-{os.urandom(8).hex()}",
            system_message="Você é um especialista em identificação de alimentos. Responda SOMENTE com JSON válido."
        )
        chat.with_model(provider, model)

        image_content = ImageContent(image_base64=image_base64)
        user_message = UserMessage(
            text=VISION_PROMPT,
            file_contents=[image_content]
        )

        response = await chat.send_message(user_message)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"AI food photo analysis error: {e}")
        raise


async def analyze_food_text(text: str) -> dict:
    """Analyze food description text using AI."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        provider = os.environ.get('AI_PROVIDER', 'gemini')
        model = os.environ.get('AI_MODEL', 'gemini-3-flash-preview')
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')

        chat = LlmChat(
            api_key=api_key,
            session_id=f"food-text-{os.urandom(8).hex()}",
            system_message="Você é um especialista em nutrição. Responda SOMENTE com JSON válido."
        )
        chat.with_model(provider, model)

        user_message = UserMessage(text=f"{MEAL_TEXT_PROMPT}\n\nTexto do usuário: {text}")
        response = await chat.send_message(user_message)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"AI food text analysis error: {e}")
        raise


async def process_agenda_message(text: str, today: str) -> dict:
    """Process agenda-related chat message."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        provider = os.environ.get('AI_PROVIDER', 'gemini')
        model = os.environ.get('AI_MODEL', 'gemini-3-flash-preview')
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')

        prompt = AGENDA_PROMPT.replace("{today}", today)
        chat = LlmChat(
            api_key=api_key,
            session_id=f"agenda-{os.urandom(8).hex()}",
            system_message=prompt
        )
        chat.with_model(provider, model)

        user_message = UserMessage(text=text)
        response = await chat.send_message(user_message)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"AI agenda processing error: {e}")
        raise


async def process_finance_message(text: str, finance_context: str) -> dict:
    """Process finance-related chat message."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        provider = os.environ.get('AI_PROVIDER', 'gemini')
        model = os.environ.get('AI_MODEL', 'gemini-3-flash-preview')
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')

        prompt = FINANCE_PROMPT.replace("{finance_context}", finance_context)
        chat = LlmChat(
            api_key=api_key,
            session_id=f"finance-{os.urandom(8).hex()}",
            system_message=prompt
        )
        chat.with_model(provider, model)

        user_message = UserMessage(text=text)
        response = await chat.send_message(user_message)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"AI finance processing error: {e}")
        raise


async def generate_meal_plan(profile: dict) -> dict:
    """Generate a meal plan based on user profile."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        provider = os.environ.get('AI_PROVIDER', 'gemini')
        model = os.environ.get('AI_MODEL', 'gemini-3-flash-preview')
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')

        prompt = MEAL_PLAN_PROMPT.format(**profile)
        chat = LlmChat(
            api_key=api_key,
            session_id=f"mealplan-{os.urandom(8).hex()}",
            system_message="Você é um nutricionista profissional. Responda SOMENTE com JSON válido."
        )
        chat.with_model(provider, model)

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"AI meal plan generation error: {e}")
        raise


def _parse_json_response(response: str) -> dict:
    """Parse JSON from AI response, handling markdown code blocks."""
    text = response.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        start = 1
        end = len(lines) - 1
        if lines[0].startswith('```json'):
            start = 1
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == '```':
                end = i
                break
        text = '\n'.join(lines[start:end])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        logger.error(f"Failed to parse JSON from AI: {text[:200]}")
        return {"error": "Falha ao processar resposta da IA", "raw": text[:500]}
