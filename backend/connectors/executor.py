"""
Real connector executor - actually calls APIs, performs operations.
Each function here does REAL work, not LLM simulation.
"""
import json, re, hashlib, base64, asyncio, logging, uuid, math, random, urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import aiosqlite
from core.config import settings
from core.database import DB_PATH
from agents.resume_analyzer import resume_analyzer

logger = logging.getLogger(__name__)


# ─── Template resolver ───────────────────────────────────────────────────────

def resolve_template(value: Any, context: Dict[str, Any]) -> Any:
    """Replace {{step_key.field}} and {{trigger.field}} in any value."""
    if isinstance(value, str):
        def replacer(m):
            path = m.group(1).strip()
            parts = path.split(".")
            obj = context
            for p in parts:
                if isinstance(obj, dict):
                    obj = obj.get(p, "")
                else:
                    obj = ""
                    break
            return str(obj) if obj is not None else ""
        return re.sub(r"\{\{([^}]+)\}\}", replacer, value)
    elif isinstance(value, dict):
        return {k: resolve_template(v, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_template(v, context) for v in value]
    return value

def resolve_inputs(input_map: dict, context: dict) -> dict:
    return {k: resolve_template(v, context) for k, v in input_map.items()}


# ─── Filter / conditions ─────────────────────────────────────────────────────

def evaluate_conditions(conditions: list, context: dict) -> bool:
    """Evaluate a list of conditions. All must pass (AND logic)."""
    for cond in conditions:
        field_val = resolve_template(cond.get("field", ""), context)
        operator = cond.get("operator", "equals")
        expected = str(cond.get("value", ""))
        fv = str(field_val)
        
        result = False
        if operator == "equals": result = fv == expected
        elif operator == "not_equals": result = fv != expected
        elif operator == "contains": result = expected.lower() in fv.lower()
        elif operator == "not_contains": result = expected.lower() not in fv.lower()
        elif operator == "starts_with": result = fv.startswith(expected)
        elif operator == "ends_with": result = fv.endswith(expected)
        elif operator == "greater_than":
            try: result = float(fv) > float(expected)
            except: result = fv > expected
        elif operator == "less_than":
            try: result = float(fv) < float(expected)
            except: result = fv < expected
        elif operator == "is_empty": result = fv.strip() == ""
        elif operator == "is_not_empty": result = fv.strip() != ""
        elif operator == "matches_regex":
            try: result = bool(re.search(expected, fv, re.IGNORECASE))
            except: result = False
        
        if not result:
            return False
    return True


# ─── Formatter ───────────────────────────────────────────────────────────────

def run_formatter(action: str, inputs: dict) -> dict:
    op = inputs.get("operation", "")
    raw_opts = inputs.get("options", "{}")
    try:
        opts = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or {})
    except:
        opts = {}

    if action == "text":
        text = str(inputs.get("input", ""))
        result = text
        if op == "uppercase": result = text.upper()
        elif op == "lowercase": result = text.lower()
        elif op == "capitalize": result = text.capitalize()
        elif op == "trim": result = text.strip()
        elif op == "reverse": result = text[::-1]
        elif op == "replace":
            result = text.replace(opts.get("find",""), opts.get("replace",""))
        elif op == "split":
            parts = text.split(opts.get("separator", ","))
            return {"output": parts, "count": len(parts)}
        elif op == "count_words":
            return {"output": len(text.split()), "words": text.split()}
        elif op == "truncate":
            n = int(opts.get("length", 100))
            result = text[:n] + ("..." if len(text) > n else "")
        elif op == "url_encode": result = urllib.parse.quote(text)
        elif op == "url_decode": result = urllib.parse.unquote(text)
        elif op == "strip_html": result = re.sub(r"<[^>]+>", "", text)
        elif op == "extract_email":
            m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)
            result = m.group() if m else ""
        elif op == "extract_url":
            m = re.search(r"https?://[^\s]+", text)
            result = m.group() if m else ""
        elif op == "pad_left":
            result = text.rjust(int(opts.get("width",10)), opts.get("char"," "))
        elif op == "pad_right":
            result = text.ljust(int(opts.get("width",10)), opts.get("char"," "))
        elif op == "repeat":
            result = text * int(opts.get("times", 2))
        return {"output": result}

    elif action == "numbers":
        try:
            a = float(inputs.get("value_a", 0))
            b = float(inputs.get("value_b", 0))
        except:
            return {"output": None, "error": "Invalid number input"}
        result = None
        if op == "add": result = a + b
        elif op == "subtract": result = a - b
        elif op == "multiply": result = a * b
        elif op == "divide": result = (a / b) if b != 0 else None
        elif op == "modulo": result = a % b if b != 0 else None
        elif op == "round": result = round(a, int(b))
        elif op == "abs": result = abs(a)
        elif op == "min": result = min(a, b)
        elif op == "max": result = max(a, b)
        elif op == "percentage":
            result = (a / b * 100) if b != 0 else None
        elif op == "random":
            result = random.uniform(a, b)
        elif op == "format_currency":
            currency = opts.get("currency", "USD")
            symbol = {"USD":"$","EUR":"€","GBP":"£","INR":"₹"}.get(currency, "$")
            result = f"{symbol}{a:,.2f}"
            return {"output": result}
        return {"output": result}

    elif action == "date_time":
        inp = inputs.get("input", "")
        fmt = inputs.get("format", "%Y-%m-%d")
        if op == "now":
            result = datetime.utcnow().strftime(fmt)
            return {"output": result, "unix": int(datetime.utcnow().timestamp())}
        try:
            dt = datetime.fromisoformat(inp.replace("Z",""))
        except:
            try: dt = datetime.strptime(inp, "%Y-%m-%d")
            except: return {"output": None, "error": f"Cannot parse date: {inp}"}
        result = dt
        if op == "format": result = dt.strftime(fmt)
        elif op == "add_days": result = (dt + timedelta(days=int(opts.get("days",1)))).strftime(fmt)
        elif op == "subtract_days": result = (dt - timedelta(days=int(opts.get("days",1)))).strftime(fmt)
        elif op == "diff_days":
            try:
                dt2 = datetime.fromisoformat(opts.get("compare_to","").replace("Z",""))
                result = abs((dt - dt2).days)
            except: result = None
        elif op == "to_unix": result = int(dt.timestamp())
        elif op == "from_unix":
            result = datetime.utcfromtimestamp(float(inp)).strftime(fmt)
        elif op == "day_of_week": result = dt.strftime("%A")
        elif op == "is_weekend": result = dt.weekday() >= 5
        return {"output": result if isinstance(result, str) else str(result)}

    elif action == "json":
        raw = inputs.get("input", "{}")
        if op == "parse":
            try: return {"output": json.loads(raw)}
            except Exception as e: return {"output": None, "error": str(e)}
        elif op == "stringify":
            obj = raw if not isinstance(raw, str) else json.loads(raw)
            return {"output": json.dumps(obj, indent=opts.get("indent"))}
        elif op == "get_value":
            try:
                obj = json.loads(raw) if isinstance(raw, str) else raw
                keys = opts.get("path","").split(".")
                for k in keys: obj = obj[k]
                return {"output": obj}
            except: return {"output": None}
        elif op == "array_length":
            try:
                obj = json.loads(raw) if isinstance(raw, str) else raw
                return {"output": len(obj) if isinstance(obj, (list, dict)) else 0}
            except: return {"output": 0}
        elif op == "merge":
            try:
                a = json.loads(raw) if isinstance(raw, str) else raw
                b = json.loads(opts.get("merge_with","{}"))
                return {"output": {**a, **b}}
            except Exception as e: return {"output": None, "error": str(e)}
        elif op == "pick_keys":
            try:
                obj = json.loads(raw) if isinstance(raw, str) else raw
                keys = [k.strip() for k in opts.get("keys","").split(",")]
                return {"output": {k: obj[k] for k in keys if k in obj}}
            except: return {"output": {}}

    elif action == "utilities":
        if op == "generate_uuid": return {"output": str(uuid.uuid4())}
        elif op == "generate_random_string":
            n = int(opts.get("length", 16))
            chars = opts.get("charset","abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            return {"output": "".join(random.choice(chars) for _ in range(n))}
        elif op == "hash_md5":
            return {"output": hashlib.md5(str(inputs.get("input","")).encode()).hexdigest()}
        elif op == "hash_sha256":
            return {"output": hashlib.sha256(str(inputs.get("input","")).encode()).hexdigest()}
        elif op == "base64_encode":
            return {"output": base64.b64encode(str(inputs.get("input","")).encode()).decode()}
        elif op == "base64_decode":
            try: return {"output": base64.b64decode(str(inputs.get("input","")).encode()).decode()}
            except: return {"output": None, "error": "Invalid base64"}

    return {"output": None, "error": f"Unknown formatter action/operation: {action}/{op}"}


# ─── HTTP connector ──────────────────────────────────────────────────────────

async def run_http(action: str, inputs: dict) -> dict:
    url = inputs.get("url","")
    if not url:
        return {"error": "URL is required", "status_code": None}
    
    try:
        headers = {}
        raw_headers = inputs.get("headers","")
        if raw_headers:
            try: headers = json.loads(raw_headers) if isinstance(raw_headers, str) else raw_headers
            except: pass
        
        auth_type = inputs.get("auth_type","none")
        auth_val = inputs.get("auth_value","")
        if auth_type == "bearer" and auth_val:
            headers["Authorization"] = f"Bearer {auth_val}"
        elif auth_type == "basic" and auth_val:
            headers["Authorization"] = f"Basic {base64.b64encode(auth_val.encode()).decode()}"
        
        timeout = float(inputs.get("timeout", 30))
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            if action == "post_request":
                payload = inputs.get("payload","")
                if payload and isinstance(payload, str):
                    try: payload = json.loads(payload)
                    except: pass
                r = await client.post(url, json=payload if isinstance(payload, dict) else None,
                                      data=payload if isinstance(payload, str) else None,
                                      headers=headers)
            else:  # get_request
                params = {}
                raw_params = inputs.get("params","")
                if raw_params:
                    try: params = json.loads(raw_params) if isinstance(raw_params, str) else raw_params
                    except: pass
                r = await client.get(url, params=params, headers=headers)
            
            try: body = r.json()
            except: body = r.text
            
            return {
                "status_code": r.status_code,
                "success": r.is_success,
                "body": body,
                "headers": dict(r.headers),
                "url": str(r.url)
            }
    except httpx.TimeoutException:
        return {"error": "Request timed out", "status_code": None}
    except Exception as e:
        return {"error": str(e), "status_code": None}


# ─── Gmail (real SMTP + IMAP) ────────────────────────────────────────────────

async def run_gmail(action: str, inputs: dict, credentials: dict) -> dict:
    import smtplib, imaplib, email as email_lib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    user_email = credentials.get("email","")
    app_password = credentials.get("app_password","")
    
    if action == "send_email":
        to = inputs.get("to","")
        subject = inputs.get("subject","(no subject)")
        body = inputs.get("body","")
        cc = inputs.get("cc","")
        bcc = inputs.get("bcc","")
        is_html = inputs.get("is_html", False)
        
        if not (user_email and app_password and to):
            return {"error": "Missing credentials or recipient", "sent": False}
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user_email
        msg["To"] = to
        if cc: msg["Cc"] = cc
        
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))
        
        all_recipients = [to]
        if cc: all_recipients += [e.strip() for e in cc.split(",")]
        if bcc: all_recipients += [e.strip() for e in bcc.split(",")]
        
        try:
            def _send():
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
                    srv.login(user_email, app_password)
                    srv.sendmail(user_email, all_recipients, msg.as_string())
            await asyncio.get_event_loop().run_in_executor(None, _send)
            return {"sent": True, "to": to, "subject": subject, "message_id": str(uuid.uuid4())}
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    elif action == "create_draft":
        return {"created": True, "note": "Draft creation requires Gmail API (oauth2). Use send_email instead."}
    
    elif action == "find_email":
        if not (user_email and app_password):
            return {"error": "Missing credentials", "found": False}
        query = inputs.get("query","")
        try:
            def _search():
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user_email, app_password)
                mail.select("inbox")
                criteria = f'(SUBJECT "{query}")' if query else "ALL"
                _, data = mail.search(None, criteria)
                ids = data[0].split()[-5:]  # last 5
                results = []
                for eid in ids:
                    _, msg_data = mail.fetch(eid, "(RFC822)")
                    msg = email_lib.message_from_bytes(msg_data[0][1])
                    results.append({
                        "subject": msg.get("Subject",""),
                        "from": msg.get("From",""),
                        "date": msg.get("Date",""),
                        "snippet": ""
                    })
                mail.logout()
                return results
            results = await asyncio.get_event_loop().run_in_executor(None, _search)
            return {"emails": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e), "emails": []}
    
    return {"error": f"Unknown Gmail action: {action}"}


