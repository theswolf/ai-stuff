import json
import logging
import os
from openai import OpenAI
from .tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)
MAX_ITERATIONS = 8
SYSTEM_PROMPT = """Sei un assistente intelligente con accesso a strumenti esterni.
Usa i tool quando servono dati aggiornati, numeri precisi o fatti specifici.
Dopo aver chiamato un tool, spiega il risultato in italiano chiaro.
Se un tool restituisce un errore, comunicalo all'utente.
"""


class AgentService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.tools = [t["schema"] for t in TOOL_REGISTRY.values()]

    def run(self, user_message: str) -> dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}]
        tool_calls_log = []
        for iteration in range(MAX_ITERATIONS):
            response = self.client.chat.completions.create(model=self.model, messages=messages, tools=self.tools, tool_choice="auto")
            choice = response.choices[0]
            message = choice.message
            finish_reason = choice.finish_reason
            messages.append(message.model_dump(exclude_none=True))
            if finish_reason == "stop" or not message.tool_calls:
                return {"answer": message.content, "iterations": iteration + 1, "tool_calls": tool_calls_log}
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                raw_args = tool_call.function.arguments
                try:
                    tool_args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    tool_args = {}
                if tool_name in TOOL_REGISTRY:
                    fn = TOOL_REGISTRY[tool_name]["function"]
                    try:
                        tool_result = fn(**tool_args)
                    except Exception as e:
                        tool_result = {"error": str(e)}
                else:
                    tool_result = {"error": f"Tool '{tool_name}' non registrato"}
                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result": tool_result})
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(tool_result, ensure_ascii=False)})
        return {"answer": "Limite di iterazioni raggiunto senza risposta finale.", "iterations": MAX_ITERATIONS, "tool_calls": tool_calls_log}
