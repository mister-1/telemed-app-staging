from auth_guard import require_login
user, roles = require_login()          # ถ้าหน้านี้เฉพาะแอดมิน ให้ใช้ require_login({'admin'})

import os, streamlit as st
st.title("ENV check (staging)")
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY",
          "SUPABASE_SERVICE_ROLE_KEY","ENV"):
    st.write(k, "→", "✓" if os.getenv(k) else "✗")
