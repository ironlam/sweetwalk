# Sweet Walk Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MVP web app that finds the best walking route A→B based on 6 quality dimensions (greenery, heritage, tranquility, water, culture, charm) for Paris, London, Munich, and New York.

**Architecture:** Monorepo with a Next.js PWA frontend (Mapbox GL JS) and a Python FastAPI backend. The backend holds pre-computed city walking graphs in memory and runs multi-criteria A* routing. Data pipeline uses osmnx + geopandas to extract OSM pedestrian graphs and score each street segment.

**Tech Stack:** Next.js 14+ / TypeScript / Tailwind / Mapbox GL JS | Python 3.12+ / FastAPI / osmnx / networkx / geopandas | Supabase (auth/DB) | uv (Python package manager)

**Design doc:** `docs/plans/2026-02-22-sweet-walk-design.md`

---

## Project Structure

```
sweetwalk/
├── frontend/                    # Next.js PWA
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Map.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── PreferenceIcons.tsx
│   │   │   ├── RouteCard.tsx
│   │   │   └── RouteResults.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── hooks/
│   │       └── useRoutes.ts
│   ├── public/
│   │   └── icons/
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── backend/                     # Python FastAPI
│   ├── src/
│   │   └── sweetwalk/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── routing/
│   │       │   ├── __init__.py
│   │       │   ├── engine.py
│   │       │   ├── schemas.py
│   │       │   └── router.py
│   │       ├── scoring/
│   │       │   ├── __init__.py
│   │       │   ├── dimensions.py
│   │       │   └── scorer.py
│   │       ├── graph/
│   │       │   ├── __init__.py
│   │       │   ├── loader.py
│   │       │   └── store.py
│   │       └── pipeline/
│   │           ├── __init__.py
│   │           ├── extract.py
│   │           ├── score.py
│   │           └── cli.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_scoring.py
│   │   ├── test_routing.py
│   │   └── test_api.py
│   ├── data/
│   ├── pyproject.toml
│   └── .python-version
├── docs/plans/
├── .env.example
└── .gitignore
```

---

## Task 1: Backend Scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/src/sweetwalk/__init__.py`
- Create: `backend/src/sweetwalk/main.py`
- Create: `backend/src/sweetwalk/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `.env.example`

**Step 1: Initialize Python project with uv**

```bash
cd backend
uv init --package sweetwalk
```

Then replace the generated `pyproject.toml` with:

```toml
[project]
name = "sweetwalk"
version = "0.1.0"
description = "Multi-criteria walking route optimizer"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115",
    "osmnx>=2.0",
    "networkx>=3.4",
    "geopandas>=1.0",
    "shapely>=2.0",
    "numpy>=2.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.scripts]
sweetwalk-pipeline = "sweetwalk.pipeline.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "httpx>=0.27",
    "pytest-asyncio>=0.24",
]
```

Write `.python-version`:
```
3.12
```

**Step 2: Create config module**

`backend/src/sweetwalk/config.py`:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mapbox_token: str = ""
    data_dir: str = "data"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "SWEETWALK_", "env_file": ".env"}


settings = Settings()
```

**Step 3: Create FastAPI app entry point**

`backend/src/sweetwalk/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sweetwalk.config import settings

app = FastAPI(title="Sweet Walk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

`backend/src/sweetwalk/__init__.py`: empty file.

**Step 4: Create test fixtures**

`backend/tests/__init__.py`: empty file.

`backend/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient

from sweetwalk.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

**Step 5: Write and run health check test**

`backend/tests/test_api.py`:
```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Run: `cd backend && uv run pytest tests/test_api.py -v`
Expected: PASS

**Step 6: Install dependencies and verify**

```bash
cd backend && uv sync
```

**Step 7: Commit**

```bash
git add backend/ .env.example
git commit -m "Scaffold Python backend with FastAPI and uv"
```

---

## Task 2: Frontend Scaffolding

**Files:**
- Create: `frontend/` (via create-next-app)
- Modify: `frontend/package.json` (add mapbox-gl)
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`

**Step 1: Create Next.js app**

```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app \
  --src-dir --import-alias "@/*" --no-turbopack
```

**Step 2: Install Mapbox GL JS**

```bash
cd frontend && npm install mapbox-gl @types/mapbox-gl
```

**Step 3: Create a minimal home page with a placeholder map**

`frontend/src/app/page.tsx`:
```tsx
export default function Home() {
  return (
    <main className="h-screen w-screen relative">
      <div className="absolute inset-0 bg-slate-100 flex items-center justify-center">
        <h1 className="text-3xl font-bold text-slate-800">Sweet Walk</h1>
      </div>
    </main>
  );
}
```

**Step 4: Run dev server to verify**

```bash
cd frontend && npm run dev
```

Open http://localhost:3000 — should see "Sweet Walk" centered.

**Step 5: Commit**

```bash
git add frontend/
git commit -m "Scaffold Next.js frontend with Tailwind"
```

---

## Task 3: OSM Graph Extraction Pipeline

**Files:**
- Create: `backend/src/sweetwalk/pipeline/__init__.py`
- Create: `backend/src/sweetwalk/pipeline/extract.py`
- Create: `backend/src/sweetwalk/pipeline/cli.py`
- Test: `backend/tests/test_pipeline.py`

**Step 1: Write failing test for graph extraction**

`backend/tests/test_pipeline.py`:
```python
import networkx as nx
from sweetwalk.pipeline.extract import extract_pedestrian_graph


def test_extract_pedestrian_graph_returns_multidigraph():
    # Use a small area: Île de la Cité, Paris (tiny, fast to download)
    G = extract_pedestrian_graph("Île de la Cité, Paris, France")
    assert isinstance(G, nx.MultiDiGraph)
    assert G.number_of_nodes() > 10
    assert G.number_of_edges() > 10


def test_edges_have_geometry():
    G = extract_pedestrian_graph("Île de la Cité, Paris, France")
    # At least some edges should have geometry
    edge_data = next(iter(G.edges(data=True)))
    u, v, data = edge_data
    assert "length" in data
```

Run: `cd backend && uv run pytest tests/test_pipeline.py -v`
Expected: FAIL (module not found)

**Step 2: Implement graph extraction**

`backend/src/sweetwalk/pipeline/__init__.py`: empty file.

`backend/src/sweetwalk/pipeline/extract.py`:
```python
import osmnx as ox
import networkx as nx
from pathlib import Path


def extract_pedestrian_graph(place_name: str) -> nx.MultiDiGraph:
    """Extract the pedestrian walking network for a given place."""
    G = ox.graph_from_place(place_name, network_type="walk")
    # Project to UTM for accurate distance calculations
    G = ox.project_graph(G)
    return G


def save_graph(G: nx.MultiDiGraph, path: Path) -> None:
    """Serialize graph to GraphML format."""
    ox.save_graphml(G, filepath=path)


def load_graph(path: Path) -> nx.MultiDiGraph:
    """Load graph from GraphML format."""
    return ox.load_graphml(filepath=path)
```

**Step 3: Run tests**

Run: `cd backend && uv run pytest tests/test_pipeline.py -v`
Expected: PASS (requires internet, downloads OSM data — may take 10-30s)

