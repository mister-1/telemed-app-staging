import os, importlib, streamlit as st

for k in ("SUPABASE_URL","SUPABASE_ANON_KEY",
          "SUPABASE_SERVICE_KEY","SUPABASE_SERVICE_ROLE_KEY","ENV"):
    v = st.secrets.get(k)
    if v and not os.getenv(k):
        os.environ[k] = str(v)
if os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
if os.getenv("SUPABASE_SERVICE_KEY") and not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]

mod = importlib.import_module("streamlit_app")
for fn in ("main", "app", "run"):
    if hasattr(mod, fn) and callable(getattr(mod, fn)):
        getattr(mod, fn)()
        break
