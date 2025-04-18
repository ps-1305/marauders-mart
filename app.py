# app.py ── Marauder’s Mart  (passbook + escrow + status workflow)
import streamlit as st, sqlite3, bcrypt, re, os, uuid, datetime, json, pathlib, requests
from PIL import Image
import folium, osmnx as ox, networkx as nx
from streamlit_folium import st_folium
from pathfinding import parse_graph_json, find_closest_node, astar, Graph, haversine

# ════════════════════════════ CONSTANTS ════════════════════════════════════
DB_NAME   = "users.db"
IMG_DIR   = "images"
VAULTS    = pathlib.Path("data/delhi_vaults.geojson")
GRAPH     = parse_graph_json("data/delhi.json")
GRAPH_FILE= pathlib.Path("data/delhi_drive.graphml")
HOUSES    = ["Gryffindor","Slytherin","Ravenclaw","Hufflepuff"]
CONDITIONS= ["Like New","Very Good","Good","Fair","Poor"]
EMAIL_RE  = re.compile(r"^[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+$")
IST       = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

BASE = "http://localhost:5173"          # C++ escrow server
os.makedirs(IMG_DIR, exist_ok=True)

# ════════════════════ ESCROW SERVER HELPERS ════════════════════════════════
def cpp_balance(u):   return requests.get(f"{BASE}/balance", params={"user":u}).json()["balance"]
def cpp_deposit(u,a): return requests.post(f"{BASE}/deposit",  json={"user":u,"amount":a}).json()["status"]=="ok"
def cpp_withdraw(u,a):return requests.post(f"{BASE}/withdraw", json={"user":u,"amount":a}).json()["status"]=="ok"
def cpp_open(b,v,p,d):r=requests.post(f"{BASE}/escrow/open",   json={"buyer":b,"vendor":v,"product":p,"delivery":d}); return r.json().get("id") if r.ok else None
def cpp_release(eid): requests.post(f"{BASE}/escrow/release", json={"id":eid})

# ═════════════════════ CACHED RESOURCES ════════════════════════════════════
@st.cache_data
def vault_json():      return json.loads(VAULTS.read_text())

@st.cache_resource
def drive_graph():     return ox.load_graphml(GRAPH_FILE) if GRAPH_FILE.exists() \
                              else ox.graph_from_place("Delhi, India","drive")

# ═════════════════════════ DATABASE ════════════════════════════════════════
@st.cache_resource
def db():
    c=sqlite3.connect(DB_NAME,check_same_thread=False)
    cur=c.cursor()
    cur.executescript("""
      CREATE TABLE IF NOT EXISTS users(
          username TEXT PRIMARY KEY, fullname TEXT, email TEXT UNIQUE,
          house TEXT, pwd_hash TEXT);

      CREATE TABLE IF NOT EXISTS listings(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          seller TEXT, name TEXT, description TEXT, price REAL,
          age_months INTEGER, condition TEXT,
          vault_id INTEGER, vault_name TEXT, vault_lat REAL, vault_lon REAL,
          img_path TEXT, ts TEXT, status TEXT DEFAULT 'OPEN');
    """)
    # add status column if db is older
    cur.execute("PRAGMA table_info(listings)")
    if "status" not in {r[1] for r in cur.fetchall()}:
        cur.execute("ALTER TABLE listings ADD COLUMN status TEXT DEFAULT 'OPEN'")
    c.commit(); return c

# ═══════════════════ USER HELPERS ══════════════════════════════════════════
def add_user(c,u,f,e,h,p):
    if not EMAIL_RE.match(e): return "Invalid e‑mail"
    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                  (u,f,e,h,bcrypt.hashpw((p+h).encode(),bcrypt.gensalt()).decode()))
        c.commit(); return ""
    except sqlite3.IntegrityError as er:
        return "E‑mail exists" if "email" in str(er).lower() else "Username taken"

def login_ok(c,u,h,p):
    row=c.execute("SELECT pwd_hash FROM users WHERE username=? AND house=?",(u,h)).fetchone()
    return row and bcrypt.checkpw((p+h).encode(),row[0].encode())