**Step 4: Create pipeline CLI**

`backend/src/sweetwalk/pipeline/cli.py`:
```python
import argparse
from pathlib import Path
from sweetwalk.pipeline.extract import extract_pedestrian_graph, save_graph


CITIES = {
    "paris": "Paris, France",
    "london": "London, United Kingdom",
    "munich": "Munich, Germany",
    "nyc": "New York City, New York, USA",
}


def main():
    parser = argparse.ArgumentParser(description="Sweet Walk data pipeline")
    parser.add_argument(
        "city",
        choices=list(CITIES.keys()),
        help="City to process",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory for graph files",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    place = CITIES[args.city]
    print(f"Extracting pedestrian graph for {place}...")

    G = extract_pedestrian_graph(place)
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    output_path = args.output_dir / f"{args.city}.graphml"
    save_graph(G, output_path)
    print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()
```

**Step 5: Commit**

```bash
git add backend/src/sweetwalk/pipeline/ backend/tests/test_pipeline.py
git commit -m "Add OSM pedestrian graph extraction pipeline"
```

---

## Task 4: Scoring Engine

**Files:**
- Create: `backend/src/sweetwalk/scoring/__init__.py`
- Create: `backend/src/sweetwalk/scoring/dimensions.py`
- Create: `backend/src/sweetwalk/scoring/scorer.py`
- Test: `backend/tests/test_scoring.py`

**Step 1: Write failing tests for individual dimension scorers**

`backend/tests/test_scoring.py`:
```python
import numpy as np
import networkx as nx
from shapely.geometry import LineString, Point, Polygon
import geopandas as gpd

from sweetwalk.scoring.dimensions import (
    score_greenery,
    score_heritage,
    score_tranquility,
    score_water,
    score_culture,
    score_charm,
)
from sweetwalk.scoring.scorer import score_graph


def _make_edge_geom():
    """A 100m street segment as a LineString."""
    return LineString([(0, 0), (100, 0)])


def test_score_tranquility_pedestrian_street():
    score = score_tranquility(highway_type="pedestrian", maxspeed=None)
    assert score == 1.0


def test_score_tranquility_primary_road():
    score = score_tranquility(highway_type="primary", maxspeed=50)
    assert score < 0.4


def test_score_tranquility_residential():
    score = score_tranquility(highway_type="residential", maxspeed=30)
    assert 0.5 <= score <= 0.8


def test_score_greenery_with_parks():
    edge_geom = _make_edge_geom()
    # A park polygon overlapping the buffer zone
    park = gpd.GeoDataFrame(
        {"geometry": [Polygon([(10, -10), (50, -10), (50, 30), (10, 30)])]},
        crs="EPSG:3857",
    )
    trees = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:3857")
    score = score_greenery(edge_geom, green_areas=park, trees=trees, buffer_m=50)
    assert score > 0.0


def test_score_greenery_no_green():
    edge_geom = _make_edge_geom()
    empty = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:3857")
    score = score_greenery(edge_geom, green_areas=empty, trees=empty, buffer_m=50)
    assert score == 0.0
```

Run: `cd backend && uv run pytest tests/test_scoring.py -v`
Expected: FAIL (modules not found)

**Step 2: Implement dimension scoring functions**

`backend/src/sweetwalk/scoring/__init__.py`: empty file.

`backend/src/sweetwalk/scoring/dimensions.py`:
```python
import numpy as np
from shapely.geometry import LineString
import geopandas as gpd


# Highway type to tranquility score mapping
TRANQUILITY_MAP = {
    "pedestrian": 1.0,
    "footway": 1.0,
    "path": 0.95,
    "living_street": 0.9,
    "cycleway": 0.85,
    "residential": 0.7,
    "service": 0.6,
    "unclassified": 0.5,
    "tertiary": 0.4,
    "secondary": 0.3,
    "primary": 0.2,
    "trunk": 0.1,
    "motorway": 0.0,
}


def score_tranquility(highway_type: str, maxspeed: float | None) -> float:
    """Score based on road type and speed limit. Pedestrian streets = 1.0."""
    if isinstance(highway_type, list):
        highway_type = highway_type[0]
    base = TRANQUILITY_MAP.get(highway_type, 0.5)

    # Speed penalty: higher speed = less tranquil
    if maxspeed is not None and maxspeed > 0:
        speed_factor = max(0.0, 1.0 - (maxspeed / 130.0))
        base = base * 0.7 + speed_factor * 0.3

    return round(min(1.0, max(0.0, base)), 3)


def score_greenery(
    edge_geom: LineString,
    green_areas: gpd.GeoDataFrame,
    trees: gpd.GeoDataFrame,
    buffer_m: float = 50.0,
) -> float:
    """Score based on green area coverage and tree density in buffer zone."""
    buffer = edge_geom.buffer(buffer_m)
    buffer_area = buffer.area

    if buffer_area == 0:
        return 0.0

    # Green area coverage ratio
    green_coverage = 0.0
    if not green_areas.empty:
        clipped = green_areas.clip(buffer)
        if not clipped.empty:
            green_coverage = clipped.geometry.area.sum() / buffer_area

    # Tree density bonus (cap at 0.3 bonus)
    tree_bonus = 0.0
    if not trees.empty:
        trees_in_buffer = trees[trees.geometry.within(buffer)]
        # Normalize: 1 tree per 10m of street = max bonus
        tree_density = len(trees_in_buffer) / max(1.0, edge_geom.length / 10.0)
        tree_bonus = min(0.3, tree_density * 0.3)

    return round(min(1.0, green_coverage + tree_bonus), 3)


def score_heritage(
    edge_geom: LineString,
    heritage_pois: gpd.GeoDataFrame,
    buffer_m: float = 50.0,
) -> float:
    """Score based on density of historic/heritage POIs in buffer zone."""
    if heritage_pois.empty:
        return 0.0

    buffer = edge_geom.buffer(buffer_m)
    pois_in_buffer = heritage_pois[heritage_pois.geometry.within(buffer)]
    count = len(pois_in_buffer)

    # Sigmoid-like scaling: 1 POI = 0.3, 3 POIs = 0.7, 5+ POIs = ~1.0
    score = 1.0 - 1.0 / (1.0 + count * 0.5)
    return round(min(1.0, score), 3)


def score_water(
    edge_geom: LineString,
    water_features: gpd.GeoDataFrame,
    buffer_m: float = 50.0,
) -> float:
    """Score based on proximity and parallelism to water features."""
    if water_features.empty:
        return 0.0

    buffer = edge_geom.buffer(buffer_m)
    water_in_buffer = water_features.clip(buffer)

    if water_in_buffer.empty:
        return 0.0

    # Base score: water is nearby
    score = 0.5

    # Parallelism bonus: does the street run along water?
    water_length_in_buffer = water_in_buffer.geometry.length.sum()
    parallelism = min(1.0, water_length_in_buffer / max(1.0, edge_geom.length))
    score += 0.5 * parallelism

    return round(min(1.0, score), 3)


def score_culture(
    edge_geom: LineString,
    culture_pois: gpd.GeoDataFrame,
    buffer_m: float = 50.0,
) -> float:
    """Score based on density of cultural POIs in buffer zone."""
    if culture_pois.empty:
        return 0.0

    buffer = edge_geom.buffer(buffer_m)
    pois_in_buffer = culture_pois[culture_pois.geometry.within(buffer)]
    count = len(pois_in_buffer)

    score = 1.0 - 1.0 / (1.0 + count * 0.5)
    return round(min(1.0, score), 3)


def score_charm(
    highway_type: str,
    cafe_count: int,
    has_nice_architecture: bool,
) -> float:
    """Composite score: street type + cafe density + architecture."""
    # Street type component (0-0.4)
    charm_streets = {"pedestrian": 0.4, "living_street": 0.35, "footway": 0.3}
    if isinstance(highway_type, list):
        highway_type = highway_type[0]
    street_score = charm_streets.get(highway_type, 0.15)

    # Cafe density component (0-0.35)
    cafe_score = min(0.35, cafe_count * 0.07)

    # Architecture component (0-0.25)
    arch_score = 0.25 if has_nice_architecture else 0.0

    return round(min(1.0, street_score + cafe_score + arch_score), 3)
```

