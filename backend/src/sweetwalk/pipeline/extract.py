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
