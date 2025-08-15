# DashBoard Telemedicine — v4.7.0
# อัปเดต:
# - ปุ่ม "ดาวน์โหลดภาพ PNG" + "ส่งออกข้อมูลที่กรองแล้ว" ย้ายไป Sidebar
# - st.date_input แสดงรูปแบบ DD/MM/YYYY
# - ลดช่องว่างด้านบนหน้า Dashboard
# - ย้าย "แนวโน้มรายวัน" แทรกระหว่าง "ตามทีม (วงกลม)" และ "ประเภทโรงพยาบาล (สรุป)"

import os, uuid, json, bcrypt, requests, random, io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime, timedelta
from typing import List, Dict
import streamlit as st
from supabase import create_client, Client

APP_VERSION = "v4.7.0"

# ---------------- Page / Theme ----------------
st.set_page_config(page_title="DashBoard Telemedicine", page_icon="📊", layout="wide")

PALETTE_PASTEL = ["#A7C7E7","#F8C8DC","#B6E2D3","#FDE2B3","#EAD7F7","#CDE5F0",
                  "#FFD6E8","#C8E6C9","#FFF3B0","#D7E3FC","#F2D7EE","#B8F1ED"]
PALETTE_DARK   = ["#60A5FA","#F472B6","#34D399","#FBBF24","#C084FC","#67E8F9",
                  "#FCA5A5","#86EFAC","#FDE68A","#A5B4FC","#F5D0FE","#99F6E4"]

SITE_CONTROL_CHOICES = ['ทีมใต้', 'ทีมเหนือ', 'ทีมอีสาน']
SYSTEM_CHOICES = ['HOSxpV4', 'HOSxpV3', 'WebPortal']
DEFAULT_SERVICE_MODELS = ['Rider', 'App', 'Station to Station']
DEFAULT_HOSPITAL_TYPES = ['รพ.ศูนย์/รพ.ทั่วไป','รพ.ชุมชน','สถาบัน/เฉพาะทาง','เอกชน/คลินิก']

# -------- 77 จังหวัด + ภูมิภาค --------
TH_PROVINCES = {
    'กรุงเทพมหานคร':'ภาคกลาง','นนทบุรี':'ภาคกลาง','ปทุมธานี':'ภาคกลาง','พระนครศรีอยุธยา':'ภาคกลาง',
    'อ่างทอง':'ภาคกลาง','ลพบุรี':'ภาคกลาง','สิงห์บุรี':'ภาคกลาง','ชัยนาท':'ภาคกลาง','สระบุรี':'ภาคกลาง',
    'นครปฐม':'ภาคกลาง','สมุทรสาคร':'ภาคกลาง','สมุทรสงคราม':'ภาคกลาง','สุพรรณบุรี':'ภาคกลาง','สมุทรปราการ':'ภาคกลาง',
    'นครนายก':'ภาคกลาง',
    'ชลบุรี':'ภาคตะวันออก','ระยอง':'ภาคตะวันออก','จันทบุรี':'ภาคตะวันออก','ตราด':'ภาคตะวันออก',
    'ฉะเชิงเทรา':'ภาคตะวันออก','ปราจีนบุรี':'ภาคตะวันออก','สระแก้ว':'ภาคตะวันออก',
    'กาญจนบุรี':'ภาคตะวันตก','ตาก':'ภาคตะวันตก','ราชบุรี':'ภาคตะวันตก','เพชรบุรี':'ภาคตะวันตก','ประจวบคีรีขันธ์':'ภาคตะวันตก',
    'เชียงใหม่':'ภาคเหนือ','เชียงราย':'ภาคเหนือ','ลำปาง':'ภาคเหนือ','ลำพูน':'ภาคเหนือ','พะเยา':'ภาคเหนือ','แพร่':'ภาคเหนือ',
    'น่าน':'ภาคเหนือ','แม่ฮ่องสอน':'ภาคเหนือ','อุตรดิตถ์':'ภาคเหนือ','สุโขทัย':'ภาคเหนือ','พิษณุโลก':'ภาคเหนือ',
    'พิจิตร':'ภาคเหนือ','กำแพงเพชร':'ภาคเหนือ','เพชรบูรณ์':'ภาคเหนือ','นครสวรรค์':'ภาคเหนือ','อุทัยธานี':'ภาคเหนือ',
    'เลย':'ภาคอีสาน','หนองคาย':'ภาคอีสาน','บึงกาฬ':'ภาคอีสาน','หนองบัวลำภู':'ภาคอีสาน','อุดรธานี':'ภาคอีสาน',
    'สกลนคร':'ภาคอีสาน','นครพนม':'ภาคอีสาน','กาฬสินธุ์':'ภาคอีสาน','มุกดาหาร':'ภาคอีสาน','ขอนแก่น':'ภาคอีสาน',
    'ชัยภูมิ':'ภาคอีสาน','นครราชสีมา':'ภาคอีสาน','บุรีรัมย์':'ภาคอีสาน','สุรินทร์':'ภาคอีสาน','ศรีสะเกษ':'ภาคอีสาน',
    'อุบลราชธานี':'ภาคอีสาน','ยโสธร':'ภาคอีสาน','อำนาจเจริญ':'ภาคอีสาน','มหาสารคาม':'ภาคอีสาน','ร้อยเอ็ด':'ภาคอีสาน',
    'ชุมพร':'ภาคใต้','ระนอง':'ภาคใต้','สุราษฎร์ธานี':'ภาคใต้','พังงา':'ภาคใต้','ภูเก็ต':'ภาคใต้','กระบี่':'ภาคใต้',
    'ตรัง':'ภาคใต้','พัทลุง':'ภาคใต้','นครศรีธรรมราช':'ภาคใต้','สงขลา':'ภาคใต้','สตูล':'ภาคใต้','ปัตตานี':'ภาคใต้',
    'ยะลา':'ภาคใต้','นราธิวาส':'ภาคใต้',
}

