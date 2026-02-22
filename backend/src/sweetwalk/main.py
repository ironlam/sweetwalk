from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sweetwalk.config import settings
from sweetwalk.graph.loader import load_city_graphs
from sweetwalk.graph.store import graph_store
from sweetwalk.routing.router import router as routing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_city_graphs(settings.data_dir)
    yield


app = FastAPI(title="Sweet Walk API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router)


@app.get("/health")
def health():
    return {"status": "ok", "cities": graph_store.cities}
