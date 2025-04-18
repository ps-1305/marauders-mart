import streamlit as st
import sqlite3, bcrypt, re, os, uuid, datetime, json, random, pathlib, pickle
from PIL import Image
import folium
from folium.plugins import MarkerCluster
from folium.features import CustomIcon
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
from pathfinding import parse_graph_json, find_closest_node, astar, Graph, haversine

# ════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════════════════
DB_NAME      = "users.db"
IMG_DIR      = "images"                        # product photos
HOUSES       = ["Gryffindor", "Slytherin", "Ravenclaw", "Hufflepuff"]
CONDITIONS   = ["Like New", "Very Good", "Good", "Fair", "Poor"]
EMAIL_RE     = re.compile(r"^[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+$")
VAULTS_PATH = pathlib.Path("data/delhi_vaults.geojson") # 500
GRAPH_FILE = pathlib.Path("data/delhi_drive.graphml")
GRAPH: Graph = parse_graph_json("data/delhi.json")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# MISC  ── rerun helper valid for all Streamlit 1.x
# ════════════════════════════════════════════════════════════════════════════
def rerun():
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()

# ════════════════════════════════════════════════════════════════════════════
# CACHE
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_vault_geojson() -> dict:
    if not VAULTS_PATH.exists():
        st.error(
            f"{VAULTS_PATH} missing. Run make_vaults.py once to create it."
        )
        st.stop()
    return json.loads(VAULTS_PATH.read_text())

@st.cache_resource(show_spinner="Loading Delhi road network …")
def load_graph() -> nx.MultiDiGraph:
    """
    Return a NetworkX graph of Delhi's drivable streets.
    First call downloads from OSM and pickles it to data/delhi_drive.graphml.
    Later calls read the local file (1‑2 s).
    """
    if GRAPH_FILE.exists():
        return ox.load_graphml(GRAPH_FILE)

    g = ox.graph_from_place("Delhi, India", network_type="drive")
    ox.save_graphml(g, GRAPH_FILE)          # cache to disk
    return g

# ════════════════════════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════════════════════════
def shortest_route(seller_vault: dict, buyer_vault: dict):
    """
    Return (latlon_path, length_m) for the shortest road path
    between the two vault Feature dicts.
    """
    g = load_graph()
    def vault_to_node(v):
        lat, lon = v["geometry"]["coordinates"][1], v["geometry"]["coordinates"][0]
        return ox.distance.nearest_nodes(g, lon, lat)

    src = vault_to_node(seller_vault)
    dst = vault_to_node(buyer_vault)

    node_path = nx.astar_path(g, src, dst, weight="length")
    length_m  = nx.path_weight(g, node_path, weight="length")

    lats = nx.get_node_attributes(g, "y")
    lons = nx.get_node_attributes(g, "x")
    latlon_path = [(lats[n], lons[n]) for n in node_path]
    return latlon_path, length_m

def vault_selector(map_key: str) -> dict | None:
    data = load_vault_geojson()
    m = folium.Map(location=[28.6139, 77.2090],
                   zoom_start=11,
                   tiles="OpenStreetMap")
    
    for feat in data["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        folium.Marker(
            location=[lat, lon],
            tooltip=feat["properties"]["name"],
            popup=(f'{feat["properties"]["name"]}<br>'
                   f'Lat {lat:.4f}, Lon {lon:.4f}')
        ).add_to(m)

    ret = st_folium(m, key=map_key, width=700, height=500)

    click = ret.get("last_object_clicked")     # will now be filled
    if click:
        for feat in data["features"]:
            lon, lat = feat["geometry"]["coordinates"]
            if abs(lat-click["lat"]) < 1e-5 and abs(lon-click["lng"]) < 1e-5:
                st.success(f'Selected {feat["properties"]["name"]}')
                return feat
    return None