# ---------------- Supabase ----------------
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error('❌ Missing SUPABASE_URL or SUPABASE_KEY.'); st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)
sb: Client = get_client()

# ---------------- Utilities ----------------
def hash_pw(pw: str) -> str: return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_pw(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception: return False

@st.cache_data(ttl=60, show_spinner=False)
def load_df(table: str) -> pd.DataFrame:
    try:
        return pd.DataFrame(sb.table(table).select('*').execute().data)
    except Exception:
        return pd.DataFrame()

def safe_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in df.columns if c in cols]

def rerun():
    try: st.rerun()
    except Exception: pass

def ensure_default_admin():
    try:
        rows = sb.table('admins').select('username').eq('username','telemed').execute().data
        if not rows:
            sb.table('admins').insert({
                'id':str(uuid.uuid4()),
                'username':'telemed',
                'password_hash':hash_pw('Telemed@DHI'),
                'role':'admin'
            }).execute()
    except Exception:
        pass
ensure_default_admin()

def get_master_names(table: str, fallback: List[str]) -> List[str]:
    try:
        df = pd.DataFrame(sb.table(table).select('name').order('name', desc=False).execute().data)
        lst = df['name'].dropna().tolist() if not df.empty and 'name' in df.columns else []
        return lst if lst else fallback
    except Exception:
        return fallback

def upsert_master(table: str, name: str):
    try:
        ex = sb.table(table).select('id').eq('name', name).limit(1).execute().data
        if ex: return
        sb.table(table).insert({'id':str(uuid.uuid4()), 'name': name}).execute()
    except Exception:
        st.warning(f'⚠️ ยังไม่มีตาราง {table} หรือเพิ่มไม่สำเร็จ')

def rename_master(table: str, old: str, new: str):
    try:
        sb.table(table).update({'name': new}).eq('name', old).execute()
    except Exception:
        st.warning(f'⚠️ เปลี่ยนชื่อใน {table} ไม่สำเร็จ')

def delete_master(table: str, name: str):
    try:
        sb.table(table).delete().eq('name', name).execute()
    except Exception:
        st.warning(f'⚠️ ลบใน {table} ไม่สำเร็จ')

def df_to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df2 = df.copy()
            for c in df2.columns:
                if pd.api.types.is_datetime64_any_dtype(df2[c]):
                    df2[c] = df2[c].dt.strftime("%Y-%m-%d")
            df2.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()

def plot(fig, key: str, config: dict | None = None):
    base = {'displaylogo': False, 'scrollZoom': True}
    if config: base.update(config)
    st.plotly_chart(fig, use_container_width=True, config=base, key=key)

