
import streamlit as st
import pandas as pd
import math
from datetime import datetime
import random

st.set_page_config(page_title="CRC Ski Jump Leaderboard", layout="wide")

# ------------------- Config -------------------
REQUIRED_COLS = ["이름", "값", "사진URL"]  # 값 = 지표(예: 평균콜시간)
THEME = {
    "gold": "#E7C873",
    "navy900": "#071A2C",
    "navy800": "#0B2238",
    "navy700": "#0F2C47",
    "ice": "#A9C7E6",
    "snow": "#FFFFFF"
}

# --------------- Demo Data --------------------
demo_df = pd.DataFrame({
    "이름": ["김민지","이준호","박서연","최지훈","정수진","오하늘","강민서","이예린","한서현","문지우","박지민","서민규","유하린"],
    "값":   [12.5, 11.8, 11.2, 10.9, 10.6, 10.3, 9.9, 9.8, 13.1, 12.0, 10.1, 11.1, 10.7],
    "사진URL": [
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
        "https://images.unsplash.com/photo-1519340241574-2cec6aef0c01",
        "https://images.unsplash.com/photo-1527980965255-d3b416303d12",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
        "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c",
        "https://images.unsplash.com/photo-1527980965255-d3b416303d12",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91",
        "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
        "https://images.unsplash.com/photo-1519340241574-2cec6aef0c01",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1",
    ]
})

# --------------- Sidebar Controls -------------
st.markdown("<h1 style='color:#E7C873; margin-bottom:0'>CRC WINTER OLYMPICS</h1>", unsafe_allow_html=True)
st.markdown("<div style='color:#CFE3FF; margin-top:-6px'>Ski Jump • Snowy Checkpoints</div>", unsafe_allow_html=True)

left, right = st.columns([1,1])
with left:
    uploaded = st.file_uploader("데이터 업로드 (CSV/XLSX) — 열: 이름, 값, 사진URL", type=["csv","xlsx"])
with right:
    use_demo = st.toggle("데모 데이터 사용", value=True)

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".xlsx"):
            df = pd.read_excel(uploaded)
        else:
            df = pd.read_csv(uploaded)
        use_demo = False
    except Exception as e:
        st.error(f"파일을 읽을 수 없어요: {e}")
        st.stop()
else:
    df = demo_df.copy() if use_demo else demo_df.copy()

# Validate
missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    st.error("누락된 열: " + ", ".join(missing))
    st.stop()

# Options
metric_name = st.text_input("지표 이름 (화면 표기용)", value="평균 콜 시간 (분)")
lower_is_better = st.radio("순위 기준", ["값이 낮을수록 상위", "값이 높을수록 상위"], horizontal=True) == "값이 낮을수록 상위"
avatar_size = st.slider("아바타 크기(px)", min_value=28, max_value=72, value=44, step=2)
show_rank_number = st.checkbox("순위 번호 표시", value=True)
max_people = st.slider("표시할 최대 인원", min_value=5, max_value=40, value=min(20, len(df)), step=1)

# Clean numeric & cut
df["값"] = pd.to_numeric(df["값"], errors="coerce")
df = df.dropna(subset=["이름","값"]).copy()
df = df.sort_values("값", ascending=lower_is_better).reset_index(drop=True).head(max_people)
df["순위"] = range(1, len(df)+1)

# Normalize to [0,1]
vmin, vmax = float(df["값"].min()), float(df["값"].max())
if vmax == vmin:
    df["t"] = 0.5
else:
    if lower_is_better:
        df["t"] = (vmax - df["값"]) / (vmax - vmin)
    else:
        df["t"] = (df["값"] - vmin) / (vmax - vmin)

# Slight jitter to reduce overlap
rng = random.Random(42)
df["jitter"] = [ (rng.random()-0.5)*0.02 for _ in range(len(df)) ]
df["t"] = (df["t"]*0.9 + 0.05 + df["jitter"]).clip(0.02, 0.98)

# Bézier curve control points for ski jump (viewport 1000x560)
P0 = (90, 380)   # start of ramp
P1 = (350, 120)  # takeoff curve control (steeper)
P2 = (920, 260)  # landing zone

def bezier(t, P0, P1, P2):
    x = (1-t)**2 * P0[0] + 2*(1-t)*t*P1[0] + t**2 * P2[0]
    y = (1-t)**2 * P0[1] + 2*(1-t)*t*P1[1] + t**2 * P2[1]
    return x, y

coords = [bezier(float(t), P0, P1, P2) for t in df["t"]]
df["x"] = [c[0] for c in coords]
df["y"] = [c[1] for c in coords]

