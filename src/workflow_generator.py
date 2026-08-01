"""
LLM-powered n8n workflow generator.

Supports OpenAI (GPT-4o with JSON mode), Anthropic (Claude), and any
OpenAI-compatible provider (OpenRouter, Grok/xAI, Gemini, DeepSeek, Kimi/Moonshot).
Uses structured prompting + validation + auto-fix for reliable JSON output.
"""

import json
import time
import uuid
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import LLM_PROVIDERS, settings
from src.node_templates import build_node_reference_json
from src.workflow_validator import auto_fix_workflow, validate_workflow

# ── System Prompt ─────────────────────────────────────────────────────────────

_NODE_REFERENCE = json.dumps(build_node_reference_json(), indent=2)

SYSTEM_PROMPT = f"""You are an expert n8n workflow engineer. Your ONLY job is to output valid n8n workflow JSON objects based on the user's natural language description.

## CRITICAL RULES
1. Output ONLY a raw JSON object — no markdown, no explanation, no code fences
2. Every field in the JSON must be valid and correctly typed
3. Node IDs must be unique UUIDs (use uuid4 format)
4. Connections must reference EXACT node names — case-sensitive
5. position must be [x, y] as integers, spaced 200px apart horizontally (start at [250,300])
6. Every workflow MUST have at least one trigger node

## n8n Workflow JSON Structure
{{
  "name": "Descriptive Workflow Name",
  "nodes": [
    {{
      "id": "unique-uuid-string",
      "name": "Exact Node Name",
      "type": "n8n-nodes-base.nodeTypeName",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {{ ... }},
      "disabled": false
    }}
  ],
  "connections": {{
    "Source Node Name": {{
      "main": [[{{"node": "Target Node Name", "type": "main", "index": 0}}]]
    }}
  }},
  "pinData": {{}},
  "versionId": "unique-uuid",
  "active": false,
  "settings": {{"executionOrder": "v1"}},
  "tags": [],
  "staticData": null
}}

## Available Node Types & Default Parameters
{_NODE_REFERENCE}

## Schedule Trigger Cron Examples
- Every day at 9am:  {{"rule": {{"interval": [{{"field": "cronExpression", "expression": "0 9 * * *"}}]}}}}
- Every hour:        {{"rule": {{"interval": [{{"field": "hours", "hoursInterval": 1}}]}}}}
- Every 30 minutes:  {{"rule": {{"interval": [{{"field": "minutes", "minutesInterval": 30}}]}}}}
- Every Monday 8am:  {{"rule": {{"interval": [{{"field": "cronExpression", "expression": "0 8 * * 1"}}]}}}}
- Every weekday:     {{"rule": {{"interval": [{{"field": "cronExpression", "expression": "0 9 * * 1-5"}}]}}}}

## Set Node (typeVersion 3) — Use for data transformation
parameters must use "assignments" structure:
{{
  "mode": "manual",
  "assignments": {{
    "assignments": [
      {{"id": "1", "name": "fieldName", "value": "={{ $json.sourceField }}", "type": "string"}}
    ]
  }},
  "options": {{}}
}}

## Code Node (typeVersion 2) — JavaScript
{{
  "jsCode": "// items is the input array\\nreturn items.map(item => ({{ json: {{ ...item.json }} }}));"
}}

## Connection Rule
Every node except the LAST in the chain must appear as a source in connections.
Connections must be chained: Trigger → Action1 → Action2 → ... → Final

## Common Workflow Patterns

### Crypto Price Alert (Schedule → HTTP → Set → Telegram)
1. scheduleTrigger: cron "0 * * * *" (hourly)
2. httpRequest: GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd
3. set: create message field with price data
4. telegram: send message to chat

### Email Notifier (Schedule → HTTP → Code → emailSend)
1. scheduleTrigger: daily cron
2. httpRequest: fetch data from API
3. code: format email body
4. emailSend: send formatted email

### Webhook Handler (webhook → code → respondToWebhook)
1. webhook: POST /webhook-path
2. code: process incoming data
3. respondToWebhook: return result

### AI Chat (chatTrigger → openAi → respondToWebhook)
1. chatTrigger
2. openAi: gpt-4o model
3. respondToWebhook: return AI response

Now generate the workflow JSON for the user's request. Output ONLY the JSON object.
"""

# ── OpenAI Generator ──────────────────────────────────────────────────────────


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,  # surface the provider's real error, not RetryError[<Future ...>]
)
async def _generate_openai(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> tuple[dict[str, Any], int]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Create an n8n workflow for: {prompt}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=max_tokens,
    )

    raw = response.choices[0].message.content or "{}"
    tokens = response.usage.total_tokens if response.usage else 0
    return json.loads(raw), tokens


