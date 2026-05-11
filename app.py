import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import date

from src.database import (
    init_db,
    add_fund,
    get_all_funds,
    get_fund,
    delete_fund,
    add_transaction as db_add_tx,
    get_transactions,
    delete_transaction,
)
from src.tracker import get_fund_summary, get_portfolio_summary, get_transaction_timeline

# ── Page ──
st.set_page_config(page_title="基金投资记录", page_icon="📈", layout="wide")
init_db()

# ── Dark Theme CSS ──
st.markdown("""<style>
/* ===== Design Tokens ===== */
:root {
  --bg-deep: #070b14;
  --bg-surface: #0d1321;
  --bg-card: #141b2d;
  --bg-card-hover: #1b2540;
  --bg-elevated: #1f2a45;
  --text-primary: #e2e8f0;
  --text-secondary: #8896ab;
  --text-muted: #5a6a82;
  --gold: #f0b90b;
  --gold-glow: rgba(240,185,11,0.12);
  --gold-subtle: rgba(240,185,11,0.04);
  --blue: #3b82f6;
  --red: #f23645;
  --green: #00c853;
  --border: rgba(255,255,255,0.06);
  --border-card: rgba(255,255,255,0.08);
  --shadow-card: 0 8px 32px rgba(0,0,0,0.5);
  --shadow-hover: 0 12px 48px rgba(0,0,0,0.6);
  --radius-card: 16px;
  --radius-sm: 10px;
  --radius-xs: 6px;
  --font-num: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}

/* ── Global ── */
.stApp {
  background:
    radial-gradient(ellipse 900px 500px at 10% 0%, rgba(240,185,11,0.025) 0%, transparent 70%),
    radial-gradient(ellipse 900px 500px at 90% 100%, rgba(59,130,246,0.025) 0%, transparent 70%),
    var(--bg-deep) !important;
}
.main > div { background: transparent !important; }
.block-container { max-width: 1200px; padding: 5rem 1rem 1.5rem !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-deep) 100%) !important;
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown { padding: 0 0.5rem; }
section[data-testid="stSidebar"] hr { border-color: var(--border); margin: 1rem 0; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: transparent !important;
  border: none !important;
  border-radius: var(--radius-xs) !important;
  padding: 0.55rem 0.75rem !important;
  margin: 1px 0;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  cursor: pointer;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--gold-subtle) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
  background: var(--gold-glow) !important;
  border-left: 3px solid var(--gold) !important;
  font-weight: 600 !important;
}
.sidebar-summary {
  font-size: 0.82rem;
  color: var(--text-secondary);
  padding: 0 0.5rem;
  display: flex;
  justify-content: space-between;
}
.sidebar-summary span { font-family: var(--font-num); color: var(--text-primary); }

/* ── Metric Cards ── */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 0.5rem;
}
.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  padding: 1rem 1.25rem;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
  animation: cardIn 0.4s ease both;
}
.metric-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius-card);
  padding: 1px;
  background: linear-gradient(135deg, rgba(240,185,11,0.15), transparent 40%, transparent 60%, rgba(59,130,246,0.1));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
.metric-card:hover {
  background: var(--bg-card-hover);
  border-color: rgba(255,255,255,0.12);
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.metric-card .label {
  font-size: 0.78rem;
  color: var(--text-secondary);
  letter-spacing: 0.03em;
  margin-bottom: 0.35rem;
  display: flex;
  align-items: center;
  gap: 4px;
}
.metric-card .value {
  font-size: 1.6rem;
  font-weight: 700;
  font-family: var(--font-num);
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.metric-card .delta {
  font-size: 0.82rem;
  font-family: var(--font-num);
  margin-top: 0.3rem;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.metric-card .delta.up { color: var(--red); }
.metric-card .delta.down { color: var(--green); }
.metric-card .help-icon {
  cursor: help;
  opacity: 0.35;
  font-size: 0.7rem;
  transition: opacity 0.2s;
  margin-left: 2px;
}
.metric-card .help-icon:hover { opacity: 0.7; }

@keyframes cardIn {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
.metric-card:nth-child(1) { animation-delay: 0.02s; }
.metric-card:nth-child(2) { animation-delay: 0.05s; }
.metric-card:nth-child(3) { animation-delay: 0.08s; }
.metric-card:nth-child(4) { animation-delay: 0.11s; }
.metric-card:nth-child(5) { animation-delay: 0.14s; }
.metric-card:nth-child(6) { animation-delay: 0.17s; }

/* ── DataFrames / Tables ── */
[data-testid="stDataFrame"] { background: transparent !important; }
[data-testid="stDataFrame"] thead tr th {
  background: var(--bg-surface) !important;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
  padding: 0.6rem 0.8rem !important;
}
[data-testid="stDataFrame"] tbody tr td {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 0.5rem 0.8rem !important;
  font-size: 0.85rem;
}
[data-testid="stDataFrame"] tbody tr:hover td {
  background: rgba(255,255,255,0.015) !important;
}

/* ── Form Elements ── */
.stSelectbox > div > div,
.stTextInput > div > div,
.stNumberInput > div > div,
.stDateInput > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xs) !important;
  transition: all 0.2s ease;
  color: var(--text-primary) !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div:focus-within,
.stNumberInput > div > div:focus-within,
.stDateInput > div > div:focus-within {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px var(--gold-glow) !important;
}
.stSelectbox > div > div > div { color: var(--text-primary) !important; }
.stTextInput label, .stNumberInput label, .stDateInput label, .stSelectbox label {
  color: var(--text-secondary) !important;
  font-size: 0.85rem !important;
}

/* ── Buttons ── */
.stButton > button {
  background: linear-gradient(135deg, var(--gold), #d4a309) !important;
  color: #070b14 !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: var(--radius-xs) !important;
  padding: 0.4rem 1.25rem !important;
  transition: all 0.2s ease !important;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(240,185,11,0.25) !important;
}
.stButton > button[kind="secondary"] {
  background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
  color: white !important;
}

/* ── Dividers & Headings ── */
hr { border-color: var(--border) !important; margin: 1.25rem 0 !important; }
h1, h2, h3 { font-weight: 700 !important; letter-spacing: -0.02em; color: var(--text-primary); }
h2 { font-size: 1.3rem !important; margin-top: 1.5rem !important; margin-bottom: 0.75rem !important; }

/* ── Info / Warning / Success / Error ── */
.stInfo, .stWarning, .stSuccess, .stError {
  border-radius: var(--radius-xs) !important;
  border: none !important;
}
.stInfo { background: rgba(59,130,246,0.1) !important; color: var(--blue) !important; }
.stWarning { background: rgba(240,185,11,0.1) !important; color: var(--gold) !important; }
.stSuccess { background: rgba(0,200,83,0.1) !important; color: var(--green) !important; }
.stError { background: rgba(242,54,69,0.1) !important; color: var(--red) !important; }

/* ── Expanders & Popovers ── */
.streamlit-expanderHeader {
  background: var(--bg-card) !important;
  border-radius: var(--radius-xs) !important;
  border: 1px solid var(--border);
  padding: 0.5rem 1rem !important;
  font-weight: 500;
}
div[data-testid="stPopover"] > div:first-child > button {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xs) !important;
  color: var(--text-primary) !important;
}

/* ── Charts ── */
.stPlotlyChart { background: transparent !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Selectbox Dropdown ── */
div[data-testid="stSelectbox"] ul {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
}
div[data-testid="stSelectbox"] ul li {
  color: var(--text-primary) !important;
}
div[data-testid="stSelectbox"] ul li:hover {
  background: var(--gold-subtle) !important;
}
</style>""", unsafe_allow_html=True)

