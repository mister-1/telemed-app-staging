import os, traceback, streamlit as st
from pathlib import Path

# --- Failsafe: แอปนี้ต้องเป็น staging เท่านั้น ---
ENV = (os.getenv("ENV") or st.secrets.get("ENV") or "").lower()
if ENV != "staging":
    st.error("This instance must run with ENV=staging. Aborting.")
    st.stop()

# โหลด secrets → ENV + alias ชื่อคีย์
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY","SUPABASE_SERVICE_ROLE_KEY","ENV"):
    v = st.secrets.get(k)
    if v and not os.getenv(k): os.environ[k] = str(v)
if os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
if os.getenv("SUPABASE_SERVICE_KEY") and not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]

# รัน streamlit_app.py แบบสคริปต์หลัก (รองรับสคริปต์คลาสสิก)
try:
    code = Path(__file__).with_name("streamlit_app.py").read_text(encoding="utf-8")
    exec(compile(code, "streamlit_app.py", "exec"), {"__name__": "__main__"})
except Exception as e:
    st.error("⚠️ Error while running streamlit_app.py"); st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)))
