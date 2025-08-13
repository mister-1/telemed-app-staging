# Telemedicine Transactions Dashboard — Upgraded (Streamlit + Supabase)
# Features: pastel UI + dark mode, KPIs, filters with quick presets,
# grouped charts with labels, drill-down per hospital, alerts with targets,
# optional LINE Notify, export CSV, CSV bulk import, seed/reset demo data,
# viewer/admin separation, admin pages (hospitals, transactions, admins, settings), rider validation.

import os
import uuid
import json
import bcrypt
import requests
import pandas as pd
import plotly.express as px
from io import StringIO
from datetime import date, timedelta
from typing import Dict, Any

import streamlit as st
from supabase import create_client, Client

# =========================
# ---------- THEME --------
# =========================
PASTEL_BG = '#F7F8FB'
PASTEL_CARD = '#FFFFFF'
PASTEL_ACCENT = '#A7C7E7'    # soft baby blue
PASTEL_ACCENT_2 = '#F8C8DC'  # soft pink
PASTEL_ACCENT_3 = '#B6E2D3'  # mint
PASTEL_TEXT = '#3E4B6D'

DARK_BG = '#0F172A'
DARK_CARD = '#111827'
DARK_TEXT = '#E5E7EB'

st.set_page_config(page_title='Telemedicine Transactions', page_icon='📊', layout='wide')

# =========================
# ---- ENV & CONNECTION ----
# =========================
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
APP_SECRET = os.getenv('APP_SECRET', 'replace-me').encode()

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error('❌ Missing SUPABASE_URL or SUPABASE_KEY environment variable.')
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb: Client = get_client()

# =========================
# ------- CONSTANTS --------
# =========================
SITE_CONTROL_CHOICES = ['ทีมใต้', 'ทีมเหนือ', 'ทีมอีสาน']
SYSTEM_CHOICES = ['HOSxpV4', 'HOSxpV3', 'WebPortal']
SERVICE_MODEL_CHOICES = ['Rider', 'App', 'Station to Station']

# Province → Region mapping (TH)
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
REGION_CHOICES = sorted(list(set(TH_PROVINCES.values())))

# =========================
# --------- SETTINGS -------
# =========================
def get_setting(key: str, default: Any=None) -> Any:
    try:
        res = sb.table('settings').select('*').eq('key', key).execute().data
        if res:
            return res[0]['value']
    except Exception:
        pass
    return default

def set_setting(key: str, value: Any):
    sb.table('settings').upsert({'key': key, 'value': value}).execute()

# Defaults
DEFAULT_TARGETS = {'daily_transactions': 50, 'utilization_alert_pct': 90}
targets = get_setting('targets', DEFAULT_TARGETS) or DEFAULT_TARGETS
line_cfg = get_setting('line_notify', {'enabled': False, 'token': ''}) or {'enabled': False, 'token': ''}

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
    data = sb.table(table).select('*').execute().data
    return pd.DataFrame(data)

def force_rerun():
    # Safer rerun helper (fixes sidebar toggle recursion issues)
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()  # for older Streamlit
        except Exception:
            pass

def reload_all():
    load_df.clear()
    force_rerun()

def ensure_default_admin():
    admins = sb.table('admins').select('username').eq('username', 'telemed').execute().data
    if not admins:
        sb.table('admins').insert({
            'id': str(uuid.uuid4()),
            'username': 'telemed',
            'password_hash': hash_pw('Telemed@DHI')
        }).execute()

def send_line_notify(message: str):
    if not isinstance(line_cfg, dict): return
    if line_cfg.get('enabled') and line_cfg.get('token'):
        try:
            requests.post(
                'https://notify-api.line.me/api/notify',
                headers={'Authorization': f"Bearer {line_cfg['token']}"},
                data={'message': message},
                timeout=5
            )
        except Exception:
            pass

ensure_default_admin()

# =========================
# ---------- THEME CSS -----
# =========================
if 'ui' not in st.session_state:
    st.session_state['ui'] = {'dark': False}

with st.sidebar:
    st.markdown('### 🎨 Appearance')
    st.session_state.ui['dark'] = st.checkbox('โหมดมืด (Dark mode)', value=st.session_state.ui['dark'], key='dark_mode_toggle')

if st.session_state.ui['dark']:
    BG, CARD, TEXT = DARK_BG, DARK_CARD, DARK_TEXT
else:
    BG, CARD, TEXT = PASTEL_BG, PASTEL_CARD, PASTEL_TEXT

