"""
App Registry - defines every available app, its triggers and actions.
This is the equivalent of Zapier's app directory.
"""

APP_REGISTRY = {
    "resume_screener": {
        "name": "Resume Screener",
        "icon": "📄",
        "category": "HR",
        "description": "Upload a resume, analyze candidate fit, and generate a summary",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "analyze_resume": {
                "label": "Analyze Resume",
                "fields": [
                    {"key": "resume_text", "label": "Resume Text", "type": "textarea", "required": True},
                    {"key": "job_title", "label": "Job Title", "type": "text"},
                    {"key": "job_description", "label": "Job Description", "type": "textarea"}
                ]
            },
        }
    },
    # ─── Email ────────────────────────────────────────────────────────────────
    "gmail": {
        "name": "Gmail",
        "icon": "📧",
        "category": "Email",
        "description": "Send and receive emails via Gmail",
        "auth_type": "oauth2_fields",  # simulate with app password / API key fields
        "credential_fields": [
            {"key": "email", "label": "Gmail Address", "type": "text"},
            {"key": "app_password", "label": "App Password", "type": "password",
             "help": "Generate at myaccount.google.com/apppasswords"},
        ],
        "triggers": {
            "new_email": {"label": "New Email", "description": "Fires when a new email arrives matching filters",
                          "fields": [{"key": "from_filter", "label": "From (optional)", "type": "text"},
                                     {"key": "subject_filter", "label": "Subject contains", "type": "text"},
                                     {"key": "label_filter", "label": "Label", "type": "text", "default": "INBOX"}]},
        },
        "actions": {
            "send_email": {"label": "Send Email", "description": "Send an email",
                           "fields": [{"key": "to", "label": "To", "type": "text", "required": True},
                                      {"key": "subject", "label": "Subject", "type": "text", "required": True},
                                      {"key": "body", "label": "Body", "type": "textarea", "required": True},
                                      {"key": "cc", "label": "CC", "type": "text"},
                                      {"key": "bcc", "label": "BCC", "type": "text"},
                                      {"key": "is_html", "label": "Send as HTML", "type": "boolean", "default": False}]},
            "find_email": {"label": "Find Email", "description": "Search for an email",
                           "fields": [{"key": "query", "label": "Search Query", "type": "text", "required": True}]},
            "create_draft": {"label": "Create Draft", "description": "Create an email draft",
                             "fields": [{"key": "to", "label": "To", "type": "text"},
                                        {"key": "subject", "label": "Subject", "type": "text"},
                                        {"key": "body", "label": "Body", "type": "textarea"}]},
        }
    },

    # ─── Slack ────────────────────────────────────────────────────────────────
    "slack": {
        "name": "Slack",
        "icon": "💬",
        "category": "Team Chat",
        "description": "Send messages and manage channels in Slack",
        "auth_type": "token",
        "credential_fields": [
            {"key": "bot_token", "label": "Bot Token", "type": "password",
             "help": "xoxb-... token from api.slack.com/apps"},
        ],
        "triggers": {
            "new_message": {"label": "New Message in Channel",
                            "fields": [{"key": "channel", "label": "Channel", "type": "text", "required": True}]},
        },
        "actions": {
            "post_message": {"label": "Send Channel Message",
                             "fields": [{"key": "channel", "label": "Channel", "type": "text", "required": True},
                                        {"key": "text", "label": "Message Text", "type": "textarea", "required": True},
                                        {"key": "username", "label": "Bot Username", "type": "text"},
                                        {"key": "icon_emoji", "label": "Icon Emoji", "type": "text"}]},
            "send_dm": {"label": "Send Direct Message",
                        "fields": [{"key": "user_email", "label": "User Email or ID", "type": "text", "required": True},
                                   {"key": "text", "label": "Message Text", "type": "textarea", "required": True}]},
            "set_status": {"label": "Set Status",
                           "fields": [{"key": "status_text", "label": "Status Text", "type": "text"},
                                      {"key": "status_emoji", "label": "Status Emoji", "type": "text"}]},
        }
    },

    # ─── Google Sheets ────────────────────────────────────────────────────────
    "google_sheets": {
        "name": "Google Sheets",
        "icon": "📊",
        "category": "Spreadsheets",
        "description": "Read and write Google Sheets data",
        "auth_type": "service_account",
        "credential_fields": [
            {"key": "service_account_json", "label": "Service Account JSON", "type": "textarea",
             "help": "Paste your service account JSON key"},
        ],
        "triggers": {
            "new_row": {"label": "New Row Added",
                        "fields": [{"key": "spreadsheet_id", "label": "Spreadsheet ID", "type": "text", "required": True},
                                   {"key": "sheet_name", "label": "Sheet Name", "type": "text", "default": "Sheet1"},
                                   {"key": "header_row", "label": "Header Row", "type": "number", "default": 1}]},
        },
        "actions": {
            "create_spreadsheet": {"label": "Create Spreadsheet",
                                   "fields": [{"key": "title", "label": "Spreadsheet Title", "type": "text", "required": True},
                                              {"key": "sheet_name", "label": "First Sheet Name", "type": "text", "default": "Sheet1"}]},
            "append_row": {"label": "Append Row",
                           "fields": [{"key": "spreadsheet_id", "label": "Spreadsheet ID", "type": "text", "required": True},
                                      {"key": "sheet_name", "label": "Sheet Name", "type": "text", "default": "Sheet1"},
                                      {"key": "values", "label": "Row Values (JSON array)", "type": "textarea", "required": True}]},
            "update_row": {"label": "Update Row",
                           "fields": [{"key": "spreadsheet_id", "label": "Spreadsheet ID", "type": "text", "required": True},
                                      {"key": "sheet_name", "label": "Sheet Name", "type": "text"},
                                      {"key": "row_number", "label": "Row Number", "type": "number", "required": True},
                                      {"key": "values", "label": "Values (JSON)", "type": "textarea", "required": True}]},
            "lookup_row": {"label": "Lookup Row",
                           "fields": [{"key": "spreadsheet_id", "label": "Spreadsheet ID", "type": "text", "required": True},
                                      {"key": "sheet_name", "label": "Sheet Name", "type": "text"},
                                      {"key": "lookup_column", "label": "Lookup Column", "type": "text", "required": True},
                                      {"key": "lookup_value", "label": "Lookup Value", "type": "text", "required": True}]},
        }
    },

    # ─── Notion ───────────────────────────────────────────────────────────────
    "notion": {
        "name": "Notion",
        "icon": "📝",
        "category": "Productivity",
        "description": "Create and update Notion pages and database entries",
        "auth_type": "token",
        "credential_fields": [
            {"key": "api_key", "label": "Internal Integration Token", "type": "password",
             "help": "Create at notion.so/my-integrations"},
        ],
        "triggers": {
            "new_database_item": {"label": "New Database Item",
                                  "fields": [{"key": "database_id", "label": "Database ID", "type": "text", "required": True}]},
        },
        "actions": {
            "create_page": {"label": "Create Page",
                            "fields": [{"key": "parent_id", "label": "Parent Page or DB ID", "type": "text", "required": True},
                                       {"key": "title", "label": "Title", "type": "text", "required": True},
                                       {"key": "content", "label": "Content (Markdown)", "type": "textarea"},
                                       {"key": "properties", "label": "Properties (JSON)", "type": "textarea"}]},
            "append_to_page": {"label": "Append to Page",
                               "fields": [{"key": "page_id", "label": "Page ID", "type": "text", "required": True},
                                          {"key": "content", "label": "Content to Append", "type": "textarea", "required": True}]},
            "update_page": {"label": "Update Page Properties",
                            "fields": [{"key": "page_id", "label": "Page ID", "type": "text", "required": True},
                                       {"key": "properties", "label": "Properties (JSON)", "type": "textarea", "required": True}]},
        }
    },

    # ─── Airtable ─────────────────────────────────────────────────────────────
    "airtable": {
        "name": "Airtable",
        "icon": "🗃️",
        "category": "Databases",
        "description": "Manage Airtable bases, tables and records",
        "auth_type": "token",
        "credential_fields": [
            {"key": "api_key", "label": "Personal Access Token", "type": "password"},
        ],
        "triggers": {
            "new_record": {"label": "New Record",
                           "fields": [{"key": "base_id", "label": "Base ID", "type": "text", "required": True},
                                      {"key": "table_name", "label": "Table Name", "type": "text", "required": True}]},
        },
        "actions": {
            "create_record": {"label": "Create Record",
                              "fields": [{"key": "base_id", "label": "Base ID", "type": "text", "required": True},
                                         {"key": "table_name", "label": "Table Name", "type": "text", "required": True},
                                         {"key": "fields", "label": "Fields (JSON)", "type": "textarea", "required": True}]},
            "update_record": {"label": "Update Record",
                              "fields": [{"key": "base_id", "label": "Base ID", "type": "text", "required": True},
                                         {"key": "table_name", "label": "Table Name", "type": "text", "required": True},
                                         {"key": "record_id", "label": "Record ID", "type": "text", "required": True},
                                         {"key": "fields", "label": "Fields to Update (JSON)", "type": "textarea", "required": True}]},
            "find_record": {"label": "Find Record",
                            "fields": [{"key": "base_id", "label": "Base ID", "type": "text", "required": True},
                                       {"key": "table_name", "label": "Table Name", "type": "text", "required": True},
                                       {"key": "filter_formula", "label": "Filter Formula", "type": "text", "required": True}]},
        }
    },

    # ─── HTTP / Webhooks ──────────────────────────────────────────────────────
    "webhooks": {
        "name": "Webhooks",
        "icon": "🔗",
        "category": "Developer Tools",
        "description": "Receive and send HTTP requests",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {
            "catch_hook": {"label": "Catch Webhook",
                           "fields": [{"key": "method", "label": "HTTP Method", "type": "select",
                                       "options": ["POST", "GET", "PUT", "PATCH"], "default": "POST"}]},
        },
        "actions": {
            "post_request": {"label": "POST Request",
                             "fields": [{"key": "url", "label": "URL", "type": "text", "required": True},
                                        {"key": "payload", "label": "Payload (JSON)", "type": "textarea"},
                                        {"key": "headers", "label": "Headers (JSON)", "type": "textarea"},
                                        {"key": "auth_type", "label": "Auth Type", "type": "select",
                                         "options": ["none","basic","bearer"], "default": "none"},
                                        {"key": "auth_value", "label": "Auth Value", "type": "text"}]},
            "get_request": {"label": "GET Request",
                            "fields": [{"key": "url", "label": "URL", "type": "text", "required": True},
                                       {"key": "params", "label": "Query Params (JSON)", "type": "textarea"},
                                       {"key": "headers", "label": "Headers (JSON)", "type": "textarea"}]},
        }
    },

    # ─── Formatter (no auth) ─────────────────────────────────────────────────
    "formatter": {
        "name": "Formatter",
        "icon": "🔄",
        "category": "Built-in Tools",
        "description": "Transform, format and manipulate data",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "text": {"label": "Text",
                     "fields": [{"key": "operation", "label": "Operation", "type": "select",
                                 "options": ["uppercase","lowercase","trim","replace","split","count_words",
                                             "truncate","url_encode","url_decode","strip_html","extract_email",
                                             "extract_url","capitalize","reverse","repeat","pad_left","pad_right"]},
                                {"key": "input", "label": "Input Text", "type": "text", "required": True},
                                {"key": "options", "label": "Options (JSON)", "type": "textarea"}]},
            "numbers": {"label": "Numbers",
                        "fields": [{"key": "operation", "label": "Operation", "type": "select",
                                    "options": ["add","subtract","multiply","divide","modulo","round",
                                                "abs","min","max","format_currency","percentage","random"]},
                                   {"key": "value_a", "label": "Value A", "type": "text", "required": True},
                                   {"key": "value_b", "label": "Value B", "type": "text"},
                                   {"key": "options", "label": "Options (JSON)", "type": "textarea"}]},
            "date_time": {"label": "Date/Time",
                          "fields": [{"key": "operation", "label": "Operation", "type": "select",
                                      "options": ["format","add_days","subtract_days","diff_days","now",
                                                  "to_unix","from_unix","day_of_week","is_weekend"]},
                                     {"key": "input", "label": "Input Date", "type": "text"},
                                     {"key": "format", "label": "Output Format", "type": "text", "default": "%Y-%m-%d"},
                                     {"key": "options", "label": "Options (JSON)", "type": "textarea"}]},
            "json": {"label": "JSON",
                     "fields": [{"key": "operation", "label": "Operation", "type": "select",
                                 "options": ["parse","stringify","get_value","set_value","merge",
                                             "pick_keys","omit_keys","flatten","array_length"]},
                                {"key": "input", "label": "Input", "type": "textarea", "required": True},
                                {"key": "options", "label": "Options (JSON)", "type": "textarea"}]},
            "utilities": {"label": "Utilities",
                          "fields": [{"key": "operation", "label": "Operation", "type": "select",
                                      "options": ["generate_uuid","generate_random_string","hash_md5",
                                                  "hash_sha256","base64_encode","base64_decode",
                                                  "line_item_to_dict","dict_to_line_item"]},
                                     {"key": "input", "label": "Input", "type": "text"},
                                     {"key": "options", "label": "Options (JSON)", "type": "textarea"}]},
        }
    },

    # ─── Filter (no auth) ────────────────────────────────────────────────────
    "filter": {
        "name": "Filter",
        "icon": "🔍",
        "category": "Built-in Tools",
        "description": "Only continue if conditions are met",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "only_continue_if": {"label": "Only Continue If",
                                 "fields": [{"key": "conditions", "label": "Conditions (JSON array)", "type": "textarea",
                                             "required": True,
                                             "help": '[{"field":"{{step1.status}}","operator":"equals","value":"active"}]'}]},
        }
    },

    # ─── Delay ───────────────────────────────────────────────────────────────
    "delay": {
        "name": "Delay",
        "icon": "⏱️",
        "category": "Built-in Tools",
        "description": "Wait before continuing",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "wait": {"label": "Delay For",
                     "fields": [{"key": "seconds", "label": "Seconds", "type": "number", "default": 5},
                                 {"key": "until", "label": "Or Wait Until (ISO datetime)", "type": "text"}]},
        }
    },

    # ─── Storage ──────────────────────────────────────────────────────────────
    "storage": {
        "name": "Storage",
        "icon": "💾",
        "category": "Built-in Tools",
        "description": "Store and retrieve data between workflow runs",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "set_value": {"label": "Set Value",
                          "fields": [{"key": "key", "label": "Key", "type": "text", "required": True},
                                     {"key": "value", "label": "Value", "type": "text", "required": True},
                                     {"key": "expire_days", "label": "Expire After (days)", "type": "number"}]},
            "get_value": {"label": "Get Value",
                          "fields": [{"key": "key", "label": "Key", "type": "text", "required": True},
                                     {"key": "default_value", "label": "Default Value", "type": "text"}]},
            "increment": {"label": "Increment Counter",
                          "fields": [{"key": "key", "label": "Counter Key", "type": "text", "required": True},
                                     {"key": "amount", "label": "Increment By", "type": "number", "default": 1}]},
        }
    },

    # ─── Paths (branching) ────────────────────────────────────────────────────
    "paths": {
        "name": "Paths",
        "icon": "🔀",
        "category": "Built-in Tools",
        "description": "Create conditional branches in your workflow",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {},
        "actions": {
            "branch": {"label": "Branch",
                       "fields": [{"key": "paths", "label": "Paths (JSON array of conditions)", "type": "textarea",
                                   "required": True,
                                   "help": '[{"label":"Path A","conditions":[{"field":"x","operator":"equals","value":"y"}],"steps":[]},...]'}]},
        }
    },

    # ─── Schedule ─────────────────────────────────────────────────────────────
    "schedule": {
        "name": "Schedule",
        "icon": "🗓️",
        "category": "Built-in Tools",
        "description": "Run workflows on a schedule",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {
            "every_x_minutes": {"label": "Every X Minutes",
                                "fields": [{"key": "interval", "label": "Every N minutes", "type": "number", "default": 15}]},
            "every_hour": {"label": "Every Hour",
                           "fields": [{"key": "minute", "label": "At minute", "type": "number", "default": 0}]},
            "every_day": {"label": "Every Day",
                          "fields": [{"key": "time", "label": "Time (HH:MM)", "type": "text", "default": "09:00"},
                                     {"key": "timezone", "label": "Timezone", "type": "text", "default": "UTC"}]},
            "every_week": {"label": "Every Week",
                           "fields": [{"key": "day", "label": "Day of Week", "type": "select",
                                       "options": ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"],
                                       "default": "monday"},
                                      {"key": "time", "label": "Time (HH:MM)", "type": "text", "default": "09:00"},
                                      {"key": "timezone", "label": "Timezone", "type": "text", "default": "UTC"}]},
            "every_month": {"label": "Every Month",
                            "fields": [{"key": "day", "label": "Day of Month", "type": "number", "default": 1},
                                       {"key": "time", "label": "Time (HH:MM)", "type": "text", "default": "09:00"},
                                       {"key": "timezone", "label": "Timezone", "type": "text", "default": "UTC"}]},
            "custom_cron": {"label": "Custom Cron",
                            "fields": [{"key": "cron", "label": "Cron Expression", "type": "text",
                                        "default": "0 9 * * 1",
                                        "help": "min hour day month weekday — e.g. '0 9 * * 1' = every Monday 9am"}]},
        },
        "actions": {}
    },

    # ─── RSS ──────────────────────────────────────────────────────────────────
    "rss": {
        "name": "RSS",
        "icon": "📡",
        "category": "Content",
        "description": "Monitor RSS/Atom feeds for new items",
        "auth_type": "none",
        "credential_fields": [],
        "triggers": {
            "new_item": {"label": "New Feed Item",
                         "fields": [{"key": "feed_url", "label": "Feed URL", "type": "text", "required": True}]},
        },
        "actions": {}
    },

    # ─── Trello ───────────────────────────────────────────────────────────────
    "trello": {
        "name": "Trello",
        "icon": "📋",
        "category": "Project Management",
        "description": "Manage Trello boards, lists and cards",
        "auth_type": "token",
        "credential_fields": [
            {"key": "api_key", "label": "API Key", "type": "text"},
            {"key": "api_token", "label": "API Token", "type": "password"},
        ],
        "triggers": {
            "new_card": {"label": "New Card",
                         "fields": [{"key": "board_id", "label": "Board ID", "type": "text", "required": True},
                                    {"key": "list_name", "label": "List Name (optional)", "type": "text"}]},
            "card_moved": {"label": "Card Moved to List",
                           "fields": [{"key": "board_id", "label": "Board ID", "type": "text", "required": True},
                                      {"key": "list_name", "label": "List Name", "type": "text", "required": True}]},
        },
        "actions": {
            "create_card": {"label": "Create Card",
                            "fields": [{"key": "board_id", "label": "Board ID", "type": "text", "required": True},
                                       {"key": "list_name", "label": "List Name", "type": "text", "required": True},
                                       {"key": "name", "label": "Card Name", "type": "text", "required": True},
                                       {"key": "description", "label": "Description", "type": "textarea"},
                                       {"key": "due_date", "label": "Due Date", "type": "text"},
                                       {"key": "labels", "label": "Labels (comma-separated)", "type": "text"}]},
            "move_card": {"label": "Move Card to List",
                          "fields": [{"key": "card_id", "label": "Card ID", "type": "text", "required": True},
                                     {"key": "list_name", "label": "List Name", "type": "text", "required": True}]},
            "add_comment": {"label": "Add Comment to Card",
                            "fields": [{"key": "card_id", "label": "Card ID", "type": "text", "required": True},
                                       {"key": "comment", "label": "Comment", "type": "textarea", "required": True}]},
        }
    },

    # ─── GitHub ───────────────────────────────────────────────────────────────
    "github": {
        "name": "GitHub",
        "icon": "🐙",
        "category": "Developer Tools",
        "description": "Automate GitHub issues, PRs and actions",
        "auth_type": "token",
        "credential_fields": [
            {"key": "token", "label": "Personal Access Token", "type": "password",
             "help": "github.com/settings/tokens"},
        ],
        "triggers": {
            "new_issue": {"label": "New Issue",
                          "fields": [{"key": "owner", "label": "Owner", "type": "text", "required": True},
                                     {"key": "repo", "label": "Repository", "type": "text", "required": True}]},
            "new_pr": {"label": "New Pull Request",
                       "fields": [{"key": "owner", "label": "Owner", "type": "text", "required": True},
                                  {"key": "repo", "label": "Repository", "type": "text", "required": True}]},
        },
        "actions": {
            "create_issue": {"label": "Create Issue",
                             "fields": [{"key": "owner", "label": "Owner", "type": "text", "required": True},
                                        {"key": "repo", "label": "Repository", "type": "text", "required": True},
                                        {"key": "title", "label": "Title", "type": "text", "required": True},
                                        {"key": "body", "label": "Body", "type": "textarea"},
                                        {"key": "labels", "label": "Labels (JSON array)", "type": "text"},
                                        {"key": "assignees", "label": "Assignees (JSON array)", "type": "text"}]},
            "create_comment": {"label": "Create Comment",
                               "fields": [{"key": "owner", "label": "Owner", "type": "text", "required": True},
                                          {"key": "repo", "label": "Repository", "type": "text", "required": True},
                                          {"key": "issue_number", "label": "Issue Number", "type": "number", "required": True},
                                          {"key": "body", "label": "Comment Body", "type": "textarea", "required": True}]},
        }
    },
}

def get_app(app_key: str) -> dict:
    return APP_REGISTRY.get(app_key, {})

def list_apps() -> list:
    return [{"key": k, "name": v["name"], "icon": v["icon"], "category": v["category"],
             "description": v["description"], "auth_type": v["auth_type"],
             "trigger_count": len(v.get("triggers", {})),
             "action_count": len(v.get("actions", {}))}
            for k, v in APP_REGISTRY.items()]

def get_trigger_fields(app_key: str, trigger_key: str) -> list:
    app = APP_REGISTRY.get(app_key, {})
    return app.get("triggers", {}).get(trigger_key, {}).get("fields", [])

def get_action_fields(app_key: str, action_key: str) -> list:
    app = APP_REGISTRY.get(app_key, {})
    return app.get("actions", {}).get(action_key, {}).get("fields", [])
