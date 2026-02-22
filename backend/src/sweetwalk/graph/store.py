import networkx as nx
from pyproj import Transformer
from scipy.spatial import KDTree
import numpy as np


class GraphStore:
    """In-memory store for city walking graphs."""

    def __init__(self):
        self.graphs: dict[str, nx.MultiDiGraph] = {}
        self._kdtrees: dict[str, KDTree] = {}
        self._node_lists: dict[str, list] = {}
        self._transformers: dict[str, Transformer] = {}
        self._bboxes: dict[str, tuple[float, float, float, float]] = {}

    def add_city(self, city: str, G: nx.MultiDiGraph) -> None:
        self.graphs[city] = G
        nodes = list(G.nodes())
        coords = np.array([(G.nodes[n]["x"], G.nodes[n]["y"]) for n in nodes])
        self._kdtrees[city] = KDTree(coords)
        self._node_lists[city] = nodes

        # Set up coordinate transformer: WGS84 (lat/lon) -> graph CRS
        graph_crs = G.graph.get("crs", "EPSG:4326")
        self._transformers[city] = Transformer.from_crs(
            "EPSG:4326", graph_crs, always_xy=True
        )

        # Pre-compute bounding box in lat/lon for fast city lookup
        inv_transformer = Transformer.from_crs(
            graph_crs, "EPSG:4326", always_xy=True
        )
        min_x, min_y = coords.min(axis=0)
        max_x, max_y = coords.max(axis=0)
        lon_min, lat_min = inv_transformer.transform(min_x, min_y)
        lon_max, lat_max = inv_transformer.transform(max_x, max_y)
        self._bboxes[city] = (lon_min, lat_min, lon_max, lat_max)

    def find_nearest_node(self, city: str, lon: float, lat: float):
        """Find nearest graph node to a WGS84 lon/lat coordinate."""
        transformer = self._transformers[city]
        x, y = transformer.transform(lon, lat)
        tree = self._kdtrees[city]
        nodes = self._node_lists[city]
        _, idx = tree.query([x, y])
        return nodes[idx]

    def find_city(self, lon: float, lat: float) -> str | None:
        """Determine which city a WGS84 lon/lat belongs to."""
        margin = 0.05  # ~5km margin in degrees
        for city in self.graphs:
            lon_min, lat_min, lon_max, lat_max = self._bboxes[city]
            if (lon_min - margin <= lon <= lon_max + margin and
                    lat_min - margin <= lat <= lat_max + margin):
                return city
        return None

    @property
    def cities(self) -> list[str]:
        return list(self.graphs.keys())


graph_store = GraphStore()
