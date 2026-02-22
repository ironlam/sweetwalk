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