# ------------------ CSS & SVG ------------------
CSS = f"""
<style>
  .stApp {{
    background: linear-gradient(180deg, {THEME['navy900']} 0%, {THEME['navy800']} 60%, {THEME['navy700']} 100%);
    color: #F0F6FF;
  }}
  .stage {{
    position: relative;
    width: 1000px;
    height: 560px;
    margin: 10px auto 20px auto;
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
    background: radial-gradient(1200px 560px at 50% 0%, rgba(255,255,255,0.06), rgba(255,255,255,0.01) 40%, rgba(0,0,0,0) 70%);
    overflow: hidden;
  }}
  /* Snowfall */
  .snowflake {{
    position: absolute; top: -10px; color: #fff; opacity: 0.9;
    animation: fall linear infinite;
    font-size: 10px;
    filter: drop-shadow(0 0 2px rgba(255,255,255,0.5));
  }}
  @keyframes fall {{
    0% {{ transform: translateY(-10px); }}
    100% {{ transform: translateY(600px); }}
  }}

  .title-flag {{
    position:absolute; left: 460px; top: 220px; width: 80px; height: 60px;
    background: rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.35);
    border-radius: 6px;
  }}

  .checkpoint {{
    position:absolute;
    width: {avatar_size}px;
    height: {avatar_size}px;
    border-radius: 999px;
    border: 2px solid {THEME['gold']};
    background-size: cover; background-position: center;
    box-shadow: 0 6px 12px rgba(0,0,0,0.35);
  }}
  .label {{
    position:absolute; transform: translate(-50%, -110%);
    color: #EAF3FF; font-weight: 800; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    white-space: nowrap; font-size: 13px;
  }}
  .metric {{
    position:absolute; transform: translate(-50%, 120%);
    color: #CFE3FF; font-size: 12px;
  }}

  .ranktag {{
    position:absolute; transform: translate(-150%, -150%);
    background: {THEME['gold']}; color: #0B1A2C; font-weight:900;
    border-radius: 999px; padding: 2px 8px; font-size: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  }}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ------------------ SVG Backdrop ------------------
svg = f"""
<svg width="1000" height="560" viewBox="0 0 1000 560" xmlns="http://www.w3.org/2000/svg">
  <!-- Mountains -->
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0E233B"/>
      <stop offset="100%" stop-color="#0B1E33"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1000" height="560" fill="url(#sky)" opacity="0.0"/>
  <g opacity="0.9">
    <path d="M0,380 L140,260 L260,360 L340,220 L500,360 L560,300 L680,360 L820,260 L1000,380 L1000,560 L0,560 Z" fill="#0F2C47"/>
    <path d="M0,420 L120,320 L220,420 L360,300 L520,420 L600,360 L760,420 L880,320 L1000,420 L1000,560 L0,560 Z" fill="#12345633"/>
  </g>
  <!-- Ski ramp (quadratic curve P0->P2 via P1) -->
  <path d="M 90 380 Q 350 120 920 260" stroke="{THEME['gold']}" stroke-width="4" fill="none" stroke-linecap="round"/>
  <!-- START marker -->
  <circle cx="90" cy="380" r="6" fill="{THEME['gold']}"/>
  <text x="90" y="405" text-anchor="middle" fill="#EAD9B0" font-size="12" font-weight="bold">START</text>
</svg>
"""

# Render stage with SVG + snow
stage = [f'<div class="stage">{svg}']

# Snowflakes
for i in range(60):
    left = random.randint(0, 980)
    dur = random.randint(6, 14)
    delay = random.randint(0, 8)
    size = random.randint(8,14)
    stage.append(f'<div class="snowflake" style="left:{left}px; animation-duration:{dur}s; animation-delay:{delay}s; font-size:{size}px;">❄</div>')

# Checkpoints (avatars along curve)
for _, row in df.iterrows():
    x = row["x"]
    y = row["y"]
    name = str(row["이름"])
    val = float(row["값"])
    photo = str(row["사진URL"]) if "사진URL" in df.columns and pd.notna(row["사진URL"]) else ""

    # Adjust to center by half avatar size
    offset = {avatar_size} / 2.0
    style = f"left:{x-offset}px; top:{y-offset}px; background-image:url('{photo}');"
    stage.append(f'<div class="checkpoint" style="{style}"></div>')
    if {str(show_rank_number).lower()}:
        stage.append(f'<div class="ranktag" style="left:{x}px; top:{y}px;">#{int(row["순위"])}</div>')
    stage.append(f'<div class="label" style="left:{x}px; top:{y}px;">{name}</div>')
    stage.append(f'<div class="metric" style="left:{x}px; top:{y}px;">{val:.1f}</div>')

stage.append('</div>')
st.markdown("".join(stage), unsafe_allow_html=True)

# Footer
st.caption(f"{metric_name} • 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