**Step 3: Run tests**

Run: `cd backend && uv run pytest tests/test_scoring.py -v`
Expected: PASS

**Step 4: Implement the graph scorer (applies all dimensions to a full graph)**

`backend/src/sweetwalk/scoring/scorer.py`:
```python
import numpy as np
import osmnx as ox
import geopandas as gpd
from shapely.geometry import LineString
import networkx as nx

from sweetwalk.scoring.dimensions import (
    score_greenery,
    score_heritage,
    score_tranquility,
    score_water,
    score_culture,
    score_charm,
)


# OSM tags for extracting feature layers
GREEN_TAGS = {"leisure": ["park", "garden", "nature_reserve"], "landuse": ["grass", "forest", "meadow"]}
TREE_TAGS = {"natural": ["tree", "tree_row"]}
HERITAGE_TAGS = {"historic": True, "heritage": True, "tourism": ["attraction"]}
WATER_TAGS = {"natural": ["water"], "waterway": ["river", "canal", "stream"]}
CULTURE_TAGS = {"tourism": ["museum", "gallery", "artwork"], "amenity": ["arts_centre", "theatre"]}
CAFE_TAGS = {"amenity": ["cafe", "restaurant"]}


def extract_feature_layers(place_name: str) -> dict[str, gpd.GeoDataFrame]:
    """Download OSM feature layers needed for scoring."""
    layers = {}

    for name, tags in [
        ("green_areas", GREEN_TAGS),
        ("trees", TREE_TAGS),
        ("heritage_pois", HERITAGE_TAGS),
        ("water_features", WATER_TAGS),
        ("culture_pois", CULTURE_TAGS),
        ("cafes", CAFE_TAGS),
    ]:
        try:
            gdf = ox.features_from_place(place_name, tags=tags)
            # Project to match the graph CRS (UTM)
            gdf = gdf.to_crs(epsg=3857)
            layers[name] = gdf
        except Exception:
            layers[name] = gpd.GeoDataFrame(geometry=[], crs="EPSG:3857")

    return layers


def score_graph(G: nx.MultiDiGraph, layers: dict[str, gpd.GeoDataFrame]) -> nx.MultiDiGraph:
    """Compute 6 quality scores for every edge in the graph.

    Adds 'scores' attribute to each edge: np.array([greenery, heritage, tranquility, water, culture, charm])
    """
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get edge geometry
        if "geometry" in data:
            edge_geom = data["geometry"]
        else:
            # Straight line between nodes
            u_data, v_data = G.nodes[u], G.nodes[v]
            edge_geom = LineString([(u_data["x"], u_data["y"]), (v_data["x"], v_data["y"])])

        highway = data.get("highway", "residential")
        maxspeed_raw = data.get("maxspeed")
        maxspeed = None
        if maxspeed_raw:
            try:
                maxspeed = float(str(maxspeed_raw).split()[0])
            except (ValueError, IndexError):
                maxspeed = None

        # Compute each dimension
        greenery = score_greenery(edge_geom, layers["green_areas"], layers["trees"])
        heritage = score_heritage(edge_geom, layers["heritage_pois"])
        tranquility = score_tranquility(highway, maxspeed)
        water = score_water(edge_geom, layers["water_features"])
        culture = score_culture(edge_geom, layers["culture_pois"])

        # Charm needs cafe count in buffer
        buffer = edge_geom.buffer(50)
        cafes = layers["cafes"]
        cafe_count = 0
        if not cafes.empty:
            cafe_count = len(cafes[cafes.geometry.within(buffer)])
        has_nice_arch = highway in ("pedestrian", "living_street")
        charm_val = score_charm(highway, cafe_count, has_nice_arch)

        data["scores"] = np.array(
            [greenery, heritage, tranquility, water, culture, charm_val],
            dtype=np.float32,
        )

    return G
```

**Step 5: Commit**

```bash
git add backend/src/sweetwalk/scoring/ backend/tests/test_scoring.py
git commit -m "Add 6-dimension scoring engine with buffer zone analysis"
```

---

## Task 5: Multi-Criteria Routing Engine

**Files:**
- Create: `backend/src/sweetwalk/routing/__init__.py`
- Create: `backend/src/sweetwalk/routing/engine.py`
- Create: `backend/src/sweetwalk/routing/schemas.py`
- Test: `backend/tests/test_routing.py`

**Step 1: Write failing tests for the routing engine**

`backend/tests/test_routing.py`:
```python
import numpy as np
import networkx as nx
from sweetwalk.routing.engine import find_routes
from sweetwalk.routing.schemas import RouteRequest, RouteResult


def _make_scored_graph():
    """Create a small test graph with scores.

    Layout:
        A --1-- B --1-- C  (direct path, low scores)
        |               |
        2               2
        |               |
        D --1-- E --1-- F  (scenic path, high scores)

    Edge weights are distances. A→B→C is direct but ugly.
    A→D→E→F→C is scenic but longer.
    """
    G = nx.MultiDiGraph()

    nodes = {
        "A": (0, 0),
        "B": (100, 0),
        "C": (200, 0),
        "D": (0, 100),
        "E": (100, 100),
        "F": (200, 100),
    }
    for name, (x, y) in nodes.items():
        G.add_node(name, x=x, y=y)

    low_scores = np.array([0.1, 0.1, 0.2, 0.0, 0.1, 0.1], dtype=np.float32)
    high_scores = np.array([0.9, 0.8, 0.9, 0.7, 0.8, 0.9], dtype=np.float32)

    # Direct path edges (low quality)
    G.add_edge("A", "B", 0, length=100, scores=low_scores)
    G.add_edge("B", "A", 0, length=100, scores=low_scores)
    G.add_edge("B", "C", 0, length=100, scores=low_scores)
    G.add_edge("C", "B", 0, length=100, scores=low_scores)

    # Scenic path edges (high quality)
    G.add_edge("A", "D", 0, length=200, scores=high_scores)
    G.add_edge("D", "A", 0, length=200, scores=high_scores)
    G.add_edge("D", "E", 0, length=100, scores=high_scores)
    G.add_edge("E", "D", 0, length=100, scores=high_scores)
    G.add_edge("E", "F", 0, length=100, scores=high_scores)
    G.add_edge("F", "E", 0, length=100, scores=high_scores)
    G.add_edge("F", "C", 0, length=200, scores=high_scores)
    G.add_edge("C", "F", 0, length=200, scores=high_scores)

    return G


def test_find_routes_returns_three_routes():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)  # Equal weights
    routes = find_routes(G, "A", "C", weights)
    assert len(routes) == 3


def test_quick_route_is_shortest():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)
    routes = find_routes(G, "A", "C", weights)
    quick = routes[0]  # First route = Quick
    assert quick.distance <= routes[1].distance
    assert quick.distance <= routes[2].distance


def test_best_walk_has_highest_score():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)
    routes = find_routes(G, "A", "C", weights)
    best = routes[2]  # Third route = Best Walk
    quick = routes[0]
    assert best.quality_score >= quick.quality_score
```

