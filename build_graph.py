import osmnx as ox, json, pathlib, math, tqdm

OUT = pathlib.Path("data/delhi.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

print("Downloading Delhi drivable graph from OpenStreetMap …")
G = ox.graph_from_place("Delhi, India", network_type="drive")
print("  nodes:", len(G), " | edges:", len(G.edges))

# Flatten into the exact format your C++ code uses
nodes = []
for node_id, attr in G.nodes(data=True):
    nodes.append(
        dict(id=int(node_id),
             lat=attr["y"],
             lon=attr["x"],
             isVault=False,        # will stay False – vaults handled elsewhere
             label="")
    )

edges = []
for u, v, attr in G.edges(data=True):
    edges.append(
        dict(source=int(u),
             target=int(v),
             distance=float(attr["length"] / 1000.0))   # convert m → km
    )

with OUT.open("w") as f:
    json.dump(dict(nodes=nodes, edges=edges), f)

print("✅  wrote", OUT, "(", OUT.stat().st_size/1024, "KB )")