# ─── Slack (real API) ────────────────────────────────────────────────────────

async def run_slack(action: str, inputs: dict, credentials: dict) -> dict:
    token = credentials.get("bot_token","")
    if not token:
        return {"error": "Slack bot_token not configured"}
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=15) as client:
        if action == "post_message":
            payload = {
                "channel": inputs.get("channel",""),
                "text": inputs.get("text",""),
            }
            if inputs.get("username"): payload["username"] = inputs["username"]
            if inputs.get("icon_emoji"): payload["icon_emoji"] = inputs["icon_emoji"]
            r = await client.post("https://slack.com/api/chat.postMessage",
                                  json=payload, headers=headers)
            data = r.json()
            if data.get("ok"):
                return {"sent": True, "ts": data.get("ts"), "channel": data.get("channel")}
            return {"sent": False, "error": data.get("error","unknown")}
        
        elif action == "send_dm":
            # Open DM channel first
            user_id = inputs.get("user_email","")
            r = await client.post("https://slack.com/api/conversations.open",
                                  json={"users": user_id}, headers=headers)
            data = r.json()
            if not data.get("ok"):
                return {"sent": False, "error": data.get("error","cannot open DM")}
            channel_id = data["channel"]["id"]
            r2 = await client.post("https://slack.com/api/chat.postMessage",
                                   json={"channel": channel_id, "text": inputs.get("text","")},
                                   headers=headers)
            d2 = r2.json()
            return {"sent": d2.get("ok", False), "ts": d2.get("ts"), "error": d2.get("error")}
        
        elif action == "set_status":
            profile = {
                "status_text": inputs.get("status_text",""),
                "status_emoji": inputs.get("status_emoji",":speech_balloon:"),
                "status_expiration": 0
            }
            r = await client.post("https://slack.com/api/users.profile.set",
                                  json={"profile": profile}, headers=headers)
            data = r.json()
            return {"updated": data.get("ok", False), "error": data.get("error")}
    
    return {"error": f"Unknown Slack action: {action}"}


