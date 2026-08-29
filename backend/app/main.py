from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.campaigns.routes import einstellungen_router
from app.campaigns.routes import router as campaigns_router
from app.config import settings
from app.entities.routes import router as entities_router
from app.graph.routes import router as graph_router
from app.items.routes import router as items_router
from app.items.routes import campaign_router as items_campaign_router
from app.traits.routes import router as traits_router
from app.traits.seed import seed_traits
from app.db.migrate import apply_migrations
from app.players.routes import gm_router as spieler_gm_router, login_router
from app.db.neo4j_driver import close_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    await apply_migrations()
    await seed_traits()
    yield
    await close_driver()


app = FastAPI(title="PnPTool API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(einstellungen_router)
app.include_router(entities_router)
app.include_router(graph_router)
app.include_router(items_router)
app.include_router(items_campaign_router)
app.include_router(traits_router)
app.include_router(login_router)
app.include_router(spieler_gm_router)

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