Run: `cd backend && uv run pytest tests/test_routing.py -v`
Expected: FAIL (modules not found)

**Step 2: Create Pydantic schemas**

`backend/src/sweetwalk/routing/__init__.py`: empty file.

`backend/src/sweetwalk/routing/schemas.py`:
```python
from pydantic import BaseModel
import numpy as np


class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    weights: list[float] = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    model_config = {"json_schema_extra": {
        "examples": [{
            "start_lat": 48.8566,
            "start_lon": 2.3522,
            "end_lat": 48.8606,
            "end_lon": 2.3376,
            "weights": [1.0, 0.5, 1.0, 0.8, 0.3, 0.5],
        }]
    }}


class RouteResult(BaseModel):
    route_type: str  # "quick", "balanced", "best_walk"
    nodes: list[str | int]
    coordinates: list[list[float]]  # [[lon, lat], ...]
    distance: float  # meters
    duration: float  # seconds (estimated at 5 km/h)
    quality_score: float  # weighted quality score 0-1
    dimension_scores: list[float]  # average score per dimension [6]


class RoutesResponse(BaseModel):
    routes: list[RouteResult]
    city: str
```

**Step 3: Implement the routing engine**

`backend/src/sweetwalk/routing/engine.py`:
```python
import heapq
import numpy as np
import networkx as nx
from sweetwalk.routing.schemas import RouteResult

WALKING_SPEED_MS = 5.0 / 3.6  # 5 km/h in m/s
DIMENSION_NAMES = ["greenery", "heritage", "tranquility", "water", "culture", "charm"]


def _weighted_cost(distance: float, scores: np.ndarray, weights: np.ndarray, alpha: float) -> float:
    """Compute edge cost: distance penalized by lack of quality.

    cost = distance * (1 + alpha * (1 - dot(scores, normalized_weights)))
    """
    w_sum = weights.sum()
    if w_sum == 0:
        return distance
    norm_weights = weights / w_sum
    quality = float(np.dot(scores, norm_weights))
    return distance * (1.0 + alpha * (1.0 - quality))


def _astar(
    G: nx.MultiDiGraph,
    source,
    target,
    weights: np.ndarray,
    alpha: float,
) -> tuple[list, float]:
    """A* search with multi-criteria cost function.

    Returns (path_nodes, total_distance).
    """
    # Heuristic: Euclidean distance between nodes
    target_x = G.nodes[target].get("x", 0)
    target_y = G.nodes[target].get("y", 0)

    def heuristic(node):
        nx_data = G.nodes[node]
        dx = nx_data.get("x", 0) - target_x
        dy = nx_data.get("y", 0) - target_y
        return (dx**2 + dy**2) ** 0.5

    # Priority queue: (f_score, counter, node)
    counter = 0
    open_set = [(heuristic(source), counter, source)]
    came_from = {}
    g_score = {source: 0.0}
    dist_score = {source: 0.0}  # Track actual distance separately

    while open_set:
        f, _, current = heapq.heappop(open_set)

        if current == target:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, dist_score[target]

        for _, neighbor, edge_data in G.edges(current, data=True):
            distance = edge_data.get("length", 1.0)
            scores = edge_data.get("scores", np.zeros(6, dtype=np.float32))
            cost = _weighted_cost(distance, scores, weights, alpha)
            tentative_g = g_score[current] + cost
            tentative_dist = dist_score[current] + distance

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                dist_score[neighbor] = tentative_dist
                counter += 1
                heapq.heappush(open_set, (tentative_g + heuristic(neighbor), counter, neighbor))

    return [], 0.0  # No path found


def _compute_route_scores(G: nx.MultiDiGraph, path: list) -> tuple[float, list[float]]:
    """Compute average dimension scores along a path."""
    if len(path) < 2:
        return 0.0, [0.0] * 6

    all_scores = []
    total_length = 0.0

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            first_edge = list(edge_data.values())[0]
            scores = first_edge.get("scores", np.zeros(6, dtype=np.float32))
            length = first_edge.get("length", 1.0)
            all_scores.append(scores * length)
            total_length += length

    if total_length == 0:
        return 0.0, [0.0] * 6

    weighted_avg = np.sum(all_scores, axis=0) / total_length
    dimension_scores = [round(float(s), 3) for s in weighted_avg]
    overall = round(float(np.mean(weighted_avg)), 3)

    return overall, dimension_scores


def _path_to_coordinates(G: nx.MultiDiGraph, path: list) -> list[list[float]]:
    """Convert node path to [[lon, lat], ...] coordinates."""
    coords = []
    for node in path:
        node_data = G.nodes[node]
        coords.append([node_data.get("x", 0), node_data.get("y", 0)])
    return coords


def find_routes(
    G: nx.MultiDiGraph,
    source,
    target,
    weights: np.ndarray,
) -> list[RouteResult]:
    """Find 3 route options: Quick, Balanced, Best Walk."""
    alphas = [
        ("quick", 0.0),
        ("balanced", 0.5),
        ("best_walk", 1.0),
    ]

    routes = []
    seen_paths = set()

    for route_type, alpha in alphas:
        path, distance = _astar(G, source, target, weights, alpha)

        if not path:
            continue

        # Dedup: if identical to a previous route, increase alpha slightly
        path_key = tuple(path)
        if path_key in seen_paths and alpha < 2.0:
            path2, distance2 = _astar(G, source, target, weights, alpha * 1.5)
            if path2 and tuple(path2) not in seen_paths:
                path, distance = path2, distance2
                path_key = tuple(path)

        seen_paths.add(path_key)
        quality_score, dimension_scores = _compute_route_scores(G, path)
        coordinates = _path_to_coordinates(G, path)
        duration = distance / WALKING_SPEED_MS

        routes.append(RouteResult(
            route_type=route_type,
            nodes=[str(n) for n in path],
            coordinates=coordinates,
            distance=round(distance, 1),
            duration=round(duration, 1),
            quality_score=quality_score,
            dimension_scores=dimension_scores,
        ))

    return routes
```

**Step 4: Run routing tests**

Run: `cd backend && uv run pytest tests/test_routing.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/sweetwalk/routing/ backend/tests/test_routing.py
git commit -m "Add multi-criteria A* routing engine with 3 route options"
```

---

## Task 6: FastAPI Route Endpoint

