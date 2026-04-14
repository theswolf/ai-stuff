import math
import httpx
from typing import Any


def calculator(expression: str) -> dict[str, Any]:
    safe_globals = {
        "__builtins__": {},
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "pow": math.pow,
        "log": math.log,
        "log10": math.log10,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
        "floor": math.floor,
        "ceil": math.ceil,
    }
    expression = expression.replace("^", "**")
    try:
        result = eval(expression, safe_globals)
        return {"result": float(result), "expression": expression}
    except ZeroDivisionError:
        return {"error": "Divisione per zero"}
    except Exception as e:
        return {"error": f"Espressione non valida: {str(e)}"}


def get_weather(city: str) -> dict[str, Any]:
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        with httpx.Client(timeout=10.0) as client:
            geo_response = client.get(geo_url, params={"name": city, "count": 1, "language": "it"})
            geo_data = geo_response.json()
            if not geo_data.get("results"):
                return {"error": f"Città '{city}' non trovata"}
            location = geo_data["results"][0]
            lat, lon = location["latitude"], location["longitude"]
            weather_response = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,wind_speed_10m,weather_code",
                    "timezone": "auto",
                },
            )
            current = weather_response.json()["current"]
            return {
                "city": location["name"],
                "country": location.get("country", ""),
                "temperature_celsius": current.get("temperature_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "condition_code": current.get("weather_code"),
                "timestamp": current.get("time"),
            }
    except Exception as e:
        return {"error": str(e)}


def search_wikipedia(query: str, language: str = "it") -> dict[str, Any]:
    try:
        with httpx.Client(timeout=10.0) as client:
            search_response = client.get(
                f"https://{language}.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "srlimit": 1, "format": "json"},
            )
            results = search_response.json()["query"]["search"]
            if not results:
                return {"error": f"Nessun risultato per '{query}'"}
            title = results[0]["title"]
            summary_response = client.get(f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}")
            summary_data = summary_response.json()
            return {
                "title": summary_data.get("title"),
                "extract": summary_data.get("extract", "")[:1000],
                "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "last_modified": summary_data.get("timestamp", ""),
            }
    except Exception as e:
        return {"error": str(e)}


TOOL_REGISTRY = {
    "calculator": {
        "function": calculator,
        "schema": {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Valuta espressioni matematiche.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Espressione matematica"}
                    },
                    "required": ["expression"],
                },
            },
        },
    },
    "get_weather": {
        "function": get_weather,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Recupera le condizioni meteo attuali per una città.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "Nome città"}},
                    "required": ["city"],
                },
            },
        },
    },
    "search_wikipedia": {
        "function": search_wikipedia,
        "schema": {
            "type": "function",
            "function": {
                "name": "search_wikipedia",
                "description": "Cerca un argomento su Wikipedia.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Argomento da cercare"},
                        "language": {"type": "string", "description": "Lingua", "default": "it"},
                    },
                    "required": ["query"],
                },
            },
        },
    },
}
