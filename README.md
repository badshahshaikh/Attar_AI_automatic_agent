# MS Fragrances AI Product Assistant

A minimal AI agent that answers customer product questions in English and Hinglish using your **live Google Sheet inventory** — no invented data, ever.

---

## Project Structure

```
Attar_AI_automatic_agent/
├── main.py                  ← FastAPI app  —  POST /chat  +  observability
├── ai_agent.py              ← OpenAI agentic loop + timing / logging
├── sheets_lookup.py         ← Live Google Sheets inventory reader
├── prompts/
│   └── system_prompt.txt    ← Editable AI personality & rules
├── chat_ui.html             ← WhatsApp-style chat UI (served at /)
├── .env.example             ← Copy to .env and add your secrets
├── requirements.txt
└── README.md
```

---

## Google Sheets Setup (do this once)

### Step 1 — Create the Google Sheet

Create a new Google Sheet. Name the first worksheet tab **Products**.

Add these exact headers in row 1:

| product_id | product_name | aliases | size_ml | price | stock_quantity | description |
|---|---|---|---|---|---|---|
| 1 | Oud Al Shams | oud, royal oud | 6 | 620 | 15 | Rich smoky Oud with warm amber base. |
| 2 | Oud Al Shams | oud, royal oud | 12 | 1100 | 0 | Rich smoky Oud with warm amber base. |
| 3 | Rose Attar | rose, gulab | 6 | 500 | 20 | Pure distilled rose petals. |

You can edit prices and stock quantities at any time — changes are reflected on the next `/chat` request.

### Step 2 — Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **IAM & Admin** → **Service Accounts**.
2. Click **Create Service Account** → give it a name → click **Done**.
3. Click the service account → **Keys** → **Add Key** → **Create new key** → **JSON**.
4. Download the JSON file.

### Step 3 — Enable the Google Sheets API

In Google Cloud Console → **APIs & Services** → **Enable APIs** → search **Google Sheets API** → Enable.

### Step 4 — Share the Sheet with the Service Account

1. Open your Google Sheet.
2. Click **Share**.
3. Paste the service account's email (looks like `name@project.iam.gserviceaccount.com`).
4. Give it **Viewer** access. Click **Done**.

### Step 5 — Set Environment Variables

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in:

```
GOOGLE_SHEET_ID=1BxiMV...  # from the sheet URL
GOOGLE_SHEET_NAME=Products

# Paste the entire contents of the downloaded JSON key on ONE line:
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...",...}
```

> **Alternatively**, set `GOOGLE_SERVICE_ACCOUNT_JSON` to the **file path** of the JSON key:
> `GOOGLE_SERVICE_ACCOUNT_JSON=./service_account.json`

---

## Windows PowerShell Setup

### 1. Activate the virtual environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install / update dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the server
```powershell
uvicorn main:app --reload
```

---

## URLs

| URL | What you get |
|---|---|
| `http://127.0.0.1:8000/` | Chat UI |
| `http://127.0.0.1:8000/docs` | Swagger — test the API directly |
| `http://127.0.0.1:8000/health` | JSON health check |

---

## Manual Testing via Chat UI

Open **http://127.0.0.1:8000/** and type a question:

- **"Do you have Oud in 6ml?"**
- **"Rose attar ka price kya hai?"**
- **"What about 12ml?"** ← follow-up keeps context
- **"Kya Musk available hai?"**

Each AI reply shows an expandable **Inventory Lookup Details** panel with the exact Google Sheet rows used.

---

## Manual Testing via Swagger

Open **http://127.0.0.1:8000/docs** → POST /chat → Try it out:

```json
{
  "message": "Do you have Rose Attar in 6ml?",
  "history": []
}
```

---

## Response Fields

| Field | Description |
|---|---|
| `reply` | The AI's customer-facing answer |
| `tool_calls_made` | Which product names/sizes the AI looked up |
| `tool_results` | The exact Google Sheet rows used |
| `updated_history` | Paste this into the next request for follow-ups |
| `observability.duration_ms` | Total request time in ms |
| `observability.tool_called` | `true` if the sheet was queried |
| `observability.lookup_args` | Arguments passed to each lookup |
| `observability.error` | Error message if something went wrong |

---

## Verifying Live Inventory Updates

1. Start a chat: `"What is the price of Rose Attar 6ml?"`  
   → Note the price in the reply.
2. Open your Google Sheet and change the price of that row.
3. Ask the same question again in a **new chat**.  
   → The new price appears immediately — no restart needed.

---

## Editing the AI Personality

Open `prompts/system_prompt.txt` and edit freely. Changes take effect on the next request — no restart needed.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI secret key |
| `OPENAI_MODEL` | optional | Model name (default: `gpt-4o-mini`) |
| `GOOGLE_SHEET_ID` | ✅ | Sheet ID from the URL |
| `GOOGLE_SHEET_NAME` | optional | Worksheet tab name (default: `Products`) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ | Full JSON content or file path of the service-account key |
