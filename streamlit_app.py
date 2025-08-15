# Telemedicine Transactions Dashboard — Modern Pastel Edition
# ปรับ UI/กราฟตามข้อเสนอ + แก้ query_params + ปุ่มขยายเต็มจอ + ปุ่มบันทึกหน้า

import os, uuid, json, bcrypt, requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from datetime import date, timedelta
from typing import Dict, Any

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ====================== THEME ======================
PASTEL_BG = '#F7F8FB'; PASTEL_CARD = '#FFFFFF'
PASTEL_TEXT = '#334155'  # slate-700
DARK_BG = '#0F172A'; DARK_CARD = '#111827'; DARK_TEXT = '#E5E7EB'

# พาเลตต์พาสเทล (ยาวพอสำหรับหลายแท่ง/หลายทีม)
PALETTE = [
    "#A7C7E7","#F8C8DC","#B6E2D3","#FDE2B3","#EAD7F7","#CDE5F0",
    "#FFD6E8","#C8E6C9","#FFF3B0","#D7E3FC","#F2D7EE","#B8F1ED"
]

st.set_page_config(page_title="Telemedicine Transactions", page_icon="📊", layout="wide")

# ================== SUPABASE CONFIG =================
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error('❌ Missing SUPABASE_URL or SUPABASE_KEY environment variable.')
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb: Client = get_client()

# =================== CONSTANTS ======================
SITE_CONTROL_CHOICES = ['ทีมใต้', 'ทีมเหนือ', 'ทีมอีสาน']
SYSTEM_CHOICES = ['HOSxpV4', 'HOSxpV3', 'WebPortal']
SERVICE_MODEL_CHOICES = ['Rider', 'App', 'Station to Station']

TH_PROVINCES: Dict[str, str] = {
  'กระบี่':'ภาคใต้','กรุงเทพมหานคร':'ภาคกลาง','กาญจนบุรี':'ภาคตะวันตก','กาฬสินธุ์':'ภาคอีสาน',
  'กำแพงเพชร':'ภาคเหนือ','ขอนแก่น':'ภาคอีสาน','จันทบุรี':'ภาคตะวันออก','ฉะเชิงเทรา':'ภาคตะวันออก',
  'ชลบุรี':'ภาคตะวันออก','ชัยนาท':'ภาคกลาง','ชัยภูมิ':'ภาคอีสาน','ชุมพร':'ภาคใต้',
  'เชียงราย':'ภาคเหนือ','เชียงใหม่':'ภาคเหนือ','ตรัง':'ภาคใต้','ตราด':'ภาคตะวันออก',
  'ตาก':'ภาคตะวันตก','นครนายก':'ภาคกลาง','นครปฐม':'ภาคกลาง','นครพนม':'ภาคอีสาน',
  'นครราชสีมา':'ภาคอีสาน','นครศรีธรรมราช':'ภาคใต้','นครสวรรค์':'ภาคเหนือ','นนทบุรี':'ภาคกลาง',
  'นราธิวาส':'ภาคใต้','น่าน':'ภาคเหนือ','บึงกาฬ':'ภาคอีสาน','บุรีรัมย์':'ภาคอีสาน',
  'ปทุมธานี':'ภาคกลาง','ประจวบคีรีขันธ์':'ภาคตะวันตก','ปราจีนบุรี':'ภาคตะวันออก','ปัตตานี':'ภาคใต้',
  'พระนครศรีอยุธยา':'ภาคกลาง','พะเยา':'ภาคเหนือ','พังงา':'ภาคใต้','พัทลุง':'ภาคใต้',
  'พิจิตร':'ภาคเหนือ','พิษณุโลก':'ภาคเหนือ','เพชรบุรี':'ภาคตะวันตก','เพชรบูรณ์':'ภาคเหนือ',
  'แพร่':'ภาคเหนือ','ภูเก็ต':'ภาคใต้','มหาสารคาม':'ภาคอีสาน','มุกดาหาร':'ภาคอีสาน',
  'แม่ฮ่องสอน':'ภาคเหนือ','ยะลา':'ภาคใต้','ยโสธร':'ภาคอีสาน','ร้อยเอ็ด':'ภาคอีสาน',
  'ระนอง':'ภาคใต้','ระยอง':'ภาคตะวันออก','ราชบุรี':'ภาคตะวันตก','ลพบุรี':'ภาคกลาง',
  'ลำปาง':'ภาคเหนือ','ลำพูน':'ภาคเหนือ','เลย':'ภาคอีสาน','ศรีสะเกษ':'ภาคอีสาน',
  'สกลนคร':'ภาคอีสาน','สงขลา':'ภาคใต้','สตูล':'ภาคใต้','สมุทรปราการ':'ภาคกลาง',
  'สมุทรสงคราม':'ภาคกลาง','สมุทรสาคร':'ภาคกลาง','สระแก้ว':'ภาคตะวันออก','สระบุรี':'ภาคกลาง',
  'สิงห์บุรี':'ภาคกลาง','สุโขทัย':'ภาคเหนือ','สุพรรณบุรี':'ภาคกลาง','สุราษฎร์ธานี':'ภาคใต้',
  'สุรินทร์':'ภาคอีสาน','หนองคาย':'ภาคอีสาน','หนองบัวลำภู':'ภาคอีสาน','อ่างทอง':'ภาคกลาง',
  'อำนาจเจริญ':'ภาคอีสาน','อุดรธานี':'ภาคอีสาน','อุตรดิตถ์':'ภาคเหนือ','อุทัยธานี':'ภาคกลาง',
  'อุบลราชธานี':'ภาคอีสาน'
}

