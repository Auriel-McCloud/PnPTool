# 🎲 Pen & Paper Companion Tool (WIP)

> **Note:** At the moment, the interface and content are in German. An English translation is planned for the future!

This is a companion tool for Pen & Paper RPGs, designed to provide Game Masters with a comprehensive planning interface alongside interactive character sheets. Currently, the logic is tailored to a homebrew Cyberpunk system (a hybrid of World of Darkness and Shadowrun mechanics).

### 🛠️ Tech Stack
* **Backend:** Python, FastAPI
* **Database:** Neo4j

*Disclaimer: This is a purely passion-driven, completely overengineered hobby project! (PS: The code is heavily AI-assisted / prompt-engineered).*

### 🚀 Roadmap & Next Steps
* **System Expansion:** Integrating frameworks for D&D and Splittermond (mechanics and structure only, no copyrighted content).
* **AI Integration:** Connecting AI models via API for smart GM/player assistance.

## ⚙️ Setup

```bash
# 1. Neo4j
docker compose up -d neo4j

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
copy ..\.env.example .env
cd .. && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# (see CLAUDE.md "Bekannte Stolpersteine" — no --reload on Windows)

# 3. Frontend
cd frontend
npm install
npm run dev
```

`backend/.env` holds all secrets and is **never** committed (see `.gitignore`).
Copy `.env.example` to `backend/.env` and fill in what you need:

| Variable | Required? | What it's for |
|---|---|---|
| `NEO4J_*` | yes | Database connection |
| `JWT_SECRET` | yes | Session cookie signing — pick any long random string |
| `GEMINI_API_KEY` / `MISTRAL_API_KEY` | optional | AI-generated content in the "Ideenschmiede" (character/story drafts). Without a key the rest of the app works normally, only the "✨ KI" buttons will error. |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | optional | Playlists on locations/events, music follows the active party. Without keys the rest of the app works normally, only "Connect Spotify" will error. |

Every third-party key is your own — get one from the respective provider's dashboard (links and setup steps are in the comments inside `.env.example`). Nothing you enter there ever leaves your machine except straight to that provider's API.