# ═══════════════════ LISTINGS HELPERS ══════════════════════════════════════
def add_listing(c,seller,nm,dc,pr,age,cond,vault,img):
    ts=datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO listings
        (seller,name,description,price,age_months,condition,
         vault_id,vault_name,vault_lat,vault_lon,img_path,ts,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'OPEN')""",
        (seller,nm,dc,pr,age,cond,
         vault["id"],vault["properties"]["name"],
         vault["geometry"]["coordinates"][1],
         vault["geometry"]["coordinates"][0],img,ts))
    c.commit()

def rows_open(c):  return c.execute("SELECT * FROM listings WHERE status='OPEN' ORDER BY id DESC").fetchall()
def rows_user(c,u):return c.execute("SELECT id,name,price,img_path FROM listings WHERE seller=? AND status='OPEN'",(u,)).fetchall()
def set_status(c,lid,st): c.execute("UPDATE listings SET status=? WHERE id=?",(st,lid)); c.commit()
def delete_listing(c,lid,u):
    p=c.execute("SELECT img_path FROM listings WHERE id=? AND seller=?",(lid,u)).fetchone()
    if p and os.path.exists(p[0]): os.remove(p[0])
    c.execute("DELETE FROM listings WHERE id=? AND seller=?",(lid,u)); c.commit()

# ═══════════════════ MAP & DELIVERY ════════════════════════════════════════
def vault_selector(k):
    m=folium.Map([28.61,77.21],zoom_start=11)
    for f in vault_json()["features"]:
        lon,lat=f["geometry"]["coordinates"]
        folium.Marker([lat,lon],tooltip=f["properties"]["name"]).add_to(m)
    r=st_folium(m,key=k,width=700,height=500).get("last_object_clicked")
    if not r: return None
    for f in vault_json()["features"]:
        lon,lat=f["geometry"]["coordinates"]
        if abs(lat-r["lat"])<1e-5 and abs(lon-r["lng"])<1e-5: return f
    return None

def fee(km): return 0 if km<=2 else 5 if km<=5 else 10 if km<=15 else 20 if km<=30 else 30

# ═══════════════════ PAGES ═════════════════════════════════════════════════
def passbook(u):
    st.header("Passbook")
    st.info(f"Balance : {cpp_balance(u):,.2f} GLX")
    col1,col2=st.columns(2)
    with col1:
        a=st.number_input("Deposit",1.0,step=1.0); 
        if st.button("Deposit") and cpp_deposit(u,a): st.rerun()
    with col2:
        a=st.number_input("Withdraw",1.0,step=1.0,key="wd");
        if st.button("Withdraw") and cpp_withdraw(u,a): st.rerun()

def sell(c,u):
    st.header("Sell item")
    n=st.text_input("Name"); d=st.text_area("Description")
    p=st.number_input("Price",0.0); age=st.number_input("Age mo",0)
    cond=st.selectbox("Condition",CONDITIONS)
    pic=st.file_uploader("Photo",["png","jpg","jpeg"])
    st.write("Pick seller vault"); v=vault_selector("sell")
    if st.button("List"):
        if not (n and d and pic and v): st.warning("Fill all"); return
        img=os.path.join(IMG_DIR,f"{uuid.uuid4().hex}.png")
        open(img,"wb").write(pic.read())
        add_listing(c,u,n,d,p,age,cond,v,img); st.rerun()

def buy(c,u):
    st.header("Marketplace")
    for row in rows_open(c):
        (lid,seller,nm,dc,pr,age,cond,_,_,_,_,img,ts,_) = row
        with st.expander(f"{nm} — {pr:.0f} GLX  (seller {seller})"):
            if os.path.exists(img): st.image(Image.open(img),use_container_width=True)
            st.write(dc)
            st.markdown(f"**Age:** {age} months | **Condition:** {cond}")
            st.caption(f"Listed on {ts.split('T')[0]}")
            if seller==u:
                if st.button("Unlist",key=f"ul{lid}"): delete_listing(c,lid,u); st.rerun()
            else:
                if st.button("Buy",key=f"buy{lid}"):
                    set_status(c,lid,"LOCKED")
                    st.session_state.update(pid=lid,page="VaultSelect")
                    st.rerun()

def vault_select(c,u):
    lid=st.session_state.get("pid")
    row=c.execute("SELECT seller,vault_lat,vault_lon,price FROM listings WHERE id=?", (lid,)).fetchone()
    if not row: st.error("Listing gone"); return
    seller,slat,slon,price=row
    st.header("Choose your vault"); v=vault_selector("buy")
    if not v: return
    n1=find_closest_node(GRAPH,slat,slon)
    n2=find_closest_node(GRAPH,v["geometry"]["coordinates"][1],v["geometry"]["coordinates"][0])
    path=astar(GRAPH,n1,n2)
    coords=[(GRAPH.nodes[n].lat,GRAPH.nodes[n].lon) for n in path]
    km=sum(haversine(GRAPH.nodes[path[i]],GRAPH.nodes[path[i+1]]) for i in range(len(path)-1))
    dfee=fee(km); st.info(f"Distance {km:,.2f} km | Delivery {dfee} GLX")
    m=folium.Map(coords[len(coords)//2],zoom_start=11)
    folium.PolyLine(coords,color="purple",weight=4).add_to(m)
    st_folium(m,key="route",width=700,height=500)

    if st.button("Confirm order"):
        eid=cpp_open(u,seller,price,dfee)
        if eid:
            st.success("Vault opened")
            st.session_state.update(eid=eid,page="AwaitDelivery")
            st.rerun()
        else: st.error("Insufficient balance")

def await_delivery(c,u):
    eid=st.session_state.get("eid"); lid=st.session_state.get("pid")
    if not eid: st.info("Nothing awaiting delivery"); return
    st.success("Waiting for delivery confirmation")
    if st.button("Received order"):
        cpp_release(eid)               # release GLX
        set_status(c,lid,"SOLD")
        st.session_state.pop("eid", None)
        st.session_state.pop("pid", None)
        st.session_state["page"] = "Buy"    
        st.rerun()

def my_open(c,u):
    st.header("Your open listings")
    for lid,nm,pr,img in rows_user(c,u):
        cols=st.columns([1,4,1])
        if os.path.exists(img): cols[0].image(Image.open(img).resize((60,60)))
        cols[1].write(f"{nm} — {pr:.0f} GLX")
        if cols[2].button("❌",key=f"x{lid}"): delete_listing(c,lid,u); st.rerun()

# ═══════════════════ ROUTER ═════════════════════════════════════════════════
def main():
    st.set_page_config("Marauder's Mart",layout="wide")
    c=db()

    if "user" in st.session_state:
        u=st.session_state["user"]
        st.sidebar.write(f"Wallet : {cpp_balance(u):,.2f} GLX")

        menu = ["Buy","Sell","Passbook","Unlist"]
        if "pid" in st.session_state: menu.append("VaultSelect")
        if "eid" in st.session_state: menu.append("AwaitDelivery")

        current = st.session_state.get("page","Buy")
        if current not in menu:
            current = menu[0]

        page = st.sidebar.radio("Menu", menu, index=menu.index(current))
        st.session_state["page"] = page

        if   page=="Buy":          buy(c,u)
        elif page=="Sell":         sell(c,u)
        elif page=="Passbook":     passbook(u)
        elif page=="Unlist":       my_open(c,u)
        elif page=="VaultSelect":  vault_select(c,u)
        elif page=="AwaitDelivery":await_delivery(c,u)

        if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
    else:
        act=st.sidebar.radio("Account",("Login","Register"))
        if act=="Login":
            u=st.text_input("Username"); h=st.selectbox("House",HOUSES); p=st.text_input("Password",type="password")
            if st.button("Login") and login_ok(c,u,h,p):
                st.session_state.update(user=u,house=h); st.rerun()
        else:
            u=st.text_input("Username"); f=st.text_input("Full name"); e=st.text_input("Email")
            h=st.selectbox("House",HOUSES); p=st.text_input("Password",type="password")
            if st.button("Create") and not (msg:=add_user(c,u,f,e,h,p)):
                st.success("Account created. Log in!")

    st.caption("CSL2020 — Data Structures & Algorithms")

if __name__=="__main__":
    main()