**Files:**
- Create: `backend/src/sweetwalk/graph/__init__.py`
- Create: `backend/src/sweetwalk/graph/store.py`
- Create: `backend/src/sweetwalk/graph/loader.py`
- Create: `backend/src/sweetwalk/routing/router.py`
- Modify: `backend/src/sweetwalk/main.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Write failing test for the route endpoint**

Append to `backend/tests/test_api.py`:
```python
import numpy as np
import networkx as nx
from sweetwalk.graph.store import graph_store


def _seed_test_graph():
    """Seed graph store with a tiny test graph."""
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:4326"
    low = np.array([0.1, 0.1, 0.2, 0.0, 0.1, 0.1], dtype=np.float32)
    high = np.array([0.9, 0.8, 0.9, 0.7, 0.8, 0.9], dtype=np.float32)

    G.add_node(1, x=2.3522, y=48.8566)
    G.add_node(2, x=2.3400, y=48.8580)
    G.add_node(3, x=2.3376, y=48.8606)
    G.add_node(4, x=2.3450, y=48.8620)

    G.add_edge(1, 2, 0, length=200, scores=low)
    G.add_edge(2, 3, 0, length=200, scores=low)
    G.add_edge(1, 4, 0, length=300, scores=high)
    G.add_edge(4, 3, 0, length=300, scores=high)
    # Reverse edges
    G.add_edge(2, 1, 0, length=200, scores=low)
    G.add_edge(3, 2, 0, length=200, scores=low)
    G.add_edge(4, 1, 0, length=300, scores=high)
    G.add_edge(3, 4, 0, length=300, scores=high)

    graph_store.graphs["test_city"] = G
    return G


def test_route_endpoint(client):
    _seed_test_graph()
    response = client.post("/api/route", json={
        "start_lat": 48.8566,
        "start_lon": 2.3522,
        "end_lat": 48.8606,
        "end_lon": 2.3376,
        "weights": [1, 1, 1, 1, 1, 1],
    })
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) >= 1


def test_route_endpoint_missing_coords(client):
    response = client.post("/api/route", json={
        "start_lat": 48.8566,
        "weights": [1, 1, 1, 1, 1, 1],
    })
    assert response.status_code == 422
```

**Step 2: Create graph store (in-memory)**

`backend/src/sweetwalk/graph/__init__.py`: empty file.

`backend/src/sweetwalk/graph/store.py`:
```python
import networkx as nx
from scipy.spatial import KDTree
import numpy as np


