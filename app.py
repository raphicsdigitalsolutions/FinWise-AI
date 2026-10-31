from __future__ import annotations
import os, json
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from src.config import APP_NAME, APP_TAGLINE, DEFAULT_MODEL, CURRENCIES, FINANCIAL_GOALS, EXPENSE_CATEGORIES
from src.financial_calculator import calculate_financial_metrics, score_band, risk_band
from src.cache_manager import configure_cache
from src.chains import build_llm, run_analysis, stream_recommendations
from src.prompts import message_demo

load_dotenv()
st.set_page_config(page_title="FinWise AI | Smart Budget Intelligence", page_icon="💠", layout="wide", initial_sidebar_state="expanded")

# ---- Styling: modular CSS sections (order matters: later sections may refine earlier ones) ----
CSS_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
"""

CSS_TOKENS = """
:root{
  --navy:#070d1b; --navy-2:#0b1530; --violet:#8c7cff; --cyan:#51e4d4; --blue:#5b8dff; --ink:#edf2ff;
  --muted:#9eafd1; --line:rgba(157,181,239,.17);
  --field:#0f1b38; --field-hover:#132345; --field-edge:rgba(140,124,255,.30); --field-edge-hover:rgba(140,124,255,.55);
  --menu:#0d1933; --r-field:12px;
  --fw-field-bg:#0f1b38; --fw-field-ink:#edf2ff; --fw-field-edge:rgba(140,124,255,.32); --fw-field-btn:#b9c9e8;
  --font-body:'DM Sans','Segoe UI',system-ui,-apple-system,sans-serif;
  --font-display:'Space Grotesk','DM Sans','Segoe UI',system-ui,sans-serif;
}
"""

CSS_BASE = """
.stApp{font-family:var(--font-body);color:var(--ink);color-scheme:dark;
  background:radial-gradient(ellipse at 8% 0%,rgba(105,75,230,.26),transparent 32%),radial-gradient(ellipse at 95% 14%,rgba(39,207,198,.17),transparent 29%),linear-gradient(145deg,#070d1b 0%,#0b1530 52%,#101c3b 100%);background-attachment:fixed}
.stApp:before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.13;background-image:linear-gradient(rgba(132,160,230,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(132,160,230,.12) 1px,transparent 1px);background-size:54px 54px;-webkit-mask-image:linear-gradient(to bottom,black,transparent 82%);mask-image:linear-gradient(to bottom,black,transparent 82%)}
.stApp input,.stApp textarea,.stApp button{font-family:inherit}
[data-testid="stHeader"]{background:rgba(7,13,27,.28)}
.block-container{max-width:1440px;padding-top:2.2rem;padding-bottom:3rem}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-family:var(--font-display)!important;letter-spacing:-.03em;color:#f5f7ff!important}
.stApp h4{font-size:1.05rem}
hr{border-color:var(--line)}
.eyebrow,.section-kicker{font-size:10px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:#83eee3}
.section-kicker{margin:26px 0 12px;display:flex;align-items:center;gap:12px;animation:fw-rise .55s ease backwards}
.section-kicker:after{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(131,238,227,.35),transparent)}
.small-muted{font-size:11px;color:#9baaca;line-height:1.6}
.disclaimer{padding:13px 16px;border-radius:13px;background:linear-gradient(100deg,rgba(246,183,77,.09),rgba(246,183,77,.035));border:1px solid rgba(246,183,77,.23);color:#f5d69a;font-size:11px;line-height:1.65;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
"""

CSS_SIDEBAR = """
[data-testid="stSidebar"]{background:linear-gradient(180deg,#081022 0%,#0e1a38 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:var(--muted)}
.side-brand{display:flex;align-items:center;gap:12px;padding:2px 0 16px}
.side-logo{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;font:700 15px var(--font-display);color:#fff;text-shadow:0 2px 6px rgba(10,14,60,.6);background:radial-gradient(circle at 30% 20%,#c8ffff 0,#69e5df 9%,#8278ff 42%,#2a3280 100%);box-shadow:inset -5px -6px 10px rgba(4,9,35,.45),inset 3px 3px 7px rgba(255,255,255,.35),0 8px 20px rgba(80,90,230,.35)}
.side-name{font:700 20px/1.1 var(--font-display);letter-spacing:-.02em;color:#f5f7ff}
.side-tag{margin-top:4px;font-size:9px;font-weight:700;letter-spacing:.2em;color:#83eee3}
.side-section{margin:22px 0 10px;padding-top:16px;border-top:1px solid var(--line);font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#9eb3e6}
.side-section.first{margin-top:4px;border-top:0;padding-top:0}
"""

CSS_HERO = """
.hero{position:relative;isolation:isolate;overflow:hidden;display:flex;align-items:center;min-height:380px;padding:44px 48px;border:1px solid rgba(157,177,255,.26);border-radius:30px;margin-bottom:22px;
  background:radial-gradient(ellipse at 78% 48%,rgba(77,101,201,.24),transparent 38%),linear-gradient(115deg,rgba(27,40,82,.98),rgba(17,34,65,.92) 58%,rgba(24,39,77,.86));
  box-shadow:0 32px 90px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.11),inset 0 -1px 0 rgba(117,150,255,.1);animation:fw-hero-in .9s cubic-bezier(.2,.7,.2,1) backwards}
.hero:before{content:'';position:absolute;z-index:-1;width:460px;height:460px;right:1%;top:-230px;border-radius:50%;border:1px solid rgba(182,219,255,.16);box-shadow:inset 0 0 70px rgba(106,223,255,.10),0 0 90px rgba(111,105,255,.18);background:radial-gradient(circle at 34% 28%,rgba(218,255,255,.85) 0%,rgba(91,220,225,.62) 5%,rgba(119,105,255,.66) 23%,rgba(53,76,157,.30) 48%,rgba(20,31,67,.03) 68%);animation:fw-orb 9s ease-in-out infinite}
.hero:after{content:'';position:absolute;z-index:-1;width:320px;height:320px;right:20%;bottom:-220px;border-radius:50%;background:rgba(80,225,214,.16);filter:blur(64px)}
.hero-copy{position:relative;z-index:4;max-width:55%;animation:fw-rise .8s .15s cubic-bezier(.2,.7,.2,1) backwards}
.hero h1{font-size:clamp(36px,4.4vw,58px);margin:13px 0 8px;line-height:1.02;max-width:670px}
.hero p{color:#bdcbea;max-width:590px;margin:12px 0 0;font-size:14px;line-height:1.7}
.hero .tag{display:inline-flex;align-items:center;gap:7px;margin-top:20px;padding:8px 13px;border:1px solid rgba(135,231,222,.28);border-radius:30px;color:#aafff1;background:linear-gradient(100deg,rgba(64,200,187,.14),rgba(112,104,255,.12));font-size:10px;font-weight:700;letter-spacing:.1em;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}

/* 3D scene: one perspective + one preserve-3d context so rings, coins and core depth-sort together */
.hero-scene{position:absolute;right:3%;top:50%;width:420px;height:330px;transform:translateY(-50%);perspective:1100px;transform-style:preserve-3d;z-index:2;animation:fw-fade 1.2s .25s ease backwards}
.orbit{position:absolute;left:50%;top:50%;width:300px;height:300px;border-radius:50%;transform-style:preserve-3d;
  border:1.5px solid;border-color:rgba(141,230,255,.62) rgba(141,230,255,.10) rgba(141,230,255,.55) rgba(141,230,255,.10);
  box-shadow:0 0 26px rgba(93,170,255,.20),inset 0 0 22px rgba(86,220,221,.10);
  transform:translate(-50%,-50%) rotateX(68deg) rotateZ(-24deg);animation:fw-orbit-a 20s linear infinite}
.orbit:before{content:'';position:absolute;left:50%;top:-5px;width:9px;height:9px;margin-left:-5px;border-radius:50%;background:#c9fff8;box-shadow:0 0 12px 3px rgba(81,228,212,.75)}
.orbit.two{width:380px;height:380px;border-color:rgba(160,140,255,.60) rgba(160,140,255,.08) rgba(160,140,255,.50) rgba(160,140,255,.08);box-shadow:0 0 28px rgba(140,124,255,.22),inset 0 0 24px rgba(140,124,255,.10);transform:translate(-50%,-50%) rotateX(68deg) rotateZ(48deg);animation:fw-orbit-b 28s linear infinite}
.orbit.two:before{background:#e3dcff;box-shadow:0 0 12px 3px rgba(140,124,255,.8)}

/* Central Rs slab: stacked layers create real thickness */
.core{position:absolute;left:50%;top:48%;width:142px;height:142px;margin:-71px 0 0 -71px;transform-style:preserve-3d;animation:fw-core-float 6s ease-in-out infinite}
.core-body{position:absolute;inset:0;transform-style:preserve-3d;transform:rotateX(14deg) rotateY(-22deg);animation:fw-core-turn 12s ease-in-out infinite}
.core-body > i{position:absolute;inset:0;display:block;border-radius:38px;box-shadow:inset 0 0 0 1px rgba(150,170,255,.18)}
.core-face{position:absolute;inset:0;display:grid;place-items:center;border-radius:38px;transform:translateZ(1px);overflow:hidden;
  background:radial-gradient(circle at 28% 20%,#c8ffff 0,#69e5df 8%,#8278ff 34%,#343b91 68%,#151e49 100%);
  box-shadow:inset -16px -20px 28px rgba(4,9,35,.50),inset 9px 9px 20px rgba(255,255,255,.34),0 0 55px rgba(105,115,255,.35)}
.core-face:before{content:'';position:absolute;inset:11px;border-radius:29px;border:1px solid rgba(255,255,255,.28);box-shadow:inset 0 0 20px rgba(255,255,255,.14),0 1px 0 rgba(10,14,60,.4)}
.core-face:after{content:'';position:absolute;inset:0;border-radius:inherit;background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.28) 46%,transparent 58%);transform:translateX(-120%);animation:fw-sheen 7s ease-in-out infinite}
.core-rs{position:relative;z-index:1;font:700 58px/1 var(--font-display);letter-spacing:-.03em;color:#f4fbff;text-shadow:0 -1px 0 rgba(255,255,255,.55),0 2px 0 rgba(30,36,120,.7),0 5px 0 rgba(20,26,95,.5),0 12px 18px rgba(5,8,40,.5)}

/* Metallic Rupee coins: face + back + 13 rim layers */
.coin{--s:88px;position:absolute;width:var(--s);height:var(--s);transform-style:preserve-3d;animation:fw-coin-float 5.6s ease-in-out infinite}
.coin.c1{left:6px;top:42px}
.coin.c2{--s:68px;right:4px;bottom:36px;animation-delay:-2.4s}
.coin:after{content:'';position:absolute;left:12%;right:12%;top:118%;height:14px;border-radius:50%;background:radial-gradient(ellipse,rgba(0,0,0,.5) 0,rgba(0,0,0,.22) 45%,transparent 72%)}
.coin-body{position:absolute;inset:0;transform-style:preserve-3d;transform:rotateX(16deg) rotateY(-24deg);animation:fw-coin-spin 16s linear infinite}
.coin.c2 .coin-body{animation-duration:21s;animation-direction:reverse}
.coin .rim{position:absolute;inset:0;display:block;transform-style:preserve-3d}
.coin .rim i{position:absolute;inset:0;display:block;border-radius:50%;background:linear-gradient(180deg,#e7f1ff 0%,#8c9fc3 24%,#4a5d86 42%,#c8d8f2 58%,#7be9dc 74%,#5b6f98 100%)}
.coin .face{position:absolute;inset:0;display:grid;place-items:center;border-radius:50%;-webkit-backface-visibility:hidden;backface-visibility:hidden;
  font:800 calc(var(--s)*.29)/1 var(--font-display);letter-spacing:-.02em;color:#c3d1ea;
  text-shadow:-1px -1px 0 rgba(255,255,255,.98),1px 2px 1px rgba(36,54,98,.85),0 3px 6px rgba(36,54,98,.35);
  background:radial-gradient(circle at 30% 22%,rgba(255,255,255,.95),rgba(255,255,255,0) 30%),radial-gradient(circle at 74% 82%,rgba(81,228,212,.42),rgba(81,228,212,0) 46%),conic-gradient(from 200deg,#f7fbff,#b2c2dd,#eef6ff,#8296b8,#f3f9ff,#a6b8d4,#f7fbff);
  box-shadow:inset 0 0 0 2px #e4edfb,inset 0 0 0 4px rgba(76,98,142,.55),inset 0 0 16px rgba(40,60,110,.42)}
.coin .face:before{content:'';position:absolute;inset:14%;border-radius:50%;border:1px solid rgba(70,92,135,.45);box-shadow:inset 0 2px 5px rgba(40,60,110,.30),0 1px 0 rgba(255,255,255,.85)}
.coin .face:after{content:'';position:absolute;inset:0;border-radius:50%;background:linear-gradient(120deg,transparent 34%,rgba(255,255,255,.45) 47%,transparent 60%);pointer-events:none}
.coin .face.front{transform:translateZ(7px)}
.coin .face.back{transform:rotateY(180deg) translateZ(7px)}

/* Floating information cards sit in front of the scene */
.float-card{position:absolute;padding:10px 13px;border-radius:13px;border:1px solid rgba(180,205,255,.28);background:linear-gradient(145deg,rgba(33,51,94,.92),rgba(13,24,52,.85));box-shadow:0 18px 35px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.16);font-size:10px;letter-spacing:.06em;color:#cfe1ff;transform:translateZ(70px);animation:fw-card-float 6s ease-in-out infinite}
.float-card b{display:block;font:700 17px var(--font-display);letter-spacing:0;color:#fff;margin-top:3px}
.float-card.f1{left:0;bottom:26px}
.float-card.f2{right:0;top:20px;animation-delay:-3s}
.float-card .up{color:#7df0d9}

@keyframes fw-hero-in{from{opacity:0;transform:translateY(18px)}}
@keyframes fw-rise{from{opacity:0;transform:translateY(14px)}}
@keyframes fw-fade{from{opacity:0}}
@keyframes fw-orb{0%,100%{transform:translate3d(0,0,0) rotate(0)}50%{transform:translate3d(-8px,16px,0) rotate(8deg)}}
@keyframes fw-orbit-a{from{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(-24deg)}to{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(336deg)}}
@keyframes fw-orbit-b{from{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(48deg)}to{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(-312deg)}}
@keyframes fw-core-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
@keyframes fw-core-turn{0%,100%{transform:rotateX(14deg) rotateY(-26deg)}50%{transform:rotateX(18deg) rotateY(-6deg)}}
@keyframes fw-coin-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@keyframes fw-coin-spin{from{transform:rotateX(16deg) rotateY(0deg)}to{transform:rotateX(16deg) rotateY(360deg)}}
@keyframes fw-card-float{0%,100%{transform:translateZ(70px) translateY(0)}50%{transform:translateZ(70px) translateY(-9px)}}
@keyframes fw-sheen{0%,55%{transform:translateX(-120%)}100%{transform:translateX(120%)}}
"""

CSS_CARDS = """
.glass{position:relative;background:linear-gradient(145deg,rgba(27,43,82,.84),rgba(13,25,52,.80));border:1px solid var(--line);border-radius:19px;padding:20px 21px;box-shadow:0 16px 42px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.055);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;animation:fw-rise .5s ease backwards}
.glass:before{content:'';position:absolute;left:20px;right:20px;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(140,124,255,.75),rgba(81,228,212,.75),transparent);opacity:.55;transition:opacity .22s ease}
.glass:hover{transform:translateY(-4px);border-color:rgba(113,211,236,.34);box-shadow:0 24px 52px rgba(0,0,0,.30),0 0 28px rgba(91,141,255,.12),inset 0 1px 0 rgba(255,255,255,.09)}
.glass:hover:before{opacity:1}
.metric-label{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:#a9badc;font-weight:700}
.metric-value{font-family:var(--font-display);font-size:clamp(20px,2vw,28px);font-weight:700;color:#f5f7ff;margin-top:9px;overflow-wrap:anywhere}
.metric-note{font-size:11px;color:#91a6d0;margin-top:5px}
.preview-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:16px}
.preview-chip{padding:12px 14px;border-radius:14px;border:1px solid var(--line);background:rgba(91,141,255,.07);font-size:12px;color:#c9d6f2;line-height:1.5}
.preview-chip b{display:block;color:#83eee3;font-size:10px;letter-spacing:.16em;text-transform:uppercase;margin-bottom:4px}
[data-testid="stForm"]{padding:19px 20px 12px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,rgba(16,29,59,.68),rgba(10,20,43,.58));box-shadow:0 18px 45px rgba(0,0,0,.15)}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:14px;background:rgba(18,31,62,.48)}
[data-testid="stAlert"]{border-radius:14px}
[data-testid="stTabs"] button{color:#bdcbea}
[data-testid="stTabs"] button[aria-selected="true"]{color:#8ff4e7}
[data-testid="stProgress"] [role="progressbar"]>div,[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,#8a78ff,#48dfd1)}
"""

CSS_CONTROLS = """
/* Labels */
[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] label,[data-testid="stWidgetLabel"] p{color:#d3def6!important;opacity:1!important}
[data-testid="stWidgetLabel"] p{font-size:.84rem;font-weight:600;margin-bottom:2px}
[data-testid="stTooltipIcon"] svg,[data-testid="stTooltipHoverTarget"] svg{color:#8ea3d1;fill:currentColor}

/* Field surface (text, password, number) */
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"]{
  background:var(--field)!important;border:1px solid var(--field-edge)!important;border-radius:var(--r-field)!important;
  min-height:44px;overflow:hidden;box-shadow:inset 0 1px 3px rgba(0,0,0,.28)!important;outline:0!important;
  transition:border-color .18s ease,box-shadow .18s ease,background-color .18s ease}
[data-testid="stTextInput"] [data-baseweb="input"]:hover,
[data-testid="stNumberInput"] [data-baseweb="input"]:hover{border-color:var(--field-edge-hover)!important;background:var(--field-hover)!important}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within{border-color:rgba(140,124,255,.85)!important;box-shadow:0 0 0 3px rgba(140,124,255,.20),inset 0 1px 3px rgba(0,0,0,.28)!important}
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stNumberInput"] [data-baseweb="input"] > div,
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stNumberInput"] [data-baseweb="base-input"]{background:transparent!important;border:0!important;box-shadow:none!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{
  background:transparent!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--cyan)!important;
  border:0!important;box-shadow:none!important;outline:0!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stNumberInput"] input::placeholder{color:#8196c0!important;-webkit-text-fill-color:#8196c0!important;opacity:1}
[data-testid="stTextInput"] input:-webkit-autofill{-webkit-box-shadow:0 0 0 40px #0f1b38 inset!important;-webkit-text-fill-color:var(--ink)!important}

/* Password reveal (eye) button: transparent so the field surface shows through; icon stays visible */
[data-testid="stTextInput"] [data-baseweb="input"] button{background:transparent!important;border:0!important;box-shadow:none!important;color:#b9c9e8!important;opacity:1!important;border-radius:0!important}
[data-testid="stTextInput"] [data-baseweb="input"] button:hover{background:rgba(140,124,255,.16)!important;color:var(--cyan)!important}
[data-testid="stTextInput"] [data-baseweb="input"] button svg{color:inherit!important;fill:currentColor!important}

/* Number input +/- steppers */
[data-testid="stNumberInput"] button{background:transparent!important;color:#b9c9e8!important;border:0!important;border-left:1px solid rgba(140,124,255,.18)!important;border-radius:0!important;box-shadow:none!important;transition:background-color .15s ease,color .15s ease}
[data-testid="stNumberInput"] button:hover:not(:disabled){background:rgba(140,124,255,.20)!important;color:var(--cyan)!important}
[data-testid="stNumberInput"] button:disabled{opacity:.35}
[data-testid="stNumberInput"] button svg{color:inherit!important;fill:currentColor!important}

/* Select boxes: control surface is the first child of [data-baseweb=select] */
[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child{
  background:var(--field)!important;border:1px solid var(--field-edge)!important;border-radius:var(--r-field)!important;
  min-height:44px;box-shadow:inset 0 1px 3px rgba(0,0,0,.28)!important;color:var(--ink)!important;transition:border-color .18s ease,box-shadow .18s ease,background-color .18s ease}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child:hover{border-color:var(--field-edge-hover)!important;background:var(--field-hover)!important}
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div:first-child{border-color:rgba(140,124,255,.85)!important;box-shadow:0 0 0 3px rgba(140,124,255,.20)!important}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child > div,
[data-testid="stSelectbox"] [data-baseweb="select"] span{background:transparent!important;color:var(--ink)!important;opacity:1!important}
[data-testid="stSelectbox"] [data-baseweb="select"] input{background:transparent!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--cyan)!important}
[data-testid="stSelectbox"] [data-baseweb="select"] svg{color:#b9c9e8!important;fill:currentColor!important;opacity:1!important}

/* Open dropdown menus render in a portal outside the app root, so they are scoped by popover/menu, not by widget */
div[data-baseweb="popover"] > div{background:var(--menu)!important;border:1px solid rgba(140,124,255,.30)!important;border-radius:14px!important;box-shadow:0 24px 60px rgba(0,0,0,.55)!important;overflow:hidden}
div[data-baseweb="popover"] [data-baseweb="menu"],div[data-baseweb="popover"] ul[role="listbox"]{background:transparent!important;padding:6px}
div[data-baseweb="popover"] li[role="option"]{background:transparent!important;color:#e6edff!important;border-radius:9px;transition:background-color .12s ease}
div[data-baseweb="popover"] li[role="option"] *{color:inherit!important;background:transparent!important}
div[data-baseweb="popover"] li[role="option"]:hover,
div[data-baseweb="popover"] li[role="option"][aria-selected="true"]{background:rgba(140,124,255,.22)!important;color:#fff!important}
div[data-baseweb="popover"] li[role="option"][aria-selected="true"]{box-shadow:inset 3px 0 0 var(--cyan)}
[data-testid="stTooltipContent"]{color:#e6edff}

/* Buttons: secondary = outlined glass, primary / form submit = gradient */
[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button{border-radius:12px;min-height:46px;font-weight:700;letter-spacing:.01em;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease,background .2s ease}
[data-testid="stButton"] button p,[data-testid="stFormSubmitButton"] button p{color:inherit!important}
[data-testid="stButton"] button[kind="secondary"],[data-testid="stButton"] button[data-testid="stBaseButton-secondary"]{background:rgba(140,124,255,.10);border:1px solid rgba(140,124,255,.42);color:#e6edff}
[data-testid="stButton"] button[kind="secondary"]:hover,[data-testid="stButton"] button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.22);border-color:#8be9df;color:#fff;transform:translateY(-2px)}
[data-testid="stButton"] button[kind="primary"],[data-testid="stButton"] button[data-testid="stBaseButton-primary"],[data-testid="stFormSubmitButton"] button{border:1px solid rgba(151,160,255,.42);background:linear-gradient(110deg,#7569ef 0%,#586fe9 55%,#3f9cda 100%);color:#fff;box-shadow:0 10px 26px rgba(83,93,220,.27),inset 0 1px 0 rgba(255,255,255,.24)}
[data-testid="stButton"] button[kind="primary"]:hover,[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover,[data-testid="stFormSubmitButton"] button:hover{border-color:#8be9df;color:#fff;transform:translateY(-2px);box-shadow:0 14px 30px rgba(83,110,220,.38),0 0 22px rgba(81,228,212,.16)}
[data-testid="stButton"] button:focus-visible,[data-testid="stFormSubmitButton"] button:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
"""

CSS_CONTROLS_FIX = """
/* Version-proof overrides: match BaseWeb/Streamlit control elements directly (no ancestor test-id needed) and win on specificity */
html body .stApp div[data-baseweb="input"],
html body .stApp [data-testid="stTextInputRootElement"],
html body .stApp [data-testid="stNumberInputContainer"]{background:#0f1b38!important;background-color:#0f1b38!important;border:1px solid rgba(140,124,255,.32)!important;border-radius:12px!important;color:#edf2ff!important;overflow:hidden}
html body .stApp div[data-baseweb="input"]:focus-within,
html body .stApp [data-testid="stNumberInputContainer"]:focus-within{border-color:rgba(140,124,255,.9)!important;box-shadow:0 0 0 3px rgba(140,124,255,.2)!important}
html body .stApp div[data-baseweb="base-input"],
html body .stApp div[data-baseweb="input"] > div{background:transparent!important;background-color:transparent!important;border:0!important;box-shadow:none!important}
html body .stApp div[data-baseweb="input"] input,
html body .stApp div[data-baseweb="base-input"] input,
html body .stApp [data-testid="stNumberInputContainer"] input{background:transparent!important;background-color:transparent!important;color:#edf2ff!important;-webkit-text-fill-color:#edf2ff!important;caret-color:#51e4d4!important;border:0!important;box-shadow:none!important}
html body .stApp div[data-baseweb="input"] button,
html body .stApp [data-testid="stNumberInputContainer"] button,
html body .stApp button[data-testid="stNumberInputStepUp"],
html body .stApp button[data-testid="stNumberInputStepDown"]{background:transparent!important;background-color:transparent!important;color:#b9c9e8!important;border:0!important;box-shadow:none!important}
html body .stApp div[data-baseweb="input"] button:hover,
html body .stApp [data-testid="stNumberInputContainer"] button:hover:not(:disabled){background:rgba(140,124,255,.22)!important;color:#51e4d4!important}
html body .stApp div[data-baseweb="input"] button svg,
html body .stApp [data-testid="stNumberInputContainer"] button svg{color:inherit!important;fill:currentColor!important}
html body .stApp div[data-baseweb="select"] > div{background:#0f1b38!important;background-color:#0f1b38!important;border:1px solid rgba(140,124,255,.32)!important;border-radius:12px!important;color:#edf2ff!important;min-height:44px}
html body .stApp div[data-baseweb="select"] > div *{background:transparent!important;background-color:transparent!important;color:#edf2ff!important;-webkit-text-fill-color:#edf2ff!important}
html body .stApp div[data-baseweb="select"] svg{color:#b9c9e8!important;fill:currentColor!important}
html body .stApp div[data-baseweb="select"]:focus-within > div{border-color:rgba(140,124,255,.9)!important;box-shadow:0 0 0 3px rgba(140,124,255,.2)!important}
html body div[data-baseweb="popover"] > div,
html body div[data-baseweb="popover"] ul,
html body div[data-baseweb="popover"] [data-baseweb="menu"]{background:#0d1933!important;background-color:#0d1933!important;color:#e6edff!important}
html body div[data-baseweb="popover"] li{background:transparent!important;color:#e6edff!important}
html body div[data-baseweb="popover"] li:hover,
html body div[data-baseweb="popover"] li[aria-selected="true"]{background:rgba(140,124,255,.24)!important;color:#fff!important}
"""

CSS_FIELDS = """
/* Text/number field surface. Works for both DOM shapes: input > base-input > input  and  base-input[RootElement] > input. */
html body [data-testid="stTextInputRootElement"]:not(#fw-r),html body [data-testid="stNumberInputContainer"]:not(#fw-r),html body div[data-baseweb="input"]:not(#fw-r){background:var(--fw-field-bg)!important;border:1px solid var(--fw-field-edge)!important;border-radius:12px!important;overflow:hidden;box-shadow:none!important;color:var(--fw-field-ink)!important}
html body div[data-baseweb="input"]:not(#fw-r) [data-testid="stTextInputRootElement"]:not(#fw-r),html body div[data-baseweb="input"]:not(#fw-r) [data-baseweb="base-input"]:not(#fw-r),html body [data-testid="stTextInputRootElement"]:not(#fw-r) [data-baseweb="base-input"]:not(#fw-r),html body [data-testid="stNumberInputContainer"]:not(#fw-r) [data-baseweb="base-input"]:not(#fw-r),html body div[data-baseweb="input"]:not(#fw-r) > div:not(#fw-r){background:transparent!important;border:0!important;box-shadow:none!important}
html body [data-testid="stTextInputRootElement"]:not(#fw-r) input,html body [data-testid="stNumberInputContainer"]:not(#fw-r) input,html body div[data-baseweb="input"]:not(#fw-r) input{background:transparent!important;color:var(--fw-field-ink)!important;-webkit-text-fill-color:var(--fw-field-ink)!important;caret-color:#51e4d4!important;border:0!important;box-shadow:none!important}
html body [data-testid="stTextInputRootElement"]:not(#fw-r) button,html body [data-testid="stNumberInputContainer"]:not(#fw-r) button,html body div[data-baseweb="input"]:not(#fw-r) button{background:transparent!important;color:var(--fw-field-btn)!important;border:0!important;box-shadow:none!important}
html body [data-testid="stTextInputRootElement"]:not(#fw-r) button svg,html body div[data-baseweb="input"]:not(#fw-r) button svg{fill:currentColor!important;color:inherit!important}
html body [data-testid="stTextInputRootElement"]:not(#fw-r):focus-within,html body [data-testid="stNumberInputContainer"]:not(#fw-r):focus-within,html body div[data-baseweb="input"]:not(#fw-r):focus-within{border-color:rgba(140,124,255,.9)!important;box-shadow:0 0 0 3px rgba(140,124,255,.2)!important}
"""

CSS_DIALOG = """
/* API-key dialog (st.dialog renders in a portal, so rules are scoped by role=dialog, not by .stApp) */
html body [role="dialog"]{overflow:hidden!important;border-radius:26px!important}
html body [role="dialog"] > div,html body [role="dialog"] > section{background:transparent!important}
html body [data-testid="stDialog"] div:has(> [role="dialog"]){background:transparent!important;box-shadow:none!important;border-radius:26px!important}
div[data-testid="stDialog"],div[data-baseweb="modal"] > div:first-child{backdrop-filter:blur(7px);-webkit-backdrop-filter:blur(7px)}
[role="dialog"]{background:radial-gradient(ellipse at 90% 0%,rgba(105,75,230,.28),transparent 45%),radial-gradient(ellipse at 0% 100%,rgba(39,207,198,.16),transparent 45%),linear-gradient(150deg,#0e1a3a,#0a1330 60%,#0c1736)!important;
  border:1px solid rgba(157,177,255,.30)!important;border-radius:26px!important;box-shadow:0 40px 110px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.10)!important;color:#edf2ff}
.st-key-fw_keybox{background:radial-gradient(ellipse at 90% 0%,rgba(105,75,230,.28),transparent 45%),radial-gradient(ellipse at 0% 100%,rgba(39,207,198,.16),transparent 45%),linear-gradient(150deg,#0e1a3a,#0a1330 60%,#0c1736)!important;
  border:1px solid rgba(157,177,255,.30)!important;border-radius:26px!important;box-shadow:0 40px 110px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.10)!important;color:#edf2ff}
[role="dialog"] h2,[role="dialog"] h1{font-family:var(--font-display)!important;color:#f5f7ff!important;letter-spacing:-.02em}
.st-key-fw_keybox h2,.st-key-fw_keybox h1{font-family:var(--font-display)!important;color:#f5f7ff!important;letter-spacing:-.02em}
[role="dialog"] button[aria-label="Close"]{color:#b9c9e8!important;background:transparent!important}
[role="dialog"] [data-testid="stWidgetLabel"] p{color:#d3def6!important;font-weight:600;font-size:.84rem}
.st-key-fw_keybox [data-testid="stWidgetLabel"] p{color:#d3def6!important;font-weight:600;font-size:.84rem}
[role="dialog"] div[data-baseweb="input"]{background:#0f1b38!important;border:1px solid rgba(140,124,255,.34)!important;border-radius:14px!important;min-height:48px;overflow:hidden}
.st-key-fw_keybox div[data-baseweb="input"]{background:#0f1b38!important;border:1px solid rgba(140,124,255,.34)!important;border-radius:14px!important;min-height:48px;overflow:hidden}
[role="dialog"] div[data-baseweb="input"]:focus-within{border-color:rgba(140,124,255,.9)!important;box-shadow:0 0 0 3px rgba(140,124,255,.22)!important}
.st-key-fw_keybox div[data-baseweb="input"]:focus-within{border-color:rgba(140,124,255,.9)!important;box-shadow:0 0 0 3px rgba(140,124,255,.22)!important}
[role="dialog"] div[data-baseweb="base-input"],[role="dialog"] div[data-baseweb="input"] > div{background:transparent!important;border:0!important}
.st-key-fw_keybox div[data-baseweb="base-input"],.st-key-fw_keybox div[data-baseweb="input"] > div{background:transparent!important;border:0!important}
[role="dialog"] input{background:transparent!important;color:#edf2ff!important;-webkit-text-fill-color:#edf2ff!important;caret-color:#51e4d4!important}
.st-key-fw_keybox input{background:transparent!important;color:#edf2ff!important;-webkit-text-fill-color:#edf2ff!important;caret-color:#51e4d4!important}
[role="dialog"] input::placeholder{color:#8196c0!important;-webkit-text-fill-color:#8196c0!important;opacity:1}
.st-key-fw_keybox input::placeholder{color:#8196c0!important;-webkit-text-fill-color:#8196c0!important;opacity:1}
[role="dialog"] div[data-baseweb="input"] button{background:transparent!important;color:#b9c9e8!important;border:0!important}
.st-key-fw_keybox div[data-baseweb="input"] button{background:transparent!important;color:#b9c9e8!important;border:0!important}
[role="dialog"] div[data-baseweb="input"] button:hover{color:#51e4d4!important;background:rgba(140,124,255,.18)!important}
.st-key-fw_keybox div[data-baseweb="input"] button:hover{color:#51e4d4!important;background:rgba(140,124,255,.18)!important}
[role="dialog"] div[data-baseweb="input"] button svg{fill:currentColor!important;color:inherit!important}
.st-key-fw_keybox div[data-baseweb="input"] button svg{fill:currentColor!important;color:inherit!important}
[role="dialog"] button[kind="primary"],[role="dialog"] button[data-testid="stBaseButton-primary"]{min-height:50px;border-radius:14px;border:1px solid rgba(151,160,255,.45)!important;background:linear-gradient(110deg,#7569ef 0%,#586fe9 55%,#3f9cda 100%)!important;color:#fff!important;font-weight:700;box-shadow:0 12px 30px rgba(83,93,220,.35),inset 0 1px 0 rgba(255,255,255,.25);transition:transform .2s ease,box-shadow .2s ease}
.st-key-fw_keybox button[kind="primary"],.st-key-fw_keybox button[data-testid="stBaseButton-primary"]{min-height:50px;border-radius:14px;border:1px solid rgba(151,160,255,.45)!important;background:linear-gradient(110deg,#7569ef 0%,#586fe9 55%,#3f9cda 100%)!important;color:#fff!important;font-weight:700;box-shadow:0 12px 30px rgba(83,93,220,.35),inset 0 1px 0 rgba(255,255,255,.25);transition:transform .2s ease,box-shadow .2s ease}
[role="dialog"] button[kind="primary"]:hover,[role="dialog"] button[data-testid="stBaseButton-primary"]:hover{transform:translateY(-2px);box-shadow:0 16px 36px rgba(83,110,220,.45),0 0 24px rgba(81,228,212,.2)}
.st-key-fw_keybox button[kind="primary"]:hover,.st-key-fw_keybox button[data-testid="stBaseButton-primary"]:hover{transform:translateY(-2px);box-shadow:0 16px 36px rgba(83,110,220,.45),0 0 24px rgba(81,228,212,.2)}
[role="dialog"] button[kind="secondary"],[role="dialog"] button[data-testid="stBaseButton-secondary"]{min-height:46px;border-radius:14px;background:rgba(140,124,255,.08)!important;border:1px solid rgba(140,124,255,.40)!important;color:#dfe8ff!important;font-weight:600}
.st-key-fw_keybox button[kind="secondary"],.st-key-fw_keybox button[data-testid="stBaseButton-secondary"]{min-height:46px;border-radius:14px;background:rgba(140,124,255,.08)!important;border:1px solid rgba(140,124,255,.40)!important;color:#dfe8ff!important;font-weight:600}
[role="dialog"] button[kind="secondary"]:hover,[role="dialog"] button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.20)!important;border-color:#8be9df!important;color:#fff!important}
.st-key-fw_keybox button[kind="secondary"]:hover,.st-key-fw_keybox button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.20)!important;border-color:#8be9df!important;color:#fff!important}
[role="dialog"] button p{color:inherit!important}
.st-key-fw_keybox button p{color:inherit!important}
.st-key-fw_keybox{padding:20px 20px 14px!important;border-radius:22px!important}
.kd-card{display:flex;align-items:center;gap:18px;padding:16px 18px;border-radius:18px;border:1px solid rgba(157,181,239,.20);background:linear-gradient(145deg,rgba(27,43,82,.70),rgba(13,25,52,.60));box-shadow:inset 0 1px 0 rgba(255,255,255,.06);margin-bottom:12px}
.kd-scene{position:relative;flex:none;width:112px;height:92px;perspective:650px;transform-style:preserve-3d}
.kd-scene .orbit{width:104px;height:104px;animation-duration:14s}
.kd-scene .coin{--s:52px;left:50%;top:50%;margin:-26px 0 0 -26px;animation-duration:5s}
.kd-scene .coin:after{display:none}
.kd-title{font:700 16px var(--font-display);color:#f5f7ff;letter-spacing:-.01em}
.kd-sub{font-size:12.5px;color:#a9badc;line-height:1.55;margin-top:5px}
.kd-note{padding:12px 15px;border-radius:14px;background:linear-gradient(100deg,rgba(246,183,77,.10),rgba(246,183,77,.04));border:1px solid rgba(246,183,77,.25);color:#f5d69a;font-size:11.5px;line-height:1.65;margin-bottom:10px}
@media(max-width:600px){.kd-card{flex-direction:column;text-align:center}}
"""

CSS_DAY = """
/* Day theme: overrides only; night (default) styling above is untouched. Hero stays a dark premium panel. */
:root{--fw-field-bg:#fff;--fw-field-ink:#10204a;--fw-field-edge:rgba(100,110,210,.42);--fw-field-btn:#4a5b8c}
html body .stApp:not(#fw-day){color:#10204a!important;color-scheme:light;background:radial-gradient(ellipse at 8% 0%,rgba(140,124,255,.22),transparent 34%),radial-gradient(ellipse at 95% 12%,rgba(81,228,212,.20),transparent 30%),linear-gradient(145deg,#f6f8ff 0%,#eaf0ff 55%,#f3f6ff 100%);background-attachment:fixed}
html body .stApp:not(#fw-day):before{opacity:.6;background-image:linear-gradient(rgba(91,100,200,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(91,100,200,.10) 1px,transparent 1px)}
html body .stApp:not(#fw-day) [data-testid="stHeader"]{background:rgba(244,247,255,.72)}
html body .stApp:not(#fw-day) [data-testid="stToolbar"] *,html body .stApp:not(#fw-day) [data-testid="stSidebarCollapseButton"] svg,html body .stApp:not(#fw-day) [data-testid="stExpandSidebarButton"] svg{color:#2a3a6a!important}
html body .stApp:not(#fw-day) h1,html body .stApp:not(#fw-day) h2,html body .stApp:not(#fw-day) h3,html body .stApp:not(#fw-day) h4{color:#0b1530!important}
html body .stApp:not(#fw-day) .hero h1{color:#f5f7ff!important}
html body .stApp:not(#fw-day) [data-testid="stSidebar"]{background:linear-gradient(180deg,#f9fbff 0%,#e8eefc 100%);border-right-color:rgba(100,110,210,.20)}
html body .stApp:not(#fw-day) .side-name{color:#0b1530}
html body .stApp:not(#fw-day) .side-tag{color:#0a8a80}
html body .stApp:not(#fw-day) .side-section{color:#5b6f9c;border-top-color:rgba(100,110,210,.22)}
html body .stApp:not(#fw-day) .section-kicker,html body .stApp:not(#fw-day) .eyebrow{color:#0a8a80}
html body .stApp:not(#fw-day) .hero .eyebrow{color:#83eee3}
html body .stApp:not(#fw-day) [data-testid="stCaptionContainer"],html body .stApp:not(#fw-day) [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#5b6f9c!important}
html body .stApp:not(#fw-day) [data-testid="stWidgetLabel"],html body .stApp:not(#fw-day) [data-testid="stWidgetLabel"] label,html body .stApp:not(#fw-day) [data-testid="stWidgetLabel"] p,html body .stApp:not(#fw-day) [data-testid="stCheckbox"] label p{color:#1d2a52!important}
html body .stApp:not(#fw-day) .small-muted,html body .stApp:not(#fw-day) .metric-note{color:#5b6f9c}
html body .stApp:not(#fw-day) .metric-label{color:#5b6f9c}
html body .stApp:not(#fw-day) .metric-value{color:#0b1530}
html body .stApp:not(#fw-day) .glass{background:linear-gradient(145deg,#ffffff,#f0f4ff);border-color:rgba(100,110,210,.20);box-shadow:0 12px 30px rgba(60,80,160,.12),inset 0 1px 0 #fff}
html body .stApp:not(#fw-day) .glass:hover{border-color:rgba(91,100,230,.42);box-shadow:0 18px 40px rgba(60,80,170,.20),0 0 24px rgba(91,141,255,.12)}
html body .stApp:not(#fw-day) .preview-chip{background:rgba(91,141,255,.08);border-color:rgba(100,110,210,.20);color:#2a3a6a}
html body .stApp:not(#fw-day) .preview-chip b{color:#0a8a80}
html body .stApp:not(#fw-day) .disclaimer{background:linear-gradient(100deg,rgba(246,183,77,.20),rgba(246,183,77,.09));border-color:rgba(214,150,40,.40);color:#7a4b00}
html body .stApp:not(#fw-day) [data-testid="stForm"]{background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(238,243,255,.82));border-color:rgba(100,110,210,.22);box-shadow:0 14px 36px rgba(60,80,160,.10)}
html body .stApp:not(#fw-day) [data-testid="stExpander"]{background:rgba(255,255,255,.78);border-color:rgba(100,110,210,.22)}
html body .stApp:not(#fw-day) [data-testid="stExpander"] summary,html body .stApp:not(#fw-day) [data-testid="stExpander"] summary p,html body .stApp:not(#fw-day) [data-testid="stExpander"] summary span{color:#10204a}
html body .stApp:not(#fw-day) [data-testid="stTabs"] button{color:#4a5b8c}
html body .stApp:not(#fw-day) [data-testid="stTabs"] button[aria-selected="true"]{color:#5b45e0}
html body .stApp:not(#fw-day) [data-testid="stAlert"] *,html body [data-testid="stAlert"] *{color:#10204a!important}
html body .stApp:not(#fw-day) [data-testid="stCode"],html body .stApp:not(#fw-day) [data-testid="stCode"] pre,html body .stApp:not(#fw-day) [data-testid="stCode"] code{background:#eef2ff!important;color:#10204a!important}
html body .stApp:not(#fw-day) hr{border-color:rgba(100,110,210,.22)}
html body .stApp:not(#fw-day) .fw-loader{background:linear-gradient(145deg,#fff,#eef3ff);border-color:rgba(100,110,210,.22)}
html body .stApp:not(#fw-day) .fw-loader-title{color:#10204a}
html body .stApp:not(#fw-day) .fw-loader-sub{color:#5b6f9c}
/* inputs */
html body .stApp:not(#fw-day) div[data-baseweb="input"],html body .stApp:not(#fw-day) [data-testid="stTextInputRootElement"],html body .stApp:not(#fw-day) [data-testid="stNumberInputContainer"]{background:#fff!important;background-color:#fff!important;border:1px solid rgba(100,110,210,.40)!important;color:#10204a!important;box-shadow:0 1px 2px rgba(40,60,140,.08)!important}
html body .stApp:not(#fw-day) div[data-baseweb="base-input"],html body .stApp:not(#fw-day) div[data-baseweb="input"] > div{background:transparent!important;background-color:transparent!important}
html body .stApp:not(#fw-day) div[data-baseweb="input"] input,html body .stApp:not(#fw-day) div[data-baseweb="base-input"] input,html body .stApp:not(#fw-day) [data-testid="stNumberInputContainer"] input{color:#10204a!important;-webkit-text-fill-color:#10204a!important;caret-color:#5b45e0!important}
html body .stApp:not(#fw-day) div[data-baseweb="input"] input::placeholder{color:#8a98bf!important;-webkit-text-fill-color:#8a98bf!important}
html body .stApp:not(#fw-day) div[data-baseweb="input"] button,html body .stApp:not(#fw-day) [data-testid="stNumberInputContainer"] button,html body .stApp:not(#fw-day) button[data-testid="stNumberInputStepUp"],html body .stApp:not(#fw-day) button[data-testid="stNumberInputStepDown"]{color:#4a5b8c!important}
html body .stApp:not(#fw-day) div[data-baseweb="input"] button:hover,html body .stApp:not(#fw-day) [data-testid="stNumberInputContainer"] button:hover:not(:disabled){background:rgba(140,124,255,.16)!important;color:#5b45e0!important}
html body .stApp:not(#fw-day) div[data-baseweb="select"] > div{background:#fff!important;background-color:#fff!important;border:1px solid rgba(100,110,210,.40)!important;color:#10204a!important;box-shadow:0 1px 2px rgba(40,60,140,.08)!important}
html body .stApp:not(#fw-day) div[data-baseweb="select"] > div *{color:#10204a!important;-webkit-text-fill-color:#10204a!important}
html body .stApp:not(#fw-day) div[data-baseweb="select"] svg{color:#4a5b8c!important}
html body div[data-baseweb="popover"] > div,html body div[data-baseweb="popover"] ul,html body div[data-baseweb="popover"] [data-baseweb="menu"]{background:#fff!important;background-color:#fff!important;color:#10204a!important;border-color:rgba(100,110,210,.30)!important;box-shadow:0 18px 44px rgba(40,60,140,.22)!important}
html body div[data-baseweb="popover"] li[role="option"]{color:#10204a!important}
html body div[data-baseweb="popover"] li[role="option"]:hover,html body div[data-baseweb="popover"] li[role="option"][aria-selected="true"]{background:rgba(140,124,255,.16)!important;color:#10204a!important}
html body [data-testid="stTooltipContent"]{color:#10204a}
/* secondary buttons (primary gradient stays) */
html body .stApp:not(#fw-day) [data-testid="stButton"] button[kind="secondary"],html body .stApp:not(#fw-day) [data-testid="stButton"] button[data-testid="stBaseButton-secondary"]{background:rgba(140,124,255,.10);border-color:rgba(100,110,210,.45);color:#2c2a8f}
html body .stApp:not(#fw-day) [data-testid="stButton"] button[kind="secondary"]:hover,html body .stApp:not(#fw-day) [data-testid="stButton"] button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.22);border-color:#5b45e0;color:#2c2a8f}
/* API-key dialog */
html body [role="dialog"]{background:linear-gradient(150deg,#ffffff,#eef3ff)!important;border-color:rgba(100,110,210,.32)!important;box-shadow:0 40px 100px rgba(40,60,140,.35)!important;color:#10204a}
/* API-key dialog */
html body .st-key-fw_keybox{background:linear-gradient(150deg,#ffffff,#eef3ff)!important;border-color:rgba(100,110,210,.32)!important;box-shadow:0 40px 100px rgba(40,60,140,.35)!important;color:#10204a}
html body [role="dialog"] h2,html body [role="dialog"] h1{color:#0b1530!important}
html body .st-key-fw_keybox h2,html body .st-key-fw_keybox h1{color:#0b1530!important}
html body [role="dialog"] [data-testid="stWidgetLabel"] p{color:#1d2a52!important}
html body .st-key-fw_keybox [data-testid="stWidgetLabel"] p{color:#1d2a52!important}
html body [role="dialog"] div[data-baseweb="input"]{background:#fff!important;border-color:rgba(100,110,210,.42)!important}
html body .st-key-fw_keybox div[data-baseweb="input"]{background:#fff!important;border-color:rgba(100,110,210,.42)!important}
html body [role="dialog"] input{color:#10204a!important;-webkit-text-fill-color:#10204a!important}
html body .st-key-fw_keybox input{color:#10204a!important;-webkit-text-fill-color:#10204a!important}
html body [role="dialog"] input::placeholder{color:#8a98bf!important;-webkit-text-fill-color:#8a98bf!important}
html body .st-key-fw_keybox input::placeholder{color:#8a98bf!important;-webkit-text-fill-color:#8a98bf!important}
html body [role="dialog"] div[data-baseweb="input"] button{color:#4a5b8c!important}
html body .st-key-fw_keybox div[data-baseweb="input"] button{color:#4a5b8c!important}
html body [role="dialog"] button[kind="secondary"],html body [role="dialog"] button[data-testid="stBaseButton-secondary"]{background:rgba(140,124,255,.10)!important;border-color:rgba(100,110,210,.45)!important;color:#2c2a8f!important}
html body .st-key-fw_keybox button[kind="secondary"],html body .st-key-fw_keybox button[data-testid="stBaseButton-secondary"]{background:rgba(140,124,255,.10)!important;border-color:rgba(100,110,210,.45)!important;color:#2c2a8f!important}
html body [role="dialog"] button[kind="secondary"]:hover,html body [role="dialog"] button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.22)!important;border-color:#5b45e0!important;color:#2c2a8f!important}
html body .st-key-fw_keybox button[kind="secondary"]:hover,html body .st-key-fw_keybox button[data-testid="stBaseButton-secondary"]:hover{background:rgba(140,124,255,.22)!important;border-color:#5b45e0!important;color:#2c2a8f!important}
html body [role="dialog"] button[aria-label="Close"]{color:#4a5b8c!important}
html body [role="dialog"] .kd-card{background:linear-gradient(145deg,#ffffff,#f0f4ff);border-color:rgba(100,110,210,.22)}
html body .st-key-fw_keybox .kd-card{background:linear-gradient(145deg,#ffffff,#f0f4ff);border-color:rgba(100,110,210,.22)}
html body [role="dialog"] .kd-title{color:#0b1530}
html body .st-key-fw_keybox .kd-title{color:#0b1530}
html body [role="dialog"] .kd-sub{color:#4a5b8c}
html body .st-key-fw_keybox .kd-sub{color:#4a5b8c}
html body [role="dialog"] .kd-note{background:linear-gradient(100deg,rgba(246,183,77,.20),rgba(246,183,77,.09));border-color:rgba(214,150,40,.40);color:#7a4b00}
html body .st-key-fw_keybox .kd-note{background:linear-gradient(100deg,rgba(246,183,77,.20),rgba(246,183,77,.09));border-color:rgba(214,150,40,.40);color:#7a4b00}
"""

CSS_LOADER = """
.fw-loader{display:flex;align-items:center;gap:18px;padding:18px 22px;border-radius:19px;border:1px solid var(--line);background:linear-gradient(145deg,rgba(27,43,82,.84),rgba(13,25,52,.80));overflow:hidden;position:relative;margin:6px 0 14px}
.fw-loader-coin{flex:none;width:40px;height:40px;border-radius:50%;display:grid;place-items:center;font:800 14px var(--font-display);color:#c3d1ea;text-shadow:-1px -1px 0 #fff,1px 1px 1px rgba(36,54,98,.8);background:conic-gradient(from 200deg,#f7fbff,#b2c2dd,#eef6ff,#8296b8,#f3f9ff,#a6b8d4,#f7fbff);box-shadow:inset 0 0 0 2px #e4edfb,inset 0 0 0 4px rgba(76,98,142,.5),0 0 20px rgba(81,228,212,.35);animation:fw-loader-spin 1.4s linear infinite}
.fw-loader-title{font-weight:700;color:#f1f5ff;font-size:14px}
.fw-loader-sub{font-size:11px;color:var(--muted);margin-top:3px}
.fw-loader-bar{position:absolute;left:0;right:0;bottom:0;height:3px;background:rgba(140,124,255,.15);overflow:hidden}
.fw-loader-bar:after{content:'';position:absolute;top:0;bottom:0;width:38%;background:linear-gradient(90deg,transparent,#8c7cff,#51e4d4,transparent);animation:fw-loader-slide 1.5s ease-in-out infinite}
@keyframes fw-loader-spin{from{transform:perspective(220px) rotateY(0)}to{transform:perspective(220px) rotateY(360deg)}}
@keyframes fw-loader-slide{from{left:-40%}to{left:102%}}
"""

CSS_RESPONSIVE = """
@media(max-width:1000px){.hero-copy{max-width:100%}.hero-scene{opacity:.85}}
@media(max-width:800px){
  .block-container{padding:1rem 1rem 2rem}
  .hero{padding:28px 22px 250px;min-height:0;align-items:flex-start}
  .hero-copy{max-width:100%}
  .hero-scene{top:auto;bottom:-6px;right:50%;transform:translateX(50%) scale(.72);transform-origin:bottom center}
  .hero:before{right:-120px;opacity:.5}
  .hero h1{font-size:34px}
  .glass{padding:16px}
}
@media(prefers-reduced-motion:reduce){
  .hero,.hero *,.hero:before,.hero *:before,.hero *:after,.glass,.section-kicker,.fw-loader *,.fw-loader *:after{animation:none!important;transition:none!important}
}
"""

CSS = "<style>" + "\n".join([CSS_FONTS, CSS_TOKENS, CSS_BASE, CSS_SIDEBAR, CSS_HERO, CSS_CARDS, CSS_CONTROLS, CSS_CONTROLS_FIX, CSS_FIELDS, CSS_DIALOG, CSS_LOADER, CSS_RESPONSIVE]) + "</style>"
st.markdown(CSS, unsafe_allow_html=True)


BRAND_COLORS = ["#8C7CFF", "#51E4D4", "#5B8DFF", "#B7ABFF", "#2FB8C9", "#8FB1FF", "#6B5CEB", "#9AF2E6", "#4668D6"]

LOADER_HTML = (
    '<div class="fw-loader" role="status" aria-live="polite"><div class="fw-loader-coin">Rs</div>'
    '<div><div class="fw-loader-title">Analysing your budget with FinWise AI...</div>'
    '<div class="fw-loader-sub">Generating educational insights from your calculated metrics</div></div>'
    '<div class="fw-loader-bar"></div></div>'
)

def _coin_html(cls: str) -> str:
    """Metallic coin: 13 stacked rim layers give thickness, front/back faces carry the embossed Rs."""
    rim = "".join(f'<i style="transform:translateZ({z}px)"></i>' for z in range(-6, 7))
    return (f'<div class="coin {cls}"><div class="coin-body"><span class="rim">{rim}</span>'
            f'<b class="face front">Rs</b><b class="face back">Rs</b></div></div>')

def _core_html(depth: int = 16) -> str:
    """Central Rs slab: layered extrusion from a violet face colour to deep navy."""
    layers = []
    for i in range(1, depth + 1):
        t = i / depth
        layers.append(f'<i style="transform:translateZ(-{i * 1.5:.1f}px);background:rgb({int(78 - 56 * t)},{int(70 - 46 * t)},{int(178 - 100 * t)})"></i>')
    return f'<div class="core"><div class="core-body">{"".join(layers)}<div class="core-face"><span class="core-rs">Rs</span></div></div></div>'

def hero_html() -> str:
    # One line per element and no blank lines: Streamlit's markdown parser ends an HTML block at a blank line.
    return "".join([
        '<div class="hero">',
        '<div class="hero-copy">',
        '<div class="eyebrow">✦ PERSONAL FINANCE · AI INTELLIGENCE</div>',
        '<h1>Make every rupee<br/>work with intention.</h1>',
        f'<p>{APP_TAGLINE} Understand your monthly cash flow, uncover spending patterns, and build a more thoughtful budget with explainable calculations and AI-powered education.</p>',
        '<div class="tag">✦ FINANCIAL CLARITY, NOT FINANCIAL ADVICE</div>',
        '</div>',
        '<div class="hero-scene" aria-hidden="true">',
        '<div class="orbit"></div><div class="orbit two"></div>',
        _core_html(),
        _coin_html("c1"), _coin_html("c2"),
        '<div class="float-card f1">MONTHLY SAVINGS<b>+18.6% <span class="up">↗</span></b></div>',
        '<div class="float-card f2">FINANCIAL FLOW<b>Rs 80,000</b></div>',
        '</div></div>',
    ])

def key_dialog_intro_html() -> str:
    return (
        '<div class="kd-card"><div class="kd-scene" aria-hidden="true"><div class="orbit"></div>' + _coin_html("") + '</div>'
        '<div><div class="kd-title">Your session, your connection</div>'
        '<div class="kd-sub">Add your OpenAI API key for this session to unlock AI insights. Python budget calculations work without one.</div></div></div>'
        '<div class="kd-note">Your key travels from your browser to this app host and is then used only to call OpenAI. Only enter it on a deployment you trust. '
        'FinWise AI keeps it in the active Streamlit session memory; it is not written to a file or to GitHub.</div>'
    )

_dialog_api = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")

def open_key_dialog() -> None:
    """Welcome dialog asking for an OpenAI key. Skipped when a key already exists or the user has seen it once."""
    if _dialog_api is None:  # very old Streamlit: the sidebar key field still works
        return

    @_dialog_api("🔑 Connect to FinWise AI")
    def _body():
        try:
            panel = st.container(key="fw_keybox")  # keyed container -> class st-key-fw_keybox (Streamlit >= 1.39)
        except TypeError:
            panel = st.container()
        with panel:
            st.markdown(key_dialog_intro_html(), unsafe_allow_html=True)
            key_in = st.text_input("OpenAI API key", type="password", placeholder="Paste your key for this session", key="fw_dialog_key")
            connect = st.button("Connect for this session", type="primary", use_container_width=True, key="fw_dialog_connect")
            skip = st.button("Continue without an API key", use_container_width=True, key="fw_dialog_skip")
            if connect:
                if key_in.strip():
                    st.session_state["fw_session_key"] = key_in.strip()
                    st.rerun()
                else:
                    st.error("Paste a key to connect, or continue without one.")
            if skip:
                st.rerun()
            if st.session_state.get("fw_session_key"):
                if st.button("Disconnect personal key", use_container_width=True, key="fw_dialog_disconnect"):
                    st.session_state.pop("fw_session_key", None)
                    st.rerun()

    _body()

def money(value: float, currency: str) -> str:
    return f"{currency} {value:,.2f}"

def metric_card(label, value, note):
    st.markdown(f'<div class="glass"><div class="metric-label">✦ {label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="side-brand"><div class="side-logo">Rs</div><div><div class="side-name">FinWise AI</div><div class="side-tag">PERSONAL FINANCE INTELLIGENCE</div></div></div>', unsafe_allow_html=True)
    if hasattr(st, "toggle"):
        day = st.toggle("Day theme", key="fw_day_theme", help="Switch between the night look (default) and the day look.")
    else:
        day = st.checkbox("Day theme", key="fw_day_theme")
    st.markdown('<div class="side-section first">Model settings</div>', unsafe_allow_html=True)
    model = st.text_input("OpenAI model", value=DEFAULT_MODEL)
    env_key = os.getenv("OPENAI_API_KEY", "")
    if _dialog_api is None:
        # Very old Streamlit without st.dialog: keep the original sidebar key field so the app stays usable.
        api_key = st.text_input("OpenAI API key", value="", type="password", help="Optional: enter a key for this session, or configure OPENAI_API_KEY in Streamlit Secrets.")
    else:
        api_key = ""
    try:
        hosted_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        hosted_key = ""
    try:
        secret_require = st.secrets.get("FINWISE_REQUIRE_USER_KEY", "")
    except Exception:
        secret_require = ""
    # Optional: set FINWISE_REQUIRE_USER_KEY=1 (env or Secrets) so every visitor must bring their own key.
    require_personal_key = _truthy(os.getenv("FINWISE_REQUIRE_USER_KEY", "")) or _truthy(secret_require)
    server_key = "" if require_personal_key else (env_key or hosted_key)
    session_key = st.session_state.get("fw_session_key", "")
    effective_key = api_key.strip() or session_key or server_key
    if _dialog_api is not None:
        if session_key:
            st.success("Personal API key connected for this session.")
        elif server_key:
            st.info("Using this app's configured API key.")
        else:
            st.warning("No API key connected. Calculations work; AI insights need a key.")
        if st.button("Connect or change API key", use_container_width=True, key="fw_open_key_dialog"):
            open_key_dialog()
    st.markdown('<div class="side-section">Cache</div>', unsafe_allow_html=True)
    cache_mode = st.selectbox("Cache mode", ["Off", "In-memory", "SQLite"], index=1)
    if st.session_state.get("_configured_cache_mode") != cache_mode:
        cache_notice = configure_cache(cache_mode)
        st.session_state["_configured_cache_mode"] = cache_mode
        st.session_state["_cache_notice"] = cache_notice
    st.caption(st.session_state.get("_cache_notice", "Cache configuration pending."))
    if cache_mode == "SQLite":
        st.warning("SQLite stores prompts and responses in plaintext. Use fictional demo data only.")
    st.markdown('<div class="side-section">About</div>', unsafe_allow_html=True)
    st.caption("A learning prototype combining deterministic Python calculations with LangChain-powered educational insights.")
    if st.button("↻ Reset session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown('<div class="disclaimer">Educational information only — not financial, investment, tax, or legal advice. Consult a qualified financial professional.</div>', unsafe_allow_html=True)

if day:
    st.markdown("<style>" + CSS_DAY + "</style>", unsafe_allow_html=True)

# Shown once per new session so visitors can bring their own key; closing it counts as "continue without a key".
if _dialog_api is not None and not st.session_state.get("fw_key_dialog_seen"):
    st.session_state["fw_key_dialog_seen"] = True
    open_key_dialog()

st.markdown(hero_html(), unsafe_allow_html=True)

st.markdown('<div class="disclaimer">⚠ EDUCATIONAL USE ONLY. FinWise AI is a course prototype, not a financial adviser. It does not connect to bank accounts, execute transactions, provide guaranteed outcomes, or recommend specific investments. Use its insights for learning and consult a qualified professional for important decisions.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-kicker">01 / Your monthly snapshot</div>', unsafe_allow_html=True)
with st.form("finance_form", clear_on_submit=False):
    top1, top2, top3 = st.columns([1.1,1,1])
    with top1:
        currency = st.selectbox("Currency", CURRENCIES, index=0)
        income = st.number_input("Monthly income", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")
    with top2:
        savings = st.number_input("Current monthly savings", min_value=0.0, value=10000.0, step=1000.0, format="%.2f")
        goal = st.selectbox("Your financial goal", FINANCIAL_GOALS)
    with top3:
        month_label = st.text_input("Budget month", value=pd.Timestamp.today().strftime("%B %Y"))
        st.markdown('<div class="small-muted">Enter approximate monthly amounts. Do not enter account numbers or credentials.</div>', unsafe_allow_html=True)
    st.markdown("#### Expense breakdown")
    expense_cols = st.columns(3)
    expenses = {}
    defaults = [18000, 15000, 6000, 5000, 4000, 3000, 3000, 8000, 2000]
    for idx, category in enumerate(EXPENSE_CATEGORIES):
        with expense_cols[idx % 3]:
            expenses[category] = st.number_input(category, min_value=0.0, value=float(defaults[idx]), step=500.0, key=f"expense_{idx}", format="%.2f")
    submitted = st.form_submit_button("✦ Analyse my budget", use_container_width=True)

if submitted:
    metrics = calculate_financial_metrics(income, expenses, savings)
    st.session_state["finwise_metrics"] = metrics
    st.session_state["finwise_currency"] = currency
    st.session_state["finwise_goal"] = goal
    st.session_state["finwise_month"] = month_label
    st.session_state["finwise_inputs"] = {
        "monthly_income": money(income, currency),
        "total_expenses": money(metrics["total_expenses"], currency),
        "remaining_income": money(metrics["remaining_income"], currency),
        "savings": money(savings, currency),
        "savings_ratio": metrics["savings_ratio"],
        "expense_ratio": metrics["expense_ratio"],
        "financial_goal": goal,
        "expense_breakdown": json.dumps({k: money(v, currency) for k,v in expenses.items()}, ensure_ascii=False),
    }
    st.session_state.pop("finwise_analysis", None)
    st.session_state.pop("finwise_narrative", None)

if "finwise_metrics" in st.session_state:
    m = st.session_state["finwise_metrics"]
    cur = st.session_state["finwise_currency"]
    inputs = st.session_state["finwise_inputs"]
    st.markdown('<div class="section-kicker">02 / Deterministic financial overview</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Monthly income", money(m["monthly_income"],cur), "Entered amount")
    with c2: metric_card("Total expenses", money(m["total_expenses"],cur), f'{m["expense_ratio"]:.1f}% of income')
    with c3: metric_card("Remaining balance", money(m["remaining_income"],cur), "Income minus expenses")
    with c4: metric_card("Current savings", money(m["current_savings"],cur), f'{m["savings_ratio"]:.1f}% of income')
    left,right = st.columns([1.15,1])
    with left:
        st.markdown("#### Spending composition")
        chart_df = pd.DataFrame([{"Category":k,"Amount":v} for k,v in m["expense_breakdown"].items() if v > 0])
        if not chart_df.empty:
            fig = px.pie(chart_df, names="Category", values="Amount", hole=.68, color_discrete_sequence=BRAND_COLORS)
            fig.update_layout(
                height=360, margin=dict(l=0, r=0, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=("#1d2a52" if day else "#dce7ff"), family="DM Sans, Segoe UI, sans-serif", size=12),
                legend=dict(orientation="h", yanchor="top", y=-.04, xanchor="center", x=.5, font=dict(size=11)),
                hoverlabel=dict(bgcolor=("#ffffff" if day else "#0b1530"), bordercolor="#8c7cff", font=dict(color=("#0b1530" if day else "#edf2ff"), size=13)),
                uniformtext=dict(minsize=10, mode="hide"),
                annotations=[dict(text=f"<span style='font-size:10px;color:{'#5b6f9c' if day else '#9eafd1'}'>TOTAL EXPENSES</span><br><b style='font-size:17px'>{money(m['total_expenses'], cur)}</b>", x=.5, y=.5, showarrow=False, font=dict(color=("#0b1530" if day else "#edf2ff")))],
            )
            fig.update_traces(
                textposition="inside", textinfo="percent", insidetextorientation="horizontal",
                marker=dict(line=dict(color=("#f4f7ff" if day else "#0b1530"), width=3)),
                hovertemplate="<b>%{label}</b><br>" + cur + " %{value:,.2f}<br>%{percent}<extra></extra>",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Add expenses to see the spending breakdown.")
    with right:
        st.markdown("#### Financial health snapshot")
        st.markdown(f'<div class="glass"><div class="metric-label">PYTHON PRELIMINARY SCORE</div><div class="metric-value">{m["preliminary_score"]}<span style="font-size:14px;color:#9eafd4"> / 100</span></div><div class="metric-note">{score_band(m["preliminary_score"])}</div></div>', unsafe_allow_html=True)
        st.progress(m["preliminary_score"]/100)
        st.markdown(f"**Rule-based risk indicator:** `{risk_band(m)}`")
        st.caption("This transparent heuristic is educational and separate from the AI-generated score.")
        if m["remaining_income"] < 0:
            st.error("Expenses exceed income. Review essential costs and debt commitments.")
        elif m["remaining_income"] == 0:
            st.warning("Your budget has no remaining balance after listed expenses.")
        else:
            st.success("Your listed expenses are within your monthly income.")
    with st.expander("LangChain message architecture · System / Human / AI"):
        demo_messages = message_demo(json.dumps({"income": money(m["monthly_income"], cur), "expenses": money(m["total_expenses"], cur), "goal": st.session_state["finwise_goal"]}))
        for message in demo_messages:
            role = message.__class__.__name__.replace("Message", "").upper()
            st.markdown(f"**{role}**")
            st.code(str(message.content), language="text")

    st.markdown('<div class="section-kicker">03 / AI-powered financial insights</div>', unsafe_allow_html=True)
    if not effective_key:
        st.warning("Add an OpenAI API key in the sidebar or configure OPENAI_API_KEY in Streamlit Secrets to generate AI insights. Python calculations above work without a key.")
    else:
        if st.button("Generate AI financial analysis", type="primary", use_container_width=True):
            try:
                llm = build_llm(effective_key, model)
                loader = st.empty()
                loader.markdown(LOADER_HTML, unsafe_allow_html=True)
                try:
                    analysis = run_analysis(llm, inputs)
                finally:
                    loader.empty()
                st.session_state["finwise_analysis"] = analysis
                st.session_state["finwise_narrative"] = ""
                st.session_state["finwise_llm_ready"] = True
            except Exception as exc:
                st.error(f"AI analysis could not be completed: {exc}")
        if st.session_state.get("finwise_analysis"):
            analysis = st.session_state["finwise_analysis"]
            score = analysis["financial_health_score"]
            a,b,c = st.columns(3)
            with a: metric_card("AI financial health", f"{score}/100", score_band(score))
            with b: metric_card("AI risk level", analysis["risk_level"], "Educational indicator")
            with c: metric_card("Your goal", st.session_state["finwise_goal"], "Selected objective")
            st.progress(score/100)
            tabs = st.tabs(["Overview", "Spending analysis", "Priorities", "Action plan"])
            with tabs[0]:
                st.markdown("#### Financial summary")
                st.write(analysis["financial_summary"])
                st.markdown("#### Budget recommendations")
                for item in analysis["budget_recommendations"]: st.markdown(f"- {item}")
                st.markdown("#### Savings strategy")
                for item in analysis["savings_strategy"]: st.markdown(f"- {item}")
            with tabs[1]:
                for item in analysis["spending_analysis"]:
                    with st.expander(item["category"]):
                        st.write(item["observation"])
                        st.info(item["recommendation"])
            with tabs[2]:
                for i,item in enumerate(analysis["top_priorities"],1): st.markdown(f"**{i}.** {item}")
            with tabs[3]:
                for i,item in enumerate(analysis["next_month_action_plan"],1): st.markdown(f"**{i}.** {item}")
            st.markdown("#### Live narrative")
            if st.button("Stream a plain-language recommendation"):
                try:
                    llm = build_llm(effective_key, model)
                    st.write_stream(stream_recommendations(llm, inputs))
                except Exception as exc:
                    st.error(f"Streaming could not be completed: {exc}")
    st.markdown('<div class="small-muted">Python computes the financial metrics and preliminary score deterministically. The AI score and recommendations are model-generated educational interpretations, not guaranteed or regulated financial assessments.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="section-kicker">02 / Your insight preview</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass"><h3>Clarity starts with the numbers.</h3><p class="small-muted">Complete your monthly snapshot and select <b>Analyse my budget</b>. FinWise will calculate your cash flow first, then let you request AI-generated educational insights.</p><div class="preview-grid"><div class="preview-chip"><b>Step 1</b>Python calculates your cash flow and preliminary score</div><div class="preview-chip"><b>Step 2</b>Explore your spending composition</div><div class="preview-chip"><b>Step 3</b>Request AI-generated educational insights</div></div></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="small-muted">FINWISE AI · EDUCATIONAL PROTOTYPE · No bank connection · No transactions · No guaranteed financial outcomes</div>', unsafe_allow_html=True)