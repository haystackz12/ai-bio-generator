###############################################################################
# AI Bio Generator – Delight Edition (Full App with working PDF download)
# Streamlit + OpenAI GPT-4o-mini
###############################################################################
import os, uuid, urllib.parse
from datetime import datetime
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from openai import OpenAI

# ─── Init ───
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Bio Generator", layout="centered", page_icon="✨")

# Session defaults
for k, v in {"history": [], "last_bio": "", "bullets": "", "role": "", "personality": ""}.items():
    st.session_state.setdefault(k, v)

# ─── Constants ───
TONE_EXAMPLES = {
    "Executive": "Seasoned leader driving innovation and growth.",
    "Friendly":  "Passionate collaborator who loves bringing ideas to life.",
    "Casual":    "Tech geek who enjoys solving real-world problems.",
    "Funny":     "Data wrangler by day, meme connoisseur by night.",
    "Bold":      "Fearless strategist turning big visions into reality."
}
VOICE_STYLES = ["Punchy & Direct", "Witty & Conversational", "Inspiring & Visionary", "Corporate & Executive"]
PLATFORMS = ["LinkedIn", "Twitter", "Resume"]
share_base = {
    "LinkedIn": "https://www.linkedin.com/sharing/share-offsite/?url=",
    "Twitter": "https://twitter.com/intent/tweet?text="
}

# ─── Helpers ───
def build_prompt(role, hl, pers, plat, tone, voice, polished=False):
    note = "The bullet points have already been polished." if polished else ""
    return f"""
You are an expert professional bio writer. {note}

Transform the details below into a compelling, {tone.lower()} bio tailored for {plat}.
Do NOT merely list facts—synthesize them into a smooth, engaging narrative in a **{voice}** voice.

Lead with impact, weave highlights naturally, sprinkle in personality if appropriate.
Limits → Twitter ≤ 300 chars · LinkedIn ≤ 500 chars · Résumé ≤ 3 sentences

### Details
Role/Title: {role or "N/A"}
Highlights: {hl or "N/A"}
Personality: {pers or "N/A"}
""".strip()

def call_gpt(prompt, temp=0.8):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert bio writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=temp, max_tokens=300
    )
    return r.choices[0].message.content.strip()

def add_history(text):
    st.session_state.history.insert(0, {
        "id": uuid.uuid4().hex[:8], "text": text,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds")
    })

def polish_bullets(raw):
    p = f"Improve these bullet points, keep one per line, make concise:\n{raw}"
    return call_gpt(p, temp=0.5)

def download_pdf(txt):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for ln in txt.splitlines():
        ln = ln.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, ln)
    pdf_output = pdf.output(dest='S').encode('latin-1')
    return BytesIO(pdf_output)

# ─── UI ───
st.title("✨ AI Bio Generator")
st.caption("Transform bullet points into captivating bios for LinkedIn, Twitter, or résumés.")

st.markdown(
    "<div style='text-align:center;font-size:0.9rem;'><b>Powered by GPT-4</b> &nbsp;|&nbsp; Created with ❤️</div>",
    unsafe_allow_html=True
)
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    platform = st.selectbox("Platform", PLATFORMS)
with c2:
    tone = st.selectbox("Tone", list(TONE_EXAMPLES), index=1)

st.caption(f"Example tone → *{TONE_EXAMPLES[tone]}*")
voice = st.selectbox("Voice style", VOICE_STYLES)

role_title = st.text_input("1️⃣  Role / Title", st.session_state.role, placeholder="Senior Data Scientist | PM")
highlights = st.text_area("2️⃣  Highlights (comma-separated)", st.session_state.bullets, height=100, placeholder="Built ML platform, Led 12-person team")
personality = st.text_input("3️⃣  Personality / Interests (optional)", st.session_state.personality, placeholder="Mentor, climber, coffee lover")

st.caption(f"Role: {len(role_title)} chars   Highlights: {len(highlights)} chars   Personality: {len(personality)} chars")

if st.button("✨ Polish My Bullet Points"):
    if highlights.strip():
        with st.spinner("Polishing…"):
            optimized = polish_bullets(highlights)
        st.session_state.bullets = optimized
        highlights = optimized
        st.success("Done! Bullet points refined.")
    else:
        st.warning("Please enter bullet points first.")

st.markdown("---")

variants = st.slider("How many bios?", 1, 3, 1)
if st.button("🚀 Generate"):
    if not role_title and not highlights:
        st.warning("Please provide at least role/title or highlights.")
    else:
        with st.spinner("Crafting bios…"):
            for _ in range(variants):
                prompt = build_prompt(role_title, highlights, personality, platform, tone, voice, polished=True)
                bio = call_gpt(prompt)
                add_history(bio)
                st.session_state.last_bio = bio
        st.session_state.role = role_title
        st.session_state.bullets = highlights
        st.session_state.personality = personality
        st.success("Bios generated! Scroll below.")

st.markdown("---")

if st.session_state.history:
    st.subheader("📝 Latest Bio(s)")
    for i, h in enumerate(st.session_state.history[:variants], 1):
        st.markdown(f"**Variant {i}:**")
        st.text_area("Generated Bio", h["text"], height=120, key=h["id"])

        colA, colB, colC, colD = st.columns(4)
        with colA:
            st.download_button("⬇ TXT", h["text"].encode(), file_name="bio.txt", mime="text/plain", key=f"txt_{h['id']}")
        with colB:
            st.download_button("⬇ Markdown", h["text"].encode(), file_name="bio.md", mime="text/markdown", key=f"md_{h['id']}")
        with colC:
            pdf_bytes = download_pdf(h["text"])
            st.download_button("⬇ PDF", pdf_bytes, file_name="bio.pdf", mime="application/pdf", key=f"pdf_{h['id']}")
        with colD:
            share_url = share_base[platform] + urllib.parse.quote(h["text"])
            st.markdown(f"[Share 🕕]({share_url})", unsafe_allow_html=True)
        st.markdown("---")

with st.sidebar:
    st.header("📜 Previous Versions")
    if st.session_state.history:
        for h in st.session_state.history:
            st.markdown(f"- {h['timestamp']} – {h['id']} · {len(h['text'])} chars")
    else:
        st.caption("No bios yet – generate one!")
