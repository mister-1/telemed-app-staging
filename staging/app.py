import os, importlib, traceback, streamlit as st

# 1) โหลด secrets เข้าสู่ ENV + ทำ alias ให้รองรับทั้งสองชื่อ
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY","SUPABASE_SERVICE_ROLE_KEY","ENV"):
    v = st.secrets.get(k)
    if v and not os.getenv(k):
        os.environ[k] = str(v)
if os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
if os.getenv("SUPABASE_SERVICE_KEY") and not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]

# 2) แถบ Debug (ซ่อนไว้ใน sidebar)
with st.sidebar:
    st.caption("staging • debug")
    for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY","ENV"):
        st.write(k, "✓" if os.getenv(k) else "✗")
    # ping Supabase แบบไม่โชว์ค่า key
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if url and key:
            create_client(url, key).table("settings").select("*").limit(1).execute()
            st.success("Supabase ping: OK")
        else:
            st.warning("Supabase ping: missing URL/KEY")
    except Exception as e:
        st.error(f"Supabase ping error: {e}")

# 3) เรียกฟังก์ชันหลักของโปรดักชัน พร้อมดัก exception ให้เห็นหน้าจอ
try:
    mod = importlib.import_module("streamlit_app")
    for fn in ("main", "app", "run"):
        if hasattr(mod, fn) and callable(getattr(mod, fn)):
            getattr(mod, fn)()
            break
    else:
        st.warning("ไม่พบฟังก์ชัน main/app/run ใน streamlit_app.py")
except Exception as e:
    st.error("⚠️ เกิดข้อผิดพลาดระหว่างรันแอป (ดู traceback ด้านล่าง)")
    st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)))
