import os, traceback, streamlit as st
from pathlib import Path

# 1) โหลด secrets → ENV + ทำ alias ให้รองรับทั้งสองชื่อ
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY","SUPABASE_SERVICE_ROLE_KEY","ENV"):
    v = st.secrets.get(k)
    if v and not os.getenv(k):
        os.environ[k] = str(v)
if os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
if os.getenv("SUPABASE_SERVICE_KEY") and not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]

# 2) รันไฟล์ streamlit_app.py แบบสคริปต์หลักทุกครั้ง (เหมือน `streamlit run streamlit_app.py`)
try:
    script_path = Path(__file__).with_name("streamlit_app.py")
    code = script_path.read_text(encoding="utf-8")
    globals_dict = {"__name__": "__main__"}
    exec(compile(code, str(script_path.name), "exec"), globals_dict)
except Exception as e:
    st.error("⚠️ เกิดข้อผิดพลาดระหว่างรัน streamlit_app.py (ดูรายละเอียดด้านล่าง)")
    st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)))