st.markdown(f'''
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  :root {{
    --bg: {BG};
    --card: {CARD};
    --text: {TEXT};
  }}
  html, body, [class*='st-'] {{ font-family: 'Kanit', system-ui, -apple-system, Segoe UI, sans-serif; }}
  .stApp {{ background-color: var(--bg); }}
  .stButton>button {{
      background: linear-gradient(135deg, {PASTEL_ACCENT}, {PASTEL_ACCENT_3});
      color: var(--text); border: none; border-radius: 14px; padding: 0.6rem 1rem; font-weight: 600;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }}
  .metric-card {{ background: var(--card); color: var(--text); padding: 1rem; border-radius: 16px; box-shadow: 0 1px 8px rgba(0,0,0,0.05); }}
  .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb='select'] > div {{
      background: var(--card); color: var(--text); border-radius: 12px;
  }}
</style>
''', unsafe_allow_html=True)

# Plotly defaults
px.defaults.template = 'plotly_white'
px.defaults.color_discrete_sequence = ['#A7C7E7','#F8C8DC','#B6E2D3','#FDE2B3','#EAD7F7','#CDE5F0','#FFD6E8']

def prettify_bar(fig, y_title=''):
    fig.update_traces(texttemplate='%{text:,}', textposition='outside', cliponaxis=False,
                      hovertemplate='<b>%{x}</b><br>ค่า: %{y:,}<extra></extra>')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide',
                      yaxis_title=y_title, margin=dict(t=30,r=20,b=40,l=50), barmode='group')
    return fig

# =========================
# ---------- AUTH ----------
# =========================
if 'auth' not in st.session_state:
    st.session_state['auth'] = {'ok': False, 'user': None}

with st.sidebar:
    st.markdown('## 🔐 Admin Login')
    if not st.session_state.auth['ok']:
        with st.form('login_form', clear_on_submit=False):
            u = st.text_input('Username', value='', key='login_u')
            p = st.text_input('Password', type='password', value='', key='login_p')
            submitted = st.form_submit_button('Login')
        if submitted:
            rows = sb.table('admins').select('*').eq('username', u).execute().data
            if rows and verify_pw(p, rows[0]['password_hash']):
                st.session_state.auth = {'ok': True, 'user': rows[0]['username']}
                st.success('เข้าสู่ระบบสำเร็จ')
                force_rerun()
            else:
                st.error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        st.write(f"✅ Logged in as **{st.session_state.auth['user']}**")
        if st.button('Logout', key='logout_btn'):
            st.session_state.auth = {'ok': False, 'user': None}
            force_rerun()

