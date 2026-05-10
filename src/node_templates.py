"""
Complete n8n node templates — every node type the agent knows about.

Each entry defines:
  type         — the n8n node type string
  typeVersion  — the version of the node
  parameters   — default / example parameters
  description  — human-readable purpose
  icon         — emoji icon for UI display
"""

from typing import Any

NODE_TEMPLATES: dict[str, dict[str, Any]] = {
    # ── Triggers ──────────────────────────────────────────────────────────────
    "start": {
        "type": "n8n-nodes-base.start",
        "typeVersion": 1,
        "description": "Manual trigger — starts the workflow when executed manually",
        "icon": "▶️",
        "parameters": {},
        "example_names": ["Start", "Manual Trigger"],
    },
    "webhook": {
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 1,
        "description": "HTTP Webhook trigger — starts workflow on incoming HTTP request",
        "icon": "🌐",
        "parameters": {
            "httpMethod": "POST",
            "path": "webhook",
            "responseMode": "onReceived",
            "options": {},
        },
        "example_names": ["Webhook", "HTTP Trigger", "Incoming Request"],
    },
    "scheduleTrigger": {
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1,
        "description": "Schedule trigger — runs workflow on cron or interval basis",
        "icon": "⏰",
        "parameters": {
            "rule": {
                "interval": [
                    {
                        "field": "cronExpression",
                        "expression": "0 9 * * *",
                    }
                ]
            }
        },
        "variants": {
            "daily_9am": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
                }
            },
            "hourly": {
                "rule": {
                    "interval": [{"field": "hours", "hoursInterval": 1}]
                }
            },
            "every_5_minutes": {
                "rule": {
                    "interval": [{"field": "minutes", "minutesInterval": 5}]
                }
            },
            "weekly_monday": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 9 * * 1"}]
                }
            },
            "custom_cron": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 0 * * *"}]
                }
            },
        },
        "example_names": ["Schedule", "Cron Trigger", "Daily Trigger"],
    },
    "chatTrigger": {
        "type": "n8n-nodes-base.chatTrigger",
        "typeVersion": 1,
        "description": "Chat trigger — receives messages from n8n chat interface",
        "icon": "💬",
        "parameters": {
            "mode": "webhook",
            "options": {},
        },
        "example_names": ["Chat Trigger", "Chat Input"],
    },
    # ── HTTP & Networking ─────────────────────────────────────────────────────
    "httpRequest": {
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4,
        "description": "Make HTTP requests to any API or URL",
        "icon": "🌍",
        "parameters": {
            "method": "GET",
            "url": "https://api.example.com/data",
            "authentication": "none",
            "sendBody": False,
            "sendHeaders": False,
            "sendQuery": False,
            "options": {},
        },
        "variants": {
            "get_json": {
                "method": "GET",
                "url": "",
                "authentication": "none",
                "options": {"response": {"response": {"responseFormat": "json"}}},
            },
            "post_json": {
                "method": "POST",
                "url": "",
                "sendBody": True,
                "contentType": "json",
                "body": "{}",
                "options": {},
            },
            "coingecko_bitcoin": {
                "method": "GET",
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                "authentication": "none",
                "options": {},
            },
            "coingecko_multi": {
                "method": "GET",
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd",
                "authentication": "none",
                "options": {},
            },
        },
        "example_names": ["HTTP Request", "Fetch Data", "API Call", "Get Price"],
    },
    # ── Logic & Control Flow ──────────────────────────────────────────────────
    "if": {
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "description": "Conditional branch — route data based on conditions",
        "icon": "🔀",
        "parameters": {
            "conditions": {
                "string": [
                    {
                        "value1": "={{ $json.status }}",
                        "operation": "equal",
                        "value2": "success",
                    }
                ]
            }
        },
        "example_names": ["IF", "Check Condition", "Route"],
    },
    "switch": {
        "type": "n8n-nodes-base.switch",
        "typeVersion": 1,
        "description": "Multi-branch switch — route to one of multiple outputs",
        "icon": "⚡",
        "parameters": {
            "dataType": "string",
            "value1": "={{ $json.type }}",
            "rules": {
                "rules": [
                    {"value2": "option1"},
                    {"value2": "option2"},
                ]
            },
            "fallbackOutput": 3,
        },
        "example_names": ["Switch", "Route By Type"],
    },
    "code": {
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "description": "Run custom JavaScript code to transform data",
        "icon": "💻",
        "parameters": {
            "jsCode": "// Transform input items\nreturn items.map(item => ({\n  json: {\n    ...item.json,\n    processed: true,\n    timestamp: new Date().toISOString()\n  }\n}));",
        },
        "variants": {
            "format_message": {
                "jsCode": "const data = items[0].json;\nreturn [{\n  json: {\n    message: `Price: $${data.price}`,\n    timestamp: new Date().toISOString()\n  }\n}];",
            },
            "extract_fields": {
                "jsCode": "return items.map(item => ({\n  json: {\n    id: item.json.id,\n    name: item.json.name,\n    value: item.json.value\n  }\n}));",
            },
            "rss_parse": {
                "jsCode": "return items.map(item => ({\n  json: {\n    title: item.json.title,\n    link: item.json.link,\n    pubDate: item.json.pubDate,\n    description: item.json.contentSnippet || item.json.content\n  }\n}));",
            },
        },
        "example_names": ["Code", "Transform", "Format", "Parse"],
    },
    "wait": {
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1,
        "description": "Pause workflow execution for a specified duration",
        "icon": "⏳",
        "parameters": {
            "resume": "after",
            "amount": 1,
            "unit": "hours",
        },
        "example_names": ["Wait", "Delay", "Pause"],
    },
    "splitInBatches": {
        "type": "n8n-nodes-base.splitInBatches",
        "typeVersion": 3,
        "description": "Split items into batches for processing",
        "icon": "📦",
        "parameters": {
            "batchSize": 10,
            "options": {},
        },
        "example_names": ["Split In Batches", "Batch", "Chunk"],
    },
    "merge": {
        "type": "n8n-nodes-base.merge",
        "typeVersion": 2,
        "description": "Merge data from multiple branches",
        "icon": "🔗",
        "parameters": {
            "mode": "combine",
            "combinationMode": "mergeByPosition",
            "options": {},
        },
        "example_names": ["Merge", "Combine", "Join"],
    },
    "set": {
        "type": "n8n-nodes-base.set",
        "typeVersion": 3,
        "description": "Set or transform data fields",
        "icon": "📝",
        "parameters": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {
                "assignments": [
                    {
                        "id": "assignment-1",
                        "name": "field_name",
                        "value": "={{ $json.source_field }}",
                        "type": "string",
                    }
                ]
            },
            "options": {},
        },
        "variants": {
            "format_crypto_message": {
                "mode": "manual",
                "assignments": {
                    "assignments": [
                        {
                            "id": "1",
                            "name": "message",
                            "value": "={{ 'Bitcoin: $' + $json.bitcoin.usd + ' USD' }}",
                            "type": "string",
                        },
                        {
                            "id": "2",
                            "name": "timestamp",
                            "value": "={{ $now.toISO() }}",
                            "type": "string",
                        },
                    ]
                },
                "options": {},
            },
        },
        "example_names": ["Set", "Set Fields", "Format Data", "Transform"],
    },
    # ── Messaging & Notifications ─────────────────────────────────────────────
    "telegram": {
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1,
        "description": "Send messages or media via Telegram Bot API",
        "icon": "📱",
        "parameters": {
            "resource": "message",
            "operation": "sendMessage",
            "chatId": "={{ $json.chatId }}",
            "text": "={{ $json.message }}",
            "additionalFields": {},
        },
        "example_names": ["Telegram", "Send Telegram", "Telegram Message"],
    },
    "slack": {
        "type": "n8n-nodes-base.slack",
        "typeVersion": 2,
        "description": "Post messages or interact with Slack channels",
        "icon": "💬",
        "parameters": {
            "resource": "message",
            "operation": "post",
            "select": "channel",
            "channelId": {
                "__rl": True,
                "value": "#general",
                "mode": "name",
            },
            "text": "={{ $json.message }}",
            "otherOptions": {},
        },
        "example_names": ["Slack", "Send to Slack", "Slack Message"],
    },
    "discord": {
        "type": "n8n-nodes-base.discord",
        "typeVersion": 2,
        "description": "Send messages to Discord via webhook or bot",
        "icon": "🎮",
        "parameters": {
            "resource": "message",
            "operation": "send",
            "webhookUri": "={{ $json.webhookUrl }}",
            "content": "={{ $json.message }}",
            "username": "n8n Bot",
        },
        "example_names": ["Discord", "Discord Message", "Send to Discord"],
    },
    "emailSend": {
        "type": "n8n-nodes-base.emailSend",
        "typeVersion": 2,
        "description": "Send emails via SMTP",
        "icon": "📧",
        "parameters": {
            "fromEmail": "noreply@example.com",
            "toEmail": "recipient@example.com",
            "subject": "Automated Email from n8n",
            "emailFormat": "html",
            "message": "<p>{{ $json.message }}</p>",
            "options": {},
        },
        "example_names": ["Send Email", "Email", "SMTP Send"],
    },
    "emailReceive": {
        "type": "n8n-nodes-base.emailReadImap",
        "typeVersion": 2,
        "description": "Read emails from IMAP mailbox",
        "icon": "📬",
        "parameters": {
            "mailbox": "INBOX",
            "action": "read",
            "options": {
                "allowUnauthorizedCerts": False,
            },
        },
        "example_names": ["Email Trigger", "Read Email", "IMAP"],
    },
    # ── Apps & Integrations ───────────────────────────────────────────────────
    "notion": {
        "type": "n8n-nodes-base.notion",
        "typeVersion": 2,
        "description": "Create and update pages in Notion databases",
        "icon": "📓",
        "parameters": {
            "resource": "databasePage",
            "operation": "create",
            "databaseId": {
                "__rl": True,
                "value": "your-database-id",
                "mode": "id",
            },
            "title": "={{ $json.title }}",
            "propertiesUi": {
                "propertyValues": []
            },
        },
        "example_names": ["Notion", "Notion Page", "Create Notion Entry"],
    },
    "googleSheets": {
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4,
        "description": "Read from and write to Google Sheets",
        "icon": "📊",
        "parameters": {
            "resource": "sheet",
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": "your-spreadsheet-id",
                "mode": "id",
            },
            "sheetName": {
                "__rl": True,
                "value": "Sheet1",
                "mode": "name",
            },
            "columns": {
                "mappingMode": "defineBelow",
                "value": {},
                "matchingColumns": [],
            },
        },
        "example_names": ["Google Sheets", "Sheets", "Append to Sheets"],
    },
    "openAi": {
        "type": "n8n-nodes-base.openAi",
        "typeVersion": 1,
        "description": "Make requests to OpenAI API for text generation",
        "icon": "🤖",
        "parameters": {
            "resource": "text",
            "operation": "message",
            "modelId": {
                "__rl": True,
                "value": "gpt-4o",
                "mode": "list",
            },
            "messages": {
                "values": [
                    {
                        "content": "={{ $json.prompt }}",
                        "role": "user",
                    }
                ]
            },
            "options": {
                "temperature": 0.7,
            },
        },
        "example_names": ["OpenAI", "GPT", "AI Response", "ChatGPT"],
    },
    "respondToWebhook": {
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1,
        "description": "Send a response back to the webhook caller",
        "icon": "↩️",
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify($json) }}",
            "options": {},
        },
        "example_names": ["Respond to Webhook", "Webhook Response", "Return Response"],
    },
}

