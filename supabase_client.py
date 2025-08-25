import os
from functools import lru_cache
from supabase import create_client, Client

URL = os.environ["SUPABASE_URL"]

@lru_cache(maxsize=1)
def supabase_readonly() -> Client:
    """ใช้สำหรับ SELECT/อ่านข้อมูลทั่วไป"""
    return create_client(URL, os.environ["SUPABASE_ANON_KEY"])

@lru_cache(maxsize=1)
def supabase_admin() -> Client:
    """ใช้เฉพาะจุดที่ต้องสิทธิ์สูงจริง ๆ (update/insert/delete/เรียก RPC แอดมิน)"""
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(URL, key)