# ════════════════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cur  = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
                      username TEXT PRIMARY KEY,
                      fullname TEXT,
                      email    TEXT UNIQUE,
                      house    TEXT,
                      pwd_hash TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS listings(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      seller      TEXT,
                      name        TEXT,
                      description TEXT,
                      price       REAL,
                      age_months  INTEGER,
                      condition   TEXT,
                      vault_id    INTEGER,
                      vault_name  TEXT,
                      vault_lat   REAL,
                      vault_lon   REAL,
                      img_path    TEXT,
                      ts          TEXT,
                      FOREIGN KEY (seller) REFERENCES users(username))""")
    conn.commit()
    return conn

# ════════════════════════════════════════════════════════════════════════════
# USER HELPERS
# ════════════════════════════════════════════════════════════════════════════
def add_user(conn, u, f, e, h, pw) -> str:
    if not EMAIL_RE.match(e):
        return "Invalid e‑mail format."
    pw_hash = bcrypt.hashpw((pw + h).encode(), bcrypt.gensalt()).decode()
    try:
        conn.execute("INSERT INTO users VALUES (?,?,?,?,?)", (u, f, e, h, pw_hash))
        conn.commit()
        return ""
    except sqlite3.IntegrityError as er:
        return "E‑mail already registered." if "email" in str(er).lower() else "Username taken."

def check_login(conn, u, h, pw) -> bool:
    row = conn.execute("SELECT pwd_hash FROM users WHERE username=? AND house=?", (u, h)).fetchone()
    return row and bcrypt.checkpw((pw + h).encode(), row[0].encode())

# ════════════════════════════════════════════════════════════════════════════
# LISTING HELPERS
# ════════════════════════════════════════════════════════════════════════════
def save_photo(uploaded) -> str:
    ext  = os.path.splitext(uploaded.name)[1].lower()
    path = os.path.join(IMG_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(uploaded.read())
    return path

def add_listing(conn, seller, name, desc, price, age, cond, vault, img_path):
    conn.execute("""INSERT INTO listings
        (seller,name,description,price,age_months,condition,
         vault_id,vault_name,vault_lat,vault_lon,img_path,ts)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (seller, name, desc, price, age, cond,
         vault["id"], vault["properties"]["name"],
         vault["geometry"]["coordinates"][1],
         vault["geometry"]["coordinates"][0],
         img_path, datetime.datetime.now(datetime.UTC)))
    conn.commit()

def all_listings(conn):
    return conn.execute("""SELECT id,seller,name,description,price,age_months,
                                  condition,vault_name,img_path,ts
                           FROM listings ORDER BY id DESC""").fetchall()

def my_listings(conn, seller):
    return conn.execute("SELECT id,name,price,img_path FROM listings WHERE seller=?",(seller,)).fetchall()

def delete_listing(conn, listing_id, seller):
    # get path to delete
    row = conn.execute("SELECT img_path FROM listings WHERE id=? AND seller=?",(listing_id,seller)).fetchone()
    if not row: return False
    img_path = row[0]
    conn.execute("DELETE FROM listings WHERE id=? AND seller=?", (listing_id, seller))
    conn.commit()
    if os.path.exists(img_path):
        os.remove(img_path)
    return True

# ════════════════════════════════════════════════════════════════════════════
# STREAMLIT  ––  PAGES
# ════════════════════════════════════════════════════════════════════════════
def page_signup(conn):
    st.subheader("Sign‑up")
    u = st.text_input("Username")
    f = st.text_input("Full name")
    e = st.text_input("E‑mail")
    h = st.selectbox("House", HOUSES)
    p = st.text_input("Password", type="password")
    if st.button("Create account"):
        if not (u and f and e and p):
            st.warning("Fill all fields.")
        else:
            msg = add_user(conn, u, f, e, h, p)
            (st.error if msg else st.success)(msg or "Account created – please log in.")

def page_login(conn):
    st.subheader("Login")
    u = st.text_input("Username")
    h = st.selectbox("House", HOUSES)
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(conn, u, h, p):
            st.session_state.update(user=u, house=h)
            rerun()
        else:
            st.error("Wrong credentials.")

# ─────────────────────────────────────────────────────────────────────────────
# SELL
# ─────────────────────────────────────────────────────────────────────────────
def page_sell(conn, user):
    st.header("Sell an item")
    name  = st.text_input("Product name")
    desc  = st.text_area("Description")
    price = st.number_input("Price (GLX)", min_value=0.0, step=1.0)
    age   = st.number_input("Age (months)", min_value=0, step=1)
    cond  = st.selectbox("Condition", CONDITIONS)
    photo = st.file_uploader("Product photo", type=["png","jpg","jpeg"])
    st.write("Select the vault (drop‑off spot) for buyers:")
    vault = vault_selector("sell_map")

    if st.button("List product"):
        if not (name and desc and photo and vault):
            st.warning("Fill every field, upload photo, select vault.")
        else:
            img_path = save_photo(photo)
            add_listing(conn, user, name, desc, price, age, cond, vault, img_path)
            st.success("Product listed!")
            rerun()

# ─────────────────────────────────────────────────────────────────────────────
# BUY
# ─────────────────────────────────────────────────────────────────────────────
def page_buy(conn, user):
    st.header("Browse & buy")
    for (lid,seller,name,desc,price,age,cond,vault,img,ts) in all_listings(conn):
        with st.expander(f"{name} — {price:.0f} GLX  (seller: {seller})"):
            if os.path.exists(img):
                st.image(Image.open(img), use_container_width=True)
            st.write(desc)
            st.markdown(f"**Age:** {age} months | **Condition:** {cond}")
            st.caption(f"Listed on {ts.split('T')[0]}")
            if seller == user:
                if st.button("Unlist", key=f"del{lid}"):
                    delete_listing(conn, lid, user)
                    st.success("Listing removed")
                    rerun()
            else:
                if st.button("Buy", key=f"buy{lid}"):
                    st.session_state["pending_buy_id"] = lid
                    st.session_state["page"] = "VaultSelect"
                    rerun()

