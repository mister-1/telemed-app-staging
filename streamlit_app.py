"""
Telemedicine Transactions Dashboard
----------------------------------

Stack:
- Frontend: Streamlit (pastel UI), Plotly Express charts (with data labels)
- Backend DB: Supabase (Postgres). Single source of truth for everyone with the link.
- Auth: Admin login (default: telemed / Telemed@DHI). Passwords stored hashed (bcrypt).

How to deploy (summary):
1) Create a free Supabase project ➜ copy SUPABASE_URL and SUPABASE_ANON_KEY.
2) In SQL editor, run the SCHEMA below (--- SCHEMA --- section) to create tables and policies.
3) Deploy this app to Streamlit Cloud or any server. Set environment variables:
   SUPABASE_URL, SUPABASE_KEY (use the ANON key for simplicity) and APP_SECRET.
4) Open the app ➜ Admin ➜ login (telemed / Telemed@DHI) ➜ manage hospitals & transactions.

Note: This single file contains the app code. At the very bottom you’ll find:
- --- SCHEMA ---: SQL you run once in Supabase
- --- TH_PROVINCES ---: Province→Region mapping
"""

import os
import uuid
import json
import bcrypt
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

import streamlit as st
from supabase import create_client, Client

# =========================
# ---------- THEME --------
# =========================
# Pastel styling via CSS + Plotly template tweaks
PASTEL_BG = "#F7F8FB"
PASTEL_CARD = "#FFFFFF"
PASTEL_ACCENT = "#A7C7E7"   # soft baby blue
PASTEL_ACCENT_2 = "#F8C8DC" # soft pink
PASTEL_ACCENT_3 = "#B6E2D3" # mint
PASTEL_TEXT = "#3E4B6D"

