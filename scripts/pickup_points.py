import json, os, random, pathlib

OUT = pathlib.Path("data/delhi_vaults.geojson")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Delhi bounding box
B = dict(lat_min=28.40, lat_max=28.88, lon_min=76.84, lon_max=77.35)

random.seed(42)                       # <- guarantees same 500 vaults forever

feats = []
for i in range(1, 501):
    lat = random.uniform(B["lat_min"], B["lat_max"])
    lon = random.uniform(B["lon_min"], B["lon_max"])
    feats.append(
        dict(
            type="Feature",
            id=i,
            properties=dict(vid=i, name=f"Vault #{i}"),
            geometry=dict(type="Point", coordinates=[lon, lat]),
        )
    )

OUT.write_text(json.dumps(dict(type="FeatureCollection", features=feats), indent=2))
print(f"✅  wrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB)")
