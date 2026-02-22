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
        nodes = list(G.nodes())
        coords = np.array([(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes])
        self._kdtrees[city] = KDTree(coords)
        self._node_lists[city] = nodes

    def find_nearest_node(self, city: str, lon: float, lat: float):
        tree = self._kdtrees[city]
        nodes = self._node_lists[city]
        _, idx = tree.query([lon, lat])
        return nodes[idx]

    def find_city(self, lon: float, lat: float) -> str | None:
        for city, G in self.graphs.items():
            nodes = self._node_lists[city]
            coords = np.array([(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes])
            min_x, min_y = coords.min(axis=0)
            max_x, max_y = coords.max(axis=0)
            margin = 0.01
            if min_x - margin <= lon <= max_x + margin and min_y - margin <= lat <= max_y + margin:
                return city
        return None

    @property
    def cities(self) -> list[str]:
        return list(self.graphs.keys())


graph_store = GraphStore()
