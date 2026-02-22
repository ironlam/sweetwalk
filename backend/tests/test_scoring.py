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