# =========================
# --------- FILTERS --------
# =========================
hospitals_df = load_df('hospitals')
colF1, colF2, colF3 = st.columns([1,1,2])
with colF1:
    hospital_names = ['(ทั้งหมด)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist())
    selected_hospital = st.selectbox('โรงพยาบาล', hospital_names, key='filter_h')
with colF2:
    today = date.today()
    start_default = today - timedelta(days=30)
    date_range = st.date_input('ช่วงวันที่', value=(start_default, today), key='filter_d')
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = (start_default, today)
with colF3:
    site_filter = st.multiselect('ทีมภูมิภาค (SiteControl)', SITE_CONTROL_CHOICES, key='filter_s')

# Quick-date presets
with st.container():
    cA, cB, cC, cD = st.columns(4)
    if cA.button('7 วันล่าสุด', key='q7'):
        start_date, end_date = (date.today()-timedelta(days=6), date.today())
    if cB.button('30 วันล่าสุด', key='q30'):
        start_date, end_date = (date.today()-timedelta(days=29), date.today())
    if cC.button('เดือนนี้', key='qmon'):
        start_date, end_date = (date.today().replace(day=1), date.today())
    if cD.button('ทั้งหมด', key='qall'):
        tx_all = load_df('transactions')
        if not tx_all.empty:
            tx_all['date'] = pd.to_datetime(tx_all['date']).dt.date
            start_date, end_date = (tx_all['date'].min(), tx_all['date'].max())

# =========================
# ------ DATA & LOGIC ------
# =========================
transactions_df = load_df('transactions')
if not transactions_df.empty:
    transactions_df['date'] = pd.to_datetime(transactions_df['date']).dt.date
    mask = (transactions_df['date'] >= start_date) & (transactions_df['date'] <= end_date)
    transactions_df = transactions_df.loc[mask].copy()

if not hospitals_df.empty and not transactions_df.empty:
    merged = transactions_df.merge(hospitals_df, left_on='hospital_id', right_on='id',
                                   how='left', suffixes=('', '_h'))
else:
    merged = pd.DataFrame(columns=['date','hospital_id','transactions_count','riders_active','name','site_control','province','region','riders_count'])

if selected_hospital != '(ทั้งหมด)':
    merged = merged.loc[merged['name'] == selected_hospital]
if site_filter:
    merged = merged.loc[merged['site_control'].isin(site_filter)]

# =========================
# ---------- KPIs ----------
# =========================
st.markdown('### 📈 ภาพรวม (Overview)')
colK1, colK2, colK3, colK4 = st.columns(4)

total_tx = int(merged['transactions_count'].sum()) if not merged.empty else 0
unique_h = merged['hospital_id'].nunique() if not merged.empty else 0
sum_riders_active = int(merged['riders_active'].sum()) if not merged.empty else 0
sum_riders_capacity = int(merged['riders_count'].sum()) if not merged.empty else 0

with colK1:
    st.markdown(f"<div class='metric-card'><b>จำนวนธุรกรรมทั้งหมด</b><h2>{total_tx:,}</h2></div>", unsafe_allow_html=True)
with colK2:
    st.markdown(f"<div class='metric-card'><b>จำนวนโรงพยาบาล</b><h2>{unique_h}</h2></div>", unsafe_allow_html=True)
with colK3:
    st.markdown(f"<div class='metric-card'><b>Rider Active (รวม)</b><h2>{sum_riders_active:,}</h2></div>", unsafe_allow_html=True)
with colK4:
    st.markdown(f"<div class='metric-card'><b>จำนวน Rider (Capacity)</b><h2>{sum_riders_capacity:,}</h2></div>", unsafe_allow_html=True)

# KPI Alerts
if targets:
    daily_total = merged.groupby('date')['transactions_count'].sum().reset_index()
    if not daily_total.empty:
        latest_row = daily_total.sort_values('date').iloc[-1]
        if latest_row['transactions_count'] < targets.get('daily_transactions', 0):
            st.warning(f"⚠️ ยอดวันนี้ ({int(latest_row['transactions_count']):,}) ต่ำกว่าเป้า {targets.get('daily_transactions'):,}")
            send_line_notify(f"[Telemed Dashboard] ยอดวันนี้ {int(latest_row['transactions_count']):,} ต่ำกว่าเป้า {targets.get('daily_transactions'):,}")

# =========================
# --------- CHARTS ---------
# =========================
if merged.empty:
    st.info('ยังไม่มีข้อมูล ลองเพิ่มจากหน้า Admin ➜ จัดการข้อมูล')
    grp_site = pd.DataFrame(); grp_h = pd.DataFrame(); daily = pd.DataFrame(); monthly = pd.DataFrame()
else:
    st.markdown('#### แยกตามทีมภูมิภาค')
    grp_site = merged.groupby('site_control').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    site_melt = grp_site.melt(id_vars=['site_control','riders_count'], value_vars=['transactions_count','riders_active'],
                              var_name='metric', value_name='value')
    site_melt['metric'] = site_melt['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
    fig1 = px.bar(site_melt, x='site_control', y='value', color='metric', text='value',
                  labels={'site_control':'ทีมภูมิภาค','value':'ค่า','metric':'ตัวชี้วัด'})
    fig1 = prettify_bar(fig1, y_title='จำนวน')
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown('#### ภาพรวมต่อโรงพยาบาล (รวมในช่วงที่เลือก)')
    grp_h = merged.groupby('name').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index().sort_values('transactions_count', ascending=False)
    hosp_melt = grp_h.melt(id_vars=['name','riders_count'], value_vars=['transactions_count','riders_active'],
                           var_name='metric', value_name='value')
    hosp_melt['metric'] = hosp_melt['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
    fig2 = px.bar(hosp_melt, x='name', y='value', color='metric', text='value',
                  labels={'name':'โรงพยาบาล','value':'ค่า','metric':'ตัวชี้วัด'})
    fig2 = prettify_bar(fig2, y_title='จำนวน')
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('#### แนวโน้มรายวัน')
    daily = merged.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
    daily_m = daily.melt(id_vars=['date'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
    daily_m['metric'] = daily_m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
    fig3 = px.bar(daily_m, x='date', y='value', color='metric', text='value',
                  labels={'date':'วันที่','value':'ค่า','metric':'ตัวชี้วัด'})
    fig3 = prettify_bar(fig3, y_title='จำนวน')
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('#### ภาพรวมรายเดือน')
    tmp = merged.copy()
    tmp['month'] = pd.to_datetime(tmp['date']).dt.to_period('M').astype(str)
    monthly = tmp.groupby('month').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
    monthly_m = monthly.melt(id_vars=['month'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
    monthly_m['metric'] = monthly_m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
    fig4 = px.bar(monthly_m, x='month', y='value', color='metric', text='value',
                  labels={'month':'เดือน','value':'ค่า','metric':'ตัวชี้วัด'})
    fig4 = prettify_bar(fig4, y_title='จำนวน')
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('#### ตารางจำนวน Transection แยกตามทีมภูมิภาค')
    st.dataframe(grp_site.rename(columns={'site_control':'ทีมภูมิภาค','transactions_count':'Transactions','riders_active':'Rider Active','riders_count':'Riders ทั้งหมด'}),
                 use_container_width=True)

    st.markdown('##### 📤 ดาวน์โหลดข้อมูล')
    def dl_button(df, label, fname):
        if df is None or df.empty: return
        buff = StringIO(); df.to_csv(buff, index=False)
        st.download_button(label=label, data=buff.getvalue().encode('utf-8-sig'), file_name=fname, mime='text/csv')
    dl_button(merged,   'ดาวน์โหลดข้อมูลที่กรองแล้ว (รายวัน)', 'transactions_filtered.csv')
    dl_button(grp_site, 'ดาวน์โหลดแยกตามทีมภูมิภาค',         'by_sitecontrol.csv')
    dl_button(grp_h,    'ดาวน์โหลดภาพรวมต่อโรงพยาบาล',        'by_hospital.csv')
    dl_button(monthly,  'ดาวน์โหลดภาพรวมรายเดือน',            'by_month.csv')

# =========================
# ------ DRILL-DOWN --------
# =========================
st.markdown('---')
st.markdown('### 🔎 Drill-down รายโรงพยาบาล')
dd_col1, dd_col2 = st.columns([2,1])
with dd_col1:
    dd_hosp = st.selectbox('เลือกโรงพยาบาล', ['(เลือก)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist()), key='dd_h')
with dd_col2:
    show_util = st.checkbox('แสดง Utilization %', value=True, key='dd_util')

if dd_hosp and dd_hosp != '(เลือก)':
    dd_df = merged[merged['name'] == dd_hosp].copy()
    if dd_df.empty and not transactions_df.empty:
        dd_df = transactions_df.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left')
        dd_df = dd_df[dd_df['name'] == dd_hosp].copy()
    if dd_df.empty:
        st.info('ยังไม่มีข้อมูลสำหรับโรงพยาบาลนี้ในช่วงวันที่ที่เลือก')
    else:
        k1, k2, k3 = st.columns(3)
        with k1: st.metric('Transactions (ช่วงที่เลือก)', f"{int(dd_df['transactions_count'].sum()):,}")
        with k2: st.metric('Rider Active รวม', f"{int(dd_df['riders_active'].sum()):,}")
        with k3:
            cap = int(dd_df['riders_count'].sum()) if 'riders_count' in dd_df.columns else 0
            st.metric('Rider Capacity รวม', f"{cap:,}")
        d1 = dd_df.groupby('date').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
        d1m = d1.melt(id_vars=['date'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
        d1m['metric'] = d1m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
        figd = px.bar(d1m, x='date', y='value', color='metric', text='value', labels={'date':'วันที่','value':'ค่า','metric':'ตัวชี้วัด'})
        figd = prettify_bar(figd, y_title='จำนวน')
        st.plotly_chart(figd, use_container_width=True)
        dd_df['month'] = pd.to_datetime(dd_df['date']).astype('datetime64[M]').astype(str)
        m1 = dd_df.groupby('month').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
        m1m = m1.melt(id_vars=['month'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
        m1m['metric'] = m1m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
        figm = px.bar(m1m, x='month', y='value', color='metric', text='value', labels={'month':'เดือน','value':'ค่า','metric':'ตัวชี้วัด'})
        figm = prettify_bar(figm, y_title='จำนวน')
        st.plotly_chart(figm, use_container_width=True)
        if show_util:
            util = dd_df.groupby('date').agg({'riders_active':'sum','riders_count':'sum'}).reset_index()
            util['Utilization %'] = (util['riders_active'] / util['riders_count']).replace([pd.NA, float('inf')], 0)*100
            figu = px.bar(util, x='date', y='Utilization %', text=util['Utilization %'].round(1).astype(str)+'%')
            figu = prettify_bar(figu, y_title='เปอร์เซ็นต์การใช้งาน')
            st.plotly_chart(figu, use_container_width=True)
        sbuff = StringIO(); dd_df.to_csv(sbuff, index=False)
        st.download_button('ดาวน์โหลด CSV ของโรงพยาบาลนี้', data=sbuff.getvalue().encode('utf-8-sig'),
                           file_name=f"{dd_hosp}_filtered.csv", mime='text/csv', key='dd_dl')

# =========================
# ---------- ADMIN ---------
# =========================
st.markdown('---')
st.markdown('## 🛠️ หน้าการจัดการ (Admin / Settings)')
if not st.session_state.auth['ok']:
    st.warning('เข้าสู่ระบบทาง Sidebar เพื่อจัดการข้อมูล')
else:
    tabs = st.tabs(['จัดการโรงพยาบาล', 'จัดการ Transaction', 'จัดการผู้ดูแล', 'ตั้งค่า & ข้อมูลตัวอย่าง'])

    # ----- Manage Hospitals -----
    with tabs[0]:
        st.markdown('### โรงพยาบาล')
        with st.expander('➕ เพิ่ม/แก้ไข โรงพยาบาล'):
            edit_mode = st.checkbox('แก้ไขรายการที่มีอยู่', value=False, key='h_edit')
            if edit_mode and not hospitals_df.empty:
                row = st.selectbox('เลือกโรงพยาบาลที่จะแก้ไข', hospitals_df['name'].tolist(), key='h_pick')
                row_data = hospitals_df[hospitals_df['name']==row].iloc[0].to_dict()
            else:
                row_data = {'id': str(uuid.uuid4())}

            name = st.text_input('ชื่อโรงพยาบาล', value=row_data.get('name', ''), key='h_name')
            provinces = list(TH_PROVINCES.keys())
            province_default = provinces.index(row_data.get('province')) if row_data.get('province') in provinces else 0
            province = st.selectbox('จังหวัด', provinces, index=province_default, key='h_prov')
            region = TH_PROVINCES.get(province, 'ภาคกลาง')
            st.info(f'ภูมิภาค: **{region}** (กำหนดอัตโนมัติจากจังหวัด)')
            site = st.selectbox('SiteControl (ทีม)', SITE_CONTROL_CHOICES,
                                index=SITE_CONTROL_CHOICES.index(row_data.get('site_control')) if row_data.get('site_control') in SITE_CONTROL_CHOICES else 0,
                                key='h_site')
            system = st.selectbox('ระบบที่ใช้', SYSTEM_CHOICES,
                                  index=SYSTEM_CHOICES.index(row_data.get('system_type')) if row_data.get('system_type') in SYSTEM_CHOICES else 0,
                                  key='h_sys')
            service_models = st.multiselect('โมเดลบริการ (เลือกได้หลายอัน)', SERVICE_MODEL_CHOICES,
                                            default=[x for x in (row_data.get('service_models') or []) if x in SERVICE_MODEL_CHOICES], key='h_models')
            riders_count = st.number_input('จำนวน Rider (Capacity)', min_value=0, step=1,
                                           value=int(row_data.get('riders_count',0)), key='h_riders')

            c1, c2 = st.columns(2)
            with c1:
                if st.button('บันทึกโรงพยาบาล', key='h_save'):
                    payload = {
                        'id': row_data.get('id', str(uuid.uuid4())),
                        'name': name.strip(),
                        'province': province,
                        'region': region,
                        'site_control': site,
                        'system_type': system,
                        'service_models': service_models,
                        'riders_count': int(riders_count)
                    }
                    if not name.strip():
                        st.error('กรุณากรอกชื่อโรงพยาบาล')
                    else:
                        if edit_mode:
                            sb.table('hospitals').update(payload).eq('id', row_data['id']).execute()
                            st.success('อัปเดตข้อมูลโรงพยาบาลแล้ว')
                        else:
                            sb.table('hospitals').insert(payload).execute()
                            st.success('เพิ่มโรงพยาบาลแล้ว')
                        reload_all()
            with c2:
                if edit_mode and st.button('🗑️ ลบโรงพยาบาล', key='h_del'):
                    sb.table('hospitals').delete().eq('id', row_data['id']).execute()
                    st.success('ลบแล้ว')
                    reload_all()

        st.markdown('#### รายชื่อโรงพยาบาล')
        st.dataframe(hospitals_df, use_container_width=True)

    # ----- Manage Transactions -----
    def validate_riders(hospital_id: str, riders_active: int) -> bool:
        try:
            rc = int(hospitals_df.loc[hospitals_df['id']==hospital_id, 'riders_count'].iloc[0])
            return riders_active <= rc
        except Exception:
            return True

    with tabs[1]:
        st.markdown('### Transaction ต่อวัน')
        if hospitals_df.empty:
            st.info('ยังไม่มีโรงพยาบาล ใส่ข้อมูลโรงพยาบาลก่อน')
        else:
            hosp_map = {r['name']: r['id'] for _, r in hospitals_df.iterrows()}
            with st.expander('➕ เพิ่ม Transaction รายวัน'):
                hname = st.selectbox('โรงพยาบาล', list(hosp_map.keys()), key='tx_add_h')
                tx_date = st.date_input('วันที่', value=date.today(), key='tx_add_d')
                tx_num = st.number_input('จำนวน Transactions', min_value=0, step=1, key='tx_add_n')
                riders_active = st.number_input('Rider Active', min_value=0, step=1, key='tx_add_ra')
                if st.button('บันทึก Transaction', key='tx_add_btn'):
                    hid = hosp_map[hname]
                    if not validate_riders(hid, int(riders_active)):
                        st.error('Rider Active มากกว่า Capacity ของโรงพยาบาลนี้')
                    else:
                        sb.table('transactions').insert({
                            'id': str(uuid.uuid4()),
                            'hospital_id': hid,
                            'date': tx_date.isoformat(),
                            'transactions_count': int(tx_num),
                            'riders_active': int(riders_active)
                        }).execute()
                        st.success('เพิ่มข้อมูลแล้ว')
                        # แจ้งเตือน Utilization หากเกินเกณฑ์
                        rc = int(hospitals_df.loc[hospitals_df['id']==hid, 'riders_count'].iloc[0])
                        util_pct = (int(riders_active)/rc*100) if rc else 0
                        if util_pct >= targets.get('utilization_alert_pct', 100):
                            send_line_notify(f"[Telemed] Utilization {util_pct:.0f}% เกินเกณฑ์ที่ตั้งไว้ {targets.get('utilization_alert_pct')}% ({hname})")
                        reload_all()

            with st.expander('📥 เพิ่ม Transaction แบบอัปโหลด CSV (คอลัมน์: hospital_name,date,transactions_count,riders_active)'):
                up = st.file_uploader('อัปโหลดไฟล์ .csv', type=['csv'])
                if up is not None:
                    dfu = pd.read_csv(up)
                    cols_lower = [c.lower() for c in dfu.columns]
                    dfu.columns = cols_lower
                    required = {'hospital_name','date','transactions_count','riders_active'}
                    if not required.issubset(set(cols_lower)):
                        st.error('หัวคอลัมน์ต้องมี: hospital_name, date(YYYY-MM-DD), transactions_count, riders_active')
                    else:
                        name_to_id = {r['name']: r['id'] for _, r in hospitals_df.iterrows()}
                        missing = [n for n in dfu['hospital_name'].unique() if n not in name_to_id]
                        if missing:
                            st.warning(f'ไม่พบโรงพยาบาล: {missing}')
                        else:
                            rows = []
                            for _, r in dfu.iterrows():
                                hid = name_to_id[r['hospital_name']]
                                ra = int(r['riders_active'])
                                if not validate_riders(hid, ra):
                                    st.error(f'Rider Active ({ra}) ของแถวโรงพยาบาล {r["hospital_name"]} มากกว่า Capacity')
                                    rows = []
                                    break
                                rows.append({
                                    'id': str(uuid.uuid4()),
                                    'hospital_id': hid,
                                    'date': str(pd.to_datetime(r['date']).date()),
                                    'transactions_count': int(r['transactions_count']),
                                    'riders_active': ra
                                })
                            if rows and st.button('บันทึกข้อมูลจาก CSV ทั้งหมด', key='tx_csv_btn'):
                                sb.table('transactions').insert(rows).execute()
                                st.success(f'เพิ่ม {len(rows)} แถวเรียบร้อย')
                                reload_all()

        st.markdown('#### ตาราง Transaction (แก้ไขได้)')
        raw_tx = load_df('transactions')
        if raw_tx.empty:
            st.info('ยังไม่มี Transaction — เพิ่มด้านบนก่อน')
            tx_view = pd.DataFrame(columns=['id', 'date', 'name', 'transactions_count', 'riders_active', 'hospital_id'])
        else:
            raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
            h_min = hospitals_df[['id', 'name']].rename(columns={'id': 'hospital_id'})
            tx_view = raw_tx.merge(h_min, on='hospital_id', how='left')
            tx_view = tx_view[['id','date','name','transactions_count','riders_active','hospital_id']]

        st.dataframe(tx_view.rename(columns={'name':'โรงพยาบาล','date':'วันที่','transactions_count':'Transactions','riders_active':'Rider Active'}),
                     use_container_width=True)

        with st.expander('✏️ แก้ไข / ลบ Transaction'):
            raw_tx = load_df('transactions')
            if raw_tx.empty:
                st.info('ยังไม่มีข้อมูล')
            else:
                pick_id = st.selectbox('เลือกแถวเพื่อแก้ไข', raw_tx['id'].tolist(), key='tx_pick')
                row = raw_tx[raw_tx['id']==pick_id].iloc[0].to_dict()
                h_id_to_name = {r['id']: r['name'] for _, r in hospitals_df.iterrows()}
                hosp_map = {r['name']: r['id'] for _, r in hospitals_df.iterrows()}
                hsel = st.selectbox('โรงพยาบาล', list(hosp_map.keys()),
                                    index=list(hosp_map.keys()).index(h_id_to_name.get(row['hospital_id'], list(hosp_map.keys())[0])),
                                    key='tx_edit_h')
                dsel = st.date_input('วันที่', value=pd.to_datetime(row['date']).date(), key='tx_edit_d')
                nsel = st.number_input('Transactions', min_value=0, step=1, value=int(row.get('transactions_count',0)), key='tx_edit_n')
                rsel = st.number_input('Rider Active', min_value=0, step=1, value=int(row.get('riders_active',0)), key='tx_edit_ra')
                c3, c4 = st.columns(2)
                with c3:
                    if st.button('บันทึกการแก้ไข', key='btn_tx_save'):
                        hid = hosp_map[hsel]
                        if not validate_riders(hid, int(rsel)):
                            st.error('Rider Active มากกว่า Capacity ของโรงพยาบาลนี้')
                        else:
                            sb.table('transactions').update({
                                'hospital_id': hid,
                                'date': dsel.isoformat(),
                                'transactions_count': int(nsel),
                                'riders_active': int(rsel)
                            }).eq('id', pick_id).execute()
                            st.success('อัปเดตแล้ว')
                            reload_all()
                with c4:
                    if st.button('ลบแถวนี้', key='btn_tx_del'):
                        sb.table('transactions').delete().eq('id', pick_id).execute()
                        st.success('ลบแล้ว')
                        reload_all()

    # ----- Manage Admins -----
    with tabs[2]:
        st.markdown('### ผู้ดูแลระบบ (Admins)')
        admins_df = load_df('admins')
        if 'created_at' in admins_df.columns:
            st.dataframe(admins_df[['username','created_at']], use_container_width=True)
        else:
            st.dataframe(admins_df[['username']], use_container_width=True)

        with st.expander('➕ เพิ่มผู้ดูแลใหม่'):
            nu = st.text_input('Username ใหม่', key='adm_new_u')
            npw = st.text_input('Password', type='password', key='adm_new_p')
            if st.button('เพิ่มผู้ดูแล', key='adm_add'):
                if not nu or not npw:
                    st.error('กรอกให้ครบ')
                elif not admins_df.empty and any(admins_df['username'].str.lower() == nu.lower()):
                    st.error('มี username นี้แล้ว')
                else:
                    sb.table('admins').insert({
                        'id': str(uuid.uuid4()),
                        'username': nu,
                        'password_hash': hash_pw(npw)
                    }).execute()
                    st.success('เพิ่มผู้ดูแลแล้ว')
                    reload_all()

        with st.expander('✏️ เปลี่ยนรหัสผ่าน / ลบผู้ดูแล'):
            if admins_df.empty:
                st.info('ยังไม่มีผู้ดูแล')
            else:
                selu = st.selectbox('เลือกผู้ใช้', admins_df['username'].tolist(), key='adm_pick')
                newpw = st.text_input('รหัสผ่านใหม่', type='password', key='adm_newpw')
                c5, c6 = st.columns(2)
                with c5:
                    if st.button('เปลี่ยนรหัสผ่าน', key='adm_chg'):
                        if not newpw:
                            st.error('กรุณากรอกรหัสผ่านใหม่')
                        else:
                            sb.table('admins').update({'password_hash': hash_pw(newpw)}).eq('username', selu).execute()
                            st.success('เปลี่ยนรหัสผ่านแล้ว')
                            reload_all()
                with c6:
                    if st.button('ลบผู้ดูแล', key='adm_del'):
                        sb.table('admins').delete().eq('username', selu).execute()
                        st.success('ลบแล้ว')
                        reload_all()

    # ----- Settings & Seed -----
    with tabs[3]:
        st.markdown('### ตั้งค่าเป้าหมาย / LINE Notify / ข้อมูลตัวอย่าง')
        tg1, tg2 = st.columns(2)
        with tg1:
            daily_target = st.number_input('เป้ายอดรายวัน (Transactions ต่อวัน)', min_value=0, step=1,
                                           value=int(targets.get('daily_transactions', 50)), key='tgt_daily')
        with tg2:
            util_thresh = st.number_input('แจ้งเตือนเมื่อ Utilization ≥ (%)', min_value=0, max_value=100, step=1,
                                          value=int(targets.get('utilization_alert_pct', 90)), key='tgt_util')
        if st.button('บันทึกเป้าหมาย', key='tgt_save'):
            set_setting('targets', {'daily_transactions': int(daily_target), 'utilization_alert_pct': int(util_thresh)})
            st.success('บันทึกเป้าหมายแล้ว')
            reload_all()

        st.markdown('#### LINE Notify (ไม่บังคับ)')
        en_line = st.checkbox('เปิดใช้ LINE Notify', value=bool(line_cfg.get('enabled')), key='line_en')
        token = st.text_input('LINE Notify Token', value=line_cfg.get('token',''), type='password', key='line_tok')
        if st.button('บันทึกการตั้งค่า LINE', key='line_save'):
            set_setting('line_notify', {'enabled': bool(en_line), 'token': token.strip()})
            st.success('บันทึก LINE Notify แล้ว')
            reload_all()

        st.markdown('#### ข้อมูลตัวอย่าง (Seed/Reset)')
        cseed, creset = st.columns(2)
        with cseed:
            if st.button('เติมข้อมูลตัวอย่าง (5 รพ. x 3 วัน)', key='seed_btn'):
                demo_hosps = [
                    ('รพ.หาดใหญ่', 'สงขลา', 'ภาคใต้', 'ทีมใต้', 'WebPortal', ['Rider','App','Station to Station'], 5),
                    ('รพ.เชียงใหม่','เชียงใหม่','ภาคเหนือ','ทีมเหนือ','HOSxpV4', ['Rider','Station to Station'], 7),
                    ('รพ.ขอนแก่น','ขอนแก่น','ภาคอีสาน','ทีมอีสาน','HOSxpV3', ['App'], 4),
                    ('รพ.ชลบุรี','ชลบุรี','ภาคตะวันออก','ทีมเหนือ','WebPortal', ['Rider','App'], 6),
                    ('รพ.นครศรีธรรมราช','นครศรีธรรมราช','ภาคใต้','ทีมใต้','HOSxpV4', ['Rider','App'], 6),
                ]
                name_to_id = {}
                for n,prov,reg,site,sys,models,rc in demo_hosps:
                    exist = sb.table('hospitals').select('*').eq('name', n).execute().data
                    if exist:
                        hid = exist[0]['id']; name_to_id[n]=hid
                    else:
                        hid = str(uuid.uuid4()); name_to_id[n]=hid
                        sb.table('hospitals').insert({'id':hid,'name':n,'province':prov,'region':reg,'site_control':site,'system_type':sys,'service_models':models,'riders_count':rc}).execute()
                from datetime import date
                days = [date.today()-timedelta(days=2), date.today()-timedelta(days=1), date.today()]
                demo_rows = []
                import random
                for n,hid in name_to_id.items():
                    for d in days:
                        t = random.randint(20,60)
                        ra = random.randint(2,7)
                        demo_rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':d.isoformat(),'transactions_count':t,'riders_active':ra})
                if demo_rows:
                    sb.table('transactions').insert(demo_rows).execute()
                st.success('เติมข้อมูลตัวอย่างเรียบร้อย')
                reload_all()
        with creset:
            if st.button('ลบข้อมูลตัวอย่าง (5 รพ.ข้างต้น + tx)', key='reset_btn'):
                target_names = ['รพ.หาดใหญ่','รพ.เชียงใหม่','รพ.ขอนแก่น','รพ.ชลบุรี','รพ.นครศรีธรรมราช']
                ids = sb.table('hospitals').select('id').in_('name', target_names).execute().data
                ids = [r['id'] for r in ids]
                if ids:
                    for hid in ids:
                        sb.table('transactions').delete().eq('hospital_id', hid).execute()
                    sb.table('hospitals').delete().in_('id', ids).execute()
                st.success('ลบข้อมูลตัวอย่างแล้ว')
                reload_all()

st.markdown('---')
st.caption('Telemedicine Dashboard • pastel/dark • Streamlit + Supabase')

# --------------------------- SCHEMA (for reference) ---------------------------
SCHEMA_SQL = r'''
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

create index if not exists idx_tx_hospital_date on public.transactions(hospital_id, date);
create index if not exists idx_hosp_site on public.hospitals(site_control);

-- Settings (key-value JSON)
create table if not exists public.settings (
  key text primary key,
  value jsonb not null,
  updated_at timestamp with time zone default now()
);

alter table public.admins enable row level security;
alter table public.hospitals enable row level security;
alter table public.transactions enable row level security;
alter table public.settings enable row level security;

drop policy if exists p_admins_all on public.admins;
drop policy if exists p_hosp_all on public.hospitals;
drop policy if exists p_tx_all on public.transactions;
drop policy if exists p_settings_all on public.settings;

create policy p_admins_all on public.admins for all using (true) with check (true);
create policy p_hosp_all on public.hospitals for all using (true) with check (true);
create policy p_tx_all on public.transactions for all using (true) with check (true);
create policy p_settings_all on public.settings for all using (true) with check (true);
'''
