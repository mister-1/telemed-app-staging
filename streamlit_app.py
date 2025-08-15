# Telemedicine Transactions Dashboard — Modern Pastel + Admin (Full)
# - ตัวกรองทีมภูมิภาค: multiselect + ปุ่ม "เลือกทั้งหมด/ล้าง"
# - Pie (Donut) ทีมภูมิภาค: label + value + percent ชัด, ขอบสีขาว, มี "รวม" ตรงกลาง
# - Bar แนวนอน (โรงพยาบาล): สีพาสเทลสลับไม่ซ้ำ, ปุ่มขยายเต็มจอด้วย st.query_params
# - Line รายวัน: แสดงตัวเลข Transactions บนจุด, Rider Active ซ่อนไว้ก่อน (legendonly)
# - ตารางทีมภูมิภาค: header gradient + in-cell bars + สีสันแถวชัดขึ้น
# - ลบข้อความปุ่ม keyboard_double_arrow_right
# - หน้าแอดมินครบ: Hospitals / Transactions / Admins / Settings+Seed
# - ใช้ st.query_params แทน experimental_* ทั้งหมด

import os, uuid, json, bcrypt, requests, random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, Any

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ---------------- Theme / palette ----------------
PASTEL_BG = '#F7F8FB'; PASTEL_CARD = '#FFFFFF'; PASTEL_TEXT = '#334155'
DARK_BG = '#0F172A'; DARK_CARD = '#111827'; DARK_TEXT = '#E5E7EB'
PALETTE = ["#A7C7E7","#F8C8DC","#B6E2D3","#FDE2B3","#EAD7F7","#CDE5F0",
           "#FFD6E8","#C8E6C9","#FFF3B0","#D7E3FC","#F2D7EE","#B8F1ED"]

st.set_page_config(page_title="Telemedicine Transactions", page_icon="📊", layout="wide")
px.defaults.template = 'plotly_white'
px.defaults.color_discrete_sequence = PALETTE

# ---------------- Supabase ----------------
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error('❌ Missing SUPABASE_URL or SUPABASE_KEY.')
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb: Client = get_client()

# ---------------- Constants ----------------
SITE_CONTROL_CHOICES = ['ทีมใต้', 'ทีมเหนือ', 'ทีมอีสาน']
SYSTEM_CHOICES = ['HOSxpV4', 'HOSxpV3', 'WebPortal']
SERVICE_MODEL_CHOICES = ['Rider', 'App', 'Station to Station']

TH_PROVINCES: Dict[str, str] = {  # ย่อไว้บางส่วน
  'กรุงเทพมหานคร':'ภาคกลาง','เชียงใหม่':'ภาคเหนือ','ขอนแก่น':'ภาคอีสาน','ชลบุรี':'ภาคตะวันออก',
  'สงขลา':'ภาคใต้','นครศรีธรรมราช':'ภาคใต้','นครราชสีมา':'ภาคอีสาน','ภูเก็ต':'ภาคใต้','ระยอง':'ภาคตะวันออก',
  'ลำปาง':'ภาคเหนือ','อุดรธานี':'ภาคอีสาน','สุราษฎร์ธานี':'ภาคใต้','บุรีรัมย์':'ภาคอีสาน'
}