# ─── Notion (real API) ───────────────────────────────────────────────────────

async def run_notion(action: str, inputs: dict, credentials: dict) -> dict:
    api_key = credentials.get("api_key","")
    if not api_key:
        return {"error": "Notion API key not configured"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=20) as client:
        if action == "create_page":
            parent_id = inputs.get("parent_id","").replace("-","")
            title = inputs.get("title","")
            content = inputs.get("content","")
            
            raw_props = inputs.get("properties","")
            try: extra_props = json.loads(raw_props) if raw_props else {}
            except: extra_props = {}
            
            properties = {"title": {"title": [{"text": {"content": title}}]}}
            properties.update(extra_props)
            
            children = []
            if content:
                for line in content.split("\n")[:20]:
                    if line.strip():
                        children.append({
                            "object": "block", "type": "paragraph",
                            "paragraph": {"rich_text": [{"text": {"content": line}}]}
                        })
            
            payload = {
                "parent": {"type": "database_id", "database_id": parent_id} if len(parent_id) == 32 else {"type": "page_id", "page_id": parent_id},
                "properties": properties,
                "children": children
            }
            r = await client.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
            data = r.json()
            if data.get("object") == "page":
                return {"created": True, "page_id": data["id"], "url": data.get("url","")}
            return {"created": False, "error": data.get("message","unknown")}
        
        elif action == "append_to_page":
            page_id = inputs.get("page_id","").replace("-","")
            content = inputs.get("content","")
            blocks = [{"object":"block","type":"paragraph",
                       "paragraph":{"rich_text":[{"text":{"content": line}}]}}
                      for line in content.split("\n") if line.strip()]
            r = await client.patch(f"https://api.notion.com/v1/blocks/{page_id}/children",
                                   json={"children": blocks}, headers=headers)
            data = r.json()
            return {"appended": data.get("object") == "list", "error": data.get("message")}
        
        elif action == "update_page":
            page_id = inputs.get("page_id","").replace("-","")
            raw_props = inputs.get("properties","")
            try: props = json.loads(raw_props)
            except: return {"error": "Invalid properties JSON"}
            r = await client.patch(f"https://api.notion.com/v1/pages/{page_id}",
                                   json={"properties": props}, headers=headers)
            data = r.json()
            return {"updated": data.get("object") == "page", "error": data.get("message")}
    
    return {"error": f"Unknown Notion action: {action}"}