# =================== SETTINGS (KV) ===================
def get_setting(key: str, default: Any=None) -> Any:
    try:
        res = sb.table('settings').select('*').eq('key', key).execute().data
        if res: return res[0]['value']
    except Exception: pass
    return default

def set_setting(key: str, value: Any):
    sb.table('settings').upsert({'key': key, 'value': value}).execute()

DEFAULT_TARGETS = {'daily_transactions': 50, 'utilization_alert_pct': 90}
targets = get_setting('targets', DEFAULT_TARGETS) or DEFAULT_TARGETS
line_cfg = get_setting('line_notify', {'enabled': False, 'token': ''}) or {'enabled': False, 'token': ''}

# ====================== HELPERS ======================
def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception: return False

@st.cache_data(ttl=60, show_spinner=False)
def load_df(table: str) -> pd.DataFrame:
    return pd.DataFrame(sb.table(table).select('*').execute().data)

def force_rerun():
    try: st.rerun()
    except Exception:
        try: st.experimental_rerun()
        except Exception: pass

def reload_all():
    load_df.clear(); force_rerun()

def send_line_notify(message: str):
    if not isinstance(line_cfg, dict): return
    if line_cfg.get('enabled') and line_cfg.get('token'):
        try:
            requests.post('https://notify-api.line.me/api/notify',
                          headers={'Authorization': f"Bearer {line_cfg['token']}"},
                          data={'message': message}, timeout=5)
        except Exception: pass

def ensure_default_admin():
    rows = sb.table('admins').select('username').eq('username','telemed').execute().data
    if not rows:
        sb.table('admins').insert({'id':str(uuid.uuid4()),'username':'telemed','password_hash':hash_pw('Telemed@DHI')}).execute()
ensure_default_admin()

# =================== BASE STYLES =====================
if 'ui' not in st.session_state: st.session_state['ui'] = {'dark': False}
with st.sidebar:
    st.markdown('### 🎨 Appearance')
    st.session_state.ui['dark'] = st.checkbox('โหมดมืด (Dark mode)', value=st.session_state.ui['dark'])

