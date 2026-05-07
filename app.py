import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# ── CSS ──
st.markdown("""
<style>
#root > div { font-family: "PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif; }
.st-key-metric_card { background:#fff; border-radius:12px; padding:4px 16px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.st-emotion-cache-1wivap2 { padding:1rem 0; }
h1,h2,h3 { font-weight:600; letter-spacing:.02em; }
hr { margin:0; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────

_PROFIT_RED = "#cf1322"
_LOSS_GREEN = "#389e0d"
_BLUE = "#1677ff"
_GRAY = "#8c8c8c"
_FUND_COLORS = px.colors.qualitative.Set2


def _fmt(v: float) -> str:
    if v >= 0:
        return f"¥{v:,.2f}"
    return f"-¥{abs(v):,.2f}"


def _pct(v: float) -> str:
    return f"{v:+.2f}%" if v else f"{v:.2f}%"


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

    # ── KPI Row ──
    kp1, kp2, kp3, kp4, kp5 = st.columns(5)
    with kp1:
        st.metric("📌 总投入", _fmt(portfolio["total_invested"]),
                  help="所有买入操作的总金额")
    with kp2:
        st.metric("💰 已收回", _fmt(portfolio["total_returned"]),
                  help="所有卖出操作的总金额")
    with kp3:
        delta = portfolio["total_profit"]
        st.metric("📈 总收益", _fmt(portfolio["total_profit"]),
                  delta=_fmt(delta) if delta else None,
                  delta_color="normal" if delta >= 0 else "inverse",
                  help="已清仓基金收益 + 持有中基金已实现收益")
    with kp4:
        st.metric("🎯 总收益率", _pct(portfolio["profit_rate"]),
                  help="总收益 ÷ 总投入")
    with kp5:
        st.metric("🏦 持有基金",
                  f"{portfolio['active_count']} / {portfolio['fund_count']}",
                  help="持有中 / 总数")

    st.divider()

    # ── Fund table (styled) ──
    cols = ["code", "name", "status", "total_invested",
            "total_profit", "profit_rate", "holding_days",
            "buy_count", "sell_count", "first_buy"]
    labels = ["基金代码", "基金名称", "状态", "总投入",
              "收益", "收益率", "持有天数",
              "加仓", "减仓", "首次买入"]

    raw = pd.DataFrame(summaries)[cols].copy()
    raw.columns = pd.Index(labels)

    styled = (raw.style
              .applymap(_style_profit, subset=["收益", "收益率"])
              .applymap(_style_status, subset=["状态"])
              .format({"总投入": "¥{:.2f}",
                       "收益": "¥{:+.2f}",
                       "收益率": "{:+.2f}%",
                       "持有天数": "{:.0f} 天"})
              .applymap(lambda v: "font-size:.85rem"))

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
            fig.update_traces(textposition="inside", textinfo="label+percent")
            fig.update_layout(
                font=dict(family="Microsoft YaHei", size=12),
                margin=dict(t=30, b=0, l=0, r=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_bar = pd.DataFrame(summaries)
            df_bar["label"] = df_bar["code"] + " " + df_bar["name"]
            fig = px.bar(df_bar, x="label", y="total_profit",
                         title="各基金收益",
                         color="total_profit",
                         color_continuous_scale=["#389e0d", "#f5f5f5", "#cf1322"],
                         text="total_profit")
            fig.update_traces(texttemplate="¥%{text:.2f}", textposition="outside")
            fig.update_layout(
                font=dict(family="Microsoft YaHei", size=12),
                xaxis_title="", yaxis_title="收益",
                margin=dict(t=30, b=0, l=0, r=0),
                showlegend=False,
            )
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
        badge_style = ("background:#1677ff10;color:#1677ff;border:1px solid #1677ff30"
                       if s["status"] == "持有中" else
                       "background:#8c8c8c10;color:#8c8c8c;border:1px solid #8c8c8c30")
        st.markdown(
            f"<span style='display:inline-block;padding:2px 14px;border-radius:20px;"
            f"font-size:.9rem;font-weight:500;{badge_style}'>{s['status']}</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    mk1, mk2, mk3, mk4, mk5, mk6 = st.columns(6)
    with mk1:
        st.metric("总投入", _fmt(s["total_invested"]))
    with mk2:
        st.metric("已收回", _fmt(s["total_returned"]))
    with mk3:
        st.metric("在投金额", _fmt(s["remaining"]))
    with mk4:
        delta = s["total_profit"]
        st.metric("收益", _fmt(delta),
                  delta=_fmt(delta) if delta else None,
                  delta_color="normal" if delta >= 0 else "inverse")
    with mk5:
        st.metric("收益率", _pct(s["profit_rate"]),
                  delta_color="normal" if s["profit_rate"] >= 0 else "inverse")
    with mk6:
        st.metric("持有天数", f"{s['holding_days']} 天")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("加仓次数", f"{s['buy_count']} 次",
                  help="加仓日期: " + ", ".join(s["buy_dates"]) if s["buy_dates"] else None)
    with col2:
        st.metric("减仓次数", f"{s['sell_count']} 次",
                  help="减仓日期: " + ", ".join(s["sell_dates"]) if s["sell_dates"] else None)

    st.divider()

    # ── Timeline chart ──
    timeline = get_transaction_timeline(fund_id)
    if timeline:
        df_tl = pd.DataFrame(timeline)
        df_tl["date_parsed"] = pd.to_datetime(df_tl["date"])
        df_tl["type_label"] = df_tl["type"].map({"buy": "买入", "sell": "卖出"})

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_tl["date_parsed"], y=df_tl["running_balance"],
            mode="lines+markers+text",
            name="在投金额",
            line=dict(color=_BLUE, width=2.5),
            marker=dict(
                color=df_tl["type"].map({"buy": _PROFIT_RED, "sell": _LOSS_GREEN}),
                size=10,
                symbol="circle",
            ),
            text=df_tl.apply(
                lambda r: f"{r['type_label']} ¥{r['amount']:.0f}", axis=1),
            textposition="top center",
            textfont=dict(size=10, family="Microsoft YaHei"),
            hovertemplate="%{x|%Y-%m-%d}<br>在投金额: ¥%{y:.2f}<br>"
                          + "%{text}<extra></extra>",
        ))
        fig.update_layout(
            title="投资时间线",
            font=dict(family="Microsoft YaHei", size=12),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="在投金额 (¥)", showgrid=True, gridcolor="#f0f0f0"),
            hovermode="x unified",
            margin=dict(t=30, b=0, l=0, r=0),
            plot_bgcolor="white",
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
                     .applymap(lambda v: f"color:{_PROFIT_RED}" if v == "买入" else (
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
        st.markdown(f"**基金** {pf['fund_count']} 只　|　"
                    f"**在投** {_fmt(pf['total_remaining'])}")

# ── Route ──────────────────────────────────────────────────

if page == "📊 总览":
    show_dashboard()
elif page == "📋 基金详情":
    show_fund_detail()
elif page == "➕ 添加基金":
    show_add_fund()
elif page == "➕ 添加交易":
    show_add_transaction()