# ── Plotly Dark Template ──
_DARK_TMPL = go.layout.Template()
_DARK_TMPL.layout = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="PingFang SC, Microsoft YaHei, sans-serif", color="#e2e8f0", size=12),
    title=dict(font=dict(size=14, color="#e2e8f0")),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=11, color="#5a6a82"),
        title=dict(font=dict(size=12, color="#8896ab")),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=11, color="#5a6a82"),
        title=dict(font=dict(size=12, color="#8896ab")),
    ),
    legend=dict(font=dict(size=11, color="#e2e8f0")),
    hoverlabel=dict(
        bgcolor="#1f2a45",
        font=dict(color="#e2e8f0", size=12),
        bordercolor="rgba(255,255,255,0.1)",
    ),
)
pio.templates["dark_finance"] = _DARK_TMPL

# ── Helpers ────────────────────────────────────────────────

_PROFIT_RED = "#f23645"
_LOSS_GREEN = "#00c853"
_BLUE = "#3b82f6"
_GRAY = "#5a6a82"
_FUND_COLORS = ["#f0b90b", "#3b82f6", "#00c853", "#f23645", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]


def _fmt(v) -> str:
    if v is None:
        return "暂无"
    if v >= 0:
        return f"¥{v:,.2f}"
    return f"-¥{abs(v):,.2f}"


