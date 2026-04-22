"""
app.py — Main Finsight application.

Handles all three pages (Dashboard, Add Expense, Budgets), the sidebar,
the light/dark theme system, and Plotly chart rendering. Everything is a
single file to keep the Streamlit routing simple — database calls are
delegated to database.py and insight generation to insights.py.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

from database import (create_table, create_budget_table, add_expense,
                      get_all_expenses, set_budget, get_budgets)
from insights import generate_insights

# Ensure runtime directories exist before any DB calls
try:
    os.makedirs("data",    exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    create_table()
    create_budget_table()
except Exception as e:
    st.error(f"Critical error during application startup: {str(e)}")
    st.stop()

# ── Session state defaults ─────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

DARK = st.session_state.theme == "dark"
now  = datetime.now()

st.set_page_config(
    page_title="Finsight",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Accent palette (same in both themes) ──────────────────────────────────────
P  = "#6366f1"   # indigo  — primary actions, Dashboard hero
V  = "#8b5cf6"   # violet  — gradient partner to indigo
CY = "#06b6d4"   # cyan    — Travel category, Transactions KPI
AM = "#f59e0b"   # amber   — Bills category, Top Category KPI
EM = "#10b981"   # emerald — Other category
RO = "#f43f5e"   # rose    — Shopping category, budget exceeded

# ── Surface tokens that differ between dark and light themes ──────────────────
if DARK:
    BG   = "#080c18"   # page background
    SURF = "#0e1625"   # sidebar background
    CARD = "#141f33"   # card / panel background
    BOR  = "#1e2d47"   # borders and grid lines
    TX1  = "#f1f5f9"   # primary text
    TX2  = "#8899b4"   # secondary text, chart labels
    TX3  = "#445577"   # muted text, section labels
    IB   = "#1a2540"   # input background
    IBR  = "#2a3d5f"   # input border
else:
    BG   = "#f0f4ff"
    SURF = "#ffffff"
    CARD = "#ffffff"
    BOR  = "#dde5f5"
    TX1  = "#0f172a"
    TX2  = "#4a5d80"
    TX3  = "#8899bb"
    IB   = "#f5f7ff"
    IBR  = "#dde5f5"

# ── Category metadata ─────────────────────────────────────────────────────────
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Other"]
CAT_ICON  = {
    "Food": "🍽️", "Travel": "✈️", "Shopping": "🛍️",
    "Bills": "📄", "Entertainment": "🎬", "Other": "📦",
}
CAT_COLOR = {
    "Food": P, "Travel": CY, "Shopping": RO,
    "Bills": AM, "Entertainment": V, "Other": EM,
}

# ── CSS ───────────────────────────────────────────────────────────────────────
# Light mode needs explicit widget overrides because Streamlit's built-in dark
# theme colours the inputs automatically, but the light theme does not.
_widget_light = f"""
    .stTextInput input, .stNumberInput input {{
        background:{IB}!important;color:{TX1}!important;border-color:{IBR}!important;
    }}
    .stSelectbox>div>div, .stMultiSelect>div>div {{
        background:{IB}!important;color:{TX1}!important;border-color:{IBR}!important;
    }}
    .stDateInput>div>div>input {{
        background:{IB}!important;color:{TX1}!important;
    }}
    label, .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stMultiSelect label, .stDateInput label {{
        color:{TX2}!important;
    }}
