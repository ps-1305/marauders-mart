import json, math, heapq, pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

# ── data structures ────────────────────────────────────────────────────────
@dataclass
class Node:
    id: int
    lat: float
    lon: float
    isVault: bool = False
    label: str = ""

@dataclass
class Edge:
    to: int
    distance: float          # in km

@dataclass
class Graph:
    nodes: Dict[int, Node] = field(default_factory=dict)
    adj  : Dict[int, List[Edge]] = field(default_factory=dict)

# ── helpers ────────────────────────────────────────────────────────────────
_R_EARTH = 6371.0
def _to_rad(deg: float) -> float: return deg * math.pi / 180.0

def haversine(a: Node, b: Node) -> float:
    dlat = _to_rad(b.lat - a.lat)
    dlon = _to_rad(b.lon - a.lon)
    s1, s2 = math.sin(dlat/2), math.sin(dlon/2)
    h = s1*s1 + math.cos(_to_rad(a.lat))*math.cos(_to_rad(b.lat))*s2*s2
    return 2*_R_EARTH*math.asin(math.sqrt(h))

# --------------------------------------------------------------------------
def parse_graph_json(path: str | pathlib.Path) -> Graph:
    g = Graph()
    data = json.loads(pathlib.Path(path).read_text())
    for nd in data["nodes"]:
        node = Node(**nd)
        g.nodes[node.id] = node
        g.adj.setdefault(node.id, [])
    for ed in data["edges"]:
        if ed["source"] in g.nodes:
            g.adj[ed["source"]].append(Edge(ed["target"], ed["distance"]))
    return g

# --------------------------------------------------------------------------
def find_closest_node(g: Graph, lat: float, lon: float) -> int:
    tmp = Node(-1, lat, lon)
    best, best_id = 1e100, -1
    for n in g.nodes.values():
        d = haversine(n, tmp)
        if d < best:
            best, best_id = d, n.id
    return best_id

# --------------------------------------------------------------------------
def astar(g: Graph, start: int, goal: int) -> List[int]:
    open_set: List[Tuple[float,int]] = []
    heapq.heappush(open_set, (0.0, start))

    g_cost = {start: 0.0}
    came   = {}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            # reconstruct
            path = [current]
            while current in came:
                current = came[current]
                path.append(current)
            return list(reversed(path))

        for e in g.adj.get(current, []):
            tentative = g_cost[current] + e.distance
            if tentative < g_cost.get(e.to, 1e100):
                came[e.to] = current
                g_cost[e.to] = tentative
                f_cost = tentative + haversine(g.nodes[e.to], g.nodes[goal])
                heapq.heappush(open_set, (f_cost, e.to))

    return []         # no path

if __name__ == "__main__":
    g = parse_graph_json("data/delhi.json")
    s, t = list(g.nodes)[:2]
    print("len path:", len(astar(g, s, t)))