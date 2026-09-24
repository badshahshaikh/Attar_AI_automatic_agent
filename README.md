# MS Fragrances AI Product Assistant

A minimal AI agent that understands customer product questions (English & Hinglish) and answers using your Excel inventory — no invented data, ever.

---

## Project Structure

```
Attar_AI_automatic_agent/
├── main.py                  ← FastAPI app, POST /chat endpoint
├── ai_agent.py              ← OpenAI agentic loop (function calling)
├── product_lookup.py        ← Excel inventory reader + search
├── create_sample_excel.py   ← One-time script to generate sample data
├── prompts/
│   └── system_prompt.txt    ← Editable AI personality & rules
├── data/
│   └── products.xlsx        ← Your inventory (replace with real data)
├── .env.example             ← Copy to .env and add your API key
├── requirements.txt
└── README.md
```

---

## Windows PowerShell Setup

### 1. Create & activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Set up your .env file
```powershell
Copy-Item .env.example .env
notepad .env   # Add your real OPENAI_API_KEY
```

### 4. Generate the sample inventory (first time only)
```powershell
python create_sample_excel.py
```
> Skip this if you already have your own `data/products.xlsx`.

### 5. Start the server
```powershell
uvicorn main:app --reload
```

The server starts at **http://localhost:8000**

---

## Manual Testing via Swagger

Open your browser at **http://localhost:8000/docs**

You will see the interactive Swagger UI. Click on **POST /chat** → **Try it out**.

### Example 1 — Fresh conversation
```json
{
  "message": "Do you have Oud in 6ml?",
  "history": []
}
```

### Example 2 — Follow-up question (paste `updated_history` from Example 1)
```json
{
  "message": "What about 12ml?",
  "history": [ ...paste updated_history from previous response... ]
}
```

### Example 3 — Hinglish
```json
{
  "message": "Rose attar ka 6ml kitne ka hai? Available hai?",
  "history": []
}
```

---

## Response Fields Explained

| Field | Description |
|---|---|
| `customer_message` | The original message you sent |
| `reply` | The AI agent's final answer |
| `tool_calls_made` | Which product lookups the AI requested (name + args) |
| `tool_results` | The actual Excel data returned for each lookup |
| `updated_history` | Full conversation — paste this back for follow-ups |

---

## Replacing Sample Data with Your Real Inventory

Replace `data/products.xlsx` with your own file. Make sure it has these column headers (exact case doesn't matter — they are normalised automatically):

| Column | Description |
|---|---|
| `product_name` | e.g. "Oud Al Shams" |
| `aliases` | comma-separated alternative names |
| `size` | e.g. "6ml", "12ml" |
| `price_inr` | price as a number |
| `in_stock` | TRUE / FALSE |
| `description` | one or two sentence product description |

---

## Editing the AI Personality

Open `prompts/system_prompt.txt` and edit freely. Changes take effect on the **next request** — no restart needed.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI secret key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use (e.g. `gpt-4o`) |
