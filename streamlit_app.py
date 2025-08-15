# DashBoard Telemedicine — v3.8
# - Fix "Go to edit" after duplicate: force widget defaults in Edit expander + close Add expander
# - Add "Cancel" to Add form (close Add expander and rerun)
# - Rename chart title & set Y-axis: ภาพรวมต่อโรงพยาบาล + yaxis_title='ชื่อโรงพยาบาล'
# - Keep all v3.7 features (placeholders, tidy filters, etc.)

import os, uuid, json, bcrypt, requests, random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from typing import List
import streamlit as st
from supabase import create_client, Client

APP_VERSION = "v3.8"

# ---------------- App / Theme ----------------
st.set_page_config(page_title="DashBoard Telemedicine", page_icon="📊", layout="wide")

PALETTE_PASTEL = ["#A7C7E7","#F8C8DC","#B6E2D3","#FDE2B3","#EAD7F7","#CDE5F0",
                  "#FFD6E8","#C8E6C9","#FFF3B0","#D7E3FC","#F2D7EE","#B8F1ED"]
PALETTE_DARK   = ["#60A5FA","#F472B6","#34D399","#FBBF24","#C084FC","#67E8F9",
                  "#FCA5A5","#86EFAC","#FDE68A","#A5B4FC","#F5D0FE","#99F6E4"]

SITE_CONTROL_CHOICES = ['ทีมใต้', 'ทีมเหนือ', 'ทีมอีสาน']
SYSTEM_CHOICES = ['HOSxpV4', 'HOSxpV3', 'WebPortal']
SERVICE_MODEL_CHOICES = ['Rider', 'App', 'Station to Station']