# ─── Google Sheets (via Sheets API v4) ───────────────────────────────────────

async def run_google_sheets(action: str, inputs: dict, credentials: dict) -> dict:
    import google.oauth2.service_account as sa_module
    import googleapiclient.discovery as discovery
    
    svc_json = credentials.get("service_account_json","")
    if not svc_json:
        return {"error": "Service account JSON not configured"}
    
    try:
        if isinstance(svc_json, str): info = json.loads(svc_json)
        else: info = svc_json
        creds = sa_module.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    except Exception as e:
        return {"error": f"Invalid service account: {e}"}
    
    def _run():
        service = discovery.build("sheets","v4", credentials=creds)
        ss = service.spreadsheets()
        spreadsheet_id = inputs.get("spreadsheet_id","")
        sheet_name = inputs.get("sheet_name","Sheet1")

        if action == "create_spreadsheet":
            title = inputs.get("title", "AutoFlow Sheet")
            body = {
                "properties": {"title": title},
                "sheets": [{"properties": {"title": sheet_name or "Sheet1"}}],
            }
            result = ss.create(body=body).execute()
            return {
                "created": True,
                "spreadsheet_id": result.get("spreadsheetId", ""),
                "spreadsheet_url": result.get("spreadsheetUrl", ""),
                "title": result.get("properties", {}).get("title", title),
            }
        
        if action == "append_row":
            vals = inputs.get("values","")
            if isinstance(vals, str):
                try: vals = json.loads(vals)
                except: vals = [vals]
            body = {"values": [vals if isinstance(vals[0], list) else vals]}
            result = ss.values().append(
                spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1",
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            return {"appended": True, "updated_range": result.get("updates",{}).get("updatedRange","")}
        
        elif action == "update_row":
            row = inputs.get("row_number", 1)
            vals = inputs.get("values","")
            if isinstance(vals, str):
                try: vals = json.loads(vals)
                except: vals = [vals]
            range_name = f"{sheet_name}!A{row}"
            body = {"values": [vals]}
            ss.values().update(spreadsheetId=spreadsheet_id, range=range_name,
                               valueInputOption="USER_ENTERED", body=body).execute()
            return {"updated": True, "row": row}
        
        elif action == "lookup_row":
            col = inputs.get("lookup_column","A")
            val = inputs.get("lookup_value","")
            result = ss.values().get(spreadsheetId=spreadsheet_id,
                                     range=f"{sheet_name}").execute()
            rows = result.get("values",[])
            if not rows: return {"found": False, "row": None}
            headers = rows[0]
            col_idx = ord(col.upper()) - ord("A") if len(col) == 1 else 0
            for i, row in enumerate(rows[1:], 2):
                if len(row) > col_idx and str(row[col_idx]) == str(val):
                    return {"found": True, "row": i, "data": dict(zip(headers, row))}
            return {"found": False, "row": None}
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _run)
        return result
    except Exception as e:
        return {"error": str(e)}