# ── Anthropic Generator ───────────────────────────────────────────────────────


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,  # surface the provider's real error, not RetryError[<Future ...>]
)
async def _generate_anthropic(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> tuple[dict[str, Any], int]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_message = (
        f"Create an n8n workflow for: {prompt}\n\n"
        "Output ONLY the JSON object — no markdown, no explanation, no code fences."
    )

    response = await client.messages.create(
        model=model,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    raw_content = response.content[0].text if response.content else "{}"
    raw_content = _extract_json_from_text(raw_content)
    tokens = response.usage.input_tokens + response.usage.output_tokens

    return json.loads(raw_content), tokens


# ── OpenAI-Compatible Generator ───────────────────────────────────────────────
# OpenRouter, Grok (xAI), Gemini, DeepSeek and Kimi/Moonshot all expose the
# OpenAI Chat Completions API; they differ only by base_url, key and model.
# We avoid response_format=json_object here since not every provider supports
# it, and instead rely on the strict system prompt + text extraction.


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,  # surface the provider's real error, not RetryError[<Future ...>]
)
async def _generate_openai_compat(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    base_url: str,
    api_key: str,
) -> tuple[dict[str, Any], int]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    user_message = (
        f"Create an n8n workflow for: {prompt}\n\n"
        "Output ONLY the JSON object — no markdown, no explanation, no code fences."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    raw = response.choices[0].message.content or "{}"
    raw = _extract_json_from_text(raw)
    tokens = response.usage.total_tokens if response.usage else 0
    return json.loads(raw), tokens


def _extract_json_from_text(text: str) -> str:
    """Extract JSON object from text that may contain markdown code fences."""
    text = text.strip()
    if text.startswith("{"):
        return text

    # Strip ```json ... ``` or ``` ... ```
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return text[start:end]

    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end]

    return text


# ── Main Generator ────────────────────────────────────────────────────────────


async def generate_workflow(
    prompt: str,
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    """
    Generate a complete n8n workflow JSON from a natural language prompt.

    Returns a dict with keys: workflow_json, llm_provider, llm_model, tokens_used, latency_ms
    Raises ValueError if generation or validation fails after retries.
    """
    provider = llm_provider or settings.llm_provider

    meta = LLM_PROVIDERS.get(provider)
    if not meta:
        raise ValueError(f"Unknown LLM provider: '{provider}'")

    # Pick a model: explicit arg wins; else reuse the configured model only when
    # it belongs to the active provider; otherwise fall back to the provider default.
    if llm_model:
        model = llm_model
    elif provider == settings.llm_provider and settings.llm_model:
        model = settings.llm_model
    else:
        model = meta["default_model"]

    temperature = settings.llm_temperature
    max_tokens = settings.llm_max_tokens

    # Fail fast (and clearly) on a missing key rather than burning three
    # retries on an SDK error nobody can read.
    api_key = settings.api_key_for(provider)
    if not api_key:
        raise ValueError(
            f"No API key configured for provider '{meta['label']}'. "
            f"Add it in Settings, or set {meta['key_attr'].upper()} in .env."
        )

    t_start = time.perf_counter()

    try:
        if provider == "openai":
            workflow_json, tokens = await _generate_openai(
                prompt, model, temperature, max_tokens
            )
        elif provider == "anthropic":
            workflow_json, tokens = await _generate_anthropic(
                prompt, model, temperature, max_tokens
            )
        else:
            workflow_json, tokens = await _generate_openai_compat(
                prompt, model, temperature, max_tokens, meta["base_url"], api_key
            )
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"LLM generation failed: {exc}") from exc

    latency_ms = (time.perf_counter() - t_start) * 1000

    # Auto-fix common structural issues before validation
    workflow_json = auto_fix_workflow(workflow_json)

    # Ensure the workflow has a name
    if not workflow_json.get("name"):
        workflow_json["name"] = _derive_name_from_prompt(prompt)

    # Validate
    result = validate_workflow(workflow_json)
    if not result.valid:
        error_summary = "; ".join(result.errors[:5])
        raise ValueError(
            f"Generated workflow failed validation ({len(result.errors)} errors): {error_summary}"
        )

    return {
        "workflow_json": workflow_json,
        "llm_provider": provider,
        "llm_model": model,
        "tokens_used": tokens,
        "latency_ms": latency_ms,
    }


def _derive_name_from_prompt(prompt: str) -> str:
    """Create a short workflow name from the prompt."""
    words = prompt.strip().split()[:6]
    name = " ".join(words)
    if len(name) > 60:
        name = name[:57] + "..."
    return name.title() if name else "Generated Workflow"


def build_minimal_workflow(name: str, description: str = "") -> dict[str, Any]:
    """Build a minimal valid n8n workflow skeleton (no LLM needed)."""
    trigger_id = str(uuid.uuid4())
    return {
        "name": name,
        "nodes": [
            {
                "id": trigger_id,
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {},
                "disabled": False,
            }
        ],
        "connections": {},
        "pinData": {},
        "versionId": str(uuid.uuid4()),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "staticData": None,
    }