BG, CARD, TEXT = (DARK_BG, DARK_CARD, DARK_TEXT) if st.session_state.ui['dark'] else (PASTEL_BG, PASTEL_CARD, PASTEL_TEXT)

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  :root {{ --bg:{BG}; --card:{CARD}; --text:{TEXT}; }}
  html, body, [class*='st-'] {{ font-family:'Kanit',system-ui,-apple-system,Segoe UI,sans-serif; color:var(--text); }}
  .stApp {{ background-color:var(--bg); }}
  .metric-card {{ background:var(--card); padding:1rem; border-radius:16px; box-shadow:0 4px 18px rgba(0,0,0,.06); }}
  .pill {{ display:inline-flex; align-items:center; gap:.5rem; background:#EFF6FF; color:#2563EB; padding:.4rem .8rem; border-radius:999px; font-weight:600; }}
  .btn-grad button {{ background:linear-gradient(135deg,#A7C7E7,#B6E2D3); border:none; color:#1f2937; font-weight:700; border-radius:12px; }}
</style>
""", unsafe_allow_html=True)

# plotly defaults
px.defaults.template = 'plotly_white'
px.defaults.color_discrete_sequence = PALETTE

def prettify_bar(fig, y_title=''):
    fig.update_traces(texttemplate='%{text:,}', textposition='outside', cliponaxis=False,
                      hovertemplate='<b>%{x}</b><br>ค่า: %{y:,}<extra></extra>')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', yaxis_title=y_title,
                      margin=dict(t=30,r=20,b=40,l=50))
    return fig

# ======================= AUTH =======================
if 'auth' not in st.session_state: st.session_state['auth']={'ok':False,'user':None}
with st.sidebar:
    st.markdown('## 🔐 Admin Login')
    if not st.session_state.auth['ok']:
        with st.form('login_form'):
            u = st.text_input('Username'); p = st.text_input('Password', type='password')
            if st.form_submit_button('Login'):
                rows = sb.table('admins').select('*').eq('username', u).execute().data
                if rows and verify_pw(p, rows[0]['password_hash']):
                    st.session_state.auth={'ok':True,'user':rows[0]['username']}; force_rerun()
                else: st.error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        st.write(f"✅ Logged in as **{st.session_state.auth['user']}**")
        if st.button('Logout'): st.session_state.auth={'ok':False,'user':None}; force_rerun()

# ===================== FILTERS ======================
hospitals_df = load_df('hospitals')
colF1, colF2, colF3, colF4 = st.columns([1.2,1.2,1.3,1])
with colF1:
    hosp_names = ['(ทั้งหมด)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist())
    selected_hospital = st.selectbox('🏥 โรงพยาบาล', hosp_names)
with colF2:
    today = date.today(); start_default = today - timedelta(days=30)
    date_range = st.date_input('📅 ช่วงวันที่', value=(start_default, today))
    start_date, end_date = (date_range if isinstance(date_range, tuple) else (start_default, today))
with colF3:
    site_filter = st.multiselect('🧭 ทีมภูมิภาค (SiteControl)', SITE_CONTROL_CHOICES)
with colF4:
    st.markdown('<div class="pill">Advanced Filter</div>', unsafe_allow_html=True)
    components.html('<button onclick="parent.window.print()">🖨️ บันทึกหน้า</button>', height=48)

# ====================== DATA ========================
transactions_df = load_df('transactions')
if not transactions_df.empty:
    transactions_df['date'] = pd.to_datetime(transactions_df['date']).dt.date
    mask = (transactions_df['date'] >= start_date) & (transactions_df['date'] <= end_date)
    transactions_df = transactions_df.loc[mask].copy()

if not hospitals_df.empty and not transactions_df.empty:
    merged = transactions_df.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left', suffixes=('', '_h'))
else:
    merged = pd.DataFrame(columns=['date','hospital_id','transactions_count','riders_active','name','site_control','province','region','riders_count'])

if selected_hospital != '(ทั้งหมด)': merged = merged.loc[merged['name'] == selected_hospital]
if site_filter: merged = merged.loc[merged['site_control'].isin(site_filter)]

# ======================= KPIs =======================
st.markdown('### 📈 ภาพรวม (Overview)')
colK1, colK2, colK3, colK4, colK5 = st.columns(5)
total_tx = int(merged['transactions_count'].sum()) if not merged.empty else 0
unique_h = merged['hospital_id'].nunique() if not merged.empty else 0
sum_riders_active = int(merged['riders_active'].sum()) if not merged.empty else 0
avg_per_day = int(merged.groupby('date')['transactions_count'].sum().mean()) if not merged.empty else 0
sum_riders_capacity = int(merged['riders_count'].fillna(0).sum()) if not merged.empty else 0
with colK1: st.markdown(f"<div class='metric-card'><b>Transaction รวม</b><h2>{total_tx:,}</h2></div>", unsafe_allow_html=True)
with colK2: st.markdown(f"<div class='metric-card'><b>โรงพยาบาลทั้งหมด</b><h2>{unique_h}</h2></div>", unsafe_allow_html=True)
with colK3: st.markdown(f"<div class='metric-card'><b>จำนวนไรเดอร์รวม</b><h2>{sum_riders_capacity:,}</h2></div>", unsafe_allow_html=True)
with colK4: st.markdown(f"<div class='metric-card'><b>เฉลี่ยต่อวัน</b><h2>{avg_per_day:,}</h2></div>", unsafe_allow_html=True)
with colK5: st.markdown(f"<div class='metric-card'><b>ไรเดอร์ Active</b><h2>{sum_riders_active:,}</h2></div>", unsafe_allow_html=True)

# ====================== CHARTS ======================
if merged.empty:
    st.info('ยังไม่มีข้อมูล ลองเพิ่มจาก Admin ➜ จัดการข้อมูล')
else:
    # ------- PIE: แยกตามทีมภูมิภาค -------
    st.markdown('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')
    grp_site = merged.groupby('site_control').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    grp_site = grp_site.sort_values('transactions_count', ascending=False)
    pie = px.pie(
        grp_site, names='site_control', values='transactions_count',
        color='site_control', color_discrete_sequence=PALETTE, hole=0.55
    )
    pie.update_traces(
        textposition='outside',
        texttemplate='<b>%{label}</b><br>%{value:,} (%{percent:.1%})',
        marker=dict(line=dict(color='#fff', width=2)),
        pull=[0.02]*len(grp_site)
    )
    pie.update_layout(
        showlegend=True, legend_title_text='ทีมภูมิภาค',
        annotations=[dict(text=f"{total_tx:,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=18))]
    )
    st.plotly_chart(pie, use_container_width=True)

    # ------- BAR H (โรงพยาบาลแนวนอน + ปุ่มขยายเต็มจอ) -------
    st.markdown('#### ภาพรวมต่อโรงพยาบาล (แนวนอน)')
    grp_h = merged.groupby('name').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    grp_h = grp_h.sort_values('transactions_count', ascending=True)
    bar_h = px.bar(
        grp_h, y='name', x='transactions_count', orientation='h', text='transactions_count',
        color='name', color_discrete_sequence=PALETTE, labels={'name':'โรงพยาบาล','transactions_count':'Transactions'}
    )
    bar_h.update_traces(textposition='outside')
    bar_h.update_layout(showlegend=False, height=max(520, 30*len(grp_h)+200), margin=dict(l=140,r=40,t=30,b=40))
    # ปุ่มขยายเต็มจอด้วย query_params (ไม่เปิดหน้าใหม่ซ้อน)
    if st.button('🔎 ขยายเต็มจอ', key='btn_expand_h'):
        st.query_params.update({'view':'hospitals'})
        st.rerun()
    components.html(bar_h.to_html(include_plotlyjs='cdn', full_html=False), height=560, scrolling=True)

    # ------- LINE (แนวโน้มรายวัน) -------
    st.markdown('#### แนวโน้มรายวัน (กราฟเส้น)')
    daily = merged.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index().sort_values('date')
    if not daily.empty:
        TH_DAYS = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
        def label_th(d):
            dts = pd.to_datetime(d)
            return f"{TH_DAYS[dts.dayofweek]} {dts.day}/{dts.month}/{str(dts.year)[-2:]}"
        labels = daily['date'].apply(label_th)

        fig_line = go.Figure()
        # Transactions (โชว์พร้อมตัวเลข)
        fig_line.add_trace(go.Scatter(
            x=labels, y=daily['transactions_count'],
            mode='lines+markers+text', name='Transactions',
            text=daily['transactions_count'], textposition='top center',
            line=dict(width=3), marker=dict(size=8, symbol='circle')
        ))
        # Rider Active (ซ่อนไว้ก่อน)
        fig_line.add_trace(go.Scatter(
            x=labels, y=daily['riders_active'],
            mode='lines+markers', name='Rider Active',
            visible='legendonly', line=dict(width=2, dash='dot'), marker=dict(size=7)
        ))
        fig_line.update_layout(
            xaxis_title='วัน/เดือน/ปี', yaxis_title='จำนวน', xaxis_tickangle=-40,
            margin=dict(t=30,r=20,b=80,l=60), hovermode='x unified'
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ------- TABLE (สรุปทีมภูมิภาค) -------
    st.markdown('#### ตารางจำนวน Transaction แยกตามทีมภูมิภาค')
    view_tbl = grp_site.rename(columns={
        'site_control':'ทีมภูมิภาค','transactions_count':'Transactions',
        'riders_active':'Rider Active','riders_count':'Riders ทั้งหมด'
    })
    try:
        st.table(view_tbl.style.background_gradient(
            cmap='YlGnBu', subset=['Transactions','Rider Active','Riders ทั้งหมด']
        ))
    except Exception:
        st.dataframe(view_tbl, use_container_width=True)

# ================== FULLSCREEN VIEW =================
if st.query_params.get('view') == 'hospitals' and not merged.empty:
    st.markdown('### ภาพรวมต่อโรงพยาบาล (เต็มจอ)')
    grp_h2 = merged.groupby('name').agg({'transactions_count':'sum'}).reset_index().sort_values('transactions_count', ascending=True)
    bar_full = px.bar(
        grp_h2, y='name', x='transactions_count', orientation='h', text='transactions_count',
        color='name', color_discrete_sequence=PALETTE
    )
    bar_full.update_traces(textposition='outside')
    bar_full.update_layout(showlegend=False, height=max(800, 35*len(grp_h2)+240), margin=dict(l=180,r=40,t=30,b=40))
    st.plotly_chart(bar_full, use_container_width=True)
    if st.button('⬅️ กลับสู่หน้า Dashboard'):
        # ล้าง view param
        st.query_params.clear()
        st.rerun()

# ================== ADMIN/SETTINGS (เหมือนเดิมทั้งหมด) ==================
# ……………………… (คงส่วน Admin CRUD/Settings/Seed ตามไฟล์เวอร์ชันก่อนหน้าโดยไม่เปลี่ยน) …
# เพื่อไม่ให้คำตอบยาวเกิน คุณคงใช้บล็อก Admin เดิมวางต่อท้ายไฟล์นี้ได้ทันที