TH_PROVINCES = {
  'กรุงเทพมหานคร':'ภาคกลาง','เชียงใหม่':'ภาคเหนือ','ขอนแก่น':'ภาคอีสาน','ชลบุรี':'ภาคตะวันออก',
  'สงขลา':'ภาคใต้','นครศรีธรรมราช':'ภาคใต้','นครราชสีมา':'ภาคอีสาน','ภูเก็ต':'ภาคใต้','ระยอง':'ภาคตะวันออก',
  'ลำปาง':'ภาคเหนือ','อุดรธานี':'ภาคอีสาน','สุราษฎร์ธานี':'ภาคใต้','บุรีรัมย์':'ภาคอีสาน'
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

# ---------------- Helpers ----------------
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
    return [c for c in cols if c in df.columns]

def rerun():
    try: st.rerun()
    except Exception: pass

def ensure_default_admin():
    try:
        rows = sb.table('admins').select('username').eq('username','telemed').execute().data
        if not rows:
            sb.table('admins').insert({'id':str(uuid.uuid4()),
                                       'username':'telemed',
                                       'password_hash':hash_pw('Telemed@DHI')}).execute()
    except Exception:
        pass
ensure_default_admin()

# UI State
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

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  .stApp {{ font-family:'Kanit',system-ui; }}
  .kpi-card {{
    background:{CARD_BG}; border:1px solid {CARD_BORDER}; color:{CARD_TXT};
    border-radius:16px; padding:1rem 1.2rem; box-shadow:0 6px 18px rgba(0,0,0,.08);
  }}
  .kpi-title {{ font-weight:600; opacity:.85; }}
  .kpi-value {{ font-size:1.8rem; font-weight:700; margin-top:.25rem; }}
  .section-title {{ font-weight:600; margin-bottom: .25rem; }}
</style>
""", unsafe_allow_html=True)

# ---------------- Auth ----------------
if 'auth' not in st.session_state: st.session_state['auth']={'ok':False,'user':None}
with st.sidebar:
    st.markdown('## 🔐 Admin')
    if not st.session_state.auth['ok']:
        with st.form('login'):
            u = st.text_input('Username'); p = st.text_input('Password', type='password')
            rows = load_df('admins')
            if st.form_submit_button('Login'):
                row = rows[rows['username']==u] if 'username' in rows.columns else pd.DataFrame()
                if not row.empty and verify_pw(p, row.iloc[0]['password_hash']):
                    st.session_state.auth={'ok':True,'user':u}; rerun()
                else:
                    st.error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        st.write(f"✅ {st.session_state.auth['user']}")
        if st.button('Logout'): st.session_state.auth={'ok':False,'user':None}; rerun()

# ---------------- Router ----------------
page = st.query_params.get('page','dashboard')
with st.sidebar:
    nav = st.radio('ไปที่', ['dashboard','admin'], index=0 if page=='dashboard' else 1, horizontal=True)
    if nav != page:
        st.query_params.update({'page':nav}); rerun()

# ---------------- Thai date format ----------------
TH_MONTHS = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
def th_date(d: date) -> str:
    return f"{d.day} {TH_MONTHS[d.month-1]} {d.year+543}"

# ---------- Dropdown-style multiselect (no widget-state writes) ----------
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
def render_chart_placeholder(title:str):
    fig = go.Figure()
    fig.add_annotation(text="ไม่มีข้อมูล", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    fig.update_layout(height=360, margin=dict(l=0,r=0,t=10,b=10))
    st.markdown(title)
    st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})

def render_dashboard():
    st.markdown("# DashBoard Telemedicine")

    hospitals_df = load_df('hospitals')
    tx_df = load_df('transactions')

    # ---------- Filters area ----------
    st.markdown("### 🎛️ ตัวกรอง")
    if 'date_range' not in st.session_state:
        today = date.today()
        st.session_state['date_range'] = (today, today)

    c_row1_left, c_row1_mid, c_row1_right = st.columns([1.6, 1.2, 1.2])
    with c_row1_left:
        today = date.today()
        dr = st.date_input('📅 ช่วงวันที่', value=st.session_state['date_range'])
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
            st.session_state['hosp_sel'] = []
            st.session_state['site_filter'] = []
            rerun()

    c_row2_left, c_row2_right = st.columns([1.6,1.2])
    with c_row2_left:
        all_names = sorted(hospitals_df['name'].dropna().unique().tolist()) if 'name' in hospitals_df.columns else []
        selected_hospitals = multiselect_dropdown("🏥 โรงพยาบาล", all_names, "hosp_sel", default_all=True)
    with c_row2_right:
        selected_sites = multiselect_dropdown("🧭 ทีมภูมิภาค", SITE_CONTROL_CHOICES, "site_filter", default_all=True)

    # ---- Capture whole page ----
    cap_col = st.columns([1,3,1])[0]
    with cap_col:
        if st.button('📸 แคปหน้าจอ'):
            st.components.v1.html("""
            <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
            <script>
            (async () => {
              const el = document.body; await new Promise(r=>setTimeout(r,350));
              html2canvas(el,{useCORS:true,windowWidth:document.body.scrollWidth,
                              windowHeight:document.body.scrollHeight,scale:2})
              .then(cv=>{const a=document.createElement('a');a.download='telemed-dashboard.png';
                         a.href=cv.toDataURL('image/png');a.click();});
            })();
            </script>
            """, height=0)

    start_date, end_date = st.session_state['date_range']

    # ---- Merge & filter ----
    if not tx_df.empty:
        tx_df['date'] = pd.to_datetime(tx_df['date']).dt.date
        tx_df = tx_df[(tx_df['date']>=start_date)&(tx_df['date']<=end_date)]
    if not tx_df.empty and not hospitals_df.empty:
        df = tx_df.merge(hospitals_df, left_on='hospital_id', right_on='id', how='left', suffixes=('','_h'))
    else:
        df = pd.DataFrame(columns=['date','hospital_id','transactions_count','riders_active','name','site_control','riders_count'])

    if st.session_state.get('site_filter'): df = df[df['site_control'].isin(st.session_state['site_filter'])]
    if st.session_state.get('hosp_sel'): df = df[df['name'].isin(st.session_state['hosp_sel'])]

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
    if not df.empty:
        gsite = df.groupby('site_control').agg({'transactions_count':'sum'}).reset_index().sort_values('transactions_count', ascending=False)
        if not gsite.empty:
            st.markdown('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')
            pie = px.pie(gsite, names='site_control', values='transactions_count',
                         color='site_control', color_discrete_sequence=PALETTE, hole=0.55)
            pie.update_traces(textposition='outside',
                              texttemplate='<b>%{label}</b><br>%{value:,} (%{percent:.1%})',
                              marker=dict(line=dict(color=('#fff' if not DARK else '#111'), width=2)),
                              pull=[0.02]*len(gsite))
            pie.update_layout(annotations=[dict(text=f"{total_tx:,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=18))])
            st.plotly_chart(pie, use_container_width=True, config={'displaylogo': False, 'scrollZoom': True})
        else:
            render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')
    else:
        render_chart_placeholder('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')

    # ---- Horizontal Bar by Hospital (rename + y-axis label) ----
    if not df.empty:
        gh = df.groupby('name').agg({'transactions_count':'sum'}).reset_index().sort_values('transactions_count', ascending=True)
        if not gh.empty:
            st.markdown('#### ภาพรวมต่อโรงพยาบาล')
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
            st.plotly_chart(bar, use_container_width=True, config={'displaylogo': False, 'scrollZoom': True})
        else:
            render_chart_placeholder('#### ภาพรวมต่อโรงพยาบาล')
    else:
        render_chart_placeholder('#### ภาพรวมต่อโรงพยาบาล')

    # ---- Daily Trend line ----
    if not df.empty:
        daily = df.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index().sort_values('date')
        if not daily.empty:
            st.markdown('#### แนวโน้มรายวัน (กราฟเส้น)')
            TH = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
            labels = daily['date'].apply(lambda d: f"{TH[pd.to_datetime(d).dayofweek]} {pd.to_datetime(d).day}/{pd.to_datetime(d).month}/{str(pd.to_datetime(d).year)[-2:]}")
            ln = go.Figure()
            ln.add_trace(go.Scatter(x=labels, y=daily['transactions_count'], mode='lines+markers+text',
                                    name='Transactions', text=daily['transactions_count'],
                                    textposition='top center', line=dict(width=3)))
            ln.add_trace(go.Scatter(x=labels, y=daily['riders_active'], mode='lines+markers',
                                    name='Rider Active', visible='legendonly',
                                    line=dict(width=2, dash='dot')))
            ln.update_layout(xaxis_title='วัน/เดือน/ปี', yaxis_title='จำนวน',
                             xaxis_tickangle=-40, margin=dict(t=30,r=20,b=80,l=60))
            st.plotly_chart(ln, use_container_width=True, config={'displaylogo': False, 'scrollZoom': True})
        else:
            render_chart_placeholder('#### แนวโน้มรายวัน (กราฟเส้น)')
    else:
        render_chart_placeholder('#### แนวโน้มรายวัน (กราฟเส้น)')

    # ---- Table by site (Plotly Table) ----
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

            header_fill = '#0b1220' if DARK else '#EEF2FF'
            header_font = '#E5E7EB' if DARK else '#334155'
            rgba = [
                'rgba(167,199,231,0.15)','rgba(248,200,220,0.15)','rgba(182,226,211,0.15)',
                'rgba(253,226,179,0.15)','rgba(234,215,247,0.15)','rgba(205,229,240,0.15)'
            ]
            row_colors = [rgba[i % len(rgba)] for i in range(len(show_df))]
            fill_matrix = [row_colors]*len(show_df.columns)

            figt = go.Figure(data=[go.Table(
                header=dict(values=list(show_df.columns), fill_color=header_fill, font=dict(color=header_font, size=12),
                            align='left', height=30),
                cells=dict(values=[show_df[c] for c in show_df.columns], fill_color=fill_matrix,
                           align='left', height=28)
            )])
            figt.update_layout(margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(figt, use_container_width=True, config={'displaylogo': False})
        else:
            st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')
    else:
        st.info('ไม่มีข้อมูลตารางในช่วงที่เลือก')

# ====================== ADMIN ======================
def render_admin():
    if not st.session_state.auth['ok']:
        st.warning('กรุณาเข้าสู่ระบบทาง Sidebar ก่อน'); return

    st.markdown("# DashBoard Telemedicine")
    st.markdown("## 🛠️ หน้าการจัดการ (Admin)")
    tabs = st.tabs(['จัดการโรงพยาบาล','จัดการ Transaction','จัดการผู้ดูแล','ตั้งค่า & ข้อมูลตัวอย่าง'])

    # ---- Hospitals ----
    with tabs[0]:
        hospitals_df = load_df('hospitals')
        st.markdown('### โรงพยาบาล')
        with st.expander('➕ เพิ่ม/แก้ไข โรงพยาบาล'):
            edit_mode = st.checkbox('แก้ไขรายการที่มีอยู่', value=False)
            if edit_mode and not hospitals_df.empty:
                sel = st.selectbox('เลือกโรงพยาบาล', hospitals_df.get('name', pd.Series(dtype=str)).tolist())
                row = hospitals_df[hospitals_df['name']==sel].iloc[0].to_dict()
            else:
                row = {'id':str(uuid.uuid4())}

            name = st.text_input('ชื่อโรงพยาบาล', value=row.get('name',''))
            provs = list(TH_PROVINCES.keys()); pidx = provs.index(row.get('province')) if row.get('province') in provs else 0
            province = st.selectbox('จังหวัด', provs, index=pidx)
            region = TH_PROVINCES.get(province, 'ภาคกลาง'); st.caption(f'ภูมิภาค: **{region}**')
            site = st.selectbox('SiteControl (ทีม)', SITE_CONTROL_CHOICES,
                                index=SITE_CONTROL_CHOICES.index(row.get('site_control')) if row.get('site_control') in SITE_CONTROL_CHOICES else 0)
            system = st.selectbox('ระบบที่ใช้', SYSTEM_CHOICES,
                                  index=SYSTEM_CHOICES.index(row.get('system_type')) if row.get('system_type') in SYSTEM_CHOICES else 0)
            models = st.multiselect('โมเดลบริการ', SERVICE_MODEL_CHOICES,
                                    default=[m for m in (row.get('service_models') or []) if m in SERVICE_MODEL_CHOICES])
            riders_count = st.number_input('จำนวน Rider (Capacity)', min_value=0, step=1, value=int(row.get('riders_count',0)))

            c1,c2 = st.columns(2)
            with c1:
                if st.button('บันทึกโรงพยาบาล'):
                    if not name.strip(): st.error('กรอกชื่อโรงพยาบาล'); st.stop()
                    payload = {'id':row.get('id',str(uuid.uuid4())),
                               'name':name.strip(),'province':province,'region':region,
                               'site_control':site,'system_type':system,'service_models':models,
                               'riders_count':int(riders_count)}
                    try:
                        if edit_mode: sb.table('hospitals').update(payload).eq('id', row['id']).execute()
                        else: sb.table('hospitals').insert(payload).execute()
                        st.success('บันทึกเรียบร้อย'); load_df.clear(); rerun()
                    except Exception:
                        st.error('บันทึกไม่สำเร็จ')

            with c2:
                confirm = st.checkbox('ยืนยันการลบโรงพยาบาลนี้และธุรกรรมทั้งหมดที่เกี่ยวข้อง', value=False, key='confirm_del_hosp')
                if edit_mode and st.button('🗑️ ยืนยันลบ', disabled=not confirm):
                    try:
                        sb.table('transactions').delete().eq('hospital_id', row['id']).execute()
                        sb.table('hospitals').delete().eq('id', row['id']).execute()
                        st.success('ลบเรียบร้อย'); load_df.clear(); rerun()
                    except Exception:
                        st.error('ลบไม่สำเร็จ')

        st.markdown('#### รายชื่อโรงพยาบาล')
        cols = [c for c in ['name','province','region','site_control','system_type','service_models','riders_count'] if c in hospitals_df.columns]
        st.dataframe(hospitals_df[cols] if not hospitals_df.empty else pd.DataFrame(columns=cols), use_container_width=True)

    # ---- Transactions ----
    with tabs[1]:
        hospitals_df = load_df('hospitals')
        st.markdown('### Transaction ต่อวัน')
        if hospitals_df.empty:
            st.info('ยังไม่มีโรงพยาบาล — เพิ่มก่อน')
        else:
            name2id = {r['name']:r['id'] for _,r in hospitals_df.iterrows()}

            # state: control expanders
            if 'open_add_tx' not in st.session_state:
                st.session_state['open_add_tx'] = True

            # เพิ่ม (prevent duplicate + UX)
            with st.expander('➕ เพิ่ม Transaction รายวัน', expanded=st.session_state.get('open_add_tx', True)):
                hname = st.selectbox('โรงพยาบาล (ค้นหาได้)', list(name2id.keys()), key='add_tx_hosp')
                tx_date = st.date_input('วันที่', value=date.today(), key='add_tx_date')
                tx_num = st.number_input('Transactions', min_value=0, step=1, key='add_tx_num')
                riders_active = st.number_input('Rider Active', min_value=0, step=1, key='add_tx_ra')
                cbtn1, cbtn2 = st.columns(2)
                with cbtn1:
                    if st.button('บันทึก Transaction', key='add_tx_btn'):
                        hid = name2id[hname]
                        try:
                            existed = sb.table('transactions').select('id').eq('hospital_id', hid).eq('date', tx_date.isoformat()).limit(1).execute().data
                            if existed:
                                st.warning('ข้อมูลวันที่นี้ของโรงพยาบาลนี้มีอยู่แล้ว กรุณาไป **แก้ไขรายการเดิม** หรือ **ยกเลิก**')
                                g1, g2 = st.columns(2)
                                with g1:
                                    if st.button('➡️ ไปหน้าแก้ไขรายการนี้', key='go_edit_dup'):
                                        st.session_state['open_edit_tx'] = True
                                        st.session_state['edit_target_h'] = hname
                                        st.session_state['edit_target_d'] = tx_date
                                        st.session_state['force_edit_reset'] = True
                                        st.session_state['open_add_tx'] = False
                                        rerun()
                                with g2:
                                    if st.button('ยกเลิก', key='cancel_dup'):
                                        st.session_state['open_add_tx'] = False
                                        rerun()
                                st.stop()
                            rc = int(hospitals_df.loc[hospitals_df['id']==hid,'riders_count'].iloc[0])
                            if riders_active > rc:
                                st.error('Rider Active มากกว่า Capacity'); st.stop()
                            sb.table('transactions').insert({
                                'id':str(uuid.uuid4()),'hospital_id':hid,'date':tx_date.isoformat(),
                                'transactions_count':int(tx_num),'riders_active':int(riders_active)
                            }).execute()
                            st.success('เพิ่มข้อมูลแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('บันทึกไม่สำเร็จ')
                with cbtn2:
                    if st.button('ยกเลิก', key='cancel_add_tx'):
                        st.session_state['open_add_tx'] = False
                        rerun()

            # ตาราง (ไม่โชว์ hospital_id + วันที่แบบไทย)
            raw_tx = load_df('transactions')
            if raw_tx.empty:
                st.info('ยังไม่มีข้อมูล')
            else:
                raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
                tx_view = raw_tx.merge(hospitals_df[['id','name']], left_on='hospital_id', right_on='id', how='left')
                tx_view['วันที่'] = tx_view['date'].apply(th_date)
                show = safe_cols(tx_view, ['วันที่','name','transactions_count','riders_active'])
                st.dataframe(tx_view[show].rename(columns={'name':'โรงพยาบาล','transactions_count':'Transactions','riders_active':'Rider Active'}),
                             use_container_width=True)

            # แก้ไข/ลบ โดยเลือก "โรงพยาบาล + วันที่" (รองรับ deep-link จาก duplicate)
            default_h = st.session_state.get('edit_target_h')
            default_d = st.session_state.get('edit_target_d', date.today())
            try:
                idx_default_h = list(name2id.keys()).index(default_h) if default_h in name2id else 0
            except Exception:
                idx_default_h = 0
            exp_open = st.session_state.get('open_edit_tx', False)

            # ถ้าถูกสั่งเปิดจาก duplicate -> ล้าง key widget เพื่อให้ index/value default ทำงาน
            if exp_open and st.session_state.get('force_edit_reset', False):
                for k in ['edit_pick_h','edit_pick_d']:
                    if k in st.session_state: st.session_state.pop(k)
                st.session_state['force_edit_reset'] = False

            with st.expander('✏️ แก้ไข / ลบ ตาม โรงพยาบาล + วันที่', expanded=exp_open):
                h_edit = st.selectbox('โรงพยาบาล', list(name2id.keys()), index=idx_default_h, key='edit_pick_h')
                d_edit = st.date_input('วันที่', value=default_d, key='edit_pick_d')
                pick_df = raw_tx[(raw_tx['hospital_id']==name2id[h_edit]) & (pd.to_datetime(raw_tx['date']).dt.date==d_edit)]
                if pick_df.empty:
                    st.info('ไม่พบข้อมูลของโรงพยาบาล/วันที่นี้')
                else:
                    row = pick_df.iloc[0].to_dict()
                    nsel = st.number_input('Transactions', min_value=0, step=1, value=int(row.get('transactions_count',0)))
                    rsel = st.number_input('Rider Active', min_value=0, step=1, value=int(row.get('riders_active',0)))
                    c1,c2 = st.columns(2)
                    with c1:
                        if st.button('บันทึกการแก้ไข', key='save_edit_tx'):
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
                        if st.button('ลบรายการนี้', key='del_edit_tx'):
                            try:
                                sb.table('transactions').delete().eq('id', row['id']).execute()
                                for k in ['open_edit_tx','edit_target_h','edit_target_d']:
                                    st.session_state.pop(k, None)
                                st.success('ลบแล้ว'); load_df.clear(); rerun()
                            except Exception:
                                st.error('ลบไม่สำเร็จ')

            # reset flags (ครั้งถัดไป expander จะไม่ค้างเปิด)
            st.session_state['open_edit_tx'] = False

    # ---- Admin users ----
    with tabs[2]:
        st.markdown('### ผู้ดูแลระบบ')
        admins_df = load_df('admins')
        if not admins_df.empty and 'username' in admins_df.columns:
            st.dataframe(admins_df[['username']], use_container_width=True)
        else:
            st.info('ยังไม่มีข้อมูลผู้ดูแล หรือไม่มีตาราง admins')
        with st.expander('➕ เพิ่มผู้ดูแล'):
            nu = st.text_input('Username ใหม่'); npw = st.text_input('Password', type='password')
            if st.button('เพิ่มผู้ดูแล'):
                if not nu or not npw: st.error('กรอกให้ครบ'); st.stop()
                try:
                    if not admins_df.empty and any(admins_df['username'].str.lower()==nu.lower()):
                        st.error('มี username นี้แล้ว'); st.stop()
                    sb.table('admins').insert({'id':str(uuid.uuid4()),'username':nu,'password_hash':hash_pw(npw)}).execute()
                    st.success('เพิ่มแล้ว'); load_df.clear(); rerun()
                except Exception:
                    st.error('เพิ่มไม่สำเร็จ')
        with st.expander('🔁 เปลี่ยนรหัสผ่าน / ลบผู้ดูแล'):
            if not admins_df.empty:
                selu = st.selectbox('เลือกผู้ใช้', admins_df['username'].tolist())
                newpw = st.text_input('รหัสผ่านใหม่', type='password')
                c1,c2 = st.columns(2)
                with c1:
                    if st.button('เปลี่ยนรหัสผ่าน'):
                        if not newpw: st.error('กรุณากรอกรหัส'); st.stop()
                        try:
                            sb.table('admins').update({'password_hash':hash_pw(newpw)}).eq('username', selu).execute()
                            st.success('เปลี่ยนแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('เปลี่ยนไม่สำเร็จ')
                with c2:
                    if st.button('ลบผู้ใช้'):
                        try:
                            sb.table('admins').delete().eq('username', selu).execute()
                            st.success('ลบแล้ว'); load_df.clear(); rerun()
                        except Exception:
                            st.error('ลบไม่สำเร็จ')

    # ---- Settings & Seed ----
    with tabs[3]:
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
                    ('รพ.หาดใหญ่','สงขลา','ภาคใต้','ทีมใต้','WebPortal',['Rider','App','Station to Station'],5),
                    ('รพ.เชียงใหม่','เชียงใหม่','ภาคเหนือ','ทีมเหนือ','HOSxpV4',['Rider','Station to Station'],7),
                    ('รพ.ขอนแก่น','ขอนแก่น','ภาคอีสาน','ทีมอีสาน','HOSxpV3',['App'],4),
                    ('รพ.ชลบุรี','ชลบุรี','ภาคตะวันออก','ทีมเหนือ','WebPortal',['Rider','App'],6),
                    ('รพ.นครศรีธรรมราช','นครศรีธรรมราช','ภาคใต้','ทีมใต้','HOSxpV4',['Rider','App'],6),
                ]
                name2id={}
                for n,prov,reg,site,sys,models,rc in demo:
                    try:
                        ex=sb.table('hospitals').select('id').eq('name',n).execute().data
                        hid=ex[0]['id'] if ex else str(uuid.uuid4())
                        if not ex:
                            sb.table('hospitals').insert({'id':hid,'name':n,'province':prov,'region':reg,
                                                          'site_control':site,'system_type':sys,'service_models':models,
                                                          'riders_count':rc}).execute()
                        name2id[n]=hid
                    except Exception: pass
                days=[date.today()-timedelta(days=2),date.today()-timedelta(days=1),date.today()]
                rows=[]
                for n,hid in name2id.items():
                    for d in days:
                        rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':d.isoformat(),
                                     'transactions_count':random.randint(20,60),'riders_active':random.randint(2,7)})
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
