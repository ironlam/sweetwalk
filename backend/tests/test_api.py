def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


import numpy as np
import networkx as nx
from sweetwalk.graph.store import graph_store


def _seed_test_graph():
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:4326"
    low = np.array([0.1, 0.1, 0.2, 0.0, 0.1, 0.1], dtype=np.float32)
    high = np.array([0.9, 0.8, 0.9, 0.7, 0.8, 0.9], dtype=np.float32)

    G.add_node(1, x=2.3522, y=48.8566)
    G.add_node(2, x=2.3400, y=48.8580)
    G.add_node(3, x=2.3376, y=48.8606)
    G.add_node(4, x=2.3450, y=48.8620)

    G.add_edge(1, 2, 0, length=200, scores=low)
    G.add_edge(2, 3, 0, length=200, scores=low)
    G.add_edge(1, 4, 0, length=300, scores=high)
    G.add_edge(4, 3, 0, length=300, scores=high)
    G.add_edge(2, 1, 0, length=200, scores=low)
    G.add_edge(3, 2, 0, length=200, scores=low)
    G.add_edge(4, 1, 0, length=300, scores=high)
    G.add_edge(3, 4, 0, length=300, scores=high)

    graph_store.graphs["test_city"] = G
    graph_store.add_city("test_city", G)
    return G


def test_route_endpoint(client):
    _seed_test_graph()
    response = client.post("/api/route", json={
        "start_lat": 48.8566,
        "start_lon": 2.3522,
        "end_lat": 48.8606,
        "end_lon": 2.3376,
        "weights": [1, 1, 1, 1, 1, 1],
    })
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) >= 1


def test_route_endpoint_missing_coords(client):
    response = client.post("/api/route", json={
        "start_lat": 48.8566,
        "weights": [1, 1, 1, 1, 1, 1],
    })
    assert response.status_code == 422