# -------- PNG Builder (Server-side) --------
def build_dashboard_png(figs: dict, title: str, subtitle: str, dark: bool=False) -> bytes:
    """รวมกราฟหลายอันให้เป็นภาพ PNG เดียวแบบยาว"""
    images = []
    order = ['pie_sitecontrol','line_daily_trend',  # << แทรก daily trend ตรงนี้
             'pie_hospital_type','bar_hospital_type',
             'bar_hospital_overview']
    for k in order:
        fig = figs.get(k)
        if fig is not None:
            try:
                img_bytes = pio.to_image(fig, format="png", scale=2)  # ต้องมี kaleido
                images.append(Image.open(io.BytesIO(img_bytes)))
            except Exception:
                pass

    bg = (17,24,39) if dark else (248,250,252)
    title_color = (229,231,235) if dark else (17,24,39)
    sub_color   = (203,213,225) if dark else (55,65,81)

    if not images:
        im = Image.new("RGB", (1280, 320), bg)
        d = ImageDraw.Draw(im); f = ImageFont.load_default()
        d.text((40,40), title, fill=title_color, font=f)
        d.text((40,80), subtitle, fill=sub_color, font=f)
        buf = io.BytesIO(); im.save(buf, "PNG"); return buf.getvalue()

    pad, header = 40, 140
    width = max(i.width for i in images)
    height = header + sum(i.height for i in images) + pad*(len(images)+1)
    canvas = Image.new("RGB", (width+pad*2, height), bg)

    d = ImageDraw.Draw(canvas); f = ImageFont.load_default()
    d.text((pad, 16), title, fill=title_color, font=f)
    d.text((pad, 52), subtitle, fill=sub_color, font=f)

    y = header - 20
    for im in images:
        canvas.paste(im, (pad, y))
        y += im.height + pad

    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return buf.getvalue()

# ---------------- Theme/UI ----------------
if 'ui' not in st.session_state: st.session_state['ui']={'dark': False}
with st.sidebar:
    st.markdown('### 🎨 การแสดงผล')
    st.session_state.ui['dark'] = st.checkbox('โหมดมืด (Dark mode)', value=st.session_state.ui['dark'])
    st.caption(f"Version: **{APP_VERSION}**")

DARK = st.session_state.ui['dark']
PALETTE = PALETTE_DARK if DARK else PALETTE_PASTEL
px.defaults.template = 'plotly_dark' if DARK else 'plotly_white'
px.defaults.color_discrete_sequence = PALETTE

CARD_BG = "#0b1220" if DARK else "#FFFFFF"
CARD_BORDER = "#1f2937" if DARK else "#E5E7EB"
CARD_TXT = "#E5E7EB" if DARK else "#334155"

# ปรับ padding บนสุดให้เตี้ยลง
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  .stApp {{ font-family:'Kanit',system-ui; }}
  .main .block-container {{ padding-top: 0.6rem; padding-bottom: 2rem; }}
  .kpi-card {{
    background:{CARD_BG}; border:1px solid {CARD_BORDER}; color:{CARD_TXT};
    border-radius:16px; padding:1rem 1.2rem; box-shadow:0 6px 18px rgba(0,0,0,.08);
  }}
  .kpi-title {{ font-weight:600; opacity:.85; }}
  .kpi-value {{ font-size:1.8rem; font-weight:700; margin-top:.25rem; }}
  .filter-wrap .stMultiSelect, .filter-wrap .stDateInput {{ margin-bottom:.25rem; }}
