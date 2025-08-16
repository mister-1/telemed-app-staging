# DashBoard Telemedicine — v4.9.3 (Full)
# - Daily trend: โค้ง (spline) + แสดงตัวเลขทุกเส้น (รวมเส้นย้อนหลัง)
# - ฟิลเตอร์: ซ่อนข้อความ keyboard_* ที่โผล่มาทับ expander/popover อย่างครอบคลุม
# - KPI ใหม่: "Transaction สะสม (เดือนนี้ถึงวันที่เลือก)" ใช้ตัวกรองทั้งหมด (ยกเว้นวันตามสูตร)
# - โหมดมืด/พาสเทล, Sidebar export PNG/CSV/Excel, หน้า Admin ครบ
#
# requirements.txt (แนะนำ):
# streamlit==1.48.1
# supabase==2.5.1
# pandas==2.2.2
# plotly==5.23.0
# kaleido==0.2.1
# Pillow==10.3.0
# bcrypt==4.2.0
# openpyxl==3.1.3
# requests==2.32.3

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

APP_VERSION = "v4.9.3"

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

@st.cache_data(ttl=60, show_spinner=False)
def load_df(table: str) -> pd.DataFrame:
    try:
        return pd.DataFrame(sb.table(table).select('*').execute().data)
    except Exception:
        return pd.DataFrame()

def safe_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in cols if c in df.columns]

def rerun():
    try: st.rerun()
    except Exception: pass