# ─────────────────────────────────────────────────────────────────────────────
# BUY – vault selection by customer
# ─────────────────────────────────────────────────────────────────────────────
def page_vault_select(conn, user):
    if "pending_buy_id" not in st.session_state:
        st.info("No purchase waiting for vault selection.")
        if st.button("Back to listings"):
            st.session_state["page"] = "Buy"
            rerun()
        return
    lid = st.session_state["pending_buy_id"]
    row = conn.execute("""SELECT vault_lat,vault_lon,vault_name, price
                          FROM listings WHERE id=?""",(lid,)).fetchone()
    if row is None:
        st.error("Listing vanished."); return

    seller_lat, seller_lon, _, price = row
    st.header(f"Choose your pick-up point")
    buyer_vault = vault_selector("buy_map")

    if buyer_vault:
        # 1) map both coords to closest graph node
        s_id = find_closest_node(GRAPH, seller_lat, seller_lon)
        b_id = find_closest_node(GRAPH,
                                 buyer_vault["geometry"]["coordinates"][1],
                                 buyer_vault["geometry"]["coordinates"][0])

        # 2) run *your* A*
        path_node_ids = astar(GRAPH, s_id, b_id)
        if not path_node_ids:
            st.error("No drivable path found."); return

        # 3) convert to lat/lon polyline
        coords = [(GRAPH.nodes[n].lat, GRAPH.nodes[n].lon) for n in path_node_ids]
        km = sum(
            haversine(GRAPH.nodes[path_node_ids[i]], GRAPH.nodes[path_node_ids[i+1]])
            for i in range(len(path_node_ids)-1)
        )
        st.header(f"Distance: {km:,.2f} km")
        final = 0
        if km < 2:
            pass
        elif 2 < km <= 5:
            final += 5 
        elif 5 < km <= 15:
            final += 15
        elif 15 < km <= 30:
            final += 20
        else:
            final = 30
        # 4) visualise
        m = folium.Map(location=coords[len(coords)//2], zoom_start=11)
        folium.PolyLine(coords, color="purple", weight=5).add_to(m)
        folium.Marker(coords[0], tooltip="Seller vault").add_to(m)
        folium.Marker(coords[-1], tooltip="Your vault").add_to(m)
        st_folium(m, key="route_map", width=700, height=500)
        st.markdown(f"Delivery charges: {final} GLX")

        if st.button("Confirm vault & order"):
            st.success("Order placed!")
            st.session_state.pop("pending_buy_id", None)
            st.session_state["page"] = "Buy"
            rerun()

# ─────────────────────────────────────────────────────────────────────────────
# UNLIST page (list only my items)
# ─────────────────────────────────────────────────────────────────────────────
def page_unlist(conn, user):
    st.header("Your listings")
    items = my_listings(conn, user)
    if not items:
        st.info("You have no active listings.")
    for lid, name, price, img in items:
        cols = st.columns([1,5,1])
        if os.path.exists(img):
            with cols[0]: st.image(Image.open(img).resize((60,60)))
        with cols[1]:    st.write(f"**{name}** — {price:.0f} GLX")
        with cols[2]:
            if st.button("Unlist", key=f"ul{lid}"):
                delete_listing(conn, lid, user)
                st.success("Removed")
                rerun()

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD after login
# ════════════════════════════════════════════════════════════════════════════
def dashboard(conn):
    user  = st.session_state["user"]
    house = st.session_state["house"]
    st.success(f"Logged in as {user} — {house}")

    menu_items = ["Buy", "Sell", "Unlist"]
    if "pending_buy_id" in st.session_state:
        menu_items.append("VaultSelect")

    choice = st.sidebar.radio(
        "Marketplace menu",
        menu_items,
        index=menu_items.index(st.session_state.get("page", "Buy"))
    )

    if choice == "Buy":
        page_buy(conn, user)
    elif choice == "Sell":
        page_sell(conn, user)
    elif choice == "Unlist":
        page_unlist(conn, user)
    elif choice == "VaultSelect":
        page_vault_select(conn, user)

    if st.sidebar.button("Logout"):
        st.session_state.clear(); rerun()

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(page_title="Marauder's Mart", layout="wide")
    st.title("Marauder's Mart")

    conn = get_conn()

    if "user" in st.session_state:
        dashboard(conn)
    else:
        action = st.sidebar.radio("Account", ("Login", "Register"))
        (page_login if action == "Login" else page_signup)(conn)

    st.caption("CSL2020 - Data Structures and Algorithms")

if __name__ == "__main__":
    main()