# ---------------- Small helpers ----------------
def hash_pw(pw: str) -> str: return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_pw(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception: return False

@st.cache_data(ttl=60, show_spinner=False)
def load_df(table: str) -> pd.DataFrame:
    return pd.DataFrame(sb.table(table).select('*').execute().data)

def force_rerun():
    try: st.rerun()
    except Exception: pass

def send_line_notify(token: str, message: str):
    if not token: return
    try:
        requests.post('https://notify-api.line.me/api/notify',
                      headers={'Authorization': f"Bearer {token}"},
                      data={'message': message}, timeout=5)
    except Exception: pass

def ensure_default_admin():
    rows = sb.table('admins').select('username').eq('username','telemed').execute().data
    if not rows:
        sb.table('admins').insert({'id':str(uuid.uuid4()),'username':'telemed','password_hash':hash_pw('Telemed@DHI')}).execute()
ensure_default_admin()

# ---------------- Appearance ----------------
if 'ui' not in st.session_state: st.session_state['ui']={'dark':False}
with st.sidebar:
    st.markdown('### 🎨 การแสดงผล')
    st.session_state.ui['dark'] = st.checkbox('โหมดมืด (Dark mode)', value=st.session_state.ui['dark'])

BG, CARD, TEXT = (DARK_BG, DARK_CARD, DARK_TEXT) if st.session_state.ui['dark'] else (PASTEL_BG, PASTEL_CARD, PASTEL_TEXT)
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600&display=swap');
  :root {{ --bg:{BG}; --card:{CARD}; --text:{TEXT}; }}
  .stApp {{ background-color:var(--bg); color:var(--text); }}
  .metric-card {{ background:var(--card); padding:1rem; border-radius:16px; box-shadow:0 6px 18px rgba(0,0,0,.06); }}
  .btn-grad button {{ background:linear-gradient(135deg,#A7C7E7,#B6E2D3); border:none; color:#1f2937; font-weight:700; border-radius:12px; }}
  .stTabs [data-baseweb="tab-list"] {{ gap: .25rem; }}
  .stTabs [data-baseweb="tab"] {{ background: #eef2ff; border-radius: 10px; padding: .4rem .8rem; }}
</style>
""", unsafe_allow_html=True)

# ---------------- Auth ----------------
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
        st.write(f"✅ เข้าสู่ระบบเป็น **{st.session_state.auth['user']}**")
        if st.button('ออกจากระบบ'): st.session_state.auth={'ok':False,'user':None}; force_rerun()

# ---------------- Filters ----------------
hospitals_df = load_df('hospitals')

colF1, colF2, colF3, colF4 = st.columns([1.2,1.2,1.6,0.9])
with colF1:
    hosp_names = ['(ทั้งหมด)'] + sorted(hospitals_df.get('name', pd.Series(dtype=str)).dropna().unique().tolist())
    selected_hospital = st.selectbox('🏥 โรงพยาบาล', hosp_names)

with colF2:
    today = date.today(); start_default = today - timedelta(days=30)
    rg = st.date_input('📅 ช่วงวันที่', value=(start_default, today))
    start_date, end_date = (rg if isinstance(rg, tuple) else (start_default, today))

with colF3:
    # multiselect + ปุ่มเลือกทั้งหมด/ล้าง
    if 'site_filter' not in st.session_state:
        st.session_state['site_filter'] = SITE_CONTROL_CHOICES[:]  # default = ทั้งหมด
    st.markdown('🧭 **ทีมภูมิภาค (SiteControl)**')
    st.session_state['site_filter'] = st.multiselect(
        label='', options=SITE_CONTROL_CHOICES, default=st.session_state['site_filter'], key='site_filter_widget'
    )
    b1,b2 = st.columns([1,1])
    with b1:
        if st.button('เลือกทั้งหมด'):
            st.session_state['site_filter'] = SITE_CONTROL_CHOICES[:]; st.rerun()
    with b2:
        if st.button('ล้างทั้งหมด'):
            st.session_state['site_filter'] = []; st.rerun()
    site_filter = st.session_state['site_filter']

with colF4:
    components.html('<button onclick="parent.window.print()">🖨️ บันทึกหน้า</button>', height=48)

# ---------------- Data merge ----------------
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

# ---------------- KPIs ----------------
st.markdown('### 📈 ภาพรวม (Overview)')
colK1, colK2, colK3, colK4, colK5 = st.columns(5)
total_tx = int(merged['transactions_count'].sum()) if not merged.empty else 0
unique_h = merged['hospital_id'].nunique() if not merged.empty else 0
sum_riders_capacity = int(merged['riders_count'].fillna(0).sum()) if not merged.empty else 0
avg_per_day = int(merged.groupby('date')['transactions_count'].sum().mean()) if not merged.empty else 0
sum_riders_active = int(merged['riders_active'].sum()) if not merged.empty else 0
with colK1: st.markdown(f"<div class='metric-card'><b>Transaction รวม</b><h2>{total_tx:,}</h2></div>", unsafe_allow_html=True)
with colK2: st.markdown(f"<div class='metric-card'><b>โรงพยาบาลทั้งหมด</b><h2>{unique_h}</h2></div>", unsafe_allow_html=True)
with colK3: st.markdown(f"<div class='metric-card'><b>จำนวนไรเดอร์รวม</b><h2>{sum_riders_capacity:,}</h2></div>", unsafe_allow_html=True)
with colK4: st.markdown(f"<div class='metric-card'><b>เฉลี่ยต่อวัน</b><h2>{avg_per_day:,}</h2></div>", unsafe_allow_html=True)
with colK5: st.markdown(f"<div class='metric-card'><b>ไรเดอร์ Active</b><h2>{sum_riders_active:,}</h2></div>", unsafe_allow_html=True)

# ---------------- Charts ----------------
if merged.empty:
    st.info('ยังไม่มีข้อมูล ลองเพิ่มจาก Admin ➜ จัดการข้อมูล')
else:
    # Pie (Donut) by SiteControl
    st.markdown('#### จำนวน Transaction ตามทีมภูมิภาค (กราฟวงกลม)')
    grp_site = merged.groupby('site_control').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    grp_site = grp_site.sort_values('transactions_count', ascending=False)
    pie = px.pie(grp_site, names='site_control', values='transactions_count',
                 color='site_control', color_discrete_sequence=PALETTE, hole=0.55)
    pie.update_traces(
        textposition='outside',
        texttemplate='<b>%{label}</b><br>%{value:,} (%{percent:.1%})',
        marker=dict(line=dict(color='#fff', width=2)),
        pull=[0.02]*len(grp_site)
    )
    pie.update_layout(showlegend=True, legend_title_text='ทีมภูมิภาค',
                      annotations=[dict(text=f"{total_tx:,}<br>รวม", x=0.5, y=0.5, showarrow=False, font=dict(size=18))])
    st.plotly_chart(pie, use_container_width=True)

    # Horizontal bar by hospital + fullscreen
    st.markdown('#### ภาพรวมต่อโรงพยาบาล (แนวนอน)')
    grp_h = merged.groupby('name').agg({'transactions_count':'sum','riders_active':'sum','riders_count':'sum'}).reset_index()
    grp_h = grp_h.sort_values('transactions_count', ascending=True)
    bar_h = px.bar(grp_h, y='name', x='transactions_count', orientation='h', text='transactions_count',
                   color='name', color_discrete_sequence=PALETTE,
                   labels={'name':'โรงพยาบาล','transactions_count':'Transactions'})
    bar_h.update_traces(textposition='outside')
    bar_h.update_layout(showlegend=False, height=max(520, 30*len(grp_h)+200), margin=dict(l=140,r=40,t=30,b=40))
    if st.button('🔎 ขยายเต็มจอ', key='expand_h'):
        st.query_params.update({'view':'hospitals'})
        st.rerun()
    components.html(bar_h.to_html(include_plotlyjs='cdn', full_html=False), height=560, scrolling=True)

    # Daily trend line
    st.markdown('#### แนวโน้มรายวัน (กราฟเส้น)')
    daily = merged.groupby('date').agg({'transactions_count':'sum','riders_active':'sum'}).reset_index().sort_values('date')
    if not daily.empty:
        TH_DAYS = ['วันจันทร์','วันอังคาร','วันพุธ','วันพฤหัสบดี','วันศุกร์','วันเสาร์','วันอาทิตย์']
        labs = daily['date'].apply(lambda d: f"{TH_DAYS[pd.to_datetime(d).dayofweek]} {pd.to_datetime(d).day}/{pd.to_datetime(d).month}/{str(pd.to_datetime(d).year)[-2:]}")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=labs, y=daily['transactions_count'],
            mode='lines+markers+text', name='Transactions',
            text=daily['transactions_count'], textposition='top center',
            line=dict(width=3), marker=dict(size=8)
        ))
        fig_line.add_trace(go.Scatter(
            x=labs, y=daily['riders_active'],
            mode='lines+markers', name='Rider Active',
            visible='legendonly', line=dict(width=2, dash='dot'), marker=dict(size=7)
        ))
        fig_line.update_layout(xaxis_title='วัน/เดือน/ปี', yaxis_title='จำนวน',
                               xaxis_tickangle=-40, margin=dict(t=30,r=20,b=80,l=60),
                               hovermode='x unified')
        st.plotly_chart(fig_line, use_container_width=True)

    # Table by SiteControl (more color)
    st.markdown('#### ตารางจำนวน Transaction แยกตามทีมภูมิภาค')
    tbl = grp_site.rename(columns={
        'site_control':'ทีมภูมิภาค','transactions_count':'Transactions',
        'riders_active':'Rider Active','riders_count':'Riders ทั้งหมด'
    })

    def color_rows(df):
        styles = []
        for i in range(len(df)):
            clr = PALETTE[i % len(PALETTE)]
            styles.append([f'background-color: {clr}22']*len(df.columns))  # 0x22 = โปร่งใส
        return pd.DataFrame(styles, columns=df.columns, index=df.index)

    try:
        styled = (tbl.style
                  .apply(color_rows, axis=None)
                  .set_table_styles([{'selector':'th','props':[('background','#EEF2FF'),('color','#334155'),('font-weight','600')]}])
                  .bar(subset=['Transactions'], color='#A7C7E7')
                  .bar(subset=['Rider Active'], color='#F8C8DC')
                  .bar(subset=['Riders ทั้งหมด'], color='#B6E2D3')
                  .format({'Transactions':'{:,}','Rider Active':'{:,}','Riders ทั้งหมด':'{:,}'}))
        st.table(styled)
    except Exception:
        st.dataframe(tbl, use_container_width=True)

# ---------------- Fullscreen view ----------------
if st.query_params.get('view') == 'hospitals' and not merged.empty:
    st.markdown('### ภาพรวมต่อโรงพยาบาล (เต็มจอ)')
    grp_h2 = merged.groupby('name').agg({'transactions_count':'sum'}).reset_index().sort_values('transactions_count', ascending=True)
    bar_full = px.bar(grp_h2, y='name', x='transactions_count', orientation='h', text='transactions_count',
                      color='name', color_discrete_sequence=PALETTE)
    bar_full.update_traces(textposition='outside')
    bar_full.update_layout(showlegend=False, height=max(800, 35*len(grp_h2)+240), margin=dict(l=180,r=40,t=30,b=40))
    st.plotly_chart(bar_full, use_container_width=True)
    if st.button('⬅️ กลับสู่ Dashboard'):
        st.query_params.clear(); st.rerun()

# ================== ADMIN / SETTINGS ==================
st.markdown('---'); st.markdown('## 🛠️ หน้าการจัดการ (Admin)')
if not st.session_state.auth['ok']:
    st.info('เข้าสู่ระบบจากแถบด้านซ้ายเพื่อแก้ไขข้อมูล')
else:
    tabs = st.tabs(['จัดการโรงพยาบาล','จัดการ Transaction','จัดการผู้ดูแล','ตั้งค่า & ข้อมูลตัวอย่าง'])

    # ---------- Hospitals ----------
    with tabs[0]:
        st.markdown('### โรงพยาบาล')
        with st.expander('➕ เพิ่ม/แก้ไข โรงพยาบาล'):
            edit_mode = st.checkbox('แก้ไขรายการที่มีอยู่', value=False)
            if edit_mode and not hospitals_df.empty:
                sel = st.selectbox('เลือกโรงพยาบาล', hospitals_df['name'].tolist())
                row = hospitals_df[hospitals_df['name']==sel].iloc[0].to_dict()
            else:
                row = {'id':str(uuid.uuid4())}

            name = st.text_input('ชื่อโรงพยาบาล', value=row.get('name',''))
            provs = list(TH_PROVINCES.keys())
            pidx = provs.index(row.get('province')) if row.get('province') in provs else 0
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
                    if not name.strip(): st.error('กรุณากรอกชื่อ'); st.stop()
                    payload = {'id':row.get('id',str(uuid.uuid4())),'name':name.strip(),'province':province,
                               'region':region,'site_control':site,'system_type':system,
                               'service_models':models,'riders_count':int(riders_count)}
                    if edit_mode: sb.table('hospitals').update(payload).eq('id', row['id']).execute(); st.success('อัปเดตแล้ว')
                    else: sb.table('hospitals').insert(payload).execute(); st.success('เพิ่มแล้ว')
                    load_df.clear(); force_rerun()
            with c2:
                if edit_mode and st.button('🗑️ ลบรายการนี้'):
                    sb.table('hospitals').delete().eq('id', row['id']).execute(); st.success('ลบแล้ว'); load_df.clear(); force_rerun()

        st.markdown('#### รายชื่อโรงพยาบาล')
        st.dataframe(load_df('hospitals'), use_container_width=True)

    # ---------- Transactions ----------
    with tabs[1]:
        st.markdown('### Transaction ต่อวัน')
        hospitals_df = load_df('hospitals')
        if hospitals_df.empty:
            st.info('ยังไม่มีโรงพยาบาล — เพิ่มก่อนด้านซ้าย')
        else:
            name2id = {r['name']:r['id'] for _,r in hospitals_df.iterrows()}
            with st.expander('➕ เพิ่ม Transaction รายวัน'):
                hname = st.selectbox('โรงพยาบาล', list(name2id.keys()))
                tx_date = st.date_input('วันที่', value=date.today())
                tx_num = st.number_input('Transactions', min_value=0, step=1)
                riders_active = st.number_input('Rider Active', min_value=0, step=1)
                if st.button('บันทึก Transaction'):
                    hid = name2id[hname]
                    rc = int(hospitals_df.loc[hospitals_df['id']==hid,'riders_count'].iloc[0])
                    if riders_active > rc: st.error('Rider Active มากกว่า Capacity'); st.stop()
                    sb.table('transactions').insert({
                        'id':str(uuid.uuid4()),'hospital_id':hid,'date':tx_date.isoformat(),
                        'transactions_count':int(tx_num),'riders_active':int(riders_active)
                    }).execute()
                    st.success('เพิ่มข้อมูลแล้ว'); load_df.clear(); force_rerun()

            st.markdown('#### ตาราง Transaction (ดู/แก้ไข)')
            raw_tx = load_df('transactions')
            if raw_tx.empty:
                st.info('ยังไม่มีข้อมูล')
            else:
                raw_tx['date'] = pd.to_datetime(raw_tx['date']).dt.date
                tx_view = raw_tx.merge(hospitals_df[['id','name']], left_on='hospital_id', right_on='id', how='left')
                tx_view = tx_view[['id','date','name','transactions_count','riders_active','hospital_id']]
                st.dataframe(tx_view.rename(columns={'name':'โรงพยาบาล','date':'วันที่','transactions_count':'Transactions','riders_active':'Rider Active'}), use_container_width=True)

            with st.expander('✏️ แก้ไข / ลบ Transaction'):
                raw_tx = load_df('transactions')
                if not raw_tx.empty:
                    pick_id = st.selectbox('เลือกแถว', raw_tx['id'].tolist())
                    row = raw_tx[raw_tx['id']==pick_id].iloc[0].to_dict()
                    id2name = {r['id']:r['name'] for _,r in hospitals_df.iterrows()}
                    name2id = {v:k for k,v in id2name.items()}
                    hsel = st.selectbox('โรงพยาบาล', list(name2id.keys()), index=list(name2id.keys()).index(id2name.get(row['hospital_id'], list(name2id.keys())[0])))
                    dsel = st.date_input('วันที่', value=pd.to_datetime(row['date']).date())
                    nsel = st.number_input('Transactions', min_value=0, step=1, value=int(row.get('transactions_count',0)))
                    rsel = st.number_input('Rider Active', min_value=0, step=1, value=int(row.get('riders_active',0)))
                    k1,k2 = st.columns(2)
                    with k1:
                        if st.button('บันทึกการแก้ไข'):
                            hid = name2id[hsel]
                            rc = int(hospitals_df.loc[hospitals_df['id']==hid,'riders_count'].iloc[0])
                            if rsel > rc: st.error('Rider Active มากกว่า Capacity'); st.stop()
                            sb.table('transactions').update({
                                'hospital_id':hid,'date':dsel.isoformat(),
                                'transactions_count':int(nsel),'riders_active':int(rsel)
                            }).eq('id', pick_id).execute()
                            st.success('อัปเดตแล้ว'); load_df.clear(); force_rerun()
                    with k2:
                        if st.button('ลบแถวนี้'):
                            sb.table('transactions').delete().eq('id', pick_id).execute()
                            st.success('ลบแล้ว'); load_df.clear(); force_rerun()

    # ---------- Admins ----------
    with tabs[2]:
        st.markdown('### ผู้ดูแลระบบ')
        admins_df = load_df('admins')
        st.dataframe(admins_df[['username']], use_container_width=True) if not admins_df.empty else st.info('ยังไม่มีผู้ดูแล')
        with st.expander('➕ เพิ่มผู้ดูแล'):
            nu = st.text_input('Username ใหม่'); npw = st.text_input('Password', type='password')
            if st.button('เพิ่มผู้ดูแล'):
                if not nu or not npw: st.error('กรอกให้ครบ'); st.stop()
                if not admins_df.empty and any(admins_df['username'].str.lower()==nu.lower()):
                    st.error('มี username นี้แล้ว'); st.stop()
                sb.table('admins').insert({'id':str(uuid.uuid4()),'username':nu,'password_hash':hash_pw(npw)}).execute()
                st.success('เพิ่มผู้ดูแลแล้ว'); load_df.clear(); force_rerun()
        with st.expander('🔁 เปลี่ยนรหัสผ่าน / ลบผู้ดูแล'):
            if not admins_df.empty:
                selu = st.selectbox('เลือกผู้ใช้', admins_df['username'].tolist())
                newpw = st.text_input('รหัสผ่านใหม่', type='password')
                c1,c2 = st.columns(2)
                with c1:
                    if st.button('เปลี่ยนรหัสผ่าน'):
                        if not newpw: st.error('กรุณากรอกรหัส'); st.stop()
                        sb.table('admins').update({'password_hash':hash_pw(newpw)}).eq('username', selu).execute()
                        st.success('เปลี่ยนแล้ว'); load_df.clear(); force_rerun()
                with c2:
                    if st.button('ลบผู้ใช้'):
                        sb.table('admins').delete().eq('username', selu).execute()
                        st.success('ลบแล้ว'); load_df.clear(); force_rerun()

    # ---------- Settings & Seed ----------
    with tabs[3]:
        st.markdown('### ตั้งค่า & ข้อมูลตัวอย่าง')
        settings = load_df('settings')
        tg = next((r['value'] for _,r in settings.iterrows() if r['key']=='targets'), {'daily_transactions':50,'utilization_alert_pct':90})
        line_cfg = next((r['value'] for _,r in settings.iterrows() if r['key']=='line_notify'), {'enabled':False,'token':''})
        c1,c2 = st.columns(2)
        with c1:
            daily_target = st.number_input('เป้ายอดรายวัน (Transactions/วัน)', min_value=0, step=1, value=int(tg.get('daily_transactions',50)))
        with c2:
            util_th = st.number_input('แจ้งเตือนเมื่อ Utilization ≥ (%)', min_value=0, max_value=100, step=1, value=int(tg.get('utilization_alert_pct',90)))
        if st.button('บันทึกเป้าหมาย'):
            sb.table('settings').upsert({'key':'targets','value':{'daily_transactions':int(daily_target),'utilization_alert_pct':int(util_th)}}).execute()
            st.success('บันทึกแล้ว'); load_df.clear()
        st.markdown('#### LINE Notify')
        en_line = st.checkbox('เปิดใช้ LINE Notify', value=bool(line_cfg.get('enabled',False)))
        token = st.text_input('LINE Notify Token', value=line_cfg.get('token',''), type='password')
        if st.button('บันทึก LINE Notify'):
            sb.table('settings').upsert({'key':'line_notify','value':{'enabled':bool(en_line),'token':token.strip()}}).execute()
            st.success('บันทึกแล้ว'); load_df.clear()

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
                    ex=sb.table('hospitals').select('id').eq('name',n).execute().data
                    hid=ex[0]['id'] if ex else str(uuid.uuid4())
                    if not ex:
                        sb.table('hospitals').insert({'id':hid,'name':n,'province':prov,'region':reg,'site_control':site,'system_type':sys,'service_models':models,'riders_count':rc}).execute()
                    name2id[n]=hid
                days=[date.today()-timedelta(days=2),date.today()-timedelta(days=1),date.today()]
                rows=[]
                for n,hid in name2id.items():
                    for d in days:
                        rows.append({'id':str(uuid.uuid4()),'hospital_id':hid,'date':d.isoformat(),
                                     'transactions_count':random.randint(20,60),'riders_active':random.randint(2,7)})
                if rows: sb.table('transactions').insert(rows).execute()
                st.success('เติมข้อมูลแล้ว'); load_df.clear(); force_rerun()
        with b:
            if st.button('ลบข้อมูลตัวอย่าง'):
                targets=['รพ.หาดใหญ่','รพ.เชียงใหม่','รพ.ขอนแก่น','รพ.ชลบุรี','รพ.นครศรีธรรมราช']
                ids=[r['id'] for r in sb.table('hospitals').select('id').in_('name',targets).execute().data]
                for hid in ids: sb.table('transactions').delete().eq('hospital_id',hid).execute()
                if ids: sb.table('hospitals').delete().in_('id',ids).execute()
                st.success('ลบแล้ว'); load_df.clear(); force_rerun()
