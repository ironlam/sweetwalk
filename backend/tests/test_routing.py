import numpy as np
import networkx as nx
from sweetwalk.routing.engine import find_routes
from sweetwalk.routing.schemas import RouteResult


def _make_scored_graph():
    """Create a small test graph with scores.

    Layout:
        A --1-- B --1-- C  (direct path, low scores)
        |               |
        2               2
        |               |
        D --1-- E --1-- F  (scenic path, high scores)

    Edge weights are distances. A->B->C is direct but ugly.
    A->D->E->F->C is scenic but longer.
    """
    G = nx.MultiDiGraph()

    nodes = {
        "A": (0, 0),
        "B": (100, 0),
        "C": (200, 0),
        "D": (0, 100),
        "E": (100, 100),
        "F": (200, 100),
    }
    for name, (x, y) in nodes.items():
        G.add_node(name, x=x, y=y)

    low_scores = np.array([0.1, 0.1, 0.2, 0.0, 0.1, 0.1], dtype=np.float32)
    high_scores = np.array([0.9, 0.8, 0.9, 0.7, 0.8, 0.9], dtype=np.float32)

    # Direct path edges (low quality)
    G.add_edge("A", "B", 0, length=100, scores=low_scores)
    G.add_edge("B", "A", 0, length=100, scores=low_scores)
    G.add_edge("B", "C", 0, length=100, scores=low_scores)
    G.add_edge("C", "B", 0, length=100, scores=low_scores)

    # Scenic path edges (high quality)
    G.add_edge("A", "D", 0, length=200, scores=high_scores)
    G.add_edge("D", "A", 0, length=200, scores=high_scores)
    G.add_edge("D", "E", 0, length=100, scores=high_scores)
    G.add_edge("E", "D", 0, length=100, scores=high_scores)
    G.add_edge("E", "F", 0, length=100, scores=high_scores)
    G.add_edge("F", "E", 0, length=100, scores=high_scores)
    G.add_edge("F", "C", 0, length=200, scores=high_scores)
    G.add_edge("C", "F", 0, length=200, scores=high_scores)

    return G


def test_find_routes_returns_three_routes():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)
    routes = find_routes(G, "A", "C", weights)
    assert len(routes) == 3


def test_quick_route_is_shortest():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)
    routes = find_routes(G, "A", "C", weights)
    quick = routes[0]
    assert quick.distance <= routes[1].distance
    assert quick.distance <= routes[2].distance


def test_best_walk_has_highest_score():
    G = _make_scored_graph()
    weights = np.array([1, 1, 1, 1, 1, 1], dtype=np.float32)
    routes = find_routes(G, "A", "C", weights)
    best = routes[2]
    quick = routes[0]
    assert best.quality_score >= quick.quality_score
