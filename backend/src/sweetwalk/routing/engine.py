import heapq
import numpy as np
import networkx as nx
from sweetwalk.routing.schemas import RouteResult

WALKING_SPEED_MS = 5.0 / 3.6  # 5 km/h in m/s


def _weighted_cost(distance: float, scores: np.ndarray, weights: np.ndarray, alpha: float) -> float:
    """Compute edge cost: distance penalized by lack of quality.
    cost = distance * (1 + alpha * (1 - dot(scores, normalized_weights)))
    """
    w_sum = weights.sum()
    if w_sum == 0:
        return distance
    norm_weights = weights / w_sum
    quality = float(np.dot(scores, norm_weights))
    return distance * (1.0 + alpha * (1.0 - quality))


def _astar(G, source, target, weights, alpha):
    """A* search with multi-criteria cost function. Returns (path_nodes, total_distance)."""
    target_x = G.nodes[target].get("x", 0)
    target_y = G.nodes[target].get("y", 0)

    def heuristic(node):
        nx_data = G.nodes[node]
        dx = nx_data.get("x", 0) - target_x
        dy = nx_data.get("y", 0) - target_y
        return (dx**2 + dy**2) ** 0.5

    counter = 0
    open_set = [(heuristic(source), counter, source)]
    came_from = {}
    g_score = {source: 0.0}
    dist_score = {source: 0.0}

    while open_set:
        f, _, current = heapq.heappop(open_set)

        if current == target:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, dist_score[target]

        for _, neighbor, edge_data in G.edges(current, data=True):
            distance = edge_data.get("length", 1.0)
            scores = edge_data.get("scores", np.zeros(6, dtype=np.float32))
            cost = _weighted_cost(distance, scores, weights, alpha)
            tentative_g = g_score[current] + cost
            tentative_dist = dist_score[current] + distance

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                dist_score[neighbor] = tentative_dist
                counter += 1
                heapq.heappush(open_set, (tentative_g + heuristic(neighbor), counter, neighbor))

    return [], 0.0


def _compute_route_scores(G, path):
    """Compute average dimension scores along a path."""
    if len(path) < 2:
        return 0.0, [0.0] * 6

    all_scores = []
    total_length = 0.0

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            first_edge = list(edge_data.values())[0]
            scores = first_edge.get("scores", np.zeros(6, dtype=np.float32))
            length = first_edge.get("length", 1.0)
            all_scores.append(scores * length)
            total_length += length

    if total_length == 0:
        return 0.0, [0.0] * 6

    weighted_avg = np.sum(all_scores, axis=0) / total_length
    dimension_scores = [round(float(s), 3) for s in weighted_avg]
    overall = round(float(np.mean(weighted_avg)), 3)

    return overall, dimension_scores


def _path_to_coordinates(G, path):
    """Convert node path to [[lon, lat], ...] coordinates."""
    coords = []
    for node in path:
        node_data = G.nodes[node]
        coords.append([node_data.get("x", 0), node_data.get("y", 0)])
    return coords


def find_routes(G, source, target, weights):
    """Find 3 route options: Quick, Balanced, Best Walk."""
    alphas = [("quick", 0.0), ("balanced", 0.5), ("best_walk", 1.0)]

    routes = []
    seen_paths = set()

    for route_type, alpha in alphas:
        path, distance = _astar(G, source, target, weights, alpha)
        if not path:
            continue

        path_key = tuple(path)
        if path_key in seen_paths and alpha < 2.0:
            path2, distance2 = _astar(G, source, target, weights, alpha * 1.5)
            if path2 and tuple(path2) not in seen_paths:
                path, distance = path2, distance2
                path_key = tuple(path)

        seen_paths.add(path_key)
        quality_score, dimension_scores = _compute_route_scores(G, path)
        coordinates = _path_to_coordinates(G, path)
        duration = distance / WALKING_SPEED_MS

        routes.append(RouteResult(
            route_type=route_type,
            nodes=[str(n) for n in path],
            coordinates=coordinates,
            distance=round(distance, 1),
            duration=round(duration, 1),
            quality_score=quality_score,
            dimension_scores=dimension_scores,
        ))

    return routes
