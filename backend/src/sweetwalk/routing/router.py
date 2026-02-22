import numpy as np
from fastapi import APIRouter, HTTPException
from pyproj import Transformer

from sweetwalk.graph.store import graph_store
from sweetwalk.routing.engine import find_routes
from sweetwalk.routing.schemas import RouteRequest, RoutesResponse

router = APIRouter(prefix="/api")


@router.post("/route", response_model=RoutesResponse)
def compute_route(req: RouteRequest):
    city = graph_store.find_city(req.start_lon, req.start_lat)
    if city is None:
        raise HTTPException(status_code=404, detail="No city graph covers these coordinates")

    G = graph_store.graphs[city]
    source = graph_store.find_nearest_node(city, req.start_lon, req.start_lat)
    target = graph_store.find_nearest_node(city, req.end_lon, req.end_lat)

    if source == target:
        raise HTTPException(status_code=400, detail="Start and end are too close")

    weights = np.array(req.weights, dtype=np.float32)
    routes = find_routes(G, source, target, weights)

    if not routes:
        raise HTTPException(status_code=404, detail="No walking route found")

    # Convert coordinates from graph CRS (UTM) back to WGS84 lon/lat
    graph_crs = G.graph.get("crs", "EPSG:4326")
    if graph_crs != "EPSG:4326":
        transformer = Transformer.from_crs(graph_crs, "EPSG:4326", always_xy=True)
        for route in routes:
            route.coordinates = [
                list(transformer.transform(x, y)) for x, y in route.coordinates
            ]

    return RoutesResponse(routes=routes, city=city)
