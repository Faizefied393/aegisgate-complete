"""Optional read-only local dashboard, using authenticated API."""
import os
import httpx
import streamlit as st

BASE = os.getenv("AEGIS_API", "http://127.0.0.1:8000")
st.set_page_config(page_title="AegisGate", layout="wide")
st.title("AegisGate — Security Validation Lab")
st.caption("Synthetic local data only. Demo identities are not real authentication.")
user = st.selectbox("Demo identity", ["alice", "bob", "carol"])
with httpx.Client(timeout=10) as client:
    response = client.post(f"{BASE}/demo/login/{user}")
    response.raise_for_status()
    headers = {"Authorization":f"Bearer {response.json()['access_token']}"}
    prompt = st.text_input("Ask the demonstration agent", "Investigate security events")
    mode = st.selectbox("Agent mode", ["demo", "claude"])
    if st.button("Run"):
        result = client.post(f"{BASE}/agent/chat",headers=headers,json={"prompt":prompt,"mode":mode})
        st.json(result.json())
    if user in {"alice", "carol"}:
        st.subheader("Detection findings")
        st.json(client.get(f"{BASE}/findings",headers=headers).json())
    if user == "carol":
        st.subheader("Audit trail")
        st.json(client.get(f"{BASE}/audit",headers=headers).json())
