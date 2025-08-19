import os, streamlit as st
# โหลด Secrets จาก Cloud เข้าสู่ env
for k in ("SUPABASE_URL","SUPABASE_ANON_KEY","SUPABASE_SERVICE_ROLE_KEY","ENV"):
    if k in st.secrets and not os.getenv(k):
        os.environ[k] = str(st.secrets[k])

# เรียก entry ของโปรดักชัน
import streamlit_app  # แค่นำเข้า ก็รันโค้ดในไฟล์นั้นทันที