def ensure_default_admin():
    try:
        rows = sb.table('admins').select('username').eq('username','telemed').execute().data
        if not rows:
            from bcrypt import gensalt, hashpw
            sb.table('admins').insert({
                'id':str(uuid.uuid4()),
                'username':'telemed',
                'password_hash':hashpw('Telemed@DHI'.encode(), gensalt()).decode(),
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
    images = []
    order = ['pie_sitecontrol','line_daily_trend','pie_hospital_type','bar_hospital_type','bar_hospital_overview']
    for k in order:
        fig = figs.get(k)
        if fig is not None:
            try:
                img_bytes = pio.to_image(fig, format="png", scale=2)  # need kaleido
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

# ---- CSS ----
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  :root {{
    --card-bg: {CARD_BG};
    --card-border: {CARD_BORDER};
    --card-text: {CARD_TXT};
  }}
  .stApp {{ font-family:'Kanit',system-ui; }}
  .main .block-container {{ padding-top: .25rem; padding-bottom: 1.6rem; }}
  h1 {{ margin: .25rem 0 .75rem 0 !important; line-height: 1.2; }}

  .kpi-card {{
    background:var(--card-bg); border:1px solid var(--card-border); color:var(--card-text);
    border-radius:16px; padding:1rem 1.2rem; box-shadow:0 6px 18px rgba(0,0,0,.08);
  }}
  .kpi-title {{ font-weight:600; opacity:.85; }}
  .kpi-value {{ font-size:1.8rem; font-weight:700; margin-top:.25rem; }}

  .filter-sticky {{ position: sticky; top: .25rem; z-index: 5; }}
  .filter-card {{
    background:var(--card-bg); border:1px solid var(--card-border); color:var(--card-text);
    border-radius:16px; padding:14px; box-shadow:0 8px 22px rgba(0,0,0,.06);
  }}
  .filter-card .stButton>button {{
    width:100%; height:46px; border-radius:12px; font-weight:600;
  }}
  .filter-grid-row1 {{
    display:grid; grid-template-columns: 1.4fr .45fr .45fr .6fr; gap:.75rem;
  }}
  .filter-grid-row2 {{
    display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:.75rem; margin-top:.6rem;
  }}
  .stExpander > div[role='button'] {{
    background:var(--card-bg); border:1px solid var(--card-border);
    border-radius:14px; padding:10px 14px;
  }}
  .stExpander .streamlit-expanderContent {{
    background:var(--card-bg); border:1px solid var(--card-border);
    border-top:none; border-radius:0 0 14px 14px; padding-top:12px;
  }}
</style>
""", unsafe_allow_html=True)

# CSS ล้าง text-input ผี + กัน margin
st.markdown("""
<style>
  #filter-card input[type="text"],
  #filter-card textarea,
  #filter-card .stTextInput,
  #filter-card div[data-baseweb="input"] {
    display:none !important;
    height:0 !important; margin:0 !important; padding:0 !important; border:0 !important;
    opacity:0 !important; overflow:hidden !important;
  }
  #filter-card [data-testid="stDateInput"] { margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

def apply_ui_patches():
    # JS ซ่อน keyboard_* และ input ผี (แบบครอบคลุมกว่าเดิม)
    st.components.v1.html("""
    <script>
      function wipeGhosts(){
        const root = document.querySelector('#filter-card');
        if(root){
          root.querySelectorAll('input[type="text"]').forEach(inp=>{
            const hasLabel = !!(inp.getAttribute('aria-label')||'').trim();
            const w = inp.getBoundingClientRect().width;
            if(!hasLabel && w > 280){
              const host = inp.closest('div');
              if(host){ host.style.display='none'; host.style.height='0px'; }
              inp.style.display='none';
            }
          });
        }
        // ซ่อนทุก element ที่มีข้อความขึ้นต้น/ประกอบด้วย 'keyboard'
        const scan = (el)=>((el.innerText||'').toLowerCase().includes('keyboard'));
        document.querySelectorAll('*').forEach(el=>{
          try{
            const ar = (el.getAttribute('aria-label')||'').toLowerCase();
            if(scan(el) || ar.includes('keyboard')){
              // อย่าซ่อนปุ่มหลักๆ: ถ้าเป็นปุ่ม expander ทั้งก้อน ไม่ซ่อน
              const role = el.getAttribute('role')||'';
              if(role==='button' && el.closest('.stExpander')) return;
              el.style.display='none';
            }
          }catch(e){}
        });
      }
      wipeGhosts();
      const obs = new MutationObserver(wipeGhosts);
      obs.observe(document.body, {subtree:true, childList:true});
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
                if not row.empty and (p and bcrypt.checkpw(p.encode(), row.iloc[0]['password_hash'].encode())):
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

# container ปุ่มดาวน์โหลด/ส่งออกใน Sidebar
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

# ---------- Daily trend backfill (with labels on all lines) ----------
def render_daily_trend_with_backfill(df_selected: pd.DataFrame,
                                     df_all_no_date: pd.DataFrame,
                                     start_date: date, end_date: date,
                                     dark: bool) -> None:
    daily_sel = (df_selected.groupby('date')
                 .agg(transactions_count=('transactions_count','sum'),
                      riders_active=('riders_active','sum'))
                 .reset_index()
                 .sort_values('date'))

    back_days = 0
    if (end_date - start_date).days <= 2:
        opt = st.selectbox(
            'เติมข้อมูลย้อนหลังสำหรับกราฟ',
            ['ไม่เติม','ย้อนหลัง 7 วัน','ย้อนหลัง 14 วัน','ย้อนหลัง 30 วัน'],
            index=1
        )
        back_days = {'ไม่เติม':0,'ย้อนหลัง 7 วัน':7,'ย้อนหลัง 14 วัน':14,'ย้อนหลัง 30 วัน':30}[opt]

    daily_back = pd.DataFrame(columns=['date','transactions_count','riders_active'])
    if back_days > 0 and not df_all_no_date.empty:
        start_ext = start_date - timedelta(days=back_days)
        mask = (df_all_no_date['date'] >= start_ext) & (df_all_no_date['date'] < start_date)
        daily_back = (df_all_no_date.loc[mask]
                      .groupby('date')
                      .agg(transactions_count=('transactions_count','sum'),
                           riders_active=('riders_active','sum'))
                      .reset_index()
                      .sort_values('date'))

    if daily_sel.empty and daily_back.empty:
        fig = go.Figure()
        fig.add_annotation(text="ไม่มีข้อมูล", x=0.5, y=0.5, showarrow=False)
        fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
        fig.update_layout(height=360, margin=dict(l=0,r=0,t=10,b=10))
        st.markdown('#### แนวโน้มรายวัน')
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})
        return

    def thai_label(d):
        THW = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
        dt = pd.to_datetime(d)
        return f"{THW[dt.dayofweek]} {dt.day}/{dt.month}/{str(dt.year)[-2:]}"

    fig = go.Figure()

    # Backfill lines (dotted + labels)
    if not daily_back.empty:
        fig.add_trace(go.Scatter(
            x=daily_back['date'].apply(thai_label),
            y=daily_back['transactions_count'],
            mode='lines+markers+text',
            name='ย้อนหลัง (Transactions)',
            text=daily_back['transactions_count'],
            textposition='top center',
            textfont=dict(size=10),
            line=dict(width=2, dash='dot'),
            line_shape='spline',
            opacity=0.85
        ))
        fig.add_trace(go.Scatter(
            x=daily_back['date'].apply(thai_label),
            y=daily_back['riders_active'],
            mode='lines+markers+text',
            name='ย้อนหลัง (Rider Active)',
            text=daily_back['riders_active'],
            textposition='top center',
            textfont=dict(size=10),
            line=dict(width=1.5, dash='dot'),
            line_shape='spline',
            opacity=0.7,
            visible='legendonly'  # ยังซ่อนไว้เป็นค่าเริ่มต้น แต่มี label พร้อม
        ))

    # Selected-range lines (main + labels)
    if not daily_sel.empty:
        fig.add_trace(go.Scatter(
            x=daily_sel['date'].apply(thai_label),
            y=daily_sel['transactions_count'],
            mode='lines+markers+text',
            name='Transactions',
            text=daily_sel['transactions_count'],
            textposition='top center',
            line=dict(width=3),
            line_shape='spline'
        ))
        fig.add_trace(go.Scatter(
            x=daily_sel['date'].apply(thai_label),
            y=daily_sel['riders_active'],
            mode='lines+markers+text',
            name='Rider Active',
            text=daily_sel['riders_active'],
            textposition='top center',
            line=dict(width=2, dash='dot'),
            line_shape='spline',
            visible='legendonly'  # ซ่อนเส้นรองไว้ก่อน
        ))

    fig.update_layout(
        xaxis_title='วัน/เดือน/ปี', yaxis_title='จำนวน',
        xaxis_tickangle=-40,
        margin=dict(t=30, r=20, b=80, l=60)
    )
    st.markdown('#### แนวโน้มรายวัน')
    st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})
    st.session_state.setdefault('figs', {})['line_daily_trend'] = fig

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
    tx_all = load_df('transactions')
    figs: Dict[str, go.Figure] = {}
    st.session_state['figs'] = figs

    # ---------- Filters ----------
    st.markdown("### 🎛️ ตัวกรอง")
    if 'date_range' not in st.session_state:
        today = date.today()
        st.session_state['date_range'] = (today, today)

    st.markdown("<div class='filter-sticky'>", unsafe_allow_html=True)
    with st.expander("🧩 ตัวกรองข้อมูล (คลิกเพื่อย่อ/ขยาย)", expanded=True):
        st.markdown("<div id='filter-card' class='filter-card'>", unsafe_allow_html=True)

        st.markdown("<div class='filter-grid-row1'>", unsafe_allow_html=True)
        col_d, col_tdy, col_mth, col_rst = st.columns([1.4, .45, .45, .6])
        with col_d:
            today = date.today()
            dr = st.date_input('📅 ช่วงวันที่',
                               value=st.session_state['date_range'],
                               format="DD/MM/YYYY",
                               key='filter_date_range')
            if isinstance(dr, tuple) and len(dr)==2:
                st.session_state['date_range'] = dr
        with col_tdy:
            if st.button('Today'):
                st.session_state['date_range'] = (today, today); rerun()
        with col_mth:
            if st.button('เดือนนี้'):
                first = today.replace(day=1)
                st.session_state['date_range'] = (first, today); rerun()
        with col_rst:
            if st.button('↺ Reset ตัวกรอง'):
                st.session_state['date_range'] = (today, today)
                for k in ['hosp_sel','site_filter','region_filter','type_filter']:
                    st.session_state[k] = []
                rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='filter-grid-row2'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            all_names = sorted(hospitals_df['name'].dropna().unique().tolist()) if 'name' in hospitals_df.columns else []
            selected_hospitals = multiselect_dropdown("🏥 โรงพยาบาล", all_names, "hosp_sel", default_all=True)
        with c2:
            selected_sites = multiselect_dropdown("🧭 ทีมภูมิภาค", SITE_CONTROL_CHOICES, "site_filter", default_all=True)
        with c3:
            regions = sorted(hospitals_df['region'].dropna().unique().tolist()) if 'region' in hospitals_df.columns else []
            selected_regions = multiselect_dropdown("🗺️ ภูมิภาค", regions, "region_filter", default_all=True)
        with c4:
            types = sorted(hospitals_df['hospital_type'].dropna().unique().tolist()) \
                    if 'hospital_type' in hospitals_df.columns \
                    else get_master_names('hospital_types', DEFAULT_HOSPITAL_TYPES)
            selected_types = multiselect_dropdown("🏷️ ประเภทโรงพยาบาล", types, "type_filter", default_all=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    start_date, end_date = st.session_state['date_range']

    # ---- Merge & filter (สองชุด) ----
    if not tx_all.empty:
        tx_all['date'] = pd.to_datetime(tx_all['date']).dt.date
        df_all_no_date = tx_all.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left', suffixes=('','_h'))
    else:
        df_all_no_date = pd.DataFrame(columns=['date','hospital_id','transactions_count','riders_active',
                                               'name','site_control','region','riders_count','hospital_type'])

    # non-date filters
    if st.session_state.get('site_filter') and 'site_control' in df_all_no_date.columns:
        df_all_no_date = df_all_no_date[df_all_no_date['site_control'].isin(st.session_state['site_filter'])]
    if st.session_state.get('hosp_sel') and 'name' in df_all_no_date.columns:
        df_all_no_date = df_all_no_date[df_all_no_date['name'].isin(st.session_state['hosp_sel'])]
    if st.session_state.get('region_filter') and 'region' in df_all_no_date.columns:
        df_all_no_date = df_all_no_date[df_all_no_date['region'].isin(st.session_state['region_filter'])]
    if st.session_state.get('type_filter') and 'hospital_type' in df_all_no_date.columns:
        df_all_no_date = df_all_no_date[df_all_no_date['hospital_type'].isin(st.session_state['type_filter'])]

    # date-filtered
    if not df_all_no_date.empty:
        df = df_all_no_date[(df_all_no_date['date'] >= start_date) & (df_all_no_date['date'] <= end_date)].copy()
    else:
        df = df_all_no_date.copy()

    # ---- KPI cards ----
    st.markdown("### 📈 ภาพรวม")
    # คำนวณเดือนนี้ถึงวันที่เลือก (อิง end_date)
    month_start = end_date.replace(day=1)
    df_month_to_end = df_all_no_date[(df_all_no_date['date'] >= month_start) & (df_all_no_date['date'] <= end_date)]
    month_accum = int(df_month_to_end['transactions_count'].sum()) if not df_month_to_end.empty else 0

    k1,k2,k3,k4,k5,k6 = st.columns(6)
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
        (k5,'ไรเดอร์ Active', f"{riders_active:,}"),
        (k6,'Transaction สะสม (เดือนนี้ถึงวันที่เลือก)', f"{month_accum:,}")
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
            pie.update_layout(annotations=[dict(text=f"{int(gsite['transactions_count'].sum()):,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=18))])
            st.plotly_chart(pie, use_container_width=True, config={'displaylogo': False})
            st.session_state['figs']['pie_sitecontrol'] = pie
        else:
            render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)', key="ph_site_pie")
    else:
        render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)', key="ph_site_pie")

    # ---- Daily Trend (with backfill & labels on all lines) ----
    render_daily_trend_with_backfill(df_selected=df,
                                     df_all_no_date=df_all_no_date,
                                     start_date=start_date,
                                     end_date=end_date,
                                     dark=DARK)

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
            st.plotly_chart(pie_t, use_container_width=True, config={'displaylogo': False})
            st.session_state['figs']['pie_hospital_type'] = pie_t

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
            st.plotly_chart(bar_t, use_container_width=True, config={'displaylogo': False})
            st.session_state['figs']['bar_hospital_type'] = bar_t
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
        st.plotly_chart(bar, use_container_width=True, config={'displaylogo': False})
        st.session_state['figs']['bar_hospital_overview'] = bar
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
            st.plotly_chart(figt, use_container_width=True, config={'displaylogo': False})
        else:
            st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')
    else:
        st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')

    # ===== Prepare downloads =====
    subtitle = (
        f"ช่วง {th_date(start_date)} – {th_date(end_date)}  |  "
        f"โรงพยาบาล: "
        f"{'ทั้งหมด' if not st.session_state.get('hosp_sel') else ', '.join(st.session_state['hosp_sel'])}  |  "
        f"ทีม: {'ทั้งหมด' if not st.session_state.get('site_filter') else ', '.join(st.session_state['site_filter'])}"
    )
    png_bytes = build_dashboard_png(st.session_state['figs'], "DashBoard Telemedicine", subtitle, dark=DARK)

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

    st.session_state['downloads'] = {
        'png_bytes': png_bytes,
        'csv_bytes': (df_csv.to_csv(index=False).encode('utf-8-sig') if not df_csv.empty else b""),
        'excel_bytes': excel_bytes
    }

# ====================== ADMIN (จัดการข้อมูล) ======================
def render_admin():
    apply_ui_patches()
    if not st.session_state.auth['ok']:
        st.warning('กรุณาเข้าสู่ระบบทาง Sidebar ก่อน'); return

    st.markdown("# DashBoard Telemedicine")
    st.markdown("## 🛠️ หน้าการจัดการ (Admin)")
    tabs = st.tabs(['จัดการโรงพยาบาล','จัดการ Transaction','ข้อมูลหลัก','จัดการผู้ดูแล','รายงาน','ตั้งค่า & ข้อมูลตัวอย่าง'])

    role = st.session_state.auth.get('role','admin')
    can_edit = role in ('admin','editor')

    # ---- Hospitals ----
    with tabs[0]:
        hospitals_df = load_df('hospitals')
        st.markdown('### โรงพยาบาล')

        type_choices = get_master_names('hospital_types', DEFAULT_HOSPITAL_TYPES)
        model_choices = get_master_names('service_models_master', DEFAULT_SERVICE_MODELS)

        with st.expander('➕ เพิ่ม/แก้ไข โรงพยาบาล', expanded=False):
            if not can_edit: st.info('สิทธิ์ viewer: อ่านอย่างเดียว')
            edit_mode = st.checkbox('แก้ไขรายการที่มีอยู่', value=False, disabled=not can_edit)
            if edit_mode and not hospitals_df.empty:
                sel = st.selectbox('เลือกโรงพยาบาล', hospitals_df.get('name', pd.Series(dtype=str)).tolist(), disabled=not can_edit)
                row = hospitals_df[hospitals_df['name']==sel].iloc[0].to_dict()
            else:
                row = {'id':str(uuid.uuid4())}

            name = st.text_input('ชื่อโรงพยาบาล', value=row.get('name',''), disabled=not can_edit)
            provs = list(TH_PROVINCES.keys()); pidx = provs.index(row.get('province')) if row.get('province') in provs else 0
            province = st.selectbox('จังหวัด', provs, index=pidx, disabled=not can_edit)
            region = TH_PROVINCES.get(province, 'ภาคกลาง'); st.caption(f'ภูมิภาค: **{region}**')

            site = st.selectbox('SiteControl (ทีม)', SITE_CONTROL_CHOICES,
                                index=SITE_CONTROL_CHOICES.index(row.get('site_control')) if row.get('site_control') in SITE_CONTROL_CHOICES else 0,
                                disabled=not can_edit)
            system = st.selectbox('ระบบที่ใช้', SYSTEM_CHOICES,
                                  index=SYSTEM_CHOICES.index(row.get('system_type')) if row.get('system_type') in SYSTEM_CHOICES else 0,
                                  disabled=not can_edit)

            ht_default = row.get('hospital_type') if row.get('hospital_type') in type_choices else type_choices[0]
            hospital_type = st.selectbox('ประเภทโรงพยาบาล', type_choices, index=type_choices.index(ht_default) if ht_default in type_choices else 0,
                                         disabled=not can_edit)

            default_models = [m for m in (row.get('service_models') or []) if m in model_choices]
            models = st.multiselect('โมเดลบริการ', model_choices, default=default_models, disabled=not can_edit)

            riders_count = st.number_input('จำนวน Rider (Capacity)', min_value=0, step=1, value=int(row.get('riders_count',0)), disabled=not can_edit)

            c1,c2 = st.columns(2)
            with c1:
                if st.button('บันทึกโรงพยาบาล', disabled=not can_edit):
                    if not name.strip(): st.error('กรอกชื่อโรงพยาบาล'); st.stop()
                    payload = {'id':row.get('id',str(uuid.uuid4())),
                               'name':name.strip(),'province':province,'region':region,
                               'site_control':site,'system_type':system,
                               'hospital_type':hospital_type,
                               'service_models':models,
                               'riders_count':int(riders_count)}
                    try:
                        if edit_mode: sb.table('hospitals').update(payload).eq('id', row['id']).execute()
                        else: sb.table('hospitals').insert(payload).execute()
                        st.success('บันทึกเรียบร้อย'); load_df.clear(); rerun()
                    except Exception:
                        st.warning('⚠️ อาจยังไม่มีคอลัมน์ hospital_type หรือ service_models ในตาราง hospitals')
                        try:
                            payload_fallback = dict(payload)
                            payload_fallback.pop('hospital_type', None)
                            payload_fallback.pop('service_models', None)
                            if edit_mode: sb.table('hospitals').update(payload_fallback).eq('id', row['id']).execute()
                            else: sb.table('hospitals').insert(payload_fallback).execute()
                            st.success('บันทึกส่วนที่ระบบรองรับแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('บันทึกไม่สำเร็จ')

            with c2:
                confirm = st.checkbox('ยืนยันการลบโรงพยาบาลนี้และธุรกรรมทั้งหมดที่เกี่ยวข้อง', value=False, key='confirm_del_hosp',
                                      disabled=not can_edit)
                if edit_mode and st.button('🗑️ ยืนยันลบ', disabled=(not can_edit or not confirm)):
                    try:
                        sb.table('transactions').delete().eq('hospital_id', row['id']).execute()
                        sb.table('hospitals').delete().eq('id', row['id']).execute()
                        st.success('ลบเรียบร้อย'); load_df.clear(); rerun()
                    except Exception:
                        st.error('ลบไม่สำเร็จ')

        st.markdown('#### รายชื่อโรงพยาบาล')
        cols = [c for c in ['name','province','region','site_control','system_type','hospital_type','service_models','riders_count'] if c in hospitals_df.columns]
        view_df = hospitals_df[cols] if (not hospitals_df.empty and cols) else pd.DataFrame(columns=['name','province','region','site_control','system_type','hospital_type','service_models','riders_count'])
        st.dataframe(view_df, use_container_width=True)

    # ---- Transactions ----
    with tabs[1]:
        hospitals_df = load_df('hospitals')
        st.markdown('### Transaction ต่อวัน')
        if hospitals_df.empty:
            st.info('ยังไม่มีโรงพยาบาล — เพิ่มก่อน')
        else:
            name2id = {r['name']:r['id'] for _,r in hospitals_df.iterrows()}

            if 'open_add_tx' not in st.session_state: st.session_state['open_add_tx'] = True
            if 'open_edit_tx' not in st.session_state: st.session_state['open_edit_tx'] = False

            with st.expander('➕ เพิ่ม Transaction รายวัน', expanded=st.session_state.get('open_add_tx', True)):
                hname = st.selectbox('โรงพยาบาล (ค้นหาได้)', list(name2id.keys()), key='add_tx_hosp', disabled=not can_edit)
                tx_date = st.date_input('วันที่', value=date.today(), key='add_tx_date', disabled=not can_edit, format="DD/MM/YYYY")
                tx_num = st.number_input('Transactions', min_value=0, step=1, key='add_tx_num', disabled=not can_edit)
                riders_active = st.number_input('Rider Active', min_value=0, step=1, key='add_tx_ra', disabled=not can_edit)
                cbtn1, cbtn2 = st.columns(2)
                with cbtn1:
                    if st.button('บันทึก Transaction', key='add_tx_btn', disabled=not can_edit):
                        hid = name2id[hname]
                        try:
                            rc_series = hospitals_df.loc[hospitals_df['id']==hid,'riders_count']
                            rc = int(rc_series.iloc[0]) if not rc_series.empty else 0
                            if riders_active > rc:
                                st.error('Rider Active มากกว่า Capacity'); st.stop()
                            sb.table('transactions').upsert(
                                {
                                  'hospital_id':hid,
                                  'date':tx_date.isoformat(),
                                  'transactions_count':int(tx_num),
                                  'riders_active':int(riders_active),
                                  'created_at': datetime.now().isoformat()
                                },
                                on_conflict=['hospital_id','date']
                            ).execute()
                            st.success('เพิ่ม/อัปเดตข้อมูลแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('บันทึกไม่สำเร็จ')
                with cbtn2:
                    if st.button('ยกเลิก', key='cancel_add_tx'):
                        st.session_state['open_add_tx'] = False
                        rerun()

            with st.expander('📥 นำเข้า CSV (hospital_name,date,transactions_count,riders_active)'):
                up = st.file_uploader('เลือกไฟล์ CSV', type=['csv'], disabled=not can_edit)
                auto_create = st.checkbox('สร้างโรงพยาบาลอัตโนมัติถ้าไม่พบ', value=False, disabled=not can_edit)
                if up is not None and can_edit:
                    try:
                        df_imp = pd.read_csv(up)
                        required = {'hospital_name','date','transactions_count','riders_active'}
                        if not required.issubset(set(df_imp.columns)):
                            st.error(f'คอลัมน์ต้องมี: {required}')
                        else:
                            for _, r in df_imp.iterrows():
                                hname = str(r['hospital_name']).strip()
                                dt = pd.to_datetime(r['date']).date()
                                tx = int(r['transactions_count'])
                                ra = int(r['riders_active'])
                                hid = name2id.get(hname)
                                if not hid and auto_create:
                                    hid = str(uuid.uuid4())
                                    payload={'id':hid,'name':hname,'province':'กรุงเทพมหานคร','region':TH_PROVINCES['กรุงเทพมหานคร'],
                                             'site_control':'ทีมเหนือ','system_type':'WebPortal','riders_count':0}
                                    try: sb.table('hospitals').insert(payload).execute(); name2id[hname]=hid
                                    except Exception: pass
                                if not hid: 
                                    st.warning(f'ข้าม: ไม่พบโรงพยาบาล {hname}'); 
                                    continue
                                sb.table('transactions').upsert(
                                    {
                                      'hospital_id':hid,
                                      'date':dt.isoformat(),
                                      'transactions_count':tx,
                                      'riders_active':ra,
                                      'created_at': datetime.now().isoformat()
                                    },
                                    on_conflict=['hospital_id','date']
                                ).execute()
                            st.success('นำเข้าเสร็จสิ้น'); load_df.clear(); rerun()
                    except Exception:
                        st.error('นำเข้าไม่สำเร็จ')

            raw_tx = load_df('transactions')
            default_h = st.session_state.get('edit_target_h')
            default_d = st.session_state.get('edit_target_d', date.today())
            try:
                idx_default_h = list(name2id.keys()).index(default_h) if default_h in name2id else 0
            except Exception:
                idx_default_h = 0

            if st.session_state.get('open_edit_tx', False) and st.session_state.get('force_edit_reset', False):
                for k in ['edit_pick_h','edit_pick_d']:
                    if k in st.session_state: st.session_state.pop(k)
                st.session_state['force_edit_reset'] = False

            with st.expander('✏️ แก้ไข / ลบ ตาม โรงพยาบาล + วันที่', expanded=st.session_state.get('open_edit_tx', False)):
                h_edit = st.selectbox('โรงพยาบาล', list(name2id.keys()), index=idx_default_h, key='edit_pick_h', disabled=not can_edit)
                d_edit = st.date_input('วันที่', value=default_d, key='edit_pick_d', disabled=not can_edit, format="DD/MM/YYYY")

                if st.button('ยกเลิกการแก้ไข'):
                    for k in ['open_edit_tx','edit_target_h','edit_target_d','force_edit_reset']:
                        st.session_state.pop(k, None)
                    rerun()

                if raw_tx.empty:
                    st.info('ยังไม่มีข้อมูล')
                else:
                    raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
                    pick_df = raw_tx[(raw_tx['hospital_id']==name2id[h_edit]) & (raw_tx['date']==d_edit)]
                    if pick_df.empty:
                        st.info('ไม่พบข้อมูลของโรงพยาบาล/วันที่นี้')
                    else:
                        row = pick_df.iloc[0].to_dict()
                        nsel = st.number_input('Transactions', min_value=0, step=1, value=int(row.get('transactions_count',0)), disabled=not can_edit)
                        rsel = st.number_input('Rider Active', min_value=0, step=1, value=int(row.get('riders_active',0)), disabled=not can_edit)
                        c1,c2 = st.columns(2)
                        with c1:
                            if st.button('บันทึกการแก้ไข', key='save_edit_tx', disabled=not can_edit):
                                try:
                                    sb.table('transactions').update({
                                        'transactions_count':int(nsel),'riders_active':int(rsel)
                                    }).eq('id', row['id']).execute()
                                    for k in ['open_edit_tx','edit_target_h','edit_target_d']:
                                        st.session_state.pop(k, None)
                                    st.success('อัปเดตแล้ว'); load_df.clear(); rerun()
                                except Exception:
                                    st.error('อัปเดตไม่สำเร็จ')
                        with c2:
                            if st.button('ลบรายการนี้', key='del_edit_tx', disabled=not can_edit):
                                try:
                                    sb.table('transactions').delete().eq('id', row['id']).execute()
                                    for k in ['open_edit_tx','edit_target_h','edit_target_d']:
                                        st.session_state.pop(k, None)
                                    st.success('ลบแล้ว'); load_df.clear(); rerun()
                                except Exception:
                                    st.error('ลบไม่สำเร็จ')

            st.markdown('#### รายการ Transaction (มุมมอง)')
            if raw_tx.empty:
                st.info('ยังไม่มีข้อมูล')
            else:
                raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
                tx_view = raw_tx.merge(hospitals_df[['id','name']], left_on='hospital_id', right_on='id', how='left')
                tx_view['วันที่'] = tx_view['date'].apply(th_date)
                show = safe_cols(tx_view, ['วันที่','name','transactions_count','riders_active'])
                st.dataframe(
                    tx_view[show].rename(columns={'name':'โรงพยาบาล','transactions_count':'Transactions','riders_active':'Rider Active'}),
                    use_container_width=True
                )

    # ---- Master Data ----
    with tabs[2]:
        st.markdown('### ข้อมูลหลัก (Master Data)')

        st.markdown('#### ประเภทโรงพยาบาล')
        types_df = load_df('hospital_types')
        show_types = types_df['name'] if ('name' in types_df.columns and not types_df.empty) else pd.Series(DEFAULT_HOSPITAL_TYPES, name='name')
        st.dataframe(pd.DataFrame({'name': show_types}), use_container_width=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            new_t = st.text_input('เพิ่มประเภท (เช่น รพช. ขนาด S)')
            if st.button('เพิ่มประเภท'):
                if new_t.strip():
                    upsert_master('hospital_types', new_t.strip()); load_df.clear(); rerun()
        with c2:
            if not show_types.empty:
                old_t = st.selectbox('เปลี่ยนชื่อ (เลือก)', show_types.tolist())
                new_name = st.text_input('ชื่อใหม่')
                if st.button('บันทึกชื่อใหม่'):
                    if new_name.strip():
                        rename_master('hospital_types', old_t, new_name.strip()); load_df.clear(); rerun()
        with c3:
            if not show_types.empty:
                del_t = st.selectbox('ลบประเภท (เลือก)', show_types.tolist(), key='del_type_sel')
                if st.button('ลบประเภทนี้'):
                    delete_master('hospital_types', del_t); load_df.clear(); rerun()

        st.divider()

        st.markdown('#### โมเดลบริการ')
        sm_df = load_df('service_models_master')
        show_sm = sm_df['name'] if ('name' in sm_df.columns and not sm_df.empty) else pd.Series(DEFAULT_SERVICE_MODELS, name='name')
        st.dataframe(pd.DataFrame({'name': show_sm}), use_container_width=True)
        s1,s2,s3 = st.columns(3)
        with s1:
            new_m = st.text_input('เพิ่มโมเดลบริการ (เช่น Rider Hub)')
            if st.button('เพิ่มโมเดล'):
                if new_m.strip():
                    upsert_master('service_models_master', new_m.strip()); load_df.clear(); rerun()
        with s2:
            if not show_sm.empty:
                old_m = st.selectbox('เปลี่ยนชื่อโมเดล (เลือก)', show_sm.tolist())
                new_m_name = st.text_input('ชื่อโมเดลใหม่')
                if st.button('บันทึกชื่อโมเดลใหม่'):
                    if new_m_name.strip():
                        rename_master('service_models_master', old_m, new_m_name.strip()); load_df.clear(); rerun()
        with s3:
            if not show_sm.empty:
                del_m = st.selectbox('ลบโมเดล (เลือก)', show_sm.tolist(), key='del_model_sel')
                if st.button('ลบโมเดลนี้'):
                    delete_master('service_models_master', del_m); load_df.clear(); rerun()

    # ---- Admin users / Roles ----
    with tabs[3]:
        st.markdown('### ผู้ดูแลระบบ & บทบาท')
        admins_df = load_df('admins')
        if not admins_df.empty:
            cols = ['username','role'] if 'role' in admins_df.columns else ['username']
            st.dataframe(admins_df[cols], use_container_width=True)
        else:
            st.info('ยังไม่มีข้อมูลผู้ดูแล หรือไม่มีตาราง admins')

        with st.expander('➕ เพิ่มผู้ดูแล'):
            nu = st.text_input('Username ใหม่'); npw = st.text_input('Password', type='password')
            nrole = st.selectbox('Role', ['admin','editor','viewer'])
            if st.button('เพิ่มผู้ดูแล'):
                if not nu or not npw: st.error('กรอกให้ครบ'); st.stop()
                try:
                    if not admins_df.empty and any(admins_df['username'].str.lower()==nu.lower()):
                        st.error('มี username นี้แล้ว'); st.stop()
                    sb.table('admins').insert({'id':str(uuid.uuid4()),'username':nu,'password_hash':hash_pw(npw),'role':nrole}).execute()
                    st.success('เพิ่มแล้ว'); load_df.clear(); rerun()
                except Exception:
                    st.error('เพิ่มไม่สำเร็จ')
        with st.expander('🔁 เปลี่ยนรหัสผ่าน / เปลี่ยนบทบาท / ลบผู้ดูแล'):
            if not admins_df.empty:
                selu = st.selectbox('เลือกผู้ใช้', admins_df['username'].tolist())
                newpw = st.text_input('รหัสผ่านใหม่', type='password')
                newrole = st.selectbox('Role ใหม่', ['admin','editor','viewer'])
                c1,c2,c3 = st.columns(3)
                with c1:
                    if st.button('เปลี่ยนรหัสผ่าน'):
                        if not newpw: st.error('กรุณากรอกรหัส'); st.stop()
                        try:
                            sb.table('admins').update({'password_hash':hash_pw(newpw)}).eq('username', selu).execute()
                            st.success('เปลี่ยนแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('เปลี่ยนไม่สำเร็จ')
                with c2:
                    if st.button('อัปเดตบทบาท'):
                        try:
                            sb.table('admins').update({'role':newrole}).eq('username', selu).execute()
                            st.success('อัปเดตบทบาทแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('อัปเดตไม่สำเร็จ')
                with c3:
                    if st.button('ลบผู้ใช้'):
                        try:
                            sb.table('admins').delete().eq('username', selu).execute()
                            st.success('ลบแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('ลบไม่สำเร็จ')

    # ---- Reports ----
    with tabs[4]:
        st.markdown("### รายงานสรุปรายเดือน")
        today = date.today()
        ym = st.date_input('เลือกเดือน', value=date(today.year, today.month, 1), format="DD/MM/YYYY")
        start = ym.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        hospitals_df = load_df('hospitals')
        tx_df = load_df('transactions')
        if tx_df.empty or hospitals_df.empty:
            st.info('ยังไม่มีข้อมูลเพียงพอ')
        else:
            tx_df['date'] = pd.to_datetime(tx_df['date']).dt.date
            mm = tx_df[(tx_df['date']>=start) & (tx_df['date']<=end)].merge(
                hospitals_df, left_on='hospital_id', right_on='id', how='left'
            )
            by_hosp = mm.groupby('name').agg(transactions=('transactions_count','sum'),
                                             ra=('riders_active','sum')).reset_index()
            by_site = mm.groupby('site_control').agg(transactions=('transactions_count','sum'),
                                                     ra=('riders_active','sum')).reset_index()
            daily = mm.groupby('date').agg(transactions=('transactions_count','sum'),
                                           ra=('riders_active','sum')).reset_index()

            st.dataframe(by_hosp.rename(columns={'name':'โรงพยาบาล','transactions':'Transactions','ra':'Rider Active'}),
                         use_container_width=True, height=300)

            ebytes = df_to_excel_bytes({
                f"{start.strftime('%Y-%m')}_by_hospital": by_hosp,
                f"{start.strftime('%Y-%m')}_by_site": by_site,
                f"{start.strftime('%Y-%m')}_daily": daily
            })
            st.download_button("ดาวน์โหลดรายงาน (Excel)", data=ebytes,
                               file_name=f"telemed_monthly_{start.strftime('%Y_%m')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            settings_df = load_df('settings')
            def get_setting(key, default):
                try:
                    v = settings_df.loc[settings_df['key']==key, 'value'].iloc[0]
                    return v if isinstance(v, dict) else default
                except Exception:
                    return default
            line_cfg = get_setting('line_notify', {'enabled':False,'token':''})
            if st.button('ส่งสรุปไป LINE Notify'):
                if not line_cfg.get('enabled') or not line_cfg.get('token'):
                    st.error('ยังไม่ตั้งค่า LINE Notify')
                else:
                    try:
                        summary_text = f"สรุป {start.strftime('%Y-%m')}\n" \
                                       f"รวมธุรกรรม: {int(mm['transactions_count'].sum()):,} รายการ\n" \
                                       f"โรงพยาบาล: {mm['hospital_id'].nunique()} แห่ง"
                        requests.post(
                            "https://notify-api.line.me/api/notify",
                            headers={"Authorization": f"Bearer {line_cfg['token']}"},
                            data={"message": summary_text}
                        )
                        st.success('ส่ง LINE แล้ว')
                    except Exception:
                        st.error('ส่ง LINE ไม่สำเร็จ')

    # ---- Settings & Seed ----
    with tabs[5]:
        st.markdown('### ตั้งค่า & ข้อมูลตัวอย่าง')
        settings_df = load_df('settings')

        def get_setting(key, default):
            try:
                v = settings_df.loc[settings_df['key']==key, 'value'].iloc[0]
                return v if isinstance(v, dict) else default
            except Exception:
                return default

        targets = get_setting('targets', {'daily_transactions':50,'utilization_alert_pct':90})
        line_cfg = get_setting('line_notify', {'enabled':False,'token':''})

        c1,c2 = st.columns(2)
        with c1:
            daily_target = st.number_input('เป้ายอดรายวัน (Transactions/วัน)', min_value=0, step=1,
                                           value=int(targets.get('daily_transactions',50)))
        with c2:
            util_th = st.number_input('แจ้งเตือนเมื่อ Utilization ≥ (%)', min_value=0, max_value=100, step=1,
                                      value=int(targets.get('utilization_alert_pct',90)))
        if st.button('บันทึกเป้าหมาย'):
            try:
                sb.table('settings').upsert({'key':'targets','value':{'daily_transactions':int(daily_target),'utilization_alert_pct':int(util_th)}}).execute()
                st.success('บันทึกแล้ว'); load_df.clear()
            except Exception:
                st.warning('ยังไม่มีตาราง settings ในฐานข้อมูล')

        st.markdown('#### LINE Notify')
        en_line = st.checkbox('เปิดใช้ LINE Notify', value=bool(line_cfg.get('enabled',False)))
        token = st.text_input('LINE Notify Token', value=line_cfg.get('token',''), type='password')
        if st.button('บันทึก LINE Notify'):
            try:
                sb.table('settings').upsert({'key':'line_notify','value':{'enabled':bool(en_line),'token':token.strip()}}).execute()
                st.success('บันทึกแล้ว'); load_df.clear()
            except Exception:
                st.warning('ยังไม่มีตาราง settings ในฐานข้อมูล')

        st.markdown('#### ตาราง settings (Raw)')
        if not settings_df.empty:
            st.dataframe(settings_df, use_container_width=True)
        else:
            st.info('ยังไม่มีข้อมูลในตาราง settings')

        st.markdown('#### ข้อมูลตัวอย่าง')
        a,b = st.columns(2)
        with a:
            if st.button('เติมข้อมูลตัวอย่าง (5 รพ. x 3 วัน)'):
                demo = [
                    ('รพ.หาดใหญ่','สงขลา','ภาคใต้','ทีมใต้','WebPortal',['Rider','App','Station to Station'],5,'รพ.ศูนย์/รพ.ทั่วไป'),
                    ('รพ.เชียงใหม่','เชียงใหม่','ภาคเหนือ','ทีมเหนือ','HOSxpV4',['Rider','Station to Station'],7,'รพ.ศูนย์/รพ.ทั่วไป'),
                    ('รพ.ขอนแก่น','ขอนแก่น','ภาคอีสาน','ทีมอีสาน','HOSxpV3',['App'],4,'รพ.ชุมชน'),
                    ('รพ.ชลบุรี','ชลบุรี','ภาคตะวันออก','ทีมเหนือ','WebPortal',['Rider','App'],6,'รพ.ศูนย์/รพ.ทั่วไป'),
                    ('รพ.นครศรีธรรมราช','นครศรีธรรมราช','ภาคใต้','ทีมใต้','HOSxpV4',['Rider','App'],6,'รพ.ศูนย์/รพ.ทั่วไป'),
                ]
                name2id={}
                for n,prov,reg,site,sys,models,rc,ht in demo:
                    try:
                        ex=sb.table('hospitals').select('id').eq('name',n).execute().data
                        hid=ex[0]['id'] if ex else str(uuid.uuid4())
                        payload={'id':hid,'name':n,'province':prov,'region':reg,
                                 'site_control':site,'system_type':sys,'service_models':models,
                                 'riders_count':rc,'hospital_type':ht}
                        if not ex:
                            try:
                                sb.table('hospitals').insert(payload).execute()
                            except Exception:
                                payload.pop('hospital_type', None); payload.pop('service_models', None)
                                sb.table('hospitals').insert(payload).execute()
                        name2id[n]=hid
                    except Exception: pass
                days=[date.today()-timedelta(days=2),date.today()-timedelta(days=1),date.today()]
                rows=[]
                for n,hid in name2id.items():
                    for d in days:
                        rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':d.isoformat(),
                                     'transactions_count':random.randint(20,60),'riders_active':random.randint(2,7),
                                     'created_at': datetime.now().isoformat()})
                if rows:
                    try: sb.table('transactions').insert(rows).execute(); st.success('เติมข้อมูลแล้ว'); load_df.clear(); rerun()
                    except Exception: st.error('เติมข้อมูลไม่สำเร็จ')
        with b:
            if st.button('ลบข้อมูลตัวอย่าง'):
                try:
                    targets=['รพ.หาดใหญ่','รพ.เชียงใหม่','รพ.ขอนแก่น','รพ.ชลบุรี','รพ.นครศรีธรรมราช']
                    ids=[r['id'] for r in sb.table('hospitals').select('id').in_('name',targets).execute().data]
                    for hid in ids: sb.table('transactions').delete().eq('hospital_id',hid).execute()
                    if ids: sb.table('hospitals').delete().in_('id',ids).execute()
                    st.success('ลบแล้ว'); load_df.clear(); rerun()
                except Exception:
                    st.error('ลบข้อมูลตัวอย่างไม่สำเร็จ')

# ---------------- Render ----------------
if st.query_params.get('page','dashboard') == 'admin':
    render_admin()
else:
    render_dashboard()

# ---------------- Sidebar downloads ----------------
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
