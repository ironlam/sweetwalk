import networkx as nx
from sweetwalk.pipeline.extract import extract_pedestrian_graph


def test_extract_pedestrian_graph_returns_multidigraph():
    # Use a small area: Île de la Cité, Paris (tiny, fast to download)
    G = extract_pedestrian_graph("Île de la Cité, Paris, France")
    assert isinstance(G, nx.MultiDiGraph)
    assert G.number_of_nodes() > 10
    assert G.number_of_edges() > 10


def test_edges_have_geometry():
    G = extract_pedestrian_graph("Île de la Cité, Paris, France")
    # At least some edges should have geometry
    edge_data = next(iter(G.edges(data=True)))
    u, v, data = edge_data
    assert "length" in data