st.set_page_config(
    page_title="Telemedicine Transactions",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {PASTEL_BG}; }}
      .stButton>button {{
          background: linear-gradient(135deg, {PASTEL_ACCENT}, {PASTEL_ACCENT_3});
          color: {PASTEL_TEXT};
          border: none; border-radius: 14px; padding: 0.6rem 1rem; font-weight: 600;
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
      }}
      .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {{
          background: {PASTEL_CARD}; color: {PASTEL_TEXT}; border-radius: 12px;
      }}
      .css-1d391kg, .e1f1d6gn2 {{ color: {PASTEL_TEXT}; }}
      .metric-card {{ background: {PASTEL_CARD}; padding: 1rem; border-radius: 16px; box-shadow: 0 1px 8px rgba(0,0,0,0.05); }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# ---- ENV & CONNECTION ----
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
APP_SECRET = os.getenv("APP_SECRET", "replace-me").encode()

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variable.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb: Client = get_client()

# =========================
# ------- CONSTANTS --------
# =========================
SITE_CONTROL_CHOICES = ["ทีมใต้", "ทีมเหนือ", "ทีมอีสาน"]
SYSTEM_CHOICES = ["HOSxpV4", "HOSxpV3", "WebPortal"]
SERVICE_MODEL_CHOICES = ["Rider", "App", "Station to Station"]

# Province ➜ Region mapping (Thai). See the full mapping at the bottom.
from collections import OrderedDict
TH_PROVINCES: Dict[str, str] = OrderedDict(json.loads('''
{
  "กระบี่":"ภาคใต้","กรุงเทพมหานคร":"ภาคกลาง","กาญจนบุรี":"ภาคตะวันตก","กาฬสินธุ์":"ภาคอีสาน",
  "กำแพงเพชร":"ภาคเหนือ","ขอนแก่น":"ภาคอีสาน","จันทบุรี":"ภาคตะวันออก","ฉะเชิงเทรา":"ภาคตะวันออก",
  "ชลบุรี":"ภาคตะวันออก","ชัยนาท":"ภาคกลาง","ชัยภูมิ":"ภาคอีสาน","ชุมพร":"ภาคใต้",
  "เชียงราย":"ภาคเหนือ","เชียงใหม่":"ภาคเหนือ","ตรัง":"ภาคใต้","ตราด":"ภาคตะวันออก",
  "ตาก":"ภาคตะวันตก","นครนายก":"ภาคกลาง","นครปฐม":"ภาคกลาง","นครพนม":"ภาคอีสาน",
  "นครราชสีมา":"ภาคอีสาน","นครศรีธรรมราช":"ภาคใต้","นครสวรรค์":"ภาคเหนือ","นนทบุรี":"ภาคกลาง",
  "นราธิวาส":"ภาคใต้","น่าน":"ภาคเหนือ","บึงกาฬ":"ภาคอีสาน","บุรีรัมย์":"ภาคอีสาน",
  "ปทุมธานี":"ภาคกลาง","ประจวบคีรีขันธ์":"ภาคตะวันตก","ปราจีนบุรี":"ภาคตะวันออก","ปัตตานี":"ภาคใต้",
  "พระนครศรีอยุธยา":"ภาคกลาง","พะเยา":"ภาคเหนือ","พังงา":"ภาคใต้","พัทลุง":"ภาคใต้",
  "พิจิตร":"ภาคเหนือ","พิษณุโลก":"ภาคเหนือ","เพชรบุรี":"ภาคตะวันตก","เพชรบูรณ์":"ภาคเหนือ",
  "แพร่":"ภาคเหนือ","ภูเก็ต":"ภาคใต้","มหาสารคาม":"ภาคอีสาน","มุกดาหาร":"ภาคอีสาน",
  "แม่ฮ่องสอน":"ภาคเหนือ","ยะลา":"ภาคใต้","ยโสธร":"ภาคอีสาน","ร้อยเอ็ด":"ภาคอีสาน",
  "ระนอง":"ภาคใต้","ระยอง":"ภาคตะวันออก","ราชบุรี":"ภาคตะวันตก","ลพบุรี":"ภาคกลาง",
  "ลำปาง":"ภาคเหนือ","ลำพูน":"ภาคเหนือ","เลย":"ภาคอีสาน","ศรีสะเกษ":"ภาคอีสาน",
  "สกลนคร":"ภาคอีสาน","สงขลา":"ภาคใต้","สตูล":"ภาคใต้","สมุทรปราการ":"ภาคกลาง",
  "สมุทรสงคราม":"ภาคกลาง","สมุทรสาคร":"ภาคกลาง","สระแก้ว":"ภาคตะวันออก","สระบุรี":"ภาคกลาง",
  "สิงห์บุรี":"ภาคกลาง","สุโขทัย":"ภาคเหนือ","สุพรรณบุรี":"ภาคกลาง","สุราษฎร์ธานี":"ภาคใต้",
  "สุรินทร์":"ภาคอีสาน","หนองคาย":"ภาคอีสาน","หนองบัวลำภู":"ภาคอีสาน","อ่างทอง":"ภาคกลาง",
  "อำนาจเจริญ":"ภาคอีสาน","อุดรธานี":"ภาคอีสาน","อุตรดิตถ์":"ภาคเหนือ","อุทัยธานี":"ภาคกลาง",
  "อุบลราชธานี":"ภาคอีสาน"
}
'''))
REGION_CHOICES = sorted(list(set(TH_PROVINCES.values())))

# =========================
# -------- HELPERS ---------
# =========================
def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

@st.cache_data(ttl=60, show_spinner=False)
def load_df(table: str) -> pd.DataFrame:
    data = sb.table(table).select("*").execute().data
    return pd.DataFrame(data)

def reload_all():
    load_df.clear()
    st.experimental_rerun()

# Ensure default admin exists
def ensure_default_admin():
    admins = sb.table("admins").select("username").eq("username", "telemed").execute().data
    if not admins:
        sb.table("admins").insert({
            "id": str(uuid.uuid4()),
            "username": "telemed",
            "password_hash": hash_pw("Telemed@DHI")
        }).execute()

ensure_default_admin()

# =========================
# ---------- AUTH ----------
# =========================
if "auth" not in st.session_state:
    st.session_state["auth"] = {"ok": False, "user": None}

with st.sidebar:
    st.markdown("## 🔐 Admin Login")
    if not st.session_state.auth["ok"]:
        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Username", value="")
            p = st.text_input("Password", type="password", value="")
            submitted = st.form_submit_button("Login")
        if submitted:
            rows = sb.table("admins").select("*").eq("username", u).execute().data
            if rows and verify_pw(p, rows[0]["password_hash"]):
                st.session_state.auth = {"ok": True, "user": rows[0]["username"]}
                st.success("เข้าสู่ระบบสำเร็จ")
                st.experimental_rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        st.write(f"✅ Logged in as **{st.session_state.auth['user']}**")
        if st.button("Logout"):
            st.session_state.auth = {"ok": False, "user": None}
            st.experimental_rerun()

# =========================
# --------- FILTERS --------
# =========================
colF1, colF2, colF3 = st.columns([1,1,2])
with colF1:
    hospitals_df = load_df("hospitals")
    hospital_names = ["(ทั้งหมด)"] + sorted(hospitals_df.get("name", pd.Series(dtype=str)).dropna().unique().tolist())
    selected_hospital = st.selectbox("โรงพยาบาล", hospital_names)
with colF2:
    today = date.today()
    start_default = today - timedelta(days=30)
    date_range = st.date_input("ช่วงวันที่", value=(start_default, today))
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = (start_default, today)
with colF3:
    site_filter = st.multiselect("ทีมภูมิภาค (SiteControl)", SITE_CONTROL_CHOICES)

# =========================
# ------ DATA & LOGIC ------
# =========================
transactions_df = load_df("transactions")
if not transactions_df.empty:
    # filter by date
    transactions_df["date"] = pd.to_datetime(transactions_df["date"]).dt.date
    mask = (transactions_df["date"] >= start_date) & (transactions_df["date"] <= end_date)
    transactions_df = transactions_df.loc[mask].copy()

# join hospitals
if not hospitals_df.empty and not transactions_df.empty:
    merged = transactions_df.merge(hospitals_df, left_on="hospital_id", right_on="id", how="left", suffixes=("", "_h"))
else:
    merged = pd.DataFrame(columns=["date","hospital_id","transactions_count","riders_active","name","site_control","province","region","riders_count"])

# extra filters
if selected_hospital != "(ทั้งหมด)":
    merged = merged.loc[merged["name"] == selected_hospital]
if site_filter:
    merged = merged.loc[merged["site_control"].isin(site_filter)]

# =========================
# ---------- KPIs ----------
# =========================
st.markdown("### 📈 ภาพรวม (Overview)")
colK1, colK2, colK3, colK4 = st.columns(4)

total_tx = int(merged["transactions_count"].sum()) if not merged.empty else 0
unique_h = merged["hospital_id"].nunique() if not merged.empty else 0
sum_riders_active = int(merged["riders_active"].sum()) if not merged.empty else 0
sum_riders_capacity = int(merged["riders_count"].sum()) if not merged.empty else 0

with colK1:
    st.markdown(f"<div class='metric-card'><b>จำนวนธุรกรรมทั้งหมด</b><h2>{total_tx:,}</h2></div>", unsafe_allow_html=True)
with colK2:
    st.markdown(f"<div class='metric-card'><b>จำนวนโรงพยาบาล</b><h2>{unique_h}</h2></div>", unsafe_allow_html=True)
with colK3:
    st.markdown(f"<div class='metric-card'><b>Rider Active (รวม)</b><h2>{sum_riders_active:,}</h2></div>", unsafe_allow_html=True)
with colK4:
    st.markdown(f"<div class='metric-card'><b>จำนวน Rider (Capacity)</b><h2>{sum_riders_capacity:,}</h2></div>", unsafe_allow_html=True)

# =========================
# --------- CHARTS ---------
# =========================
if merged.empty:
    st.info("ยังไม่มีข้อมูล ลองเพิ่มจากหน้า Admin ➜ จัดการข้อมูล")
else:
    # 1) By SiteControl (ทีมภูมิภาค)
    st.markdown("#### แยกตามทีมภูมิภาค")
    grp_site = merged.groupby("site_control").agg({
        "transactions_count":"sum",
        "riders_active":"sum",
        "riders_count":"sum"
    }).reset_index()
    fig1 = px.bar(grp_site, x="site_control", y="transactions_count", text="transactions_count",
                  labels={"site_control":"ทีมภูมิภาค","transactions_count":"Transactions"})
    fig1.update_traces(textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

    # 2) Per Hospital (total in range)
    st.markdown("#### ภาพรวมต่อโรงพยาบาล (รวมในช่วงที่เลือก)")
    grp_h = merged.groupby("name").agg({
        "transactions_count":"sum",
        "riders_active":"sum",
        "riders_count":"sum"
    }).reset_index().sort_values("transactions_count", ascending=False)
    fig2 = px.bar(grp_h, x="name", y="transactions_count", text="transactions_count",
                  labels={"name":"โรงพยาบาล","transactions_count":"Transactions"})
    fig2.update_traces(textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

    # 3) Daily trend (selected filter)
    st.markdown("#### แนวโน้มรายวัน")
    daily = merged.groupby("date").agg({"transactions_count":"sum","riders_active":"sum"}).reset_index()
    fig3 = px.bar(daily, x="date", y="transactions_count", text="transactions_count",
                  labels={"date":"วันที่","transactions_count":"Transactions"})
    fig3.update_traces(textposition='outside')
    st.plotly_chart(fig3, use_container_width=True)

    # 4) Monthly overview
    st.markdown("#### ภาพรวมรายเดือน")
    tmp = merged.copy()
    tmp["month"] = pd.to_datetime(tmp["date"]).dt.to_period("M").astype(str)
    monthly = tmp.groupby("month").agg({"transactions_count":"sum","riders_active":"sum"}).reset_index()
    fig4 = px.bar(monthly, x="month", y="transactions_count", text="transactions_count",
                  labels={"month":"เดือน","transactions_count":"Transactions"})
    fig4.update_traces(textposition='outside')
    st.plotly_chart(fig4, use_container_width=True)

    # Table: Transactions by SiteControl
    st.markdown("#### ตารางจำนวน Transection แยกตามทีมภูมิภาค")
    st.dataframe(grp_site.rename(columns={
        "site_control":"ทีมภูมิภาค",
        "transactions_count":"Transactions",
        "riders_active":"Rider Active",
        "riders_count":"Riders ทั้งหมด"
    }), use_container_width=True)

# =========================
# ---------- ADMIN ---------
# =========================
st.markdown("---")
st.markdown("## 🛠️ หน้าการจัดการ (Admin)")
if not st.session_state.auth["ok"]:
    st.warning("เข้าสู่ระบบทาง Sidebar เพื่อจัดการข้อมูล")
else:
    tabs = st.tabs(["จัดการโรงพยาบาล", "จัดการ Transaction", "จัดการผู้ดูแล (Admin)"])

    # ----- Manage Hospitals -----
    with tabs[0]:
        st.markdown("### โรงพยาบาล")
        with st.expander("➕ เพิ่ม/แก้ไข โรงพยาบาล"):
            edit_mode = st.checkbox("แก้ไขรายการที่มีอยู่", value=False)
            if edit_mode and not hospitals_df.empty:
                row = st.selectbox("เลือกโรงพยาบาลที่จะแก้ไข", hospitals_df["name"].tolist())
                row_data = hospitals_df[hospitals_df["name"]==row].iloc[0].to_dict()
            else:
                row_data = {"id": str(uuid.uuid4())}

            name = st.text_input("ชื่อโรงพยาบาล", value=row_data.get("name", ""))
            province = st.selectbox("จังหวัด", list(TH_PROVINCES.keys()), index= list(TH_PROVINCES.keys()).index(row_data.get("province","กระบี่")) if row_data.get("province") in TH_PROVINCES else 0)
            region = TH_PROVINCES.get(province, "ภาคกลาง")
            st.info(f"ภูมิภาค: **{region}** (กำหนดอัตโนมัติจากจังหวัด)")
            site = st.selectbox("SiteControl (ทีม)", SITE_CONTROL_CHOICES, index=max(0, SITE_CONTROL_CHOICES.index(row_data.get("site_control","ทีมใต้")) if row_data.get("site_control") in SITE_CONTROL_CHOICES else 0))
            system = st.selectbox("ระบบที่ใช้", SYSTEM_CHOICES, index=max(0, SYSTEM_CHOICES.index(row_data.get("system_type","HOSxpV4")) if row_data.get("system_type") in SYSTEM_CHOICES else 0))
            service_models = st.multiselect("โมเดลบริการ (เลือกได้หลายอัน)", SERVICE_MODEL_CHOICES, default=[x for x in (row_data.get("service_models") or []) if x in SERVICE_MODEL_CHOICES])
            riders_count = st.number_input("จำนวน Rider (Capacity)", min_value=0, step=1, value=int(row_data.get("riders_count",0)))

            c1, c2 = st.columns(2)
            with c1:
                if st.button("บันทึกโรงพยาบาล"):
                    payload = {
                        "id": row_data.get("id", str(uuid.uuid4())),
                        "name": name.strip(),
                        "province": province,
                        "region": region,
                        "site_control": site,
                        "system_type": system,
                        "service_models": service_models,
                        "riders_count": int(riders_count)
                    }
                    if not name.strip():
                        st.error("กรุณากรอกชื่อโรงพยาบาล")
                    else:
                        if edit_mode:
                            sb.table("hospitals").update(payload).eq("id", row_data["id"]).execute()
                            st.success("อัปเดตข้อมูลโรงพยาบาลแล้ว")
                        else:
                            sb.table("hospitals").insert(payload).execute()
                            st.success("เพิ่มโรงพยาบาลแล้ว")
                        reload_all()
            with c2:
                if edit_mode and st.button("🗑️ ลบโรงพยาบาล"):
                    sb.table("hospitals").delete().eq("id", row_data["id"]).execute()
                    st.success("ลบแล้ว")
                    reload_all()

        st.markdown("#### รายชื่อโรงพยาบาล")
        st.dataframe(hospitals_df, use_container_width=True)

    # ----- Manage Transactions -----
    with tabs[1]:
        st.markdown("### Transaction ต่อวัน")
        if hospitals_df.empty:
            st.info("ยังไม่มีโรงพยาบาล ใส่ข้อมูลโรงพยาบาลก่อน")
        else:
            hosp_map = {r["name"]: r["id"] for _, r in hospitals_df.iterrows()}
            with st.expander("➕ เพิ่ม Transaction รายวัน"):
                hname = st.selectbox("โรงพยาบาล", list(hosp_map.keys()), key="tx_add_h")
                tx_date = st.date_input("วันที่", value=date.today(), key="tx_add_d")
                tx_num = st.number_input("จำนวน Transactions", min_value=0, step=1, key="tx_add_n")
                riders_active = st.number_input("Rider Active", min_value=0, step=1, key="tx_add_ra")
                if st.button("บันทึก Transaction"):
                    sb.table("transactions").insert({
                        "id": str(uuid.uuid4()),
                        "hospital_id": hosp_map[hname],
                        "date": tx_date.isoformat(),
                        "transactions_count": int(tx_num),
                        "riders_active": int(riders_active)
                    }).execute()
                    st.success("เพิ่มข้อมูลแล้ว")
                    reload_all()

            st.markdown("#### ตาราง Transaction (แก้ไขได้)")
            # Editable grid-like approach
            # For inline edit per row, provide a selector then allow edit
            tx_view = merged[["date","name","transactions_count","riders_active","hospital_id","id" if "id" in merged.columns else "hospital_id"]].copy()
            if "id" not in tx_view.columns:
                # reload raw to ensure we have transaction id
                raw_tx = load_df("transactions")
                tx_view = raw_tx.merge(hospitals_df[["id","name"]], left_on="hospital_id", right_on="id", suffixes=("","_h"))
                tx_view = tx_view[["id","date","name","transactions_count","riders_active","hospital_id"]]

            st.dataframe(tx_view.rename(columns={"name":"โรงพยาบาล","date":"วันที่","transactions_count":"Transactions","riders_active":"Rider Active"}), use_container_width=True)

            with st.expander("✏️ แก้ไข / ลบ Transaction"):
                raw_tx = load_df("transactions")
                if raw_tx.empty:
                    st.info("ยังไม่มีข้อมูล")
                else:
                    pick_id = st.selectbox("เลือกแถวเพื่อแก้ไข", raw_tx["id"].tolist())
                    row = raw_tx[raw_tx["id"]==pick_id].iloc[0].to_dict()
                    h_id_to_name = {r["id"]: r["name"] for _, r in hospitals_df.iterrows()}
                    hsel = st.selectbox("โรงพยาบาล", list(hosp_map.keys()), index=list(hosp_map.keys()).index(h_id_to_name.get(row["hospital_id"], list(hosp_map.keys())[0])))
                    dsel = st.date_input("วันที่", value=pd.to_datetime(row["date"]).date())
                    nsel = st.number_input("Transactions", min_value=0, step=1, value=int(row.get("transactions_count",0)))
                    rsel = st.number_input("Rider Active", min_value=0, step=1, value=int(row.get("riders_active",0)))
                    c3, c4 = st.columns(2)
                    with c3:
                        if st.button("บันทึกการแก้ไข", key="btn_tx_save"):
                            sb.table("transactions").update({
                                "hospital_id": hosp_map[hsel],
                                "date": dsel.isoformat(),
                                "transactions_count": int(nsel),
                                "riders_active": int(rsel)
                            }).eq("id", pick_id).execute()
                            st.success("อัปเดตแล้ว")
                            reload_all()
                    with c4:
                        if st.button("ลบแถวนี้", key="btn_tx_del"):
                            sb.table("transactions").delete().eq("id", pick_id).execute()
                            st.success("ลบแล้ว")
                            reload_all()

    # ----- Manage Admins -----
    with tabs[2]:
        st.markdown("### ผู้ดูแลระบบ (Admins)")
        admins_df = load_df("admins")
        st.dataframe(admins_df[["username","created_at"]] if "created_at" in admins_df.columns else admins_df[["username"]], use_container_width=True)

        with st.expander("➕ เพิ่มผู้ดูแลใหม่"):
            nu = st.text_input("Username ใหม่")
            npw = st.text_input("Password", type="password")
            if st.button("เพิ่มผู้ดูแล"):
                if not nu or not npw:
                    st.error("กรอกให้ครบ")
                elif any(admins_df["username"].str.lower() == nu.lower()):
                    st.error("มี username นี้แล้ว")
                else:
                    sb.table("admins").insert({
                        "id": str(uuid.uuid4()),
                        "username": nu,
                        "password_hash": hash_pw(npw)
                    }).execute()
                    st.success("เพิ่มผู้ดูแลแล้ว")
                    reload_all()

        with st.expander("✏️ เปลี่ยนรหัสผ่าน / ลบผู้ดูแล"):
            if admins_df.empty:
                st.info("ยังไม่มีผู้ดูแล")
            else:
                selu = st.selectbox("เลือกผู้ใช้", admins_df["username"].tolist())
                newpw = st.text_input("รหัสผ่านใหม่", type="password")
                c5, c6 = st.columns(2)
                with c5:
                    if st.button("เปลี่ยนรหัสผ่าน"):
                        if not newpw:
                            st.error("กรุณากรอกรหัสผ่านใหม่")
                        else:
                            sb.table("admins").update({"password_hash": hash_pw(newpw)}).eq("username", selu).execute()
                            st.success("เปลี่ยนรหัสผ่านแล้ว")
                            reload_all()
                with c6:
                    if st.button("ลบผู้ดูแล"):
                        sb.table("admins").delete().eq("username", selu).execute()
                        st.success("ลบแล้ว")
                        reload_all()

# =========================
# ---------- FOOTER --------
# =========================
st.markdown("---")
st.caption("Telemedicine Dashboard • pastel theme • built with Streamlit + Supabase")


# ==================================================================
# --------------------------- SCHEMA -------------------------------
# ==================================================================
# Run this in Supabase SQL Editor once.
SCHEMA_SQL = r"""
-- Admins
create table if not exists public.admins (
  id uuid primary key,
  username text unique not null,
  password_hash text not null,
  created_at timestamp with time zone default now()
);

-- Hospitals
create table if not exists public.hospitals (
  id uuid primary key,
  name text unique not null,
  province text not null,
  region text not null,
  site_control text not null check (site_control in ('ทีมใต้','ทีมเหนือ','ทีมอีสาน')),
  system_type text not null check (system_type in ('HOSxpV4','HOSxpV3','WebPortal')),
  service_models text[] not null default '{}',
  riders_count integer not null default 0,
  created_at timestamp with time zone default now()
);

-- Transactions (daily)
create table if not exists public.transactions (
  id uuid primary key,
  hospital_id uuid references public.hospitals(id) on delete cascade,
  date date not null,
  transactions_count integer not null default 0,
  riders_active integer not null default 0,
  created_at timestamp with time zone default now()
);

-- Helpful indexes
create index if not exists idx_tx_hospital_date on public.transactions(hospital_id, date);
create index if not exists idx_hosp_site on public.hospitals(site_control);

-- RLS (for anon usage). For simplicity we allow full read/write from anon. Restrict in production.
alter table public.admins enable row level security;
alter table public.hospitals enable row level security;
alter table public.transactions enable row level security;

drop policy if exists p_admins_all on public.admins;
drop policy if exists p_hosp_all on public.hospitals;
drop policy if exists p_tx_all on public.transactions;

create policy p_admins_all on public.admins for all using (true) with check (true);
create policy p_hosp_all on public.hospitals for all using (true) with check (true);
create policy p_tx_all on public.transactions for all using (true) with check (true);
"""

# ==================================================================
# ------------------------ TH_PROVINCES ----------------------------
# ==================================================================
# If you want the full dict in one place for reuse:
TH_PROVINCES_FULL_JSON = json.dumps(TH_PROVINCES, ensure_ascii=False)
