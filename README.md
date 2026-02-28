# Property Climate Risk Scorer

A web app that scores any property's flood and wildfire risk using real climate data APIs and AI-generated explanations.

---

## 🗂️ File Structure

```
IRVINEHACKS-PROJECT/
├── backend/
│   ├── main.py            ← Nivedha (Melissa) + Sristi (FEMA/CalFire)
│   ├── risk_scorer.py     ← You — scoring formula
│   ├── ai_service.py      ← Cathryn — Gemini AI
│   ├── .env               ← API keys — YOU MUST CREATE THIS (not in repo)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── .gitignore
```

---

## 👥 Who Works On What

| Person | File | Task |
|---|---|---|
| You | `risk_scorer.py` | Converts raw zone data into 0-100 risk scores |
| Nivedha | `main.py` → `geocode()` | Melissa API — address to lat/lng |
| Sristi | `main.py` → `get_flood_zone()` + `get_calfire_zone()` | FEMA + CalFire API calls |
| Cathryn | `ai_service.py` | Gemini AI — explanation, probabilities, recommendations |

---

## ⚙️ Setup After Cloning

### 1. Clone the repo
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Set up the Python environment
```bash
cd backend
python -m venv venv
```

Activate it:
- **Mac/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file
Inside `/backend`, create a file called `.env`:
```
MELISSA_KEY=get_this_from_team
GEMINI_KEY=get_your_own_free_key
```

> 🔑 **Gemini key** (Cathryn): get it free at https://aistudio.google.com → "Get API Key"
>
> 🔑 **Melissa key**: get it from your teammate, everyone shares one

### 5. Run the backend
```bash
uvicorn main:app --reload
```
Test at `http://localhost:8000` — should see `{"message": "ClimateCheck API is running!"}`

### 6. Test the full risk endpoint
```
http://localhost:8000/risk?address=123 Main St, Irvine CA
```

### 7. Open the frontend
Just open `frontend/index.html` directly in your browser. No extra server needed.

---

## 🧪 How to Test Your Piece Independently

**You (risk_scorer.py):**
```bash
python risk_scorer.py
# should print {"flood": 90, "fire": 90, "overall": 90}
```

**Cathryn (ai_service.py):**
```bash
python ai_service.py
# should print a JSON with explanation, recommendations, probabilities
```

**Nivedha + Sristi (main.py functions):**
Run the server and hit the `/risk` endpoint in your browser.

---

## 🌿 Git Workflow

Work on your own branch — never commit directly to main:

```bash
git checkout -b feature/your-name-task
# do your work...
git add .
git commit -m "describe what you did"
git push origin feature/your-name-task
# open a Pull Request on GitHub to merge into main
```

---

## ⚠️ Important Notes
- **Never commit `.env`** — share keys over Discord/text
- Always activate venv before running anything: `source venv/bin/activate`
- Backend runs on **port 8000**, frontend is just a static HTML file
- If you get a CORS error, make sure the backend server is running first