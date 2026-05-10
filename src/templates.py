"""
Pre-built n8n workflow templates — no LLM required.
These are complete, deployment-ready workflow JSON definitions.
"""

import uuid
from typing import Any


def _uid() -> str:
    return str(uuid.uuid4())


def _build_crypto_price_alert() -> dict[str, Any]:
    trigger_name = "Schedule Trigger"
    http_name = "Fetch Crypto Prices"
    set_name = "Format Message"
    telegram_name = "Send to Telegram"

    return {
        "name": "Crypto Price Alert",
        "nodes": [
            {
                "id": _uid(),
                "name": trigger_name,
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": "0 * * * *"}
                        ]
                    }
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": http_name,
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [450, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
                    "authentication": "none",
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": set_name,
                "type": "n8n-nodes-base.set",
                "typeVersion": 3,
                "position": [650, 300],
                "parameters": {
                    "mode": "manual",
                    "assignments": {
                        "assignments": [
                            {
                                "id": "1",
                                "name": "message",
                                "value": "={{ '🚀 Crypto Update\\nBTC: $' + $json.bitcoin.usd + '\\nETH: $' + $json.ethereum.usd }}",
                                "type": "string",
                            }
                        ]
                    },
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": telegram_name,
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1,
                "position": [850, 300],
                "parameters": {
                    "resource": "message",
                    "operation": "sendMessage",
                    "chatId": "YOUR_CHAT_ID",
                    "text": "={{ $json.message }}",
                    "additionalFields": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            trigger_name: {
                "main": [[{"node": http_name, "type": "main", "index": 0}]]
            },
            http_name: {
                "main": [[{"node": set_name, "type": "main", "index": 0}]]
            },
            set_name: {
                "main": [[{"node": telegram_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["crypto", "telegram", "alert"],
        "staticData": None,
    }


def _build_email_to_notion() -> dict[str, Any]:
    email_name = "Read Email"
    set_name = "Extract Data"
    notion_name = "Append to Notion"

    return {
        "name": "Email to Notion",
        "nodes": [
            {
                "id": _uid(),
                "name": email_name,
                "type": "n8n-nodes-base.emailReadImap",
                "typeVersion": 2,
                "position": [250, 300],
                "parameters": {
                    "mailbox": "INBOX",
                    "action": "read",
                    "options": {"allowUnauthorizedCerts": False},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": set_name,
                "type": "n8n-nodes-base.set",
                "typeVersion": 3,
                "position": [450, 300],
                "parameters": {
                    "mode": "manual",
                    "assignments": {
                        "assignments": [
                            {
                                "id": "1",
                                "name": "title",
                                "value": "={{ $json.subject }}",
                                "type": "string",
                            },
                            {
                                "id": "2",
                                "name": "content",
                                "value": "={{ $json.text }}",
                                "type": "string",
                            },
                            {
                                "id": "3",
                                "name": "from",
                                "value": "={{ $json.from.value[0].address }}",
                                "type": "string",
                            },
                        ]
                    },
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": notion_name,
                "type": "n8n-nodes-base.notion",
                "typeVersion": 2,
                "position": [650, 300],
                "parameters": {
                    "resource": "databasePage",
                    "operation": "create",
                    "databaseId": {
                        "__rl": True,
                        "value": "YOUR_DATABASE_ID",
                        "mode": "id",
                    },
                    "title": "={{ $json.title }}",
                    "propertiesUi": {"propertyValues": []},
                },
                "disabled": False,
            },
        ],
        "connections": {
            email_name: {
                "main": [[{"node": set_name, "type": "main", "index": 0}]]
            },
            set_name: {
                "main": [[{"node": notion_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["email", "notion", "productivity"],
        "staticData": None,
    }


def _build_daily_report() -> dict[str, Any]:
    trigger_name = "Daily Schedule"
    http_name = "Fetch Report Data"
    code_name = "Format Report"
    email_name = "Send Report Email"

    return {
        "name": "Daily Report Email",
        "nodes": [
            {
                "id": _uid(),
                "name": trigger_name,
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": "0 8 * * 1-5"}
                        ]
                    }
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": http_name,
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [450, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://api.example.com/daily-stats",
                    "authentication": "none",
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": code_name,
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [650, 300],
                "parameters": {
                    "jsCode": (
                        "const data = items[0].json;\n"
                        "const date = new Date().toLocaleDateString('en-US', {weekday:'long', year:'numeric', month:'long', day:'numeric'});\n"
                        "const body = `<h2>Daily Report — ${date}</h2>`\n"
                        "  + `<p>Total: ${data.total || 'N/A'}</p>`\n"
                        "  + `<p>Active: ${data.active || 'N/A'}</p>`;\n"
                        "return [{json: {subject: `Daily Report — ${date}`, body}}];"
                    )
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": email_name,
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2,
                "position": [850, 300],
                "parameters": {
                    "fromEmail": "reports@example.com",
                    "toEmail": "team@example.com",
                    "subject": "={{ $json.subject }}",
                    "emailFormat": "html",
                    "message": "={{ $json.body }}",
                    "options": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            trigger_name: {
                "main": [[{"node": http_name, "type": "main", "index": 0}]]
            },
            http_name: {
                "main": [[{"node": code_name, "type": "main", "index": 0}]]
            },
            code_name: {
                "main": [[{"node": email_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["report", "email", "daily"],
        "staticData": None,
    }


def _build_webhook_to_discord() -> dict[str, Any]:
    webhook_name = "Incoming Webhook"
    code_name = "Transform Payload"
    discord_name = "Post to Discord"

    return {
        "name": "Webhook to Discord",
        "nodes": [
            {
                "id": _uid(),
                "name": webhook_name,
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "discord-notify",
                    "responseMode": "onReceived",
                    "options": {},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": code_name,
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [450, 300],
                "parameters": {
                    "jsCode": (
                        "const body = items[0].json.body || items[0].json;\n"
                        "const message = body.message || JSON.stringify(body, null, 2);\n"
                        "const title = body.title || 'Notification';\n"
                        "return [{json: {content: `**${title}**\\n${message}`}}];"
                    )
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": discord_name,
                "type": "n8n-nodes-base.discord",
                "typeVersion": 2,
                "position": [650, 300],
                "parameters": {
                    "resource": "message",
                    "operation": "send",
                    "webhookUri": "YOUR_DISCORD_WEBHOOK_URL",
                    "content": "={{ $json.content }}",
                    "username": "n8n Bot",
                },
                "disabled": False,
            },
        ],
        "connections": {
            webhook_name: {
                "main": [[{"node": code_name, "type": "main", "index": 0}]]
            },
            code_name: {
                "main": [[{"node": discord_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["webhook", "discord", "notification"],
        "staticData": None,
    }


def _build_rss_to_email() -> dict[str, Any]:
    trigger_name = "Daily RSS Schedule"
    http_name = "Fetch RSS Feed"
    code_name = "Parse RSS Items"
    email_name = "Email Newsletter"

    return {
        "name": "RSS Feed to Email",
        "nodes": [
            {
                "id": _uid(),
                "name": trigger_name,
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": "0 7 * * *"}
                        ]
                    }
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": http_name,
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [450, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://feeds.bbci.co.uk/news/rss.xml",
                    "authentication": "none",
                    "options": {"response": {"response": {"responseFormat": "text"}}},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": code_name,
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [650, 300],
                "parameters": {
                    "jsCode": (
                        "const xml = items[0].json.data || '';\n"
                        "// Simple RSS item extraction\n"
                        "const titles = [...xml.matchAll(/<title><![CDATA[(.*?)]]><\\/title>/gs)].slice(1, 6).map(m => m[1]);\n"
                        "const links = [...xml.matchAll(/<link>(https?.*?)<\\/link>/g)].slice(0, 5).map(m => m[1]);\n"
                        "let body = '<h2>Today\\'s Top News</h2><ul>';\n"
                        "titles.forEach((t, i) => { body += `<li><a href='${links[i] || '#'}'>${t}</a></li>`; });\n"
                        "body += '</ul>';\n"
                        "return [{json: {subject: 'Daily News Digest', body}}];"
                    )
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": email_name,
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2,
                "position": [850, 300],
                "parameters": {
                    "fromEmail": "news@example.com",
                    "toEmail": "subscriber@example.com",
                    "subject": "={{ $json.subject }}",
                    "emailFormat": "html",
                    "message": "={{ $json.body }}",
                    "options": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            trigger_name: {
                "main": [[{"node": http_name, "type": "main", "index": 0}]]
            },
            http_name: {
                "main": [[{"node": code_name, "type": "main", "index": 0}]]
            },
            code_name: {
                "main": [[{"node": email_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["rss", "email", "news"],
        "staticData": None,
    }


def _build_ai_chat() -> dict[str, Any]:
    chat_name = "Chat Trigger"
    ai_name = "OpenAI Response"
    respond_name = "Respond to Webhook"

    return {
        "name": "AI Chat Simple",
        "nodes": [
            {
                "id": _uid(),
                "name": chat_name,
                "type": "n8n-nodes-base.chatTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {"mode": "webhook", "options": {}},
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": ai_name,
                "type": "n8n-nodes-base.openAi",
                "typeVersion": 1,
                "position": [450, 300],
                "parameters": {
                    "resource": "text",
                    "operation": "message",
                    "modelId": {"__rl": True, "value": "gpt-4o", "mode": "list"},
                    "messages": {
                        "values": [
                            {
                                "content": "={{ $json.chatInput }}",
                                "role": "user",
                            }
                        ]
                    },
                    "options": {"temperature": 0.7},
                },
                "disabled": False,
            },
            {
                "id": _uid(),
                "name": respond_name,
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1,
                "position": [650, 300],
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify({output: $json.message.content}) }}",
                    "options": {},
                },
                "disabled": False,
            },
        ],
        "connections": {
            chat_name: {
                "main": [[{"node": ai_name, "type": "main", "index": 0}]]
            },
            ai_name: {
                "main": [[{"node": respond_name, "type": "main", "index": 0}]]
            },
        },
        "pinData": {},
        "versionId": _uid(),
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": ["ai", "chat", "openai"],
        "staticData": None,
    }


BUILTIN_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Crypto Price Alert",
        "description": "Fetch Bitcoin & Ethereum prices from CoinGecko every hour and send to Telegram.",
        "category": "crypto",
        "tags": ["crypto", "telegram", "schedule", "alert"],
        "workflow": _build_crypto_price_alert(),
    },
    {
        "name": "Email to Notion",
        "description": "Read incoming emails via IMAP and append them as pages in a Notion database.",
        "category": "productivity",
        "tags": ["email", "notion", "imap", "productivity"],
        "workflow": _build_email_to_notion(),
    },
    {
        "name": "Daily Report Email",
        "description": "Every weekday at 8am, fetch stats from an API, format them, and email a report.",
        "category": "reporting",
        "tags": ["report", "email", "schedule", "daily"],
        "workflow": _build_daily_report(),
    },
    {
        "name": "Webhook to Discord",
        "description": "Receive POST webhook payloads and forward formatted messages to a Discord channel.",
        "category": "notifications",
        "tags": ["webhook", "discord", "notification"],
        "workflow": _build_webhook_to_discord(),
    },
    {
        "name": "RSS Feed to Email",
        "description": "Every morning at 7am, fetch an RSS feed and email a digest of top stories.",
        "category": "news",
        "tags": ["rss", "email", "news", "digest"],
        "workflow": _build_rss_to_email(),
    },
    {
        "name": "AI Chat Simple",
        "description": "Accept chat messages via webhook, process them through OpenAI GPT-4o, and respond.",
        "category": "ai",
        "tags": ["ai", "chat", "openai", "webhook"],
        "workflow": _build_ai_chat(),
    },
]
