import os, streamlit as st
st.title("ENV check (staging)")
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_KEY",
          "SUPABASE_SERVICE_ROLE_KEY","ENV"):
    st.write(k, "→", "✓" if os.getenv(k) else "✗")