# Node type string → template key mapping for LLM reference
NODE_TYPE_MAP: dict[str, str] = {
    "n8n-nodes-base.start": "start",
    "n8n-nodes-base.webhook": "webhook",
    "n8n-nodes-base.scheduleTrigger": "scheduleTrigger",
    "n8n-nodes-base.chatTrigger": "chatTrigger",
    "n8n-nodes-base.httpRequest": "httpRequest",
    "n8n-nodes-base.if": "if",
    "n8n-nodes-base.switch": "switch",
    "n8n-nodes-base.code": "code",
    "n8n-nodes-base.wait": "wait",
    "n8n-nodes-base.splitInBatches": "splitInBatches",
    "n8n-nodes-base.merge": "merge",
    "n8n-nodes-base.set": "set",
    "n8n-nodes-base.telegram": "telegram",
    "n8n-nodes-base.slack": "slack",
    "n8n-nodes-base.discord": "discord",
    "n8n-nodes-base.emailSend": "emailSend",
    "n8n-nodes-base.emailReadImap": "emailReceive",
    "n8n-nodes-base.notion": "notion",
    "n8n-nodes-base.googleSheets": "googleSheets",
    "n8n-nodes-base.openAi": "openAi",
    "n8n-nodes-base.respondToWebhook": "respondToWebhook",
}

# Node icons for UI display
NODE_ICONS: dict[str, str] = {k: v["icon"] for k, v in NODE_TEMPLATES.items()}


def get_node_template(template_key: str) -> dict[str, Any] | None:
    return NODE_TEMPLATES.get(template_key)


def get_node_type_description() -> str:
    """Build a compact reference string for the LLM system prompt."""
    lines: list[str] = []
    for key, tpl in NODE_TEMPLATES.items():
        node_type = tpl["type"]
        desc = tpl["description"]
        params_preview = str(tpl["parameters"])[:120].rstrip() + "..."
        lines.append(f"- {node_type} (key={key}): {desc}")
        lines.append(f"  Default params: {params_preview}")
    return "\n".join(lines)


def build_node_reference_json() -> dict[str, Any]:
    """Compact node reference for embedding in LLM prompts."""
    reference: dict[str, Any] = {}
    for key, tpl in NODE_TEMPLATES.items():
        reference[tpl["type"]] = {
            "typeVersion": tpl["typeVersion"],
            "defaultParameters": tpl["parameters"],
            "description": tpl["description"],
        }
    return reference