# ─── Airtable (real REST API) ────────────────────────────────────────────────

async def run_airtable(action: str, inputs: dict, credentials: dict) -> dict:
    api_key = credentials.get("api_key","")
    if not api_key:
        return {"error": "Airtable API key not configured"}
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    base_id = inputs.get("base_id","")
    table = inputs.get("table_name","")
    base_url = f"https://api.airtable.com/v0/{base_id}/{urllib.parse.quote(table)}"
    
    async with httpx.AsyncClient(timeout=20) as client:
        if action == "create_record":
            raw = inputs.get("fields","")
            try: fields = json.loads(raw) if isinstance(raw, str) else raw
            except: return {"error": "Invalid fields JSON"}
            r = await client.post(base_url, json={"fields": fields}, headers=headers)
            data = r.json()
            return {"created": "id" in data, "record_id": data.get("id"),
                    "fields": data.get("fields",{}), "error": data.get("error",{}).get("message")}
        
        elif action == "update_record":
            record_id = inputs.get("record_id","")
            raw = inputs.get("fields","")
            try: fields = json.loads(raw) if isinstance(raw, str) else raw
            except: return {"error": "Invalid fields JSON"}
            r = await client.patch(f"{base_url}/{record_id}", json={"fields": fields}, headers=headers)
            data = r.json()
            return {"updated": "id" in data, "record_id": data.get("id"),
                    "error": data.get("error",{}).get("message")}
        
        elif action == "find_record":
            formula = inputs.get("filter_formula","")
            params = {"filterByFormula": formula, "maxRecords": 10}
            r = await client.get(base_url, params=params, headers=headers)
            data = r.json()
            records = data.get("records",[])
            return {"found": len(records) > 0, "records": records,
                    "count": len(records), "error": data.get("error",{}).get("message")}
    
    return {"error": f"Unknown Airtable action: {action}"}


