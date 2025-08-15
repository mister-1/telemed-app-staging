# Telemedicine Transactions Dashboard — Upgraded v2 (Streamlit + Supabase)
# - Pie: แยกตามทีมภูมิภาค
# - Horizontal bar + scroll + หน้าขยายเต็มจอ
# - Daily trend: line + แกน X เป็น "วันจันทร์ 18/8/25"
# - ตารางทีมภูมิภาคมีสีสัน
# - แก้ Drill-down ให้ robust (เดือน/NaN)
# - ปุ่ม 🖨️ บันทึกหน้าเป็น PDF/ภาพ (print ทั้งหน้า)
# - คงหน้า Admin ครบ: Hospitals / Transactions / Admins / Settings+Seed

import os, uuid, json, bcrypt, requests
import pandas as pd
import plotly.express as px
from io import StringIO
from datetime import date, timedelta
from typing import Dict, Any

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ============= THEME =============
PASTEL_BG = '#F7F8FB'; PASTEL_CARD = '#FFFFFF'
PASTEL_ACCENT = '#A7C7E7'; PASTEL_ACCENT_3 = '#B6E2D3'
PASTEL_TEXT = '#3E4B6D'
DARK_BG = '#0F172A'; DARK_CARD = '#111827'; DARK_TEXT = '#E5E7EB'

st.set_page_config(page_title='Telemedicine Transactions', page_icon='📊', layout='wide')

# ========== ENV & SUPABASE =========
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error('❌ Missing SUPABASE_URL or SUPABASE_KEY environment variable.')
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb: Client = get_client()

# ============= CONSTANTS ===========
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

# ============ SETTINGS (KV) ============
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

# ============ HELPERS ============
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

# ============ THEME / CSS ============
if 'ui' not in st.session_state: st.session_state['ui'] = {'dark': False}
with st.sidebar:
    st.markdown('### 🎨 Appearance')
    st.session_state.ui['dark'] = st.checkbox('โหมดมืด (Dark mode)', value=st.session_state.ui['dark'])

BG, CARD, TEXT = (DARK_BG, DARK_CARD, DARK_TEXT) if st.session_state.ui['dark'] else (PASTEL_BG, PASTEL_CARD, PASTEL_TEXT)

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  :root {{ --bg:{BG}; --card:{CARD}; --text:{TEXT}; }}
  html, body, [class*='st-'] {{ font-family:'Kanit',system-ui,-apple-system,Segoe UI,sans-serif; }}
  .stApp {{ background-color:var(--bg); }}
  .metric-card {{ background:var(--card); color:var(--text); padding:1rem; border-radius:16px; box-shadow:0 1px 8px rgba(0,0,0,.05);}}
