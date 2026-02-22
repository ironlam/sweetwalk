# Sweet Walk - Design Document

**Date:** 2026-02-22
**Status:** Approved
**Scope:** MVP / Proof of Concept

## Vision

Sweet Walk helps people find the best walking route from A to B based on *experience quality* rather than just distance or time. Unlike Google Maps (which optimizes for efficiency), Sweet Walk optimizes for beauty, nature, culture, tranquility, and charm.

**Target cities (MVP):** Paris, London, Munich, New York

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    SWEET WALK                           │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  Next.js PWA  │───>│  FastAPI     │───>│ Supabase  │ │
│  │  + Mapbox GL  │<───│  Routing API │    │ (Auth/DB) │ │
│  └──────────────┘    └──────┬───────┘    └───────────┘ │
│                             │                           │
│                    ┌────────▼────────┐                  │
│                    │  City Graphs    │                  │
│                    │  (Pre-computed) │                  │
│                    │  Paris │ London │                  │
│                    │  Munich│  NYC   │                  │
│                    └─────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

**Three layers:**

1. **Frontend** - Next.js PWA with Mapbox GL JS for maps, icon-tap preference UI, photo cards for onboarding
2. **Routing API** - Python FastAPI service holding city walking graphs in memory, running multi-criteria A*
3. **Data layer** - Supabase for user accounts, saved walks, taste profiles. Pre-computed city graphs as serialized files loaded at startup

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14+, React, TypeScript | App framework, SSR, API proxy |
| Maps | Mapbox GL JS | Map rendering, custom styling |
| Styling | Tailwind CSS | Responsive mobile-first UI |
| PWA | next-pwa | Installable, offline caching |
| Routing API | Python FastAPI | Route computation endpoints |
| Graph | osmnx, networkx | OSM graph extraction, pathfinding |
| Geospatial | geopandas, shapely | Spatial scoring (buffer zones) |
| Auth & DB | Supabase | User auth, profiles, saved walks |
| Geocoding | Mapbox Geocoding API | Address/place search |

## Scoring Engine

### The 6 Quality Dimensions

Each street segment (graph edge) receives a score from 0 to 1 for each dimension:

| Dimension | OSM Data Sources | Computation |
|-----------|-----------------|-------------|
| **Greenery** | `leisure=park`, `natural=tree/tree_row`, `landuse=grass/forest`, `leisure=garden` | Area of green features in 50m buffer + tree count, normalized by segment length |
| **Heritage** | `historic=*`, `heritage=*`, `tourism=attraction`, `building:architecture=*` | POI density in buffer, weighted by significance (UNESCO > local) |
| **Tranquility** | `highway=*` type, `maxspeed`, inverse of commercial density | Inverse scoring: pedestrian=1.0, residential=0.7, primary=0.2 |
| **Water** | `natural=water`, `waterway=river/canal`, `amenity=fountain` | Binary proximity + parallelism bonus (street runs along water) |
| **Culture** | `tourism=museum/gallery`, `amenity=arts_centre/theatre`, `tourism=artwork` | POI count in buffer, weighted by type |
| **Charm** | `highway=pedestrian/living_street`, `amenity=cafe/restaurant`, building age proxies | Composite: street type + cafe density + architectural character |

### Scoring Methodology

- **Buffer zone approach:** For each edge, create a 50m buffer around its geometry. Count/measure relevant OSM features within this buffer.
- **Normalization:** Percentile-based normalization per city to [0-1] range. "High greenery" means the same thing relatively within each city.
- **Safety floor:** All routes must pass basic safety filtering (no isolated unlit paths at night). Safety is a filter, not a scoring dimension.

### Routing Cost Function

```
cost(edge) = edge.distance * (1 + alpha * (1 - dot(edge.scores, user_weights)))
```

- `edge.scores` = 6D vector of quality scores for this street segment
- `user_weights` = 6D vector of user preferences (from icon taps + taste profile)
- `alpha` = detour tolerance parameter

### 3 Route Options

For every query, generate 3 routes with diversity constraints:

1. **Quick** (alpha=0) - Shortest walking path
2. **Balanced** (alpha=0.5) - Good quality, moderate detour
3. **Best Walk** (alpha=1.0) - Highest quality score, longest detour

## User Experience

### Interaction Model