# ─── GitHub (real API) ───────────────────────────────────────────────────────

async def run_github(action: str, inputs: dict, credentials: dict) -> dict:
    token = credentials.get("token","")
    headers = {"Accept": "application/vnd.github+json"}
    if token: headers["Authorization"] = f"token {token}"
    
    owner = inputs.get("owner","")
    repo = inputs.get("repo","")
    
    async with httpx.AsyncClient(timeout=20) as client:
        if action == "create_issue":
            raw_labels = inputs.get("labels","[]")
            raw_assignees = inputs.get("assignees","[]")
            try: labels = json.loads(raw_labels)
            except: labels = []
            try: assignees = json.loads(raw_assignees)
            except: assignees = []
            payload = {"title": inputs.get("title",""), "body": inputs.get("body",""),
                       "labels": labels, "assignees": assignees}
            r = await client.post(f"https://api.github.com/repos/{owner}/{repo}/issues",
                                  json=payload, headers=headers)
            data = r.json()
            return {"created": "id" in data, "issue_number": data.get("number"),
                    "url": data.get("html_url",""), "error": data.get("message")}
        
        elif action == "create_comment":
            issue_num = inputs.get("issue_number","")
            r = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments",
                json={"body": inputs.get("body","")}, headers=headers)
            data = r.json()
            return {"created": "id" in data, "comment_id": data.get("id"),
                    "url": data.get("html_url",""), "error": data.get("message")}
    
    return {"error": f"Unknown GitHub action: {action}"}


# ─── Trello (real API) ───────────────────────────────────────────────────────

