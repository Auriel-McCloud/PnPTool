---
title: Tech-Stack
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [backend, frontend, datenmodell]
sources: [../../../CLAUDE.md]
status: aktuell
---

# Tech-Stack

- **Backend:** FastAPI, Neo4j async driver, JWT in httpOnly-Cookie, bcrypt
  direkt (nicht passlib — inkompatibel mit `bcrypt>=4.1`, siehe
  [[../../ENTWICKLUNGSHISTORIE.md]])
- **Datenbank:** Neo4j 5 in Docker — siehe [[neo4j-datenmodell]]
- **Frontend:** React 19 + TypeScript + Vite, Cytoscape.js **direkt**, kein
  Wrapper (`react-cytoscapejs` hatte Re-Layout-Bugs bei jedem Re-Render)
- **Deployment:** aktuell Windows-Dev, später Debian/nginx geplant

## Lokaler Start

```powershell
docker compose up -d neo4j     # NIE docker run, siehe neo4j-datenmodell
cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001  # ohne --reload!
cd frontend && npm run dev
```

`uvicorn --reload` ist auf Windows defekt (Reloader-Parent kann sterben,
Worker serviert alten Code weiter) — siehe
[[../../ENTWICKLUNGSHISTORIE.md]] für die volle Stolperstein-Liste.

## Siehe auch

- [[neo4j-datenmodell]] — Docker-Compose-Pflicht im Detail
- [[../../ENTWICKLUNGSHISTORIE.md]] — alle technischen Stolpersteine
