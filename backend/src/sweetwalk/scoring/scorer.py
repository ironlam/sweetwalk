import logging

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

logger = logging.getLogger(__name__)

# OSM tags for extracting feature layers
GREEN_TAGS = {"leisure": ["park", "garden", "nature_reserve"], "landuse": ["grass", "forest", "meadow"]}
TREE_TAGS = {"natural": ["tree", "tree_row"]}
HERITAGE_TAGS = {"historic": True, "heritage": True, "tourism": ["attraction"]}
WATER_TAGS = {"natural": ["water"], "waterway": ["river", "canal", "stream"]}
CULTURE_TAGS = {"tourism": ["museum", "gallery", "artwork"], "amenity": ["arts_centre", "theatre"]}
CAFE_TAGS = {"amenity": ["cafe", "restaurant"]}


def extract_feature_layers(place_name: str, crs: str = "EPSG:3857") -> dict[str, gpd.GeoDataFrame]:
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
            # Project to match the graph CRS (e.g., UTM)
            gdf = gdf.to_crs(crs)
            layers[name] = gdf
        except Exception as e:
            logger.warning("Failed to download %s for %s: %s", name, place_name, e)
            layers[name] = gpd.GeoDataFrame(geometry=[], crs=crs)

    return layers


def score_graph(G: nx.MultiDiGraph, layers: dict[str, gpd.GeoDataFrame]) -> nx.MultiDiGraph:
    """Compute 6 quality scores for every edge in the graph.

    Adds 'scores' attribute to each edge: np.array([greenery, heritage, tranquility, water, culture, charm])
    """
    # Ensure feature layers match the graph's CRS
    graph_crs = G.graph.get("crs", "EPSG:3857")
    for name, gdf in layers.items():
        if not gdf.empty and gdf.crs is not None and gdf.crs != graph_crs:
            layers[name] = gdf.to_crs(graph_crs)

    cafes = layers["cafes"]

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
        cafe_count = 0
        if not cafes.empty:
            candidate_idx = cafes.sindex.query(buffer, predicate="intersects")
            if len(candidate_idx) > 0:
                cafe_count = int(cafes.iloc[candidate_idx].within(buffer).sum())
        has_nice_arch = highway in ("pedestrian", "living_street")
        charm_val = score_charm(highway, cafe_count, has_nice_arch)

        data["scores"] = np.array(
            [greenery, heritage, tranquility, water, culture, charm_val],
            dtype=np.float32,
        )

    return G