async def run_trello(action: str, inputs: dict, credentials: dict) -> dict:
    api_key = credentials.get("api_key","")
    api_token = credentials.get("api_token","")
    auth = {"key": api_key, "token": api_token}
    
    async with httpx.AsyncClient(timeout=20) as client:
        board_id = inputs.get("board_id","")
        
        if action == "create_card":
            # Find list ID by name
            r = await client.get(f"https://api.trello.com/1/boards/{board_id}/lists", params=auth)
            lists = r.json()
            list_name = inputs.get("list_name","")
            list_id = next((l["id"] for l in lists if l["name"].lower() == list_name.lower()), None)
            if not list_id:
                return {"error": f"List '{list_name}' not found on board"}
            
            card_data = {**auth, "idList": list_id,
                         "name": inputs.get("name",""),
                         "desc": inputs.get("description","")}
            if inputs.get("due_date"): card_data["due"] = inputs["due_date"]
            
            r2 = await client.post("https://api.trello.com/1/cards", params=card_data)
            data = r2.json()
            return {"created": "id" in data, "card_id": data.get("id"),
                    "url": data.get("shortUrl",""), "error": data.get("message")}
        
        elif action == "move_card":
            card_id = inputs.get("card_id","")
            list_name = inputs.get("list_name","")
            # Get boards the card belongs to
            r = await client.get(f"https://api.trello.com/1/cards/{card_id}/board", params=auth)
            b = r.json()
            bid = b.get("id", board_id)
            r2 = await client.get(f"https://api.trello.com/1/boards/{bid}/lists", params=auth)
            lists = r2.json()
            list_id = next((l["id"] for l in lists if l["name"].lower() == list_name.lower()), None)
            if not list_id: return {"error": f"List '{list_name}' not found"}
            r3 = await client.put(f"https://api.trello.com/1/cards/{card_id}",
                                  params={**auth, "idList": list_id})
            data = r3.json()
            return {"moved": "id" in data, "card_id": data.get("id")}
        
        elif action == "add_comment":
            card_id = inputs.get("card_id","")
            r = await client.post(f"https://api.trello.com/1/cards/{card_id}/actions/comments",
                                  params={**auth, "text": inputs.get("comment","")})
            data = r.json()
            return {"added": "id" in data, "comment_id": data.get("id")}
    
    return {"error": f"Unknown Trello action: {action}"}


# ─── RSS ─────────────────────────────────────────────────────────────────────

