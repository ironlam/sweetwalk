from pydantic import BaseModel


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
    route_type: str
    nodes: list[str | int]
    coordinates: list[list[float]]
    distance: float
    duration: float
    quality_score: float
    dimension_scores: list[float]


class RoutesResponse(BaseModel):
    routes: list[RouteResult]
    city: str