</style>
""", unsafe_allow_html=True)

px.defaults.template = 'plotly_white'
px.defaults.color_discrete_sequence = ['#A7C7E7','#F8C8DC','#B6E2D3','#FDE2B3','#EAD7F7','#CDE5F0','#FFD6E8']

def prettify_bar(fig, y_title=''):
    fig.update_traces(texttemplate='%{text:,}', textposition='outside', cliponaxis=False,
                      hovertemplate='<b>%{x}</b><br>ค่า: %{y:,}<extra></extra>')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', yaxis_title=y_title,
                      margin=dict(t=30,r=20,b=40,l=50))
    return fig

# ============ AUTH ============
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

# ============ FILTERS ============
hospitals_df = load_df('hospitals')
colF1, colF2, colF3, colF4 = st.columns([1,1,2,1])
with colF1:
    hosp_names = ['(ทั้งหมด)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist())
    selected_hospital = st.selectbox('โรงพยาบาล', hosp_names)
with colF2:
    today = date.today(); start_default = today - timedelta(days=30)
    date_range = st.date_input('ช่วงวันที่', value=(start_default, today))
    start_date, end_date = (date_range if isinstance(date_range, tuple) else (start_default, today))
with colF3:
    site_filter = st.multiselect('ทีมภูมิภาค (SiteControl)', SITE_CONTROL_CHOICES)
with colF4:
    components.html('<button onclick="parent.window.print()">🖨️ บันทึกหน้าเป็น PDF/ภาพ</button>', height=50)

# ============ DATA ============
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

# ============ KPIs ============
st.markdown('### 📈 ภาพรวม (Overview)')
colK1, colK2, colK3, colK4 = st.columns(4)
total_tx = int(merged['transactions_count'].sum()) if not merged.empty else 0
unique_h = merged['hospital_id'].nunique() if not merged.empty else 0
sum_riders_active = int(merged['riders_active'].sum()) if not merged.empty else 0
sum_riders_capacity = int(merged['riders_count'].fillna(0).sum()) if not merged.empty else 0
with colK1: st.markdown(f"<div class='metric-card'><b>จำนวนธุรกรรมทั้งหมด</b><h2>{total_tx:,}</h2></div>", unsafe_allow_html=True)
with colK2: st.markdown(f"<div class='metric-card'><b>จำนวนโรงพยาบาล</b><h2>{unique_h}</h2></div>", unsafe_allow_html=True)
with colK3: st.markdown(f"<div class='metric-card'><b>Rider Active (รวม)</b><h2>{sum_riders_active:,}</h2></div>", unsafe_allow_html=True)
with colK4: st.markdown(f"<div class='metric-card'><b>จำนวน Rider (Capacity)</b><h2>{sum_riders_capacity:,}</h2></div>", unsafe_allow_html=True)

# ============ CHARTS ============
if merged.empty:
    st.info('ยังไม่มีข้อมูล ลองเพิ่มจากหน้า Admin ➜ จัดการข้อมูล')
else:
    # --- Pie by SiteControl ---
    st.markdown('#### แยกตามทีมภูมิภาค (กราฟวงกลม)')
    grp_site = merged.groupby('site_control').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    fig_pie = px.pie(grp_site, names='site_control', values='transactions_count',
                     hole=0.3, labels={'site_control':'ทีมภูมิภาค','transactions_count':'Transactions'})
    fig_pie.update_traces(textposition='inside', textinfo='label+percent+value')
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Hospital overview horizontal bar + scroll + full screen ---
    st.markdown('#### ภาพรวมต่อโรงพยาบาล (แนวนอน)')
    grp_h = merged.groupby('name').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index().sort_values('transactions_count', ascending=True)
    fig_h = px.bar(grp_h, y='name', x='transactions_count', orientation='h', text='transactions_count',
                   labels={'name':'โรงพยาบาล','transactions_count':'Transactions'})
    fig_h.update_traces(textposition='outside')
    fig_h.update_layout(height=max(500, 30*len(grp_h)+200), margin=dict(l=120,r=40,t=30,b=40))
    st.markdown("[🔎 ขยายเต็มจอ](?view=hospitals)", unsafe_allow_html=True)
    components.html(fig_h.to_html(include_plotlyjs='cdn', full_html=False), height=550, scrolling=True)

    # --- Daily trend line with Thai weekday label ---
    st.markdown('#### แนวโน้มรายวัน (กราฟเส้น)')
    daily = merged.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index().sort_values('date')
    if not daily.empty:
        th_weekdays = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
        def make_label(d):
            dts = pd.to_datetime(d)
            return f"{th_weekdays[dts.dayofweek]} {dts.day}/{dts.month}/{str(dts.year)[-2:]}"
        daily['label'] = daily['date'].apply(make_label)
        dm = daily.melt(id_vars=['date','label'], value_vars=['transactions_count','riders_active'],
                        var_name='metric', value_name='value')
        dm['metric'] = dm['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
        fig_line = px.line(dm, x='label', y='value', color='metric', markers=True,
                           labels={'label':'วัน/เดือน/ปี','value':'ค่า','metric':'ตัวชี้วัด'})
        fig_line.update_traces(mode='lines+markers', hovertemplate='<b>%{x}</b><br>ค่า: %{y:,}<extra></extra>')
        fig_line.update_layout(xaxis_tickangle=-45, margin=dict(t=30,r=20,b=80,l=50))
        st.plotly_chart(fig_line, use_container_width=True)

    # --- Colored table by SiteControl ---
    st.markdown('#### ตารางจำนวน Transection แยกตามทีมภูมิภาค (มีสีสัน)')
    tbl = grp_site.rename(columns={'site_control':'ทีมภูมิภาค','transactions_count':'Transactions','riders_active':'Rider Active','riders_count':'Riders ทั้งหมด'})
    try:
        st.table(tbl.style.background_gradient(cmap='YlGnBu', subset=['Transactions','Rider Active','Riders ทั้งหมด']))
    except Exception:
        st.dataframe(tbl, use_container_width=True)

# ============ FULLSCREEN VIEW ============
qp = st.experimental_get_query_params()
view_param = (qp.get('view', [None])[0] if isinstance(qp, dict) else None)
if view_param == 'hospitals' and not merged.empty:
    st.markdown('### ภาพรวมต่อโรงพยาบาล (เต็มจอ)')
    grp_h2 = merged.groupby('name').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index().sort_values('transactions_count', ascending=True)
    fig_full = px.bar(grp_h2, y='name', x='transactions_count', orientation='h', text='transactions_count',
                      labels={'name':'โรงพยาบาล','transactions_count':'Transactions'})
    fig_full.update_traces(textposition='outside')
    fig_full.update_layout(height=max(700, 35*len(grp_h2)+200), margin=dict(l=160,r=40,t=30,b=40))
    st.plotly_chart(fig_full, use_container_width=True)

# ============ DRILL-DOWN ============
st.markdown('---'); st.markdown('### 🔎 Drill-down รายโรงพยาบาล')
dd_col1, dd_col2 = st.columns([2,1])
with dd_col1:
    dd_hosp = st.selectbox('เลือกโรงพยาบาล', ['(เลือก)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist()))
with dd_col2:
    show_util = st.checkbox('แสดง Utilization %', value=True)

if dd_hosp and dd_hosp != '(เลือก)':
    dd_df = merged[merged['name'] == dd_hosp].copy()
    if dd_df.empty and not transactions_df.empty:
        dd_df = transactions_df.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left')
        dd_df = dd_df[dd_df['name'] == dd_hosp].copy()
    if dd_df.empty:
        st.info('ยังไม่มีข้อมูลสำหรับโรงพยาบาลนี้ในช่วงวันที่ที่เลือก')
    else:
        dd_df['riders_count'] = dd_df['riders_count'].fillna(0).astype(int)
        k1, k2, k3 = st.columns(3)
        with k1: st.metric('Transactions (ช่วงที่เลือก)', f"{int(dd_df['transactions_count'].sum()):,}")
        with k2: st.metric('Rider Active รวม', f"{int(dd_df['riders_active'].sum()):,}")
        with k3: st.metric('Rider Capacity รวม', f"{int(dd_df['riders_count'].sum()):,}")

        d1 = dd_df.groupby('date').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
        d1m = d1.melt(id_vars=['date'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
        d1m['metric'] = d1m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
        figd = px.bar(d1m, x='date', y='value', color='metric', text='value', labels={'date':'วันที่','value':'ค่า','metric':'ตัวชี้วัด'})
        figd = prettify_bar(figd, y_title='จำนวน'); st.plotly_chart(figd, use_container_width=True)

        dd_df['month'] = pd.to_datetime(dd_df['date']).dt.to_period('M').astype(str)  # FIX
        m1 = dd_df.groupby('month').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index()
        m1m = m1.melt(id_vars=['month'], value_vars=['transactions_count','riders_active'], var_name='metric', value_name='value')
        m1m['metric'] = m1m['metric'].map({'transactions_count':'Transactions','riders_active':'Rider Active'})
        figm = px.bar(m1m, x='month', y='value', color='metric', text='value', labels={'month':'เดือน','value':'ค่า','metric':'ตัวชี้วัด'})
        figm = prettify_bar(figm, y_title='จำนวน'); st.plotly_chart(figm, use_container_width=True)

        if show_util:
            util = dd_df.groupby('date').agg({'riders_active':'sum','riders_count':'sum'}).reset_index()
            util['Utilization %'] = (util['riders_active'] / util['riders_count']).replace([pd.NA, float('inf')], 0)*100
            figu = px.line(util, x='date', y='Utilization %', markers=True)
            figu.update_layout(yaxis_title='เปอร์เซ็นต์การใช้งาน'); st.plotly_chart(figu, use_container_width=True)

# ================== ADMIN / SETTINGS / SEED ==================
st.markdown('---'); st.markdown('## 🛠️ หน้าการจัดการ (Admin / Settings)')
if not st.session_state.auth['ok']:
    st.warning('เข้าสู่ระบบทาง Sidebar เพื่อจัดการข้อมูล')
else:
    tabs = st.tabs(['จัดการโรงพยาบาล', 'จัดการ Transaction', 'จัดการผู้ดูแล', 'ตั้งค่า & ข้อมูลตัวอย่าง'])

    # ----- Hospitals -----
    with tabs[0]:
        st.markdown('### โรงพยาบาล')
        with st.expander('➕ เพิ่ม/แก้ไข โรงพยาบาล'):
            edit_mode = st.checkbox('แก้ไขรายการที่มีอยู่', value=False)
            if edit_mode and not hospitals_df.empty:
                row = st.selectbox('เลือกโรงพยาบาลที่จะแก้ไข', hospitals_df['name'].tolist())
                row_data = hospitals_df[hospitals_df['name']==row].iloc[0].to_dict()
            else:
                row_data = {'id': str(uuid.uuid4())}

            name = st.text_input('ชื่อโรงพยาบาล', value=row_data.get('name',''))
            provinces = list(TH_PROVINCES.keys())
            province_default = provinces.index(row_data.get('province')) if row_data.get('province') in provinces else 0
            province = st.selectbox('จังหวัด', provinces, index=province_default)
            region = TH_PROVINCES.get(province, 'ภาคกลาง')
            st.info(f'ภูมิภาค: **{region}** (จากจังหวัด)')
            site = st.selectbox('SiteControl (ทีม)', SITE_CONTROL_CHOICES,
                                index=SITE_CONTROL_CHOICES.index(row_data.get('site_control')) if row_data.get('site_control') in SITE_CONTROL_CHOICES else 0)
            system = st.selectbox('ระบบที่ใช้', SYSTEM_CHOICES,
                                  index=SYSTEM_CHOICES.index(row_data.get('system_type')) if row_data.get('system_type') in SYSTEM_CHOICES else 0)
            service_models = st.multiselect('โมเดลบริการ (เลือกได้หลายอัน)', SERVICE_MODEL_CHOICES,
                                            default=[x for x in (row_data.get('service_models') or []) if x in SERVICE_MODEL_CHOICES])
            riders_count = st.number_input('จำนวน Rider (Capacity)', min_value=0, step=1,
                                           value=int(row_data.get('riders_count',0)))

            c1, c2 = st.columns(2)
            with c1:
                if st.button('บันทึกโรงพยาบาล'):
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
                if edit_mode and st.button('🗑️ ลบโรงพยาบาล'):
                    sb.table('hospitals').delete().eq('id', row_data['id']).execute()
                    st.success('ลบแล้ว'); reload_all()

        st.markdown('#### รายชื่อโรงพยาบาล')
        st.dataframe(hospitals_df, use_container_width=True)

    # ----- Transactions -----
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
                hname = st.selectbox('โรงพยาบาล', list(hosp_map.keys()))
                tx_date = st.date_input('วันที่', value=date.today())
                tx_num = st.number_input('จำนวน Transactions', min_value=0, step=1)
                riders_active = st.number_input('Rider Active', min_value=0, step=1)
                if st.button('บันทึก Transaction'):
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
                        rc = int(hospitals_df.loc[hospitals_df['id']==hid, 'riders_count'].iloc[0])
                        util_pct = (int(riders_active)/rc*100) if rc else 0
                        if util_pct >= targets.get('utilization_alert_pct', 100):
                            send_line_notify(f"[Telemed] Utilization {util_pct:.0f}% ≥ {targets.get('utilization_alert_pct')}% ({hname})")
                        reload_all()

            with st.expander('📥 เพิ่ม Transaction แบบอัปโหลด CSV (คอลัมน์: hospital_name,date,transactions_count,riders_active)'):
                up = st.file_uploader('อัปโหลดไฟล์ .csv', type=['csv'])
                if up is not None:
                    dfu = pd.read_csv(up)
                    dfu.columns = [c.lower() for c in dfu.columns]
                    required = {'hospital_name','date','transactions_count','riders_active'}
                    if not required.issubset(set(dfu.columns)):
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
                                    st.error(f'Rider Active ({ra}) ของ {r["hospital_name"]} มากกว่า Capacity'); rows=[]; break
                                rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':str(pd.to_datetime(r['date']).date()),
                                             'transactions_count':int(r['transactions_count']),'riders_active':ra})
                            if rows and st.button('บันทึกข้อมูลจาก CSV ทั้งหมด'):
                                sb.table('transactions').insert(rows).execute()
                                st.success(f'เพิ่ม {len(rows)} แถวเรียบร้อย'); reload_all()

        st.markdown('#### ตาราง Transaction (แก้ไขได้)')
        raw_tx = load_df('transactions')
        if raw_tx.empty:
            st.info('ยังไม่มี Transaction — เพิ่มด้านบนก่อน')
            tx_view = pd.DataFrame(columns=['id','date','name','transactions_count','riders_active','hospital_id'])
        else:
            raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
            h_min = hospitals_df[['id','name']].rename(columns={'id':'hospital_id'})
            tx_view = raw_tx.merge(h_min, on='hospital_id', how='left')
            tx_view = tx_view[['id','date','name','transactions_count','riders_active','hospital_id']]

        st.dataframe(tx_view.rename(columns={'name':'โรงพยาบาล','date':'วันที่','transactions_count':'Transactions','riders_active':'Rider Active'}),
                     use_container_width=True)

        with st.expander('✏️ แก้ไข / ลบ Transaction'):
            raw_tx = load_df('transactions')
            if raw_tx.empty:
                st.info('ยังไม่มีข้อมูล')
            else:
                pick_id = st.selectbox('เลือกแถวเพื่อแก้ไข', raw_tx['id'].tolist())
                row = raw_tx[raw_tx['id']==pick_id].iloc[0].to_dict()
                h_id_to_name = {r['id']: r['name'] for _, r in hospitals_df.iterrows()}
                hosp_map = {r['name']: r['id'] for _, r in hospitals_df.iterrows()}
                hsel = st.selectbox('โรงพยาบาล', list(hosp_map.keys()),
                                    index=list(hosp_map.keys()).index(h_id_to_name.get(row['hospital_id'], list(hosp_map.keys())[0])))
                dsel = st.date_input('วันที่', value=pd.to_datetime(row['date']).date())
                nsel = st.number_input('Transactions', min_value=0, step=1, value=int(row.get('transactions_count',0)))
                rsel = st.number_input('Rider Active', min_value=0, step=1, value=int(row.get('riders_active',0)))
                c3, c4 = st.columns(2)
                with c3:
                    if st.button('บันทึกการแก้ไข'):
                        hid = hosp_map[hsel]
                        if not validate_riders(hid, int(rsel)):
                            st.error('Rider Active มากกว่า Capacity')
                        else:
                            sb.table('transactions').update({'hospital_id':hid,'date':dsel.isoformat(),
                                                             'transactions_count':int(nsel),'riders_active':int(rsel)}).eq('id', pick_id).execute()
                            st.success('อัปเดตแล้ว'); reload_all()
                with c4:
                    if st.button('ลบแถวนี้'):
                        sb.table('transactions').delete().eq('id', pick_id).execute()
                        st.success('ลบแล้ว'); reload_all()

    # ----- Admins -----
    with tabs[2]:
        st.markdown('### ผู้ดูแลระบบ (Admins)')
        admins_df = load_df('admins')
        if 'created_at' in admins_df.columns:
            st.dataframe(admins_df[['username','created_at']], use_container_width=True)
        else:
            st.dataframe(admins_df[['username']], use_container_width=True)

        with st.expander('➕ เพิ่มผู้ดูแลใหม่'):
            nu = st.text_input('Username ใหม่')
            npw = st.text_input('Password', type='password')
            if st.button('เพิ่มผู้ดูแล'):
                if not nu or not npw:
                    st.error('กรอกให้ครบ')
                elif not admins_df.empty and any(admins_df['username'].str.lower() == nu.lower()):
                    st.error('มี username นี้แล้ว')
                else:
                    sb.table('admins').insert({'id':str(uuid.uuid4()),'username':nu,'password_hash':hash_pw(npw)}).execute()
                    st.success('เพิ่มผู้ดูแลแล้ว'); reload_all()

        with st.expander('✏️ เปลี่ยนรหัสผ่าน / ลบผู้ดูแล'):
            if admins_df.empty:
                st.info('ยังไม่มีผู้ดูแล')
            else:
                selu = st.selectbox('เลือกผู้ใช้', admins_df['username'].tolist())
                newpw = st.text_input('รหัสผ่านใหม่', type='password')
                c5, c6 = st.columns(2)
                with c5:
                    if st.button('เปลี่ยนรหัสผ่าน'):
                        if not newpw: st.error('กรุณากรอกรหัสผ่านใหม่')
                        else:
                            sb.table('admins').update({'password_hash':hash_pw(newpw)}).eq('username', selu).execute()
                            st.success('เปลี่ยนรหัสผ่านแล้ว'); reload_all()
                with c6:
                    if st.button('ลบผู้ดูแล'):
                        sb.table('admins').delete().eq('username', selu).execute()
                        st.success('ลบแล้ว'); reload_all()

    # ----- Settings & Seed -----
    with tabs[3]:
        st.markdown('### ตั้งค่าเป้าหมาย / LINE Notify / ข้อมูลตัวอย่าง')
        tg1, tg2 = st.columns(2)
        with tg1:
            daily_target = st.number_input('เป้ายอดรายวัน (Transactions ต่อวัน)', min_value=0, step=1,
                                           value=int(targets.get('daily_transactions', 50)))
        with tg2:
            util_thresh = st.number_input('แจ้งเตือนเมื่อ Utilization ≥ (%)', min_value=0, max_value=100, step=1,
                                          value=int(targets.get('utilization_alert_pct', 90)))
        if st.button('บันทึกเป้าหมาย'):
            set_setting('targets', {'daily_transactions': int(daily_target), 'utilization_alert_pct': int(util_thresh)})
            st.success('บันทึกเป้าหมายแล้ว'); reload_all()

        st.markdown('#### LINE Notify (ไม่บังคับ)')
        en_line = st.checkbox('เปิดใช้ LINE Notify', value=bool(line_cfg.get('enabled')))
        token = st.text_input('LINE Notify Token', value=line_cfg.get('token',''), type='password')
        if st.button('บันทึกการตั้งค่า LINE'):
            set_setting('line_notify', {'enabled': bool(en_line), 'token': token.strip()})
            st.success('บันทึก LINE Notify แล้ว'); reload_all()

        st.markdown('#### ข้อมูลตัวอย่าง (Seed/Reset)')
        cseed, creset = st.columns(2)
        with cseed:
            if st.button('เติมข้อมูลตัวอย่าง (5 รพ. x 3 วัน)'):
                demo_hosps = [
                    ('รพ.หาดใหญ่','สงขลา','ภาคใต้','ทีมใต้','WebPortal',['Rider','App','Station to Station'],5),
                    ('รพ.เชียงใหม่','เชียงใหม่','ภาคเหนือ','ทีมเหนือ','HOSxpV4',['Rider','Station to Station'],7),
                    ('รพ.ขอนแก่น','ขอนแก่น','ภาคอีสาน','ทีมอีสาน','HOSxpV3',['App'],4),
                    ('รพ.ชลบุรี','ชลบุรี','ภาคตะวันออก','ทีมเหนือ','WebPortal',['Rider','App'],6),
                    ('รพ.นครศรีธรรมราช','นครศรีธรรมราช','ภาคใต้','ทีมใต้','HOSxpV4',['Rider','App'],6),
                ]
                name_to_id = {}
                for n,prov,reg,site,sys,models,rc in demo_hosps:
                    exist = sb.table('hospitals').select('*').eq('name', n).execute().data
                    if exist: hid = exist[0]['id']
                    else:
                        hid = str(uuid.uuid4())
                        sb.table('hospitals').insert({'id':hid,'name':n,'province':prov,'region':reg,'site_control':site,'system_type':sys,'service_models':models,'riders_count':rc}).execute()
                    name_to_id[n]=hid
                days = [date.today()-timedelta(days=2), date.today()-timedelta(days=1), date.today()]
                demo_rows = []
                import random
                for n,hid in name_to_id.items():
                    for d in days:
                        demo_rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':d.isoformat(),
                                          'transactions_count':random.randint(20,60),'riders_active':random.randint(2,7)})
                if demo_rows: sb.table('transactions').insert(demo_rows).execute()
                st.success('เติมข้อมูลตัวอย่างเรียบร้อย'); reload_all()
        with creset:
            if st.button('ลบข้อมูลตัวอย่าง'):
                target_names = ['รพ.หาดใหญ่','รพ.เชียงใหม่','รพ.ขอนแก่น','รพ.ชลบุรี','รพ.นครศรีธรรมราช']
                ids = sb.table('hospitals').select('id').in_('name', target_names).execute().data
                ids = [r['id'] for r in ids]
                if ids:
                    for hid in ids:
                        sb.table('transactions').delete().eq('hospital_id', hid).execute()
                    sb.table('hospitals').delete().in_('id', ids).execute()
                st.success('ลบข้อมูลตัวอย่างแล้ว'); reload_all()

st.markdown('---')
st.caption('Telemedicine Dashboard • pastel/dark • Streamlit + Supabase')