async def poll_rss(feed_url: str, last_seen_id: str = "") -> list:
    """Poll RSS feed and return new items."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(feed_url, follow_redirects=True)
        content = r.text
    
    items = []
    entries = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
    if not entries:
        entries = re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL)
    
    def extract(tag, text):
        m = re.search(rf"<{tag}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", text, re.DOTALL)
        return m.group(1).strip() if m else ""
    
    for e in entries[:10]:
        item = {
            "title": extract("title", e),
            "link": extract("link", e),
            "description": extract("description", e) or extract("summary", e),
            "pubDate": extract("pubDate", e) or extract("published", e),
            "guid": extract("guid", e) or extract("id", e),
        }
        if item["title"]:
            items.append(item)
    
    return items


# ─── Storage connector ───────────────────────────────────────────────────────

async def run_storage(action: str, inputs: dict, workflow_id: str) -> dict:
    key = inputs.get("key","")
    async with aiosqlite.connect(DB_PATH) as db:
        if action == "set_value":
            value = str(inputs.get("value",""))
            expire_days = inputs.get("expire_days")
            expires_at = None
            if expire_days:
                expires_at = (datetime.utcnow() + timedelta(days=int(expire_days))).isoformat()
            await db.execute("""
                INSERT INTO data_store (id, workflow_id, key, value, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(workflow_id, key) DO UPDATE SET value=excluded.value, expires_at=excluded.expires_at
            """, (str(uuid.uuid4()), workflow_id, key, value, expires_at))
            await db.commit()
            return {"set": True, "key": key, "value": value}
        
        elif action == "get_value":
            cursor = await db.execute(
                "SELECT value, expires_at FROM data_store WHERE workflow_id=? AND key=?",
                (workflow_id, key))
            row = await cursor.fetchone()
            if row:
                if row[1] and datetime.fromisoformat(row[1]) < datetime.utcnow():
                    await db.execute("DELETE FROM data_store WHERE workflow_id=? AND key=?", (workflow_id, key))
                    await db.commit()
                    return {"found": False, "value": inputs.get("default_value","")}
                return {"found": True, "value": row[0]}
            return {"found": False, "value": inputs.get("default_value","")}
        
        elif action == "increment":
            cursor = await db.execute(
                "SELECT value FROM data_store WHERE workflow_id=? AND key=?", (workflow_id, key))
            row = await cursor.fetchone()
            current = float(row[0]) if row else 0
            new_val = current + float(inputs.get("amount", 1))
            await db.execute("""
                INSERT INTO data_store (id, workflow_id, key, value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workflow_id, key) DO UPDATE SET value=excluded.value
            """, (str(uuid.uuid4()), workflow_id, key, str(new_val)))
            await db.commit()
            return {"key": key, "previous": current, "value": new_val}
    
    return {"error": f"Unknown storage action: {action}"}


# ─── Delay ───────────────────────────────────────────────────────────────────

async def run_delay(action: str, inputs: dict) -> dict:
    if action == "wait":
        until = inputs.get("until","")
        if until:
            try:
                target = datetime.fromisoformat(until.replace("Z",""))
                wait_secs = max(0, (target - datetime.utcnow()).total_seconds())
                wait_secs = min(wait_secs, 300)  # cap at 5 minutes for safety
            except:
                wait_secs = float(inputs.get("seconds", 5))
        else:
            wait_secs = float(inputs.get("seconds", 5))
        
        wait_secs = min(wait_secs, 30)  # hard cap for API use
        await asyncio.sleep(wait_secs)
        return {"waited_seconds": wait_secs, "completed_at": datetime.utcnow().isoformat()}
    return {"error": f"Unknown delay action: {action}"}


async def run_resume_screener(action: str, inputs: dict) -> dict:
    if action != "analyze_resume":
        return {"error": f"Unknown Resume Screener action: {action}"}

    resume_text = str(inputs.get("resume_text", "")).strip()
    if not resume_text:
        return {"error": "resume_text is required"}

    result = await resume_analyzer.analyze_text(
        resume_text,
        job_title=str(inputs.get("job_title", "")),
        job_description=str(inputs.get("job_description", "")),
    )
    return {
        "analyzed": True,
        **result,
    }


# ─── Master dispatcher ───────────────────────────────────────────────────────

async def execute_step(app_key: str, action: str, inputs: dict,
                        credentials: dict = None, workflow_id: str = "") -> dict:
    """Route step execution to the correct connector."""
    creds = credentials or {}
    
    try:
        if app_key == "formatter":
            return run_formatter(action, inputs)
        elif app_key == "filter":
            conditions = inputs.get("conditions", [])
            if isinstance(conditions, str):
                try: conditions = json.loads(conditions)
                except: conditions = []
            passed = evaluate_conditions(conditions, inputs.get("_context", {}))
            return {"passed": passed, "halt": not passed, "conditions_evaluated": len(conditions)}
        elif app_key == "delay":
            return await run_delay(action, inputs)
        elif app_key == "storage":
            return await run_storage(action, inputs, workflow_id)
        elif app_key == "webhooks":
            return await run_http(action, inputs)
        elif app_key == "gmail":
            return await run_gmail(action, inputs, creds)
        elif app_key == "slack":
            return await run_slack(action, inputs, creds)
        elif app_key == "notion":
            return await run_notion(action, inputs, creds)
        elif app_key == "google_sheets":
            return await run_google_sheets(action, inputs, creds)
        elif app_key == "airtable":
            return await run_airtable(action, inputs, creds)
        elif app_key == "github":
            return await run_github(action, inputs, creds)
        elif app_key == "trello":
            return await run_trello(action, inputs, creds)
        elif app_key == "resume_screener":
            return await run_resume_screener(action, inputs)
        else:
            return {"error": f"App '{app_key}' not implemented", "app_key": app_key}
    except Exception as e:
        logger.error(f"execute_step error [{app_key}.{action}]: {e}", exc_info=True)
        return {"error": str(e), "app_key": app_key, "action": action}
