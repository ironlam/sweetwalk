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