""" if not DARK else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {{ font-family:'Inter',sans-serif; }}
.stApp {{ background:{BG}; }}

[data-testid="stSidebar"] {{
    background:{SURF}!important;
    border-right:1px solid {BOR}!important;
}}
[data-testid="stSidebarContent"] {{ padding-top:20px!important; }}

/* Hide the deploy toolbar; keep the sidebar toggle visible */
[data-testid="stToolbarActions"] {{ display:none; }}
footer {{ visibility:hidden; }}

{_widget_light}

/* ── Hero banner ── */
.hero {{
    border-radius:20px;
    padding:48px 44px;
    margin-bottom:32px;
    position:relative;
    overflow:hidden;
}}
.hero-chip {{
    display:inline-block;
    font-size:.65rem;
    font-weight:700;
    color:rgba(255,255,255,.5);
    text-transform:uppercase;
    letter-spacing:.14em;
    background:rgba(255,255,255,.1);
    border:1px solid rgba(255,255,255,.15);
    border-radius:100px;
    padding:3px 12px;
    margin-bottom:16px;
}}
.hero-title {{
    font-size:2.6rem;
    font-weight:900;
    color:#fff;
    letter-spacing:-.05em;
    line-height:1;
    margin-bottom:12px;
}}
.hero-sub {{
    color:rgba(255,255,255,.6);
    font-size:.92rem;
    line-height:1.6;
    max-width:520px;
}}
.blob {{
    position:absolute;
    border-radius:50%;
    pointer-events:none;
}}

/* ── KPI cards ── */
.kpi {{
    border-radius:14px;
    padding:22px 20px;
    border:1px solid {BOR};
    background:{CARD};
    border-left:4px solid;
    height:100%;
    transition:box-shadow .2s;
}}
.kpi:hover {{ box-shadow:0 4px 24px rgba(0,0,0,.12); }}
.kpi-label {{
    font-size:.67rem;font-weight:700;color:{TX3};
    text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;
}}
.kpi-value {{
    font-size:1.8rem;font-weight:800;color:{TX1};
    letter-spacing:-.04em;line-height:1;margin-bottom:5px;
}}
.kpi-hint {{ font-size:.73rem;color:{TX2}; }}

/* ── Section label ── */
.sec {{
    font-size:.65rem;font-weight:700;color:{TX3};
    text-transform:uppercase;letter-spacing:.12em;
    margin:28px 0 14px;
    padding-bottom:8px;
    border-bottom:1px solid {BOR};
}}

/* ── Chart wrapper ── */
.chw {{
    background:{CARD};border:1px solid {BOR};
    border-radius:14px;padding:4px;margin-bottom:4px;
}}

/* ── Insight rows ── */
.ins {{
    display:flex;gap:10px;align-items:flex-start;
    padding:13px 15px;border-radius:10px;
    background:{CARD};border:1px solid {BOR};margin-bottom:8px;
}}
.ins .ic {{ font-size:1rem;flex-shrink:0;margin-top:1px; }}
.ins .tx {{ font-size:.85rem;color:{TX2};line-height:1.5; }}

/* ── Budget alert rows ── */
.al {{
    display:flex;gap:12px;border-radius:10px;
    padding:13px 16px;margin-bottom:8px;border:1px solid;
}}
.al.re {{ background:rgba(244,63,94,.07);border-color:rgba(244,63,94,.25); }}
.al.ye {{ background:rgba(245,158,11,.07);border-color:rgba(245,158,11,.25); }}
.al.gn {{ background:rgba(16,185,129,.06);border-color:rgba(16,185,129,.2); }}
.al-t  {{ font-size:.875rem;color:{TX1};font-weight:500; }}
.al-m  {{ font-size:.78rem;color:{TX2};margin-top:2px; }}

/* ── Budget progress rows ── */
.bu {{
    background:{CARD};border:1px solid {BOR};
    border-radius:12px;padding:18px 20px;margin-bottom:10px;
}}
.bu-hd {{
    display:flex;justify-content:space-between;
    align-items:center;margin-bottom:12px;
}}
.bu-cat  {{ font-size:.9rem;font-weight:700;color:{TX1}; }}
.bu-bar  {{ background:{BG};border-radius:4px;height:7px;overflow:hidden;margin-bottom:8px; }}
.bu-nums {{ display:flex;justify-content:space-between;font-size:.78rem;color:{TX2}; }}
.bu-nums strong {{ color:{TX1};font-weight:600; }}

/* ── Empty state ── */
.emp {{
    text-align:center;padding:60px 24px;background:{CARD};
    border:1px solid {BOR};border-radius:16px;
}}
.emp .ei {{ font-size:2.4rem;margin-bottom:12px; }}
.emp .eh {{ font-size:.95rem;color:{TX2};font-weight:600; }}
.emp .es {{ font-size:.82rem;color:{TX3};margin-top:6px; }}

/* ── Sidebar components ── */
.sb-month-card {{
    background:linear-gradient(135deg,{P}22,{V}14);
    border:1px solid {P}40;
    border-radius:14px;padding:18px 16px;margin-bottom:16px;
}}
.sb-month-label {{
    font-size:.62rem;font-weight:700;color:{P};
    text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;
}}
.sb-month-val {{
    font-size:1.7rem;font-weight:900;color:{TX1};
    letter-spacing:-.04em;line-height:1;
}}
.sb-month-sub {{ font-size:.72rem;color:{TX2};margin-top:5px; }}

.sb-nav-label {{
    font-size:.6rem;font-weight:700;color:{TX3};
    text-transform:uppercase;letter-spacing:.12em;
    margin-bottom:8px;
}}

.sb-cat-row {{
    display:flex;align-items:center;gap:8px;
    padding:5px 2px;
}}
.sb-dot  {{ width:8px;height:8px;border-radius:50%;flex-shrink:0; }}
.sb-cn   {{ font-size:.82rem;color:{TX2};flex:1; }}
.sb-ca   {{ font-size:.78rem;font-weight:700;color:{TX1}; }}

.sb-tips {{
    background:{CARD};border:1px solid {BOR};
    border-radius:10px;padding:12px 14px;margin-top:4px;
}}
.sb-tip {{ font-size:.78rem;color:{TX3};line-height:1.6; }}

/* ── Buttons ── */
.stButton>button {{
    border-radius:10px!important;
    font-weight:600!important;
    font-size:.875rem!important;
    padding:9px 16px!important;
    transition:all .2s!important;
}}
.stButton>button[kind="primary"] {{
    background:linear-gradient(135deg,{P},{V})!important;
    border:none!important;color:#fff!important;
}}
.stButton>button[kind="primary"]:hover {{
    transform:translateY(-1px)!important;
    box-shadow:0 8px 24px {P}60!important;
}}
.stButton>button[kind="secondary"] {{
    background:{CARD}!important;
    border:1px solid {BOR}!important;
    color:{TX2}!important;
}}
.stButton>button[kind="secondary"]:hover {{
    border-color:{P}!important;color:{P}!important;
}}
.stDownloadButton>button {{
    background:{CARD}!important;border:1px solid {BOR}!important;
    color:{TX2}!important;border-radius:10px!important;
    font-size:.875rem!important;transition:all .2s!important;
}}
.stDownloadButton>button:hover {{
    border-color:{P}!important;color:{P}!important;
}}

[data-testid="stDataFrame"] {{
    border-radius:10px;overflow:hidden;border:1px solid {BOR}!important;
}}
hr {{ border-color:{BOR}!important; }}
</style>
""", unsafe_allow_html=True)