**Primary:** Icon tap weighting
- 6 icons always visible at bottom of screen (Greenery, Heritage, Tranquility, Water, Culture, Charm)
- 1 tap = nice to have, 2 taps = important, 3 taps = must have
- Zero configuration, works across languages, intuitive

**Secondary:** Photo preference cards (onboarding + profile building)
- Show pairs of real street photos from the target city
- "Which vibe do you prefer?" - swipe left/right
- 4-5 swipes during onboarding builds initial taste profile
- Occasional cards during app use refine the profile over time

### User Flow

```
1. ONBOARDING (first use)
   └── 4-5 photo preference swipes → baseline taste profile

2. HOME SCREEN
   ├── Map centered on current location
   ├── "Where do you want to go?" search bar / tap on map
   └── 6 preference icons (pre-filled from taste profile)

3. ROUTE RESULTS
   ├── 3 routes displayed on map (different colors)
   ├── Quick / Balanced / Best Walk with time estimates
   ├── Score breakdown per route (using same 6 icons)
   └── Photo previews of highlights along each route

4. NAVIGATION
   ├── Turn-by-turn walking directions
   └── Highlight notifications ("Approaching: Notre-Dame")
```

## Data Pipeline

**Runs offline, monthly updates:**

1. Download OSM data for each city (via Overpass API or Geofabrik extracts)
2. Extract pedestrian walking graph using `osmnx`
3. For each edge, compute 6 quality scores using buffer zone analysis
4. Serialize scored graphs (GeoPackage or pickle format)
5. Deploy updated graphs to the routing server

**Scale estimates per city:**
- ~150K-300K edges per city graph
- 6 float scores per edge + geometry
- ~50-100MB in memory per city
- Total for 4 cities: ~400MB RAM

## API Design

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/route` | POST | Compute 3 routes. Input: start coords, end coords, weights[6]. Returns: 3 routes with geometries, scores, time estimates |
| `/api/search` | GET | Geocoding. Proxies to Mapbox Geocoding API |
| `/api/taste` | POST | Save/update user taste profile |
| `/api/curated` | GET | Get curated/editorial walks for a city |
| `/api/walk/save` | POST | Save a completed or bookmarked walk |

## Data Model (Supabase)

### users
- id, email, created_at

### taste_profiles
- user_id, greenery_weight, heritage_weight, tranquility_weight, water_weight, culture_weight, charm_weight

### saved_walks
- id, user_id, city, start_coords, end_coords, route_geometry, route_type, scores, created_at

### curated_walks
- id, city, title, description, route_geometry, scores, photos, author

## Hybrid Model: Algorithmic + Curated

- **Algorithmic routing** handles any A-to-B request using the multi-criteria A* engine
- **Curated routes** serve as "editor's picks" - great walks hand-picked or community-submitted
- Curated routes also serve as validation data for the scoring algorithm
- Future: community can submit and rate walks, creating a feedback loop

## MVP Scope

### In Scope
- Web app (mobile-first PWA) with Mapbox maps
- 4 cities: Paris, London, Munich, New York
- 6 scoring dimensions from OSM data
- Icon tap preference selector
- 3 route options (Quick / Balanced / Best Walk)
- Basic user accounts (Supabase Auth)
- Save/bookmark walks
- Turn-by-turn navigation view

### Out of Scope (v2+)
- Photo preference card onboarding (v2)
- Community curated routes (v2)
- Time-of-day awareness / safety scoring (v2)
- Offline maps / full offline support (v2)
- Additional cities beyond the initial 4 (v2)
- Social features (share walks, follow friends) (v3)
- Native mobile apps (v3)

## Key References

- [Customized Pleasant Pedestrian Routes - Heidelberg University](https://giscienceblog.uni-heidelberg.de/2018/11/07/generating-customized-pleasant-pedestrian-routes-based-on-openstreetmap-data/)
- [OpenRouteService Green Routing](https://giscience.github.io/openrouteservice-workshop/usecases/green_routing.html)
- [OSMnx - Python Street Networks](https://geoffboeing.com/2016/11/osmnx-python-street-networks/)
- [Urban Walkability Analysis with OSM](https://gispofinland.medium.com/analysing-urban-walkability-using-openstreetmap-and-python-33815d045204)
- [OSM Historic Tags](https://wiki.openstreetmap.org/wiki/Key:historic)
- [Valhalla Dynamic Costing](https://valhalla.github.io/valhalla/sif/dynamic-costing/)