def _pct(v) -> str:
    if v is None:
        return "暂无"
    return f"{v:+.2f}%" if v else f"{v:.2f}%"


def _metric_card(label, value, delta=None, delta_color="normal", help_text=None):
    """Custom HTML metric card: red up = positive, green down = negative (Chinese convention)."""
    delta_html = ""
    if delta is not None:
        if delta_color == "inverse":
            is_up = delta < 0
        else:
            is_up = delta >= 0
        cls = "up" if is_up else "down"
        arrow = "↑" if is_up else "↓"
        formatted = _fmt(delta)
        delta_html = f'<div class="delta {cls}">{arrow} {formatted}</div>'

    help_icon = (
        f'<span class="help-icon" title="{help_text}">&#9432;</span>'
        if help_text
        else ""
    )
    return (
        f'<div class="metric-card">'
        f'<div class="label">{label}{help_icon}</div>'
        f'<div class="value">{value}</div>'
        f"{delta_html}</div>"
    )


def _style_profit(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return f"color:{_PROFIT_RED};font-weight:600"
        if val < 0:
            return f"color:{_LOSS_GREEN};font-weight:600"
    return ""


def _style_status(val):
    if val == "持有中":
        return f"color:{_BLUE};font-weight:600"
    if val == "已清仓":
        return f"color:{_GRAY}"
    return ""


def _fund_options():
    funds = get_all_funds()
    return {f"{f['code']} - {f['name']}": f["id"] for f in funds}, funds


def _tx_type_label(t: str) -> str:
    return "买入" if t == "buy" else "卖出"


# ── Pages ──────────────────────────────────────────────────

def show_dashboard():
    summaries = get_fund_summary()
    if not summaries:
        st.info("👋 还没有投资记录，先在左侧「添加基金」和「添加交易」开始吧。")
        return

    portfolio = get_portfolio_summary(summaries)

    # ── KPI Row (custom metric cards) ──
    profit = portfolio["total_profit"]
    cards = [
        _metric_card("📌 总投入", _fmt(portfolio["total_invested"]),
                      help_text="所有买入操作的总金额"),
        _metric_card("💰 已收回", _fmt(portfolio["total_returned"]),
                      help_text="所有卖出操作的总金额"),
        _metric_card("📈 总收益", _fmt(profit),
                      delta=profit if profit else None,
                      help_text="已清仓基金的收益汇总"),
        _metric_card("🎯 总收益率", _pct(portfolio["profit_rate"]),
                      help_text="总收益 ÷ 总投入"),
        _metric_card("🏦 持有基金",
                      f"{portfolio['active_count']} / {portfolio['fund_count']}",
                      help_text="持有中 / 总数"),
    ]
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)

    st.divider()

    # ── Fund table (styled) ──
    cols = ["code", "name", "status", "total_invested",
            "total_profit", "profit_rate", "holding_days",
            "add_count", "reduce_count", "first_buy"]
    labels = ["基金代码", "基金名称", "状态", "总投入",
              "收益", "收益率", "持有天数",
              "加仓", "减仓", "首次买入"]

    raw = pd.DataFrame(summaries)[cols].copy()
    raw.columns = pd.Index(labels)

    styled = (raw.style
              .map(_style_profit, subset=["收益", "收益率"])
              .map(_style_status, subset=["状态"])
              .format({"总投入": "¥{:.2f}",
                       "收益": lambda x: "暂无" if x is None else f"¥{x:+,.2f}",
                       "收益率": lambda x: "暂无" if x is None else f"{x:+.2f}%",
                       "持有天数": "{:.0f} 天"})
              .map(lambda v: "font-size:.85rem"))

    st.subheader("📋 基金总览")
    st.dataframe(styled, hide_index=True, use_container_width=True)

    # ── Charts ──
    active = [s for s in summaries if s["remaining"] > 0]
    if active:
        col1, col2 = st.columns(2)
        with col1:
            df_pie = pd.DataFrame(active, columns=["name", "remaining"])
            fig = px.pie(df_pie, values="remaining", names="name",
                         title="持仓分布 (按在投金额)",
                         color_discrete_sequence=_FUND_COLORS,
                         hole=0.4)
            fig.update_traces(textposition="inside", textinfo="label+percent",
                              textfont=dict(size=12, color="#e2e8f0"))
            fig.update_layout(template="dark_finance",
                              margin=dict(t=30, b=0, l=0, r=0),
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            closed_funds = [s for s in summaries if s["total_profit"] is not None]
            if closed_funds:
                df_bar = pd.DataFrame(closed_funds)
                df_bar["label"] = df_bar["code"] + " " + df_bar["name"]
                fig = px.bar(df_bar, x="label", y="total_profit",
                             title="各基金收益 (已清仓)",
                             color="total_profit",
                             color_continuous_scale=["#00c853", "#1a1a2e", "#f23645"],
                             text="total_profit")
                fig.update_traces(texttemplate="¥%{text:.2f}", textposition="outside",
                                  textfont=dict(size=11, color="#e2e8f0"))
                fig.update_layout(template="dark_finance",
                                  xaxis_title="", yaxis_title="收益",
                                  margin=dict(t=30, b=0, l=0, r=0),
                                  showlegend=False,
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)


def show_fund_detail():
    options, funds = _fund_options()
    if not options:
        st.info("还没有基金，先去添加吧。")
        return

    sel = st.selectbox("选择基金", list(options.keys()))
    fund_id = options[sel]

    summary = get_fund_summary(fund_id)
    if not summary:
        st.warning("基金数据异常")
        return
    s = summary[0]

    # ── Fund header & KPIs ──
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        st.markdown(f"### {s['code']}")
    with col2:
        st.markdown(f"<span style='font-size:1.4rem;font-weight:600'>{s['name']}</span>",
                    unsafe_allow_html=True)
    with col3:
        badge_bg = "rgba(240,185,11,0.12)" if s["status"] == "持有中" else "rgba(90,106,130,0.12)"
        badge_fg = "#f0b90b" if s["status"] == "持有中" else "#5a6a82"
        st.markdown(
            f"<span style='display:inline-block;padding:2px 14px;border-radius:20px;"
            f"font-size:.85rem;font-weight:500;background:{badge_bg};color:{badge_fg};"
            f"border:1px solid rgba(255,255,255,0.06)'>{s['status']}</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Metric cards row ──
    profit = s["total_profit"]
    rate = s["profit_rate"]
    cards = [
        _metric_card("总投入", _fmt(s["total_invested"])),
        _metric_card("已收回", _fmt(s["total_returned"])),
        _metric_card("在投金额", _fmt(s["remaining"])),
        _metric_card("收益", "暂无" if profit is None else _fmt(profit),
                      delta=profit if profit else None),
        _metric_card("收益率", "暂无" if rate is None else _pct(rate),
                      delta=rate if rate else None),
        _metric_card("持有天数", f"{s['holding_days']} 天"),
    ]
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)

    # ── Add/Reduce counts ──
    col1, col2 = st.columns(2)
    with col1:
        st.metric("加仓次数", f"{s['add_count']} 次",
                  help="加仓日期: " + ", ".join(s["add_dates"]) if s["add_dates"] else None)
    with col2:
        st.metric("减仓次数", f"{s['reduce_count']} 次",
                  help="减仓日期: " + ", ".join(s["reduce_dates"]) if s["reduce_dates"] else None)

    st.divider()

    # ── 交易柱状图 ──
    timeline = get_transaction_timeline(fund_id)
    if timeline:
        df_tl = pd.DataFrame(timeline)
        df_tl["date_parsed"] = pd.to_datetime(df_tl["date"])
        df_tl["type_label"] = df_tl["type"].map({"buy": "买入", "sell": "卖出"})
        df_tl["bar_color"] = df_tl["type"].map({"buy": _BLUE, "sell": _LOSS_GREEN})

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_tl["date_parsed"],
            y=df_tl["amount"],
            name="交易金额",
            marker_color=df_tl["bar_color"],
            text=df_tl.apply(
                lambda r: f"{r['type_label']}<br>¥{r['amount']:,.0f}", axis=1),
            textposition="outside",
            textfont=dict(size=11, family="PingFang SC, Microsoft YaHei"),
            hovertemplate="%{x|%Y-%m-%d}<br>"
                          + "%{text}<br>"
                          + "在投金额: ¥%{customdata:,.2f}<extra></extra>",
            customdata=df_tl[["running_balance"]],
        ))

        fig.update_layout(
            template="dark_finance",
            title="交易记录",
            xaxis=dict(title="", showgrid=False, tickformat="%Y-%m-%d"),
            yaxis=dict(title="金额 (¥)", showgrid=True, zeroline=True),
            hovermode="x unified",
            margin=dict(t=30, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Transaction table ──
    txs = get_transactions(fund_id)
    if txs:
        st.subheader("交易记录")
        df_tx = pd.DataFrame(txs)[["date", "type", "amount", "fee", "shares", "nav", "note", "id"]]
        df_tx.columns = ["日期", "类型", "金额", "手续费", "份额", "净值", "备注", "id"]
        df_tx["类型"] = df_tx["类型"].map({"buy": "买入", "sell": "卖出"})

        styled_tx = (df_tx.drop(columns=["id"]).style
                     .map(lambda v: f"color:{_PROFIT_RED}" if v == "买入" else (
                         f"color:{_LOSS_GREEN}" if v == "卖出" else ""),
                               subset=["类型"])
                     .format({"金额": "¥{:.2f}", "手续费": "¥{:.2f}",
                              "份额": "{:.2f}" if any(df_tx["份额"].notna()) else None,
                              "净值": "{:.4f}" if any(df_tx["净值"].notna()) else None}))

        st.dataframe(styled_tx, hide_index=True, use_container_width=True)

        # ── Delete transaction ──
        with st.popover("🗑️ 删除交易记录", use_container_width=False):
            del_opts = {f"#{r['id']} {r['date']} {_tx_type_label(r['type'])} ¥{r['amount']:.2f}": r["id"]
                        for r in txs}
            if del_opts:
                to_del = st.selectbox("选择要删除的记录", list(del_opts.keys()))
                if st.button("确认删除", type="primary", use_container_width=True):
                    delete_transaction(del_opts[to_del])
                    st.success("已删除")
                    st.rerun()

    # ── Delete fund ──
    with st.expander("⚠️ 危险操作"):
        if st.button("删除该基金及所有交易记录", type="primary"):
            delete_fund(fund_id)
            st.success("已删除")
            st.rerun()


def show_add_fund():
    st.subheader("添加基金")
    with st.form("add_fund_form", clear_on_submit=True):
        code = st.text_input("基金代码 *", max_chars=20,
                             placeholder="如: 110011")
        name = st.text_input("基金名称 *", max_chars=100,
                             placeholder="如: 易方达中小盘混合")
        type_ = st.selectbox("基金类型", ["", "股票型", "混合型",
                                        "债券型", "指数型", "货币型",
                                        "QDII", "FOF", "其他"])
        ok = st.form_submit_button("添加", type="primary", use_container_width=True)

    if ok:
        errs = []
        if not code or not code.strip():
            errs.append("基金代码")
        if not name or not name.strip():
            errs.append("基金名称")
        if errs:
            st.error(f"请填写: {'、'.join(errs)}")
        else:
            try:
                add_fund(code.strip(), name.strip(), type_)
                st.success(f"✅ 基金 {code} {name} 添加成功")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def show_add_transaction():
    options, funds = _fund_options()
    if not options:
        st.info("请先添加基金。")
        return

    st.subheader("添加交易记录")
    with st.form("add_tx_form", clear_on_submit=True):
        fund_sel = st.selectbox("基金 *", list(options.keys()))
        c1, c2 = st.columns(2)
        with c1:
            tx_type = st.selectbox("交易类型 *", ["buy", "sell"],
                                   format_func=_tx_type_label)
        with c2:
            tx_date = st.date_input("交易日期 *", date.today(), max_value=date.today())

        amount = st.number_input("金额 * (买入花费 / 卖出总价)",
                                 min_value=0.0, step=100.0, format="%.2f")

        c1, c2 = st.columns(2)
        with c1:
            shares = st.number_input("份额 (可选)", min_value=0.0, step=100.0, format="%.2f")
        with c2:
            nav = st.number_input("净值/单价 (可选)", min_value=0.0, step=0.01, format="%.4f")

        fee = st.number_input("手续费", min_value=0.0, step=1.0, format="%.2f")
        note = st.text_input("备注", max_chars=200)

        ok = st.form_submit_button("添加", type="primary", use_container_width=True)

    if ok:
        if amount <= 0:
            st.error("金额必须大于 0")
        else:
            db_add_tx(
                fund_id=options[fund_sel],
                type_=tx_type,
                date_=tx_date.isoformat(),
                amount=amount,
                shares=shares if shares > 0 else None,
                nav=nav if nav > 0 else None,
                fee=fee,
                note=note,
            )
            st.success("✅ 交易记录已添加")
            st.rerun()


# ── Sidebar ────────────────────────────────────────────────

with st.sidebar:
    st.title("📈 基金投资记录")
    st.caption(f"v1.0  |  数据: `data/touzi.db`")
    st.divider()
    page = st.radio(
        "导航",
        ["📊 总览", "📋 基金详情", "➕ 添加基金", "➕ 添加交易"],
        label_visibility="collapsed",
    )

    # Quick stats in sidebar
    summaries = get_fund_summary()
    if summaries:
        st.divider()
        pf = get_portfolio_summary(summaries)
        st.markdown(
            f'<div class="sidebar-summary">'
            f"<span>基金 {pf['fund_count']} 只</span>"
            f"<span>在投 <span>{_fmt(pf['total_remaining'])}</span></span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Route ──────────────────────────────────────────────────

if page == "📊 总览":
    show_dashboard()
elif page == "📋 基金详情":
    show_fund_detail()
elif page == "➕ 添加基金":
    show_add_fund()
elif page == "➕ 添加交易":
    show_add_transaction()