</style>
""", unsafe_allow_html=True)

def apply_ui_patches():
    st.components.v1.html("""
    <script>
      setTimeout(()=>{
        const hideTexts = ['keyboard_double_arrow_right','keboard','keyboard'];
        document.querySelectorAll('button,div,span,label').forEach(el=>{
          const t=(el.innerText||'').trim();
          if(hideTexts.includes(t)){ el.style.display='none'; }
        });
      }, 0);
    </script>
    """, height=0)

# ---------------- Auth ----------------
if 'auth' not in st.session_state: st.session_state['auth']={'ok':False,'user':None,'role':'viewer'}
with st.sidebar:
    st.markdown('## 🔐 Admin')
    if not st.session_state.auth['ok']:
        with st.form('login'):
            u = st.text_input('Username'); p = st.text_input('Password', type='password')
            rows = load_df('admins')
            if st.form_submit_button('Login'):
                row = rows[rows['username']==u] if 'username' in rows.columns else pd.DataFrame()
                if not row.empty and verify_pw(p, row.iloc[0]['password_hash']):
                    role = row.iloc[0]['role'] if 'role' in row.columns and pd.notna(row.iloc[0]['role']) else 'admin'
                    st.session_state.auth={'ok':True,'user':u,'role':role}; rerun()
                else:
                    st.error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        st.write(f"✅ {st.session_state.auth['user']}  ·  role: **{st.session_state.auth['role']}**")
        if st.button('Logout'): st.session_state.auth={'ok':False,'user':None,'role':'viewer'}; rerun()

# ---------------- Router ----------------
page = st.query_params.get('page','dashboard')
with st.sidebar:
    choices = ['dashboard','admin']
    if page not in choices: page = 'dashboard'
    nav = st.radio('ไปที่', choices, index=choices.index(page), horizontal=True)
    if nav != page:
        st.query_params.update({'page':nav}); rerun()

# container สำหรับปุ่มดาวน์โหลด/ส่งออกใน Sidebar (จะเติมตอน render เสร็จ)
with st.sidebar:
    sidebar_dl_container = st.container()

# ---------------- Thai date ----------------
TH_MONTHS = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
def th_date(d: date) -> str:
    return f"{d.day} {TH_MONTHS[d.month-1]} {d.year+543}"

# ---------- Dropdown-style multiselect ----------
def multiselect_dropdown(label: str, options: list, state_key: str, default_all: bool = True):
    options = options or []
    current = st.session_state.get(state_key, options[:] if default_all else [])
    current = [x for x in current if x in options]
    st.session_state[state_key] = current

    use_pop = hasattr(st, "popover")
    container = st.popover(label) if use_pop else st.expander(label, expanded=False)
    with container:
        sel = st.multiselect(" ", options=options, default=current,
                             label_visibility="collapsed", placeholder="พิมพ์เพื่อค้นหา...")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("เลือกทั้งหมด", key=f"{state_key}_all_btn"):
                st.session_state[state_key] = options[:]; rerun()
        with c2:
            if st.button("ล้างทั้งหมด", key=f"{state_key}_clear_btn"):
                st.session_state[state_key] = []; rerun()
        with c3:
            if st.button("เสร็จสิ้น ✅", key=f"{state_key}_done_btn"):
                st.session_state[state_key] = sel or []; rerun()

    if sel is not None and sel != st.session_state[state_key]:
        st.session_state[state_key] = sel
    return st.session_state[state_key]

# ====================== DASHBOARD ======================
def render_chart_placeholder(title:str, key:str):
    fig = go.Figure()
    fig.add_annotation(text="ไม่มีข้อมูล", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    fig.update_layout(height=360, margin=dict(l=0,r=0,t=10,b=10))
    st.markdown(title)
    plot(fig, key=key)

def render_dashboard():
    apply_ui_patches()
    st.markdown("# DashBoard Telemedicine")

    hospitals_df = load_df('hospitals')
    tx_df = load_df('transactions')

    figs: Dict[str, go.Figure] = {}  # เก็บกราฟไว้สำหรับทำ PNG
    export_payload = {}               # เก็บข้อมูลส่งออก CSV/Excel

    # ---------- Filters ----------
    st.markdown("### 🎛️ ตัวกรอง")
    if 'date_range' not in st.session_state:
        today = date.today()
        st.session_state['date_range'] = (today, today)

    with st.container():
        st.markdown("<div class='filter-wrap'>", unsafe_allow_html=True)
        c_row1_left, c_row1_mid, c_row1_right = st.columns([1.6, 1.4, 1.2])
        with c_row1_left:
            today = date.today()
            # แสดงเป็น วัน/เดือน/ปี
            dr = st.date_input('📅 ช่วงวันที่', value=st.session_state['date_range'],
                               format="DD/MM/YYYY")
            if isinstance(dr, tuple) and len(dr)==2:
                st.session_state['date_range'] = dr
        with c_row1_mid:
            colA, colB = st.columns(2)
            with colA:
                if st.button('Today'):
                    st.session_state['date_range'] = (today, today); rerun()
            with colB:
                if st.button('เดือนนี้'):
                    first = today.replace(day=1)
                    st.session_state['date_range'] = (first, today); rerun()
        with c_row1_right:
            if st.button('↺ Reset ตัวกรอง'):
                st.session_state['date_range'] = (today, today)
                for k in ['hosp_sel','site_filter','region_filter','type_filter']:
                    st.session_state[k] = []
                rerun()

        c_row2_a, c_row2_b, c_row2_c, c_row2_d = st.columns([1.4,1.1,1.1,1.2])
        with c_row2_a:
            all_names = sorted(hospitals_df['name'].dropna().unique().tolist()) if 'name' in hospitals_df.columns else []
            selected_hospitals = multiselect_dropdown("🏥 โรงพยาบาล", all_names, "hosp_sel", default_all=True)
        with c_row2_b:
            selected_sites = multiselect_dropdown("🧭 ทีมภูมิภาค", SITE_CONTROL_CHOICES, "site_filter", default_all=True)
        with c_row2_c:
            regions = sorted(hospitals_df['region'].dropna().unique().tolist()) if 'region' in hospitals_df.columns else []
            selected_regions = multiselect_dropdown("🗺️ ภูมิภาค", regions, "region_filter", default_all=True)
        with c_row2_d:
            types = sorted(hospitals_df['hospital_type'].dropna().unique().tolist()) if 'hospital_type' in hospitals_df.columns \
                    else get_master_names('hospital_types', DEFAULT_HOSPITAL_TYPES)
            selected_types = multiselect_dropdown("🏷️ ประเภทโรงพยาบาล", types, "type_filter", default_all=True)
        st.markdown("</div>", unsafe_allow_html=True)

    start_date, end_date = st.session_state['date_range']

    # ---- Merge & filter ----
    if not tx_df.empty:
        tx_df['date'] = pd.to_datetime(tx_df['date']).dt.date
        tx_df = tx_df[(tx_df['date']>=start_date)&(tx_df['date']<=end_date)]
    if not tx_df.empty and not hospitals_df.empty:
        df = tx_df.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left', suffixes=('','_h'))
    else:
        df = pd.DataFrame(columns=['date','hospital_id','transactions_count','riders_active',
                                   'name','site_control','region','riders_count','hospital_type'])

    if st.session_state.get('site_filter') and 'site_control' in df.columns:
        df = df[df['site_control'].isin(st.session_state['site_filter'])]
    if st.session_state.get('hosp_sel') and 'name' in df.columns:
        df = df[df['name'].isin(st.session_state['hosp_sel'])]
    if st.session_state.get('region_filter') and 'region' in df.columns:
        df = df[df['region'].isin(st.session_state['region_filter'])]
    if st.session_state.get('type_filter') and 'hospital_type' in df.columns:
        df = df[df['hospital_type'].isin(st.session_state['type_filter'])]

    # ---- KPI cards ----
    st.markdown("### 📈 ภาพรวม")
    k1,k2,k3,k4,k5 = st.columns(5)
    total_tx = int(df['transactions_count'].sum()) if not df.empty else 0
    uniq_h   = df['hospital_id'].nunique() if not df.empty else 0
    riders_cap = int(df['riders_count'].fillna(0).sum()) if not df.empty else 0
    avg_day  = int(df.groupby('date')['transactions_count'].sum().mean()) if not df.empty else 0
    riders_active = int(df['riders_active'].sum()) if not df.empty else 0
    for col, title, val in [
        (k1,'Transaction รวม', f"{total_tx:,}"),
        (k2,'โรงพยาบาลทั้งหมด', f"{uniq_h}"),
        (k3,'จำนวนไรเดอร์รวม', f"{riders_cap:,}"),
        (k4,'เฉลี่ยต่อวัน', f"{avg_day:,}"),
        (k5,'ไรเดอร์ Active', f"{riders_active:,}")
    ]:
        col.markdown(f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{val}</div></div>", unsafe_allow_html=True)

    # ---- Pie by SiteControl ----
    st.markdown('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')
    if not df.empty and df['site_control'].notna().any():
        gsite = df.groupby('site_control').agg({'transactions_count':'sum'}).reset_index().sort_values('transactions_count', ascending=False)
        if not gsite.empty:
            pie = px.pie(gsite, names='site_control', values='transactions_count',
                         color='site_control', color_discrete_sequence=PALETTE, hole=0.55)
            pie.update_traces(textposition='outside',
                              texttemplate='<b>%{label}</b><br>%{value:,} (%{percent:.1%})',
                              marker=dict(line=dict(color=('#fff' if not DARK else '#111'), width=2)),
                              pull=[0.02]*len(gsite))
            pie.update_layout(annotations=[dict(text=f"{total_tx:,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=18))])
            plot(pie, key="pie_sitecontrol")
            figs['pie_sitecontrol'] = pie
        else:
            render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)', key="ph_site_pie")
    else:
        render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)', key="ph_site_pie")

    # ---- Daily Trend (ย้ายมาอยู่ตรงนี้) ----
    st.markdown('#### แนวโน้มรายวัน')
    if not df.empty:
        daily = df.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index().sort_values('date')
        if not daily.empty:
            TH = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
            labels = daily['date'].apply(lambda d: f"{TH[pd.to_datetime(d).dayofweek]} {pd.to_datetime(d).day}/{pd.to_datetime(d).month}/{str(pd.to_datetime(d).year)[-2:]}")
            ln = go.Figure()
            ln.add_trace(go.Scatter(
                x=labels, y=daily['transactions_count'],
                mode='lines+markers+text',
                name='Transactions',
                text=daily['transactions_count'],
                textposition='top center',
                line=dict(width=3),
                line_shape='spline'
            ))
            ln.add_trace(go.Scatter(
                x=labels, y=daily['riders_active'],
                mode='lines+markers',
                name='Rider Active',
                visible='legendonly',
                line=dict(width=2, dash='dot'),
                line_shape='spline'
            ))
            ln.update_layout(xaxis_title='วัน/เดือน/ปี', yaxis_title='จำนวน',
                             xaxis_tickangle=-40, margin=dict(t=30,r=20,b=80,l=60))
            plot(ln, key="line_daily_trend")
            figs['line_daily_trend'] = ln
        else:
            render_chart_placeholder('#### แนวโน้มรายวัน', key="ph_daily_trend")
    else:
        render_chart_placeholder('#### แนวโน้มรายวัน', key="ph_daily_trend")

    # ---- By Hospital Type (summary) ----
    st.markdown('### 🏷️ ประเภทโรงพยาบาล (สรุป)')
    if not df.empty and 'hospital_type' in df.columns and df['hospital_type'].notna().any():
        gtype_sum = df.groupby('hospital_type', dropna=True).agg(
            transactions_count=('transactions_count','sum'),
            riders_active=('riders_active','sum'),
            riders_total=('riders_count','sum'),
            hospitals_count=('hospital_id','nunique')
        ).reset_index()
        gtype_sum['avg_tx_per_hosp'] = gtype_sum['transactions_count'] / gtype_sum['hospitals_count']
        gtype_sum = gtype_sum.sort_values('transactions_count', ascending=False)

        ui1, ui2, _ = st.columns([1.3, 1.1, 2.6])
        with ui1:
            sort_metric = st.selectbox('เรียงกราฟตาม', ['จำนวน Transaction','จำนวนโรงพยาบาล'], index=0, key='sort_metric_type')
        with ui2:
            sort_dir = st.selectbox('ทิศทาง', ['มาก→น้อย','น้อย→มาก'], index=0, key='sort_dir_type')

        if sort_metric == 'จำนวนโรงพยาบาล':
            gtype_for_bar = gtype_sum.sort_values('hospitals_count', ascending=(sort_dir=='น้อย→มาก'))
        else:
            gtype_for_bar = gtype_sum.sort_values('transactions_count', ascending=(sort_dir=='น้อย→มาก'))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('#### สัดส่วนตามประเภทโรงพยาบาล (กราฟวงกลม)')
            pie_t = px.pie(gtype_sum, names='hospital_type', values='transactions_count',
                           color='hospital_type', color_discrete_sequence=PALETTE, hole=0.55)
            pie_t.update_traces(textposition='outside',
                                texttemplate='<b>%{label}</b><br>%{value:,} (%{percent:.1%})',
                                marker=dict(line=dict(color=('#fff' if not DARK else '#111'), width=2)),
                                pull=[0.02]*len(gtype_sum))
            pie_t.update_layout(annotations=[dict(text=f"{int(gtype_sum.transactions_count.sum()):,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=16))])
            plot(pie_t, key="pie_hospital_type")
            figs['pie_hospital_type'] = pie_t

        with c2:
            st.markdown('#### ภาพรวมตามประเภทโรงพยาบาล')
            bar_t = px.bar(
                gtype_for_bar, y='hospital_type', x='transactions_count', orientation='h',
                text='transactions_count',
                color='hospital_type', color_discrete_sequence=PALETTE
            )
            bar_t.update_traces(textposition='outside')
            bar_t.update_layout(showlegend=False, margin=dict(l=160,r=40,t=30,b=30),
                                yaxis_title='ประเภท', xaxis_title='Transactions',
                                height=max(420, 50*len(gtype_for_bar)+180))
            plot(bar_t, key="bar_hospital_type")
            figs['bar_hospital_type'] = bar_t
    else:
        render_chart_placeholder('#### สัดส่วน/ภาพรวมตามประเภทโรงพยาบาล', key="ph_type_summary")

    # ---- Hospital Overview ----
    st.markdown('#### ภาพรวมต่อโรงพยาบาล')
    if not df.empty:
        gh = df.groupby('name').agg({'transactions_count':'sum'}).reset_index()
        cs1, cs2, _ = st.columns([1.3, 1.2, 3])
        with cs1:
            sort_by = st.selectbox('เรียงตาม', ['ยอด Transaction','ชื่อโรงพยาบาล'], index=0)
        with cs2:
            if sort_by == 'ยอด Transaction':
                order = st.selectbox('ทิศทาง', ['มาก→น้อย','น้อย→มาก'], index=0)
                gh = gh.sort_values('transactions_count', ascending=(order=='น้อย→มาก'))
            else:
                order = st.selectbox('ทิศทาง', ['ก→ฮ','ฮ→ก'], index=0)
                gh = gh.sort_values('name', ascending=(order=='ก→ฮ'))

        gh = gh.reset_index(drop=True)
        bar = px.bar(gh, y='name', x='transactions_count', orientation='h', text='transactions_count',
                     color='name', color_discrete_sequence=PALETTE)
        bar.update_traces(textposition='outside')
        bar.update_layout(
            showlegend=False,
            height=max(520, 30*len(gh)+200),
            margin=dict(l=160,r=40,t=30,b=40),
            yaxis_title='ชื่อโรงพยาบาล',
            xaxis_title='Transactions'
        )
        plot(bar, key="bar_hospital_overview")
        figs['bar_hospital_overview'] = bar
    else:
        render_chart_placeholder('#### ภาพรวมต่อโรงพยาบาล', key="ph_hospital_overview")

    # ---- Table by site ----
    st.markdown('#### ตารางจำนวน Transaction แยกตามทีมภูมิภาค')
    if not df.empty:
        site_tbl = df.groupby('site_control').agg(
            Transactions=('transactions_count','sum'),
            Rider_Active=('riders_active','sum'),
            Riders_Total=('riders_count','sum')
        ).reset_index().rename(columns={'site_control':'ทีมภูมิภาค'})
        if not site_tbl.empty:
            show_df = site_tbl.copy()
            show_df['Transactions']  = show_df['Transactions'].map('{:,}'.format)
            show_df['Rider_Active']  = show_df['Rider_Active'].map('{:,}'.format)
            show_df['Riders_Total']  = show_df['Riders_Total'].map('{:,}'.format)

            header_fill = '#111827' if DARK else '#E6EFFF'
            header_font = '#E5E7EB' if DARK else '#1F2937'
            header_line = '#374151' if DARK else '#BFD2FF'
            rgba = [
                'rgba(167,199,231,0.15)','rgba(248,200,220,0.15)','rgba(182,226,211,0.15)',
                'rgba(253,226,179,0.15)','rgba(234,215,247,0.15)','rgba(205,229,240,0.15)'
            ]
            row_colors = [rgba[i % len(rgba)] for i in range(len(show_df))]
            fill_matrix = [row_colors]*len(show_df.columns)

            figt = go.Figure(data=[go.Table(
                header=dict(
                    values=[f"<b>{c}</b>" for c in show_df.columns],
                    fill_color=header_fill,
                    font=dict(color=header_font, size=13),
                    align='left', height=34,
                    line_color=header_line, line_width=1.2
                ),
                cells=dict(
                    values=[show_df[c] for c in show_df.columns],
                    fill_color=fill_matrix,
                    align='left', height=28
                )
            )])
            figt.update_layout(margin=dict(l=0,r=0,t=0,b=0))
            plot(figt, key="tbl_site_summary")
        else:
            st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')
    else:
        st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')

    # ===== เตรียมข้อมูลดาวน์โหลด/ส่งออกสำหรับ Sidebar =====
    subtitle = (
        f"ช่วง {th_date(start_date)} – {th_date(end_date)}  |  "
        f"โรงพยาบาล: "
        f"{'ทั้งหมด' if not selected_hospitals or len(selected_hospitals)==len(all_names) else ', '.join(selected_hospitals)}  |  "
        f"ทีม: {'ทั้งหมด' if not selected_sites or len(selected_sites)==len(SITE_CONTROL_CHOICES) else ', '.join(selected_sites)}"
    )
    png_bytes = build_dashboard_png(figs, "DashBoard Telemedicine", subtitle, dark=DARK)

    # เตรียม CSV/Excel export
    if not df.empty:
        df_csv = df.copy()
        df_csv['date'] = pd.to_datetime(df_csv['date'])
        gh = df.groupby('name').agg({'transactions_count':'sum'}).reset_index()
        gsite = df.groupby('site_control').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
        daily = df.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
        excel_bytes = df_to_excel_bytes({"filtered": df_csv, "by_hospital": gh, "by_site": gsite, "daily": daily})
    else:
        df_csv = pd.DataFrame()
        excel_bytes = b""

    # เก็บไว้ใน session เพื่อไปวาดปุ่มใน Sidebar
    st.session_state['downloads'] = {
        'png_bytes': png_bytes,
        'csv_bytes': (df_csv.to_csv(index=False).encode('utf-8-sig') if not df_csv.empty else b""),
        'excel_bytes': excel_bytes
    }

# ====================== ADMIN (เหมือนเดิม ย่อจากเวอร์ชันก่อน) ======================
def render_admin():
    apply_ui_patches()
    if not st.session_state.auth['ok']:
        st.warning('กรุณาเข้าสู่ระบบทาง Sidebar ก่อน'); return

    st.markdown("# DashBoard Telemedicine")
    st.markdown("## 🛠️ หน้าการจัดการ (Admin)")
    tabs = st.tabs(['จัดการโรงพยาบาล','จัดการ Transaction','ข้อมูลหลัก','จัดการผู้ดูแล','รายงาน','ตั้งค่า & ข้อมูลตัวอย่าง'])

    role = st.session_state.auth.get('role','admin')
    can_edit = role in ('admin','editor')

    # ... (โค้ดส่วน Admin ทั้งหมดเหมือนเวอร์ชัน 4.6.0 ก่อนหน้า - ไม่ตัดทอนในที่นี้เพื่อความครบถ้วน)
    # เพื่อความกระชับในคำตอบนี้: โปรดนำ "ส่วน Admin" จากเวอร์ชันก่อนหน้ามาวางแทนบล็อกนี้แบบ 1:1
    # หากต้องการ ผมส่งไฟล์เต็มทั้งก้อนพร้อมบล็อก Admin แบบขยายได้อีกครั้ง

    st.info("⚠️ ในคำตอบนี้ย่อส่วน Admin เพื่อไม่ให้ข้อความเกินจำกัด — ใช้บล็อก Admin เดิมจาก v4.6.0 ได้เลย (ไม่กระทบฟังก์ชัน Sidebar ใหม่)")

# ---------------- Render main page ----------------
if st.query_params.get('page','dashboard') == 'admin':
    render_admin()
else:
    render_dashboard()

# ---------------- Sidebar: ปุ่มดาวน์โหลด/ส่งออก ----------------
with sidebar_dl_container:
    st.markdown("## ⬇️ บันทึก/ส่งออก")
    dls = st.session_state.get('downloads', {})
    if dls.get('png_bytes'):
        st.download_button("📸 ดาวน์โหลดภาพ PNG", data=dls['png_bytes'],
                           file_name=f"telemed_dashboard_{date.today().isoformat()}.png", mime="image/png",
                           use_container_width=True)
    if dls.get('csv_bytes'):
        st.download_button("CSV (ข้อมูลที่กรองแล้ว)", data=dls['csv_bytes'],
                           file_name=f"telemed_filtered_{date.today().isoformat()}.csv", mime="text/csv",
                           use_container_width=True)
    if dls.get('excel_bytes'):
        st.download_button("Excel (หลายชีต)", data=dls['excel_bytes'],
                           file_name=f"telemed_export_{date.today().isoformat()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
