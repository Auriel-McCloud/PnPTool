# 🎲 Pen & Paper Companion Tool

> **Note:** At the moment, the interface and content are in German. An English translation is planned for the future!

This is a companion tool for Pen & Paper RPGs. Game Masters get a campaign graph (people, places, factions, events, items, relationships), a wiki, live table popups, shops, combat, and an AI-assisted idea forge. Players get interactive character sheets and a messenger.

The rules logic is currently tailored to a homebrew Cyberpunk system called **NeotopiA** (World of Darkness–style attributes, Shadowrun cyberware/rigging, Mage spheres). Other systems are a later idea, not the current work.

### 🛠️ Tech Stack
* **Backend:** Python 3.12, FastAPI
* **Database:** Neo4j 5 (Docker)
* **Frontend:** React 19, TypeScript, Vite

*Disclaimer: This is a purely passion-driven, completely overengineered hobby project! (PS: The code is heavily AI-assisted / prompt-engineered).*

### 🚀 What's in, what's next
* **In:** campaign graph + wiki, GM/player roles, character creation, shops, messenger, live popups, optional AI drafts (Gemini or Mistral), optional Spotify playlists on locations/events.
* **Next (when we get to it):** Cyberdecks as real items, more table-polish, maybe other rule systems later. English UI is still only a wish.

### ⚙️ Setup

Local dev on Windows. Neo4j **must** come from Compose (named volume) — never a one-off `docker run`, that throws the graph away.

```bash
# 1. Neo4j
docker compose up -d neo4j

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy ..\.env.example .env
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# (see CLAUDE.md "Bekannte Stolpersteine" — no --reload on Windows)

# 3. Frontend (second terminal)
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
| `GEMINI_API_KEY` / `MISTRAL_API_KEY` | optional | AI drafts in the "Ideenschmiede" (✨ KI + Beratung). Without a key the rest of the app works; only those buttons will error. |
| `KI_PROVIDER` | optional | `"gemini"` or `"mistral"` — which of the two keys is active. |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | optional | Playlists on locations/events, music follows the active party. Without keys the rest of the app works; only "Connect Spotify" will error. |

Every third-party key is your own — get one from the respective provider's dashboard (links and setup steps are in the comments inside `.env.example`). Nothing you enter there ever leaves your machine except straight to that provider's API.
