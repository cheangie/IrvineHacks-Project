# 🌎 ClimateCheck — Property Climate Risk Scorer

A web app that scores any property's flood and wildfire risk using real climate data APIs and AI-generated explanations.

---

## 🗂️ File Structure

```
IRVINEHACKS-PROJECT/
├── backend/
│   ├── main.py            ← FastAPI server + API calls (You + Sristi)
│   ├── risk_scorer.py     ← Risk scoring formula (Nivedha)
│   ├── ai_service.py      ← Gemini AI integration (Cathryn)
│   ├── .env               ← API keys — YOU MUST CREATE THIS (not in repo)
│   └── requirements.txt   ← Python dependencies
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── .gitignore
```

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
Inside the `/backend` folder, create a file called `.env` and paste this in:
```
MELISSA_KEY=get_this_from_team
GEMINI_KEY=get_your_own_free_key
```

> 🔑 Get your free Gemini key at: https://aistudio.google.com → "Get API Key"
> 
> 🔑 Get the Melissa key from your teammate — everyone shares one key.

### 5. Run the backend server
Make sure your venv is active, then:
```bash
uvicorn main:app --reload
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

Test it by going to `http://localhost:8000` in your browser — you should see `{"message": "ClimateCheck API is running!"}`

### 6. Test the risk endpoint
Go to:
```
http://localhost:8000/risk?address=123 Main St, Irvine CA
```
You should get back a JSON response with scores and AI analysis.

### 7. Open the frontend
Just open `frontend/index.html` directly in your browser. No server needed for the frontend.

---

## 👥 Who Works On What

| Person | File | Task |
|---|---|---|
| You + Sristi | `backend/main.py` | FastAPI server, Melissa + FEMA API calls |
| Nivedha | `backend/risk_scorer.py` | Flood/fire scoring formula |
| Cathryn | `backend/ai_service.py` | Gemini AI explanation + probabilities |
| Everyone later | `frontend/` | UI, charts, report display |

---

## 🌿 Git Workflow

Always work on your own branch — never commit directly to main:

```bash
git checkout -b feature/your-name-task   # create your branch
# do your work...
git add .
git commit -m "describe what you did"
git push origin feature/your-name-task
# then open a Pull Request on GitHub to merge into main
```

---

## ⚠️ Important Notes

- **Never commit your `.env` file** — it's in `.gitignore` for a reason. Share keys over Discord/text.
- Always make sure your **venv is activated** before running anything (`source venv/bin/activate`)
- The backend runs on **port 8000**, frontend is just a static file — no port needed
- If you get a CORS error, make sure the backend is running before opening the frontend