# ── UI helper functions ────────────────────────────────────────────────────────

def kpi(label, value, hint, color):
    """Render a single KPI card with a coloured left border."""
    st.markdown(
        f'<div class="kpi" style="border-left-color:{color}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-hint">{hint}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def sec(label):
    """Render an uppercase section divider label."""
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)

def hero(title, subtitle, gradient, chip="Finsight"):
    """
    Render a full-width gradient hero banner at the top of a page.

    Each page passes its own gradient so users get a distinct visual per section.
    The decorative blobs are purely CSS — no images needed.
    """
    st.markdown(
        f'<div class="hero" style="background:{gradient}">'
        f'  <div class="blob" style="top:-60px;right:-60px;width:240px;height:240px;'
        f'       background:rgba(255,255,255,.08)"></div>'
        f'  <div class="blob" style="bottom:-80px;right:100px;width:300px;height:300px;'
        f'       background:rgba(255,255,255,.04)"></div>'
        f'  <div class="blob" style="top:40%;left:-40px;width:120px;height:120px;'
        f'       background:rgba(255,255,255,.06)"></div>'
        f'  <div class="hero-chip">{chip}</div>'
        f'  <div class="hero-title">{title}</div>'
        f'  <div class="hero-sub">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def plotly_fig(fig, height=340):
    """
    Apply a consistent transparent theme to any Plotly figure.

    Removes the modebar clutter, sets fonts and gridline colours to match the
    active theme tokens, and returns the mutated figure for chaining.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=TX2, size=11),
        margin=dict(l=0, r=0, t=32, b=0),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TX2)),
        modebar_remove=[
            "zoom", "pan", "select", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d", "toImage",
        ],
    )
    fig.update_xaxes(gridcolor=BOR, zerolinecolor=BOR, tickfont_color=TX3)
    fig.update_yaxes(gridcolor=BOR, zerolinecolor=BOR, tickfont_color=TX3)
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Brand header
    st.markdown(
        f'<div style="padding:0 0 20px">'
        f'  <div style="font-size:1.25rem;font-weight:900;color:{TX1};letter-spacing:-.03em">'
        f'    💡 Finsight'
        f'  </div>'
        f'  <div style="font-size:.7rem;color:{TX3};margin-top:3px;letter-spacing:.03em">'
        f'    Smart Personal Finance'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Pull all expenses upfront so the sidebar stats stay current on every rerun
    raw_all     = get_all_expenses()
    month_total = 0
    month_count = 0
    cat_month   = {}
    if raw_all:
        df_all = pd.DataFrame(raw_all, columns=["ID", "Amount", "Category", "Date", "Note"])
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        mdf = df_all[
            (df_all["Date"].dt.month == now.month) &
            (df_all["Date"].dt.year  == now.year)
        ]
        month_total = mdf["Amount"].sum()
        month_count = len(mdf)
        cat_month   = mdf.groupby("Category")["Amount"].sum().to_dict()

    month_name = now.strftime("%B %Y")
    st.markdown(
        f'<div class="sb-month-card">'
        f'  <div class="sb-month-label">📅 {month_name}</div>'
        f'  <div class="sb-month-val">₹{month_total:,.0f}</div>'
        f'  <div class="sb-month-sub">'
        f'    {month_count} transaction{"s" if month_count != 1 else ""} this month'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Navigation buttons — active page gets a filled primary style
    st.markdown(f'<div class="sb-nav-label">Navigation</div>', unsafe_allow_html=True)
    nav_items = [("🏠", "Dashboard"), ("➕", "Add Expense"), ("💰", "Budgets")]
    for icon, name in nav_items:
        active = st.session_state.page == name
        if st.button(
            f"{icon}  {name}",
            key=f"nav_{name}",
            width="stretch",
            type="primary" if active else "secondary",
        ):
            st.session_state.page = name
            st.rerun()

    st.divider()

    # Per-category spend breakdown for the current month
    if cat_month:
        st.markdown(
            f'<div class="sb-nav-label">Spending by Category</div>',
            unsafe_allow_html=True,
        )
        for cat, amt in sorted(cat_month.items(), key=lambda x: -x[1]):
            color = CAT_COLOR.get(cat, EM)
            icon  = CAT_ICON.get(cat, "📦")
            st.markdown(
                f'<div class="sb-cat-row">'
                f'  <div class="sb-dot" style="background:{color}"></div>'
                f'  <span class="sb-cn">{icon} {cat}</span>'
                f'  <span class="sb-ca">₹{amt:,.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.divider()

    st.markdown(
        f'<div class="sb-tips">'
        f'  <div class="sb-tip">💡 Track every expense to get accurate spending insights and smarter budget alerts.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # Light / dark theme toggle
    st.markdown(f'<div class="sb-nav-label">Appearance</div>', unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button(
            "☀️ Light",
            width="stretch",
            type="primary" if not DARK else "secondary",
        ):
            st.session_state.theme = "light"
            st.rerun()
    with tc2:
        if st.button(
            "🌙 Dark",
            width="stretch",
            type="primary" if DARK else "secondary",
        ):
            st.session_state.theme = "dark"
            st.rerun()

    st.markdown(
        f'<div style="text-align:center;font-size:.65rem;color:{TX3};margin-top:16px;">'
        f'  v1.0 · Finsight</div>',
        unsafe_allow_html=True,
    )


# ── Page routing ───────────────────────────────────────────────────────────────
page = st.session_state.page


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if page == "Dashboard":
    hero(
        "Your Dashboard",
        "Track, analyze, and understand every rupee — all in one place.",
        f"linear-gradient(135deg, {P} 0%, {V} 55%, {CY} 100%)",
        chip="📊 Finsight · Overview",
    )

    raw = get_all_expenses()
    if not raw:
        st.markdown(
            '<div class="emp"><div class="ei">📭</div>'
            '<div class="eh">No expenses yet</div>'
            '<div class="es">Go to <b>Add Expense</b> to record your first transaction.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    df = pd.DataFrame(raw, columns=["ID", "Amount", "Category", "Date", "Note"])
    df["Date"] = pd.to_datetime(df["Date"])

    # Date range + category filters
    sec("Filters")
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    with fc1: start = st.date_input("Start date", df["Date"].min().date())
    with fc2: end   = st.date_input("End date",   df["Date"].max().date())
    with fc3:
        cats = st.multiselect(
            "Categories",
            df["Category"].unique().tolist(),
            default=df["Category"].unique().tolist(),
        )

    fdf = df[
        (df["Date"].dt.date >= start) &
        (df["Date"].dt.date <= end)   &
        (df["Category"].isin(cats))
    ]

    # Summary KPIs
    sec("Overview")
    total = fdf["Amount"].sum()
    count = len(fdf)
    avg   = fdf["Amount"].mean() if count else 0
    top   = fdf.groupby("Category")["Amount"].sum().idxmax() if count else "—"

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Total Spent",   f"₹{total:,.2f}",               f"{count} transactions", P)
    with k2: kpi("Transactions",  str(count),                      "in selected range",     CY)
    with k3: kpi("Avg per Entry", f"₹{avg:,.2f}",                 "across categories",     V)
    with k4: kpi("Top Category",  f"{CAT_ICON.get(top,'')} {top}", "highest spending",      AM)

    # Bar + donut charts side by side
    sec("Spending Breakdown")
    cat_sum = fdf.groupby("Category")["Amount"].sum().reset_index()
    cat_sum.columns = ["Category", "Amount"]
    colors = [CAT_COLOR.get(c, P) for c in cat_sum["Category"]]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chw">', unsafe_allow_html=True)
        fig_bar = go.Figure(go.Bar(
            x=cat_sum["Category"], y=cat_sum["Amount"],
            marker=dict(color=colors, line_width=0),
            text=[f"₹{v:,.0f}" for v in cat_sum["Amount"]],
            textposition="outside",
            textfont=dict(size=11, color=TX2),
            hovertemplate="<b>%{x}</b><br>₹%{y:,.2f}<extra></extra>",
        ))
        fig_bar.update_layout(title=dict(text="By Category", font=dict(color=TX3, size=11)))
        st.plotly_chart(plotly_fig(fig_bar), width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chw">', unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=cat_sum["Category"], values=cat_sum["Amount"],
            hole=0.6,
            marker=dict(colors=colors, line=dict(color=BG, width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color=TX2),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.2f} (%{percent})<extra></extra>",
        ))
        fig_pie.update_layout(
            title=dict(text="Category Share", font=dict(color=TX3, size=11)),
            showlegend=False,
            annotations=[dict(
                text=f"₹{total:,.0f}", x=0.5, y=0.5, showarrow=False,
                font=dict(size=15, color=TX1, family="Inter"),
            )],
        )
        st.plotly_chart(plotly_fig(fig_pie), width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)

    # Monthly spend trend line
    sec("Monthly Trend")
    mon = fdf.copy()
    mon["Month"] = mon["Date"].dt.to_period("M")
    trend = mon.groupby("Month")["Amount"].sum().reset_index()
    trend["Month"] = trend["Month"].astype(str)

    st.markdown('<div class="chw">', unsafe_allow_html=True)
    if trend.empty:
        st.info("No data available for the selected filters.")
    else:
        # Spline smoothing only makes sense with more than one data point
        line_shape = "spline" if len(trend) > 1 else "linear"
        fig_line = go.Figure(go.Scatter(
            x=trend["Month"], y=trend["Amount"],
            mode="lines+markers",
            line=dict(color=P, width=2.5, shape=line_shape),
            marker=dict(color=P, size=7, line=dict(color=BG, width=2)),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.08)",
            hovertemplate="<b>%{x}</b><br>₹%{y:,.2f}<extra></extra>",
        ))
        fig_line.update_layout(
            title=dict(text="Monthly Spending Trend", font=dict(color=TX3, size=11)),
        )
        st.plotly_chart(plotly_fig(fig_line, height=280), width='stretch')
    st.markdown('</div>', unsafe_allow_html=True)

    # Smart insights (left) and budget alerts (right)
    sec("Insights & Budget Status")
    ic, bc = st.columns(2)

    with ic:
        st.markdown(
            f'<div style="font-size:.85rem;font-weight:700;color:{TX1};margin-bottom:12px;">'
            f'🧠 Smart Insights</div>',
            unsafe_allow_html=True,
        )
        ico_list = ["💡", "🏆", "📉", "⚠️", "🔍"]
        for i, text in enumerate(generate_insights(fdf)):
            st.markdown(
                f'<div class="ins">'
                f'<span class="ic">{ico_list[i % len(ico_list)]}</span>'
                f'<span class="tx">{text}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with bc:
        st.markdown(
            f'<div style="font-size:.85rem;font-weight:700;color:{TX1};margin-bottom:12px;">'
            f'🚨 Budget Alerts</div>',
            unsafe_allow_html=True,
        )
        budgets   = get_budgets()
        cat_spend = fdf.groupby("Category")["Amount"].sum()
        shown = False
        for cat, spend in cat_spend.items():
            if cat not in budgets:
                continue
            shown = True
            limit = budgets[cat]
            pct   = spend / limit * 100 if limit > 0 else 0
            ico   = CAT_ICON.get(cat, "📦")
            if spend > limit:
                cls, badge, badge_color = "re", "EXCEEDED",   "#f43f5e"
            elif pct >= 80:
                cls, badge, badge_color = "ye", "NEAR LIMIT", "#f59e0b"
            else:
                cls, badge, badge_color = "gn", "ON TRACK",   "#10b981"
            st.markdown(
                f'<div class="al {cls}">'
                f'  <span style="font-size:1.1rem">{ico}</span>'
                f'  <div style="flex:1">'
                f'    <div class="al-t">{cat}'
                f'      <span style="color:{badge_color};font-size:.7rem;font-weight:700;margin-left:6px">'
                f'        {badge}</span>'
                f'    </div>'
                f'    <div class="al-m">₹{spend:,.2f} of ₹{limit:,.2f} · {pct:.0f}%</div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if not shown:
            st.caption("No budgets configured. Go to **Budgets** to set limits.")

    # Full transactions table with formatted columns
    sec("All Transactions")
    disp = fdf.drop(columns=["ID"]).copy()
    disp["Date"]   = disp["Date"].dt.strftime("%d %b %Y")
    disp["Amount"] = disp["Amount"].apply(lambda x: f"₹{x:,.2f}")
    st.dataframe(disp, width='stretch', hide_index=True)

    # CSV export of the currently filtered view
    sec("Export")
    ec, _ = st.columns([1, 4])
    with ec:
        try:
            csv_data = fdf.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️  Download CSV",
                data=csv_data,
                file_name=f"expenses_{now.strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Failed to generate CSV export: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
#  ADD EXPENSE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Add Expense":
    hero(
        "Add Expense",
        "Log a new transaction and keep your spending data accurate and up to date.",
        f"linear-gradient(135deg, #0891b2 0%, {CY} 60%, #22d3ee 100%)",
        chip="➕ New Transaction",
    )

    # Narrow the form to the centre third of the page for readability
    _, fc, _ = st.columns([1, 2, 1])
    with fc:
        sec("Transaction Details")
        amount   = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        category = st.selectbox(
            "Category", CATEGORIES,
            format_func=lambda c: f"{CAT_ICON.get(c,'')}  {c}",
        )
        date = st.date_input("Date", value=datetime.today().date())
        note = st.text_input("Note", placeholder="Optional — e.g. Lunch at café")
        st.write("")
        if st.button("Add Expense", width="stretch", type="primary"):
            if amount <= 0:
                st.error("Amount must be greater than ₹0")
            else:
                if add_expense(amount, category, str(date), note):
                    st.success(
                        f"✅  ₹{amount:,.2f} added under **{category}**"
                        f" on {date.strftime('%d %b %Y')}"
                    )
                else:
                    st.error("Failed to save the expense due to a database error. Please try again.")

    # Show the five most recent entries below the form as a quick confirmation
    raw = get_all_expenses()
    if raw:
        df_all = pd.DataFrame(raw, columns=["ID", "Amount", "Category", "Date", "Note"])
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        recent = (
            df_all.sort_values("Date", ascending=False)
                  .head(5)
                  .drop(columns=["ID"])
                  .copy()
        )
        recent["Date"]   = recent["Date"].dt.strftime("%d %b %Y")
        recent["Amount"] = recent["Amount"].apply(lambda x: f"₹{x:,.2f}")

        _, rc, _ = st.columns([1, 2, 1])
        with rc:
            sec("Recent Transactions")
            st.dataframe(recent, width='stretch', hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
#  BUDGETS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Budgets":
    hero(
        "Budget Manager",
        "Set monthly spending limits and get real-time alerts before you overspend.",
        f"linear-gradient(135deg, #b45309 0%, {AM} 55%, #fbbf24 100%)",
        chip="💰 Spending Limits",
    )

    _, fc, _ = st.columns([1, 2, 1])
    with fc:
        sec("Set / Update Budget")
        b_cat = st.selectbox(
            "Category", CATEGORIES,
            format_func=lambda c: f"{CAT_ICON.get(c,'')}  {c}",
            key="bcat",
        )
        b_amt = st.number_input(
            "Monthly Budget (₹)", min_value=0.0, step=100.0, format="%.2f"
        )
        st.write("")
        if st.button("Save Budget", width="stretch", type="primary"):
            if b_amt <= 0:
                st.error("Budget must be greater than ₹0")
            else:
                if set_budget(b_cat, b_amt):
                    st.success(f"✅  Budget for **{b_cat}** set to ₹{b_amt:,.2f}")
                    st.rerun()
                else:
                    st.error("Failed to save the budget due to a database error. Please try again.")

    budgets = get_budgets()
    if budgets:
        # Load current-month spending to compare against each budget limit
        sec(f"Monthly Overview · {now.strftime('%B %Y')}")
        raw = get_all_expenses()
        cat_sp = {}
        if raw:
            df_all = pd.DataFrame(raw, columns=["ID", "Amount", "Category", "Date", "Note"])
            df_all["Date"] = pd.to_datetime(df_all["Date"])
            mdf = df_all[
                (df_all["Date"].dt.month == now.month) &
                (df_all["Date"].dt.year  == now.year)
            ]
            cat_sp = mdf.groupby("Category")["Amount"].sum().to_dict()

        for cat, limit in budgets.items():
            spent = cat_sp.get(cat, 0)
            pct   = min(spent / limit * 100, 100) if limit > 0 else 0
            ico   = CAT_ICON.get(cat, "📦")
            if spent > limit:
                bar_color, status, status_color = "#f43f5e", "EXCEEDED",   "#f43f5e"
            elif pct >= 80:
                bar_color, status, status_color = "#f59e0b", "NEAR LIMIT", "#f59e0b"
            else:
                bar_color, status, status_color = "#10b981", "ON TRACK",   "#10b981"
            st.markdown(
                f'<div class="bu">'
                f'  <div class="bu-hd">'
                f'    <span class="bu-cat">{ico}  {cat}</span>'
                f'    <span style="font-size:.72rem;font-weight:700;color:{status_color}">{status}</span>'
                f'  </div>'
                f'  <div class="bu-bar">'
                f'    <div style="background:{bar_color};width:{pct:.1f}%;'
                f'         height:100%;border-radius:4px;"></div>'
                f'  </div>'
                f'  <div class="bu-nums">'
                f'    <span>Spent: <strong>₹{spent:,.2f}</strong></span>'
                f'    <span>Limit: <strong>₹{limit:,.2f}</strong></span>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="emp"><div class="ei">📋</div>'
            '<div class="eh">No budgets yet</div>'
            '<div class="es">Use the form above to set your first spending limit.</div>'
            '</div>',
            unsafe_allow_html=True,
        )