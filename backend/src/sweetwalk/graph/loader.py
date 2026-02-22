from pathlib import Path
import numpy as np
import osmnx as ox
import networkx as nx

from sweetwalk.graph.store import graph_store


def _parse_scores(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Convert string-serialized score arrays back to numpy arrays.

    GraphML serializes numpy arrays as strings like '[0.1 0.2 0.3 0.4 0.5 0.6]'.
    This function parses them back.
    """
    for u, v, key, data in G.edges(keys=True, data=True):
        scores = data.get("scores")
        if scores is not None and isinstance(scores, str):
            # Parse string like "[0.1 0.2 0.3 0.4 0.5 0.6]"
            cleaned = scores.strip("[]")
            data["scores"] = np.fromstring(cleaned, sep=" ", dtype=np.float32)
        elif scores is None:
            data["scores"] = np.zeros(6, dtype=np.float32)
    return G


def load_city_graphs(data_dir: str | Path) -> None:
    """Load all pre-computed city graphs from the data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        return

    for graphml_file in data_path.glob("*.graphml"):
        city = graphml_file.stem
        G = ox.load_graphml(filepath=graphml_file)
        G = _parse_scores(G)
        graph_store.add_city(city, G)
        print(f"Loaded {city}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