class GraphStore:
    """In-memory store for city walking graphs."""

    def __init__(self):
        self.graphs: dict[str, nx.MultiDiGraph] = {}
        self._kdtrees: dict[str, KDTree] = {}
        self._node_lists: dict[str, list] = {}

    def add_city(self, city: str, G: nx.MultiDiGraph) -> None:
        self.graphs[city] = G
        # Build KDTree for nearest-node lookup
        nodes = list(G.nodes())
        coords = np.array([(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes])
        self._kdtrees[city] = KDTree(coords)
        self._node_lists[city] = nodes

    def find_nearest_node(self, city: str, lon: float, lat: float):
        """Find the nearest graph node to a given coordinate."""
        tree = self._kdtrees[city]
        nodes = self._node_lists[city]
        _, idx = tree.query([lon, lat])
        return nodes[idx]

    def find_city(self, lon: float, lat: float) -> str | None:
        """Determine which city a coordinate belongs to (simple bounding box check)."""
        for city, G in self.graphs.items():
            nodes = self._node_lists[city]
            coords = np.array([(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes])
            min_x, min_y = coords.min(axis=0)
            max_x, max_y = coords.max(axis=0)
            margin = 0.01  # ~1km margin
            if min_x - margin <= lon <= max_x + margin and min_y - margin <= lat <= max_y + margin:
                return city
        return None

    @property
    def cities(self) -> list[str]:
        return list(self.graphs.keys())


graph_store = GraphStore()
```

**Step 3: Create the API router**

`backend/src/sweetwalk/routing/router.py`:
```python
import numpy as np
from fastapi import APIRouter, HTTPException

from sweetwalk.graph.store import graph_store
from sweetwalk.routing.engine import find_routes
from sweetwalk.routing.schemas import RouteRequest, RoutesResponse

router = APIRouter(prefix="/api")


@router.post("/route", response_model=RoutesResponse)
def compute_route(req: RouteRequest):
    # Find which city these coordinates belong to
    city = graph_store.find_city(req.start_lon, req.start_lat)
    if city is None:
        raise HTTPException(status_code=404, detail="No city graph covers these coordinates")

    G = graph_store.graphs[city]

    # Find nearest nodes to start/end coordinates
    source = graph_store.find_nearest_node(city, req.start_lon, req.start_lat)
    target = graph_store.find_nearest_node(city, req.end_lon, req.end_lat)

    if source == target:
        raise HTTPException(status_code=400, detail="Start and end are too close")

    weights = np.array(req.weights, dtype=np.float32)
    routes = find_routes(G, source, target, weights)

    if not routes:
        raise HTTPException(status_code=404, detail="No walking route found")

    return RoutesResponse(routes=routes, city=city)
```

**Step 4: Wire router into the FastAPI app**

Update `backend/src/sweetwalk/main.py` — add the router import and include it:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sweetwalk.config import settings
from sweetwalk.routing.router import router as routing_router

app = FastAPI(title="Sweet Walk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 5: Add scipy dependency**

Add `scipy>=1.14` to the `dependencies` list in `backend/pyproject.toml`, then:
```bash
cd backend && uv sync
```

**Step 6: Run all API tests**

Run: `cd backend && uv run pytest tests/test_api.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/
git commit -m "Add route API endpoint with graph store and nearest-node lookup"
```

---

## Task 7: Graph Loader + Pipeline Integration

**Files:**
- Create: `backend/src/sweetwalk/graph/loader.py`
- Modify: `backend/src/sweetwalk/pipeline/cli.py` (add scoring step)
- Modify: `backend/src/sweetwalk/main.py` (load graphs at startup)

**Step 1: Create graph loader**

`backend/src/sweetwalk/graph/loader.py`:
```python
from pathlib import Path
import osmnx as ox
import networkx as nx

from sweetwalk.graph.store import graph_store


def load_city_graphs(data_dir: str | Path) -> None:
    """Load all pre-computed city graphs from the data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        return

    for graphml_file in data_path.glob("*.graphml"):
        city = graphml_file.stem
        G = ox.load_graphml(filepath=graphml_file)
        graph_store.add_city(city, G)
        print(f"Loaded {city}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
```

**Step 2: Update main.py to load graphs at startup**

Update `backend/src/sweetwalk/main.py` — add lifespan:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sweetwalk.config import settings
from sweetwalk.graph.loader import load_city_graphs
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
    from sweetwalk.graph.store import graph_store
    return {"status": "ok", "cities": graph_store.cities}
```

**Step 3: Update pipeline CLI to include scoring**

Update `backend/src/sweetwalk/pipeline/cli.py` to also run the scoring step after graph extraction:
```python
import argparse
from pathlib import Path
from sweetwalk.pipeline.extract import extract_pedestrian_graph, save_graph
from sweetwalk.scoring.scorer import extract_feature_layers, score_graph


CITIES = {
    "paris": "Paris, France",
    "london": "London, United Kingdom",
    "munich": "Munich, Germany",
    "nyc": "New York City, New York, USA",
}


def main():
    parser = argparse.ArgumentParser(description="Sweet Walk data pipeline")
    parser.add_argument("city", choices=list(CITIES.keys()), help="City to process")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--skip-scoring", action="store_true", help="Skip scoring step (graph only)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    place = CITIES[args.city]

    print(f"[1/3] Extracting pedestrian graph for {place}...")
    G = extract_pedestrian_graph(place)
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    if not args.skip_scoring:
        print(f"[2/3] Downloading feature layers for scoring...")
        layers = extract_feature_layers(place)
        for name, gdf in layers.items():
            print(f"  {name}: {len(gdf)} features")

        print(f"[3/3] Scoring edges...")
        G = score_graph(G, layers)

    output_path = args.output_dir / f"{args.city}.graphml"
    save_graph(G, output_path)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
```

**Step 4: Commit**

```bash
git add backend/
git commit -m "Add graph loader and full pipeline with scoring integration"
```

---

## Task 8: Frontend Map Component

**Files:**
- Create: `frontend/src/components/Map.tsx`
- Create: `frontend/src/lib/types.ts`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/layout.tsx`

**Step 1: Create shared types**

`frontend/src/lib/types.ts`:
```typescript
export interface RouteResult {
  route_type: "quick" | "balanced" | "best_walk";
  nodes: string[];
  coordinates: [number, number][];
  distance: number;
  duration: number;
  quality_score: number;
  dimension_scores: number[];
}

export interface RoutesResponse {
  routes: RouteResult[];
  city: string;
}

export interface RouteRequest {
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  weights: number[];
}

export const DIMENSIONS = [
  { key: "greenery", icon: "🌳", label: "Greenery" },
  { key: "heritage", icon: "🏛️", label: "Heritage" },
  { key: "tranquility", icon: "🤫", label: "Tranquility" },
  { key: "water", icon: "💧", label: "Water" },
  { key: "culture", icon: "🎨", label: "Culture" },
  { key: "charm", icon: "✨", label: "Charm" },
] as const;
```

**Step 2: Create the Map component**

`frontend/src/components/Map.tsx`:
```tsx
"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface MapProps {
  onStartSet: (lngLat: [number, number]) => void;
  onEndSet: (lngLat: [number, number]) => void;
  routes?: GeoJSON.FeatureCollection[];
  selectedRouteIndex?: number;
}

const ROUTE_COLORS = ["#94a3b8", "#3b82f6", "#10b981"]; // gray, blue, green

export default function Map({ onStartSet, onEndSet, routes, selectedRouteIndex }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const startMarker = useRef<mapboxgl.Marker | null>(null);
  const endMarker = useRef<mapboxgl.Marker | null>(null);
  const [clickMode, setClickMode] = useState<"start" | "end">("start");

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [2.3522, 48.8566], // Paris default
      zoom: 13,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    map.current.addControl(
      new mapboxgl.GeolocateControl({ trackUserLocation: true }),
      "top-right"
    );

    map.current.on("click", (e) => {
      const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat];

      if (clickMode === "start") {
        if (startMarker.current) startMarker.current.remove();
        startMarker.current = new mapboxgl.Marker({ color: "#10b981" })
          .setLngLat(lngLat)
          .addTo(map.current!);
        onStartSet(lngLat);
        setClickMode("end");
      } else {
        if (endMarker.current) endMarker.current.remove();
        endMarker.current = new mapboxgl.Marker({ color: "#ef4444" })
          .setLngLat(lngLat)
          .addTo(map.current!);
        onEndSet(lngLat);
        setClickMode("start");
      }
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Draw routes on map
  useEffect(() => {
    if (!map.current || !routes) return;

    const m = map.current;

    // Wait for map to be loaded
    const draw = () => {
      // Remove existing route layers
      for (let i = 0; i < 3; i++) {
        if (m.getLayer(`route-${i}`)) m.removeLayer(`route-${i}`);
        if (m.getSource(`route-${i}`)) m.removeSource(`route-${i}`);
      }

      // Add route layers
      routes.forEach((geojson, i) => {
        m.addSource(`route-${i}`, { type: "geojson", data: geojson });
        m.addLayer({
          id: `route-${i}`,
          type: "line",
          source: `route-${i}`,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": ROUTE_COLORS[i],
            "line-width": selectedRouteIndex === i ? 6 : 3,
            "line-opacity": selectedRouteIndex === i ? 1 : 0.5,
          },
        });
      });
    };

    if (m.isStyleLoaded()) draw();
    else m.on("load", draw);
  }, [routes, selectedRouteIndex]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 text-sm text-slate-600 shadow-sm">
        Tap map to set {clickMode === "start" ? "start point" : "destination"}
      </div>
    </div>
  );
}
```

**Step 3: Update layout and page**

Update `frontend/src/app/layout.tsx` to set full-height viewport:
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sweet Walk",
  description: "Find the most beautiful walk from A to B",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
```

Update `frontend/src/app/page.tsx` — integrate map with state:
```tsx
"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
        />
      </div>
    </main>
  );
}
```

**Step 4: Add NEXT_PUBLIC_MAPBOX_TOKEN to .env.example**

Append to `.env.example`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
SWEETWALK_MAPBOX_TOKEN=your_mapbox_token_here
SWEETWALK_DATA_DIR=backend/data
```

**Step 5: Commit**

```bash
git add frontend/ .env.example
git commit -m "Add Mapbox map component with start/end point selection"
```

---

## Task 9: Frontend Preference Icons Component

**Files:**
- Create: `frontend/src/components/PreferenceIcons.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: Create the PreferenceIcons component**

`frontend/src/components/PreferenceIcons.tsx`:
```tsx
"use client";

import { useState } from "react";
import { DIMENSIONS } from "@/lib/types";

interface PreferenceIconsProps {
  onChange: (weights: number[]) => void;
}

export default function PreferenceIcons({ onChange }: PreferenceIconsProps) {
  // 0 = off, 1 = nice to have, 2 = important, 3 = must have
  const [taps, setTaps] = useState<number[]>(DIMENSIONS.map(() => 0));

  const handleTap = (index: number) => {
    const next = [...taps];
    next[index] = (next[index] + 1) % 4; // Cycle 0 → 1 → 2 → 3 → 0
    setTaps(next);
    // Convert taps to weights: 0→0, 1→0.33, 2→0.66, 3→1.0
    onChange(next.map((t) => t / 3));
  };

  return (
    <div className="flex items-center justify-center gap-3 px-4 py-3 bg-white border-t border-slate-200">
      {DIMENSIONS.map((dim, i) => (
        <button
          key={dim.key}
          onClick={() => handleTap(i)}
          className={`
            flex flex-col items-center gap-1 p-2 rounded-xl transition-all
            ${taps[i] === 0 ? "opacity-40" : ""}
            ${taps[i] === 1 ? "opacity-70 bg-slate-100" : ""}
            ${taps[i] === 2 ? "opacity-90 bg-blue-50 ring-1 ring-blue-200" : ""}
            ${taps[i] === 3 ? "opacity-100 bg-blue-100 ring-2 ring-blue-400 scale-110" : ""}
          `}
          title={`${dim.label}: ${["Off", "Nice to have", "Important", "Must have"][taps[i]]}`}
        >
          <span className="text-2xl">{dim.icon}</span>
          <div className="flex gap-0.5">
            {[1, 2, 3].map((level) => (
              <div
                key={level}
                className={`w-1.5 h-1.5 rounded-full ${
                  taps[i] >= level ? "bg-blue-500" : "bg-slate-200"
                }`}
              />
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
```

**Step 2: Wire into page.tsx**

Update `frontend/src/app/page.tsx`:
```tsx
"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import PreferenceIcons from "@/components/PreferenceIcons";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);
  const [weights, setWeights] = useState<number[]>([0, 0, 0, 0, 0, 0]);

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
        />
      </div>
      <PreferenceIcons onChange={setWeights} />
    </main>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/PreferenceIcons.tsx frontend/src/app/page.tsx
git commit -m "Add preference icons component with tap-to-weight interaction"
```

---

## Task 10: Frontend API Integration + Route Display

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/useRoutes.ts`
- Create: `frontend/src/components/RouteCard.tsx`
- Create: `frontend/src/components/RouteResults.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: Create API client**

`frontend/src/lib/api.ts`:
```typescript
import { RouteRequest, RoutesResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchRoutes(request: RouteRequest): Promise<RoutesResponse> {
  const res = await fetch(`${API_BASE}/api/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
```

**Step 2: Create useRoutes hook**

`frontend/src/hooks/useRoutes.ts`:
```typescript
"use client";

import { useState, useCallback } from "react";
import { fetchRoutes } from "@/lib/api";
import { RoutesResponse } from "@/lib/types";

export function useRoutes() {
  const [data, setData] = useState<RoutesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (
      start: [number, number],
      end: [number, number],
      weights: number[]
    ) => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchRoutes({
          start_lat: start[1],
          start_lon: start[0],
          end_lat: end[1],
          end_lon: end[0],
          weights,
        });
        setData(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, search, clear };
}
```

**Step 3: Create RouteCard component**

`frontend/src/components/RouteCard.tsx`:
```tsx
import { RouteResult, DIMENSIONS } from "@/lib/types";

interface RouteCardProps {
  route: RouteResult;
  isSelected: boolean;
  color: string;
  onSelect: () => void;
}

const ROUTE_LABELS = {
  quick: "Quick",
  balanced: "Balanced",
  best_walk: "Best Walk",
} as const;

function formatDuration(seconds: number): string {
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h${m > 0 ? ` ${m}m` : ""}`;
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

export default function RouteCard({ route, isSelected, color, onSelect }: RouteCardProps) {
  return (
    <button
      onClick={onSelect}
      className={`
        w-full text-left p-3 rounded-xl transition-all
        ${isSelected ? "bg-white shadow-md ring-2" : "bg-slate-50 hover:bg-white hover:shadow-sm"}
      `}
      style={isSelected ? { ringColor: color } : {}}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
          <span className="font-semibold text-sm text-slate-800">
            {ROUTE_LABELS[route.route_type]}
          </span>
        </div>
        <div className="text-xs text-slate-500">
          {formatDistance(route.distance)} · {formatDuration(route.duration)}
        </div>
      </div>
      <div className="flex gap-2">
        {route.dimension_scores.map((score, i) => (
          <div key={DIMENSIONS[i].key} className="flex items-center gap-0.5" title={DIMENSIONS[i].label}>
            <span className="text-xs">{DIMENSIONS[i].icon}</span>
            <div className="w-8 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${Math.round(score * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </button>
  );
}
```

**Step 4: Create RouteResults panel**

`frontend/src/components/RouteResults.tsx`:
```tsx
import { RoutesResponse } from "@/lib/types";
import RouteCard from "./RouteCard";

interface RouteResultsProps {
  data: RoutesResponse;
  selectedIndex: number;
  onSelect: (index: number) => void;
}

const ROUTE_COLORS = ["#94a3b8", "#3b82f6", "#10b981"];

export default function RouteResults({ data, selectedIndex, onSelect }: RouteResultsProps) {
  return (
    <div className="flex flex-col gap-2 p-4 bg-white/95 backdrop-blur-sm border-t border-slate-200 max-h-[40vh] overflow-y-auto">
      {data.routes.map((route, i) => (
        <RouteCard
          key={route.route_type}
          route={route}
          isSelected={selectedIndex === i}
          color={ROUTE_COLORS[i]}
          onSelect={() => onSelect(i)}
        />
      ))}
    </div>
  );
}
```

**Step 5: Wire everything together in page.tsx**

Update `frontend/src/app/page.tsx`:
```tsx
"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import PreferenceIcons from "@/components/PreferenceIcons";
import RouteResults from "@/components/RouteResults";
import { useRoutes } from "@/hooks/useRoutes";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

function routeToGeoJSON(coordinates: [number, number][]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates,
        },
      },
    ],
  };
}

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);
  const [weights, setWeights] = useState<number[]>([0, 0, 0, 0, 0, 0]);
  const [selectedRoute, setSelectedRoute] = useState(2); // Default: Best Walk
  const { data, loading, error, search } = useRoutes();

  // Auto-search when both points are set
  useEffect(() => {
    if (start && end) {
      search(start, end, weights);
    }
  }, [start, end, weights, search]);

  const routeGeoJSONs = data?.routes.map((r) => routeToGeoJSON(r.coordinates));

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
          routes={routeGeoJSONs}
          selectedRouteIndex={selectedRoute}
        />
        {loading && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-sm rounded-full px-4 py-2 shadow-sm text-sm text-slate-600">
            Finding your best walks...
          </div>
        )}
        {error && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-red-50 rounded-full px-4 py-2 shadow-sm text-sm text-red-600">
            {error}
          </div>
        )}
      </div>
      {data && (
        <RouteResults
          data={data}
          selectedIndex={selectedRoute}
          onSelect={setSelectedRoute}
        />
      )}
      <PreferenceIcons onChange={setWeights} />
    </main>
  );
}
```

**Step 6: Add NEXT_PUBLIC_API_URL to env**

Append to `.env.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Step 7: Commit**

```bash
git add frontend/ .env.example
git commit -m "Add route display with API integration and route cards"
```

---

## Task 11: Search Bar with Geocoding

**Files:**
- Create: `frontend/src/components/SearchBar.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: Create SearchBar component**

`frontend/src/components/SearchBar.tsx`:
```tsx
"use client";

import { useState, useCallback, useRef } from "react";

interface SearchResult {
  place_name: string;
  center: [number, number];
}

interface SearchBarProps {
  label: string;
  onSelect: (lngLat: [number, number]) => void;
  value?: string;
}

export default function SearchBar({ label, onSelect, value }: SearchBarProps) {
  const [query, setQuery] = useState(value || "");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();

  const search = useCallback(async (q: string) => {
    if (q.length < 3) {
      setResults([]);
      return;
    }
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const res = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(q)}.json?access_token=${token}&limit=5`
    );
    const data = await res.json();
    setResults(
      data.features?.map((f: { place_name: string; center: [number, number] }) => ({
        place_name: f.place_name,
        center: f.center,
      })) || []
    );
    setIsOpen(true);
  }, []);

  const handleInput = (val: string) => {
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(val), 300);
  };

  const handleSelect = (result: SearchResult) => {
    setQuery(result.place_name);
    setIsOpen(false);
    onSelect(result.center);
  };

  return (
    <div className="relative">
      <input
        type="text"
        placeholder={label}
        value={query}
        onChange={(e) => handleInput(e.target.value)}
        onFocus={() => results.length > 0 && setIsOpen(true)}
        className="w-full px-4 py-2.5 bg-white rounded-xl border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      {isOpen && results.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
          {results.map((r, i) => (
            <li key={i}>
              <button
                onClick={() => handleSelect(r)}
                className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 border-b border-slate-100 last:border-0"
              >
                {r.place_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**Step 2: Add search bars to page.tsx**

Update the top of the map area in `frontend/src/app/page.tsx` to include search bars in an overlay:
```tsx
"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import PreferenceIcons from "@/components/PreferenceIcons";
import RouteResults from "@/components/RouteResults";
import SearchBar from "@/components/SearchBar";
import { useRoutes } from "@/hooks/useRoutes";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

function routeToGeoJSON(coordinates: [number, number][]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {},
        geometry: { type: "LineString", coordinates },
      },
    ],
  };
}

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);
  const [weights, setWeights] = useState<number[]>([0, 0, 0, 0, 0, 0]);
  const [selectedRoute, setSelectedRoute] = useState(2);
  const { data, loading, error, search } = useRoutes();

  useEffect(() => {
    if (start && end) {
      search(start, end, weights);
    }
  }, [start, end, weights, search]);

  const routeGeoJSONs = data?.routes.map((r) => routeToGeoJSON(r.coordinates));

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
          routes={routeGeoJSONs}
          selectedRouteIndex={selectedRoute}
        />
        {/* Search overlay */}
        <div className="absolute top-4 left-4 right-4 flex flex-col gap-2 z-10">
          <SearchBar label="Start point..." onSelect={setStart} />
          <SearchBar label="Where do you want to go?" onSelect={setEnd} />
        </div>
        {loading && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-sm rounded-full px-4 py-2 shadow-sm text-sm text-slate-600">
            Finding your best walks...
          </div>
        )}
        {error && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-red-50 rounded-full px-4 py-2 shadow-sm text-sm text-red-600">
            {error}
          </div>
        )}
      </div>
      {data && (
        <RouteResults
          data={data}
          selectedIndex={selectedRoute}
          onSelect={setSelectedRoute}
        />
      )}
      <PreferenceIcons onChange={setWeights} />
    </main>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/
git commit -m "Add geocoding search bars with Mapbox autocomplete"
```

---

## Task 12: Generate City Graph Data (Paris test run)

**Step 1: Run the pipeline for a small Paris area first (Île de la Cité)**

This validates the full pipeline end-to-end before processing a full city.

```bash
cd backend && uv run python -c "
from sweetwalk.pipeline.extract import extract_pedestrian_graph, save_graph
from sweetwalk.scoring.scorer import extract_feature_layers, score_graph
from pathlib import Path

place = 'Île de la Cité, Paris, France'
print('Extracting graph...')
G = extract_pedestrian_graph(place)
print(f'Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}')

print('Downloading feature layers...')
layers = extract_feature_layers(place)

print('Scoring edges...')
G = score_graph(G, layers)

Path('data').mkdir(exist_ok=True)
save_graph(G, Path('data/paris_test.graphml'))
print('Done!')
"
```

**Step 2: Run full Paris pipeline**

```bash
cd backend && uv run sweetwalk-pipeline paris --output-dir data
```

Note: This will take several minutes for the full Paris graph. Expect ~100-200K nodes/edges.

**Step 3: Test the API with real data**

```bash
cd backend && uv run fastapi dev src/sweetwalk/main.py
```

In another terminal:
```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"start_lat": 48.8566, "start_lon": 2.3522, "end_lat": 48.8606, "end_lon": 2.3376, "weights": [1,1,1,1,1,1]}'
```

Expected: JSON with 3 routes.

**Step 4: Commit data gitignore note**

The `.graphml` files are large and already gitignored. Document in a README how to regenerate them.

```bash
git add backend/
git commit -m "Validate pipeline with Paris test data"
```

---

## Task 13: PWA Setup

**Files:**
- Modify: `frontend/next.config.ts`
- Create: `frontend/public/manifest.json`
- Modify: `frontend/src/app/layout.tsx`

**Step 1: Install next-pwa**

```bash
cd frontend && npm install next-pwa
```

**Step 2: Create manifest**

`frontend/public/manifest.json`:
```json
{
  "name": "Sweet Walk",
  "short_name": "SweetWalk",
  "description": "Find the most beautiful walk from A to B",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**Step 3: Update next.config.ts**

```typescript
import withPWA from "next-pwa";

const config = withPWA({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
})({
  // Next.js config
});

export default config;
```

**Step 4: Add manifest link to layout**

Update `frontend/src/app/layout.tsx` head:
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sweet Walk",
  description: "Find the most beautiful walk from A to B",
  manifest: "/manifest.json",
  themeColor: "#3b82f6",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
```

**Step 5: Create placeholder icons**

Generate simple placeholder icons (will be replaced with proper branding later):
```bash
mkdir -p frontend/public/icons
# For now, create placeholder PNGs — replace with real icons before launch
```

**Step 6: Commit**

```bash
git add frontend/
git commit -m "Add PWA support with manifest and service worker"
```

---

## Task 14: End-to-End Integration Test

**Step 1: Start both servers**

Terminal 1 (backend):
```bash
cd backend && SWEETWALK_DATA_DIR=data uv run fastapi dev src/sweetwalk/main.py
```

Terminal 2 (frontend):
```bash
cd frontend && npm run dev
```

**Step 2: Manual smoke test checklist**

- [ ] Open http://localhost:3000
- [ ] Map loads with Mapbox tiles
- [ ] Can type in search bars and see autocomplete results
- [ ] Can tap map to set start and end points
- [ ] Can tap preference icons (cycling through 0-3 dots)
- [ ] After setting both points, 3 routes appear on map
- [ ] Route cards show distance, duration, and score breakdowns
- [ ] Clicking a route card highlights it on the map
- [ ] Health endpoint returns loaded cities: http://localhost:8000/health

**Step 3: Fix any integration issues found during smoke test**

**Step 4: Final commit**

```bash
git add -A
git commit -m "Complete MVP integration: frontend + backend + pipeline"
```

---

## Task 15: Generate Remaining City Graphs

Run the pipeline for the remaining 3 cities. Each may take 5-30 minutes depending on city size.

```bash
cd backend
uv run sweetwalk-pipeline london --output-dir data
uv run sweetwalk-pipeline munich --output-dir data
uv run sweetwalk-pipeline nyc --output-dir data
```

Verify all 4 cities load:
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "ok", "cities": ["paris", "london", "munich", "nyc"]}`
