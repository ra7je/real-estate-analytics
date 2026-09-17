
import streamlit as st
import pandas as pd
import altair as alt
from streamlit_autorefresh import st_autorefresh

# ============================================================
# REAL ESTATE ANALYTICS - PRODUCTION STYLE STREAMLIT DASHBOARD
# Purpose:
#   Present real-estate KPIs, trends, city performance,
#   developer performance and property analytics in a
#   professional business-dashboard format.
#
# Data source:
#   REAL_ESTATE_ANALYTICS.SEMANTIC.VW_TRANSACTION_ANALYTICS
#
# Dashboard pages:
#   1. Executive Summary
#   2. City Insights
#   3. Developer Performance
#   4. Property Explorer
#
# Important:
#   The dashboard reads the semantic view dynamically.
#   When Snowpipe + downstream automation loads new data,
#   rerunning/refreshing the Streamlit app reflects the data.
#   Streamlit width uses the current width='stretch' API.
# ============================================================

# ============================================================
# AUTOMATIC DATA REFRESH
# ============================================================
st.set_page_config(
    page_title="Real Estate Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Re-run the full dashboard every 60 seconds so newly loaded
# Snowflake records appear automatically after Snowpipe/tasks finish.
st_autorefresh(interval=60_000, key="real_estate_auto_refresh")

# ============================================================
# PROFESSIONAL DASHBOARD STYLING
# ============================================================

st.markdown(
    """
    <style>
    /* ==========================================================
       CLEAN SINGLE-VIEW BI DASHBOARD
       UI ONLY — Snowflake/data logic is unchanged.
       ========================================================== */

    .main .block-container {
        max-width: 1480px;
        padding: 0.10rem 0.85rem 0.10rem 0.85rem;
        margin-top: 0 !important;
    }

    [data-testid="stAppViewContainer"] .main {
        padding-top: 0 !important;
    }

    [data-testid="stHeader"] {
        height: 1.7rem;
    }

    /* Header */
    .top-title {
        font-size: 24px;
        font-weight: 750;
        line-height: 1.0;
        color: #252b38;
        margin: 0;
    }

    .top-subtitle {
        font-size: 11px;
        line-height: 1.0;
        color: #7b8494;
        margin-top: 4px;
    }

    /* Navigation */
    div[data-testid="stRadio"] {
        margin: 0 !important;
    }

    div[data-testid="stRadio"] > div {
        gap: 0.10rem;
    }

    div[data-testid="stRadio"] label {
        padding: 3px 9px !important;
        font-size: 12px !important;
        line-height: 1.1 !important;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e6eb;
        border-radius: 8px;
        padding: 7px 10px;
        min-height: 58px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        line-height: 1.0 !important;
        color: #697386 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 20px !important;
        line-height: 1.05 !important;
        font-weight: 720 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Page titles: reserve real space so subtitles/charts never overlap. */
    .dashboard-title {
        font-size: 20px;
        font-weight: 750;
        line-height: 1.05;
        color: #252b38;
        margin: 3px 0 0 0;
    }

    .dashboard-subtitle {
        font-size: 10px;
        line-height: 1.15;
        color: #7b8494;
        margin: 2px 0 5px 0;
    }

    .section-title {
        font-size: 13px;
        font-weight: 700;
        line-height: 1.15;
        color: #303746;
        margin: 5px 0 1px 0;
        min-height: 15px;
    }

    /* Every chart gets its own title row and its own vertical box. */
    .chart-box {
        background: #ffffff;
        border: 1px solid #e6e9ee;
        border-radius: 7px;
        padding: 5px 7px 2px 7px;
        box-sizing: border-box;
        overflow: hidden;
    }

    /* Tight, predictable Streamlit spacing. */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.45rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.18rem;
    }

    /* Filter popover */
    div[data-testid="stPopoverBody"] {
        width: min(1000px, 92vw) !important;
    }

    div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] {
        gap: 0.45rem;
    }

    div[data-testid="stDateInput"] label,
    div[data-testid="stMultiSelect"] label {
        font-size: 10px !important;
        margin-bottom: 1px !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 32px !important;
        border-radius: 6px !important;
        font-size: 11px !important;
    }

    /* Hide Streamlit footer. */
    footer {
        visibility: hidden;
    }

    /* Avoid horizontal overflow. */
    html, body {
        overflow-x: hidden !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================
# Works on Streamlit Community Cloud using [connections.snowflake]
# secrets, and also works in Streamlit in Snowflake.

# The connection is periodically recreated so a long-lived Streamlit
# session cannot keep using an expired Snowflake authentication token.
conn = st.connection("snowflake", ttl=300)

# ============================================================
# LOAD SEMANTIC DATA
# ============================================================

QUERY = """
SELECT
    TXN_ID,
    TXN_DATE,
    CITY_NAME,
    REGION,
    CITY_CLASS,
    DEVELOPER_NAME,
    SEGMENT,
    PROPERTY_TYPE,
    BHK,
    PROJECT_STATUS,
    SALES_CHANNEL,
    TXN_STATUS,
    LIST_PRICE_LAKHS,
    DISCOUNT_PCT,
    SALE_PRICE_LAKHS,
    NET_SALE_PRICE
FROM REAL_ESTATE_ANALYTICS.SEMANTIC.VW_TRANSACTION_ANALYTICS
"""

# ttl=0 disables query-result caching, so every dashboard rerun reads
# the current contents of the Snowflake semantic view. If a cached
# connection has become stale, reset it once and retry the query.
try:
    df = conn.query(QUERY, ttl=0, show_spinner=False)
except Exception as exc:
    if "390114" in str(exc) or "Authentication token has expired" in str(exc):
        conn.reset()
        df = conn.query(QUERY, ttl=0, show_spinner=False)
    else:
        raise

if df.empty:
    st.warning("No transaction data is currently available.")
    st.stop()

df["TXN_DATE"] = pd.to_datetime(df["TXN_DATE"], errors="coerce").dt.date
df["BHK"] = df["BHK"].astype("string").fillna("Unknown")

# ============================================================
# DISPLAY FORMATTING HELPERS
# ============================================================

def format_lakhs(value):
    """Format INR values stored in lakhs using readable real-estate units."""
    if value is None or pd.isna(value):
        return "₹0"

    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 100:
        return f"{sign}₹{value / 100:,.2f} Cr"
    return f"{sign}₹{value:,.2f} L"


def format_kpi_sales(value):
    """Compact KPI formatter so large values always fit inside KPI cards."""
    if value is None or pd.isna(value):
        return "₹0"

    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 100:
        return f"{sign}₹{value / 100:,.2f} Cr"
    if value >= 1:
        return f"{sign}₹{value:,.1f} L"
    return f"{sign}₹{value:,.2f} L"


def format_price(value):
    if pd.isna(value):
        return "₹0"
    value = float(value)
    if abs(value) >= 100:
        return f"₹{value/100:.2f} Cr"
    return f"₹{value:,.1f} L"

def format_pct(value):
    return f"{float(value):.2f}%"

def clean_numeric_columns(frame):
    # Format both source column names and dashboard display names.
    result = frame.copy()

    sales_cols = ["SALES_VALUE", "Sales Value", "TOTAL_SALES_LAKHS", "Total Sales Value"]
    avg_price_cols = ["AVG_SALE_PRICE", "Avg Sale Price", "AVG_SALE_PRICE_LAKHS", "Average Sale Price"]
    discount_cols = ["AVG_DISCOUNT_PCT", "Avg Discount %", "Average Discount %"]

    for col in sales_cols:
        if col in result.columns:
            result[col] = result[col].map(format_lakhs)

    for col in avg_price_cols:
        if col in result.columns:
            result[col] = result[col].map(format_price)

    for col in discount_cols:
        if col in result.columns:
            result[col] = result[col].map(format_pct)

    return result


# ============================================================
# CLEAN TOP HEADER + NAVIGATION + FILTER POPOVER
# ============================================================
min_date = df["TXN_DATE"].min()
max_date = df["TXN_DATE"].max()

head_left, head_right = st.columns([6.8, 2.2])

with head_left:
    st.markdown(
        """
        <div class="top-title">Real Estate Analytics</div>
        <div class="top-subtitle">Management Analytics Platform</div>
        """,
        unsafe_allow_html=True,
    )

with head_right:
    st.markdown(
        '<div style="text-align:right;font-size:11px;color:#7b8494;padding-top:8px;">'
        'Live Analytics Dashboard</div>',
        unsafe_allow_html=True,
    )

nav_col, filter_col, refresh_col = st.columns([7.3, 1.35, 1.0])

with nav_col:
    page = st.radio(
        "Navigate",
        [
            "Executive Summary",
            "City Insights",
            "Developer Performance",
            "Property Explorer",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

with filter_col:
    with st.popover("🔎 Filters", use_container_width=True):
        st.markdown("**Dashboard Filters**")

        pf1, pf2, pf3, pf4, pf5 = st.columns(5)

        with pf1:
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key=f"date_range_{min_date}_{max_date}_{len(df)}",
            )
        with pf2:
            selected_cities = st.multiselect(
                "City",
                sorted(df["CITY_NAME"].dropna().unique().tolist()),
                default=[],
                placeholder="All Cities",
            )
        with pf3:
            selected_regions = st.multiselect(
                "Region",
                sorted(df["REGION"].dropna().unique().tolist()),
                default=[],
                placeholder="All Regions",
            )
        with pf4:
            selected_city_classes = st.multiselect(
                "City Class",
                sorted(df["CITY_CLASS"].dropna().unique().tolist()),
                default=[],
                placeholder="All Classes",
            )
        with pf5:
            selected_developers = st.multiselect(
                "Developer",
                sorted(df["DEVELOPER_NAME"].dropna().unique().tolist()),
                default=[],
                placeholder="All Developers",
            )

        pf6, pf7, pf8, pf9, pf10 = st.columns(5)

        with pf6:
            selected_segments = st.multiselect(
                "Segment",
                sorted(df["SEGMENT"].dropna().unique().tolist()),
                default=[],
                placeholder="All Segments",
            )
        with pf7:
            selected_property_types = st.multiselect(
                "Property Type",
                sorted(df["PROPERTY_TYPE"].dropna().unique().tolist()),
                default=[],
                placeholder="All Property Types",
            )
        with pf8:
            selected_project_statuses = st.multiselect(
                "Project Status",
                sorted(df["PROJECT_STATUS"].dropna().unique().tolist()),
                default=[],
                placeholder="All Project Statuses",
            )
        with pf9:
            selected_sales_channels = st.multiselect(
                "Sales Channel",
                sorted(df["SALES_CHANNEL"].dropna().unique().tolist()),
                default=[],
                placeholder="All Sales Channels",
            )
        with pf10:
            selected_txn_statuses = st.multiselect(
                "Transaction Status",
                sorted(df["TXN_STATUS"].dropna().unique().tolist()),
                default=[],
                placeholder="All Transaction Statuses",
            )

with refresh_col:
    if st.button("↻ Refresh", use_container_width=True):
        conn.reset()
        st.rerun()

# ============================================================
# APPLY FILTERS
# ============================================================
filtered_df = df.copy()

if len(date_range) == 2:
    # Keep records with a missing date visible when the full date range is selected.
    # If the user narrows the date range, only dates inside that range are shown.
    full_date_range = date_range[0] == min_date and date_range[1] == max_date
    if full_date_range:
        filtered_df = filtered_df[
            filtered_df["TXN_DATE"].isna()
            | (
                (filtered_df["TXN_DATE"] >= date_range[0])
                & (filtered_df["TXN_DATE"] <= date_range[1])
            )
        ]
    else:
        filtered_df = filtered_df[
            (filtered_df["TXN_DATE"] >= date_range[0])
            & (filtered_df["TXN_DATE"] <= date_range[1])
        ]

if selected_cities:
    filtered_df = filtered_df[filtered_df["CITY_NAME"].isin(selected_cities)]
if selected_regions:
    filtered_df = filtered_df[filtered_df["REGION"].isin(selected_regions)]
if selected_city_classes:
    filtered_df = filtered_df[filtered_df["CITY_CLASS"].isin(selected_city_classes)]
if selected_developers:
    filtered_df = filtered_df[filtered_df["DEVELOPER_NAME"].isin(selected_developers)]
if selected_segments:
    filtered_df = filtered_df[filtered_df["SEGMENT"].isin(selected_segments)]
if selected_property_types:
    filtered_df = filtered_df[filtered_df["PROPERTY_TYPE"].isin(selected_property_types)]
if selected_project_statuses:
    filtered_df = filtered_df[filtered_df["PROJECT_STATUS"].isin(selected_project_statuses)]
if selected_sales_channels:
    filtered_df = filtered_df[filtered_df["SALES_CHANNEL"].isin(selected_sales_channels)]
if selected_txn_statuses:
    filtered_df = filtered_df[filtered_df["TXN_STATUS"].isin(selected_txn_statuses)]

# ============================================================
# COMMON CALCULATIONS
# ============================================================
total_transactions = filtered_df["TXN_ID"].nunique()
total_sales = filtered_df["SALE_PRICE_LAKHS"].sum()
avg_sale_price = filtered_df["SALE_PRICE_LAKHS"].mean()
avg_discount = filtered_df["DISCOUNT_PCT"].mean()

cancelled_transactions = (
    filtered_df["TXN_STATUS"].astype(str).str.upper().eq("CANCELLED").sum()
)
cancellation_rate = (
    cancelled_transactions / total_transactions * 100
    if total_transactions > 0 else 0
)

# ============================================================
# COMPACT CHART HELPERS
# ============================================================
def compact_chart(chart, height=160):
    return (
        chart
        .properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelFontSize=9,
            titleFontSize=9,
            labelLimit=95,
            titlePadding=4,
        )
        .configure_legend(labelFontSize=9, titleFontSize=9)
    )

def chart_card(title, chart, height=160):
    # Each chart gets a real title row followed by a controlled chart area.
    # This prevents titles from colliding with the chart canvas.
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )
    st.altair_chart(compact_chart(chart, height=height), width="stretch")

def empty_message():
    st.info("No data available for the selected filters.")

# ============================================================
# PAGE 1 — EXECUTIVE SUMMARY
# ============================================================
if page == "Executive Summary":

    st.markdown(
        '<div class="dashboard-title">Executive Summary</div>'
        '<div class="dashboard-subtitle">Executive performance overview across cities, developers and property segments</div>',
        unsafe_allow_html=True,
    )

    # Row 1: KPI strip — deliberately compact to match a BI dashboard.
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Transactions", f"{total_transactions:,}")
    with k2:
        st.metric("Total Sales", format_kpi_sales(total_sales))
    with k3:
        st.metric("Avg Sale Price", format_price(avg_sale_price))
    with k4:
        st.metric("Avg Discount", format_pct(avg_discount))
    with k5:
        st.metric("Cancellation", format_pct(cancellation_rate))

    # Row 2: sales trend + regional distribution.
    if not filtered_df.empty:
        trend = filtered_df.copy()
        trend["DATE"] = pd.to_datetime(trend["TXN_DATE"], errors="coerce")
        trend = trend.dropna(subset=["DATE"])

        if not trend.empty:
            span = (trend["DATE"].max() - trend["DATE"].min()).days
            if span <= 31:
                trend["PERIOD"] = trend["DATE"].dt.floor("D")
                period_title = "Date"
            elif span <= 180:
                trend["PERIOD"] = trend["DATE"].dt.to_period("W").dt.start_time
                period_title = "Week"
            else:
                trend["PERIOD"] = trend["DATE"].dt.to_period("M").dt.start_time
                period_title = "Month"

            trend = (
                trend.groupby("PERIOD", as_index=False)
                .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
                     TRANSACTIONS=("TXN_ID", "nunique"))
            )

            region = (
                filtered_df.groupby("REGION", as_index=False)
                .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
                .sort_values("SALES_VALUE", ascending=False)
            )

            c1, c2 = st.columns([2.05, 1])
            with c1:
                chart_card(
                    "Sales Trend",
                    alt.Chart(trend)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("PERIOD:T", title=period_title, axis=alt.Axis(format="%b %Y")),
                        y=alt.Y("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                        tooltip=[
                            alt.Tooltip("PERIOD:T", title=period_title, format="%d %b %Y"),
                            alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                            alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                        ],
                    ),
                )
            with c2:
                chart_card(
                    "Sales by Region",
                    alt.Chart(region)
                    .mark_arc(innerRadius=38)
                    .encode(
                        theta=alt.Theta("SALES_VALUE:Q"),
                        color=alt.Color("REGION:N", title="Region"),
                        tooltip=[
                            alt.Tooltip("REGION:N", title="Region"),
                            alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                        ],
                    ),
                )

        # Row 3: top cities + segment mix.
        city = (
            filtered_df.groupby("CITY_NAME", as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
                 TRANSACTIONS=("TXN_ID", "nunique"))
            .sort_values("SALES_VALUE", ascending=False)
            .head(8)
        )

        segment = (
            filtered_df.groupby("SEGMENT", as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
            .sort_values("SALES_VALUE", ascending=False)
        )

        c3, c4 = st.columns([1.25, 1])
        with c3:
            chart_card(
                "Top Cities by Sales",
                alt.Chart(city)
                .mark_bar()
                .encode(
                    x=alt.X("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                    y=alt.Y("CITY_NAME:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("CITY_NAME:N", title="City"),
                        alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                        alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                    ],
                ),
            )
        with c4:
            chart_card(
                "Sales by Segment",
                alt.Chart(segment)
                .mark_arc(innerRadius=38)
                .encode(
                    theta=alt.Theta("SALES_VALUE:Q"),
                    color=alt.Color("SEGMENT:N", title="Segment"),
                    tooltip=[
                        alt.Tooltip("SEGMENT:N", title="Segment"),
                        alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    ],
                ),
            )

# ============================================================
# PAGE 2 — CITY INSIGHTS
# ============================================================
elif page == "City Insights":

    st.markdown(
        '<div class="dashboard-title">City Insights</div>'
        '<div class="dashboard-subtitle">Compare sales activity across cities, regions and city classes</div>',
        unsafe_allow_html=True,
    )

    city_perf = (
        filtered_df.groupby(["CITY_NAME", "REGION", "CITY_CLASS"], as_index=False)
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            AVG_SALE_PRICE=("SALE_PRICE_LAKHS", "mean"),
        )
        .sort_values("SALES_VALUE", ascending=False)
    )

    if city_perf.empty:
        empty_message()
    else:
        top = city_perf.iloc[0]
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Cities in View", f"{city_perf['CITY_NAME'].nunique():,}")
        with k2:
            st.metric("Leading City", str(top["CITY_NAME"]))
        with k3:
            st.metric("Leading City Sales", format_lakhs(top["SALES_VALUE"]))

        city_top = city_perf.head(8)
        region = (
            filtered_df.groupby("REGION", as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
            .sort_values("SALES_VALUE", ascending=False)
        )

        c1, c2 = st.columns([1.35, 1])
        with c1:
            chart_card(
                "Sales by City",
                alt.Chart(city_top)
                .mark_bar()
                .encode(
                    x=alt.X("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                    y=alt.Y("CITY_NAME:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("CITY_NAME:N", title="City"),
                        alt.Tooltip("REGION:N", title="Region"),
                        alt.Tooltip("CITY_CLASS:N", title="Class"),
                        alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    ],
                ),
            )
        with c2:
            chart_card(
                "Sales by Region",
                alt.Chart(region)
                .mark_arc(innerRadius=38)
                .encode(
                    theta=alt.Theta("SALES_VALUE:Q"),
                    color=alt.Color("REGION:N", title="Region"),
                    tooltip=[
                        alt.Tooltip("REGION:N", title="Region"),
                        alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    ],
                ),
            )

        segment_city = (
            filtered_df.groupby(["CITY_NAME", "SEGMENT"], as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
        )

        chart_card(
            "Segment Mix by City",
            alt.Chart(segment_city)
            .mark_bar()
            .encode(
                x=alt.X("CITY_NAME:N", title=None, sort="-y"),
                y=alt.Y("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                color=alt.Color("SEGMENT:N", title="Segment"),
                tooltip=[
                    alt.Tooltip("CITY_NAME:N", title="City"),
                    alt.Tooltip("SEGMENT:N", title="Segment"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                ],
            ),
        )

# ============================================================
# PAGE 3 — DEVELOPER PERFORMANCE
# ============================================================
elif page == "Developer Performance":

    st.markdown(
        '<div class="dashboard-title">Developer Performance</div>'
        '<div class="dashboard-subtitle">Measure developer sales contribution and transaction volume</div>',
        unsafe_allow_html=True,
    )

    dev = (
        filtered_df.groupby("DEVELOPER_NAME", as_index=False)
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            AVG_SALE_PRICE=("SALE_PRICE_LAKHS", "mean"),
        )
        .sort_values("SALES_VALUE", ascending=False)
    )

    if dev.empty:
        empty_message()
    else:
        top = dev.iloc[0]
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Developers in View", f"{dev['DEVELOPER_NAME'].nunique():,}")
        with k2:
            st.metric("Top Developer", str(top["DEVELOPER_NAME"]))
        with k3:
            st.metric("Top Developer Sales", format_lakhs(top["SALES_VALUE"]))

        c1, c2 = st.columns(2)
        with c1:
            chart_card(
                "Top Developers by Sales",
                alt.Chart(dev.head(8))
                .mark_bar()
                .encode(
                    x=alt.X("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                    y=alt.Y("DEVELOPER_NAME:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("DEVELOPER_NAME:N", title="Developer"),
                        alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    ],
                ),
            )
        with c2:
            volume = dev.sort_values("TRANSACTIONS", ascending=False).head(8)
            chart_card(
                "Top Developers by Transactions",
                alt.Chart(volume)
                .mark_bar()
                .encode(
                    x=alt.X("TRANSACTIONS:Q", title="Transactions"),
                    y=alt.Y("DEVELOPER_NAME:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("DEVELOPER_NAME:N", title="Developer"),
                        alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                    ],
                ),
            )

        status = (
            filtered_df.groupby("PROJECT_STATUS", as_index=False)
            .agg(
                TRANSACTIONS=("TXN_ID", "nunique"),
                SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            )
            .sort_values("TRANSACTIONS", ascending=False)
        )

        chart_card(
            "Project Status Mix",
            alt.Chart(status)
            .mark_arc(innerRadius=38)
            .encode(
                theta=alt.Theta("TRANSACTIONS:Q"),
                color=alt.Color("PROJECT_STATUS:N", title="Project Status"),
                tooltip=[
                    alt.Tooltip("PROJECT_STATUS:N", title="Status"),
                    alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                ],
            ),
        )

# ============================================================
# PAGE 4 — PROPERTY EXPLORER
# ============================================================
elif page == "Property Explorer":

    st.markdown(
        '<div class="dashboard-title">Property Explorer</div>'
        '<div class="dashboard-subtitle">Explore property demand across type, segment, BHK and project status</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Property Types", f"{filtered_df['PROPERTY_TYPE'].nunique():,}")
    with k2:
        st.metric("Segments", f"{filtered_df['SEGMENT'].nunique():,}")
    with k3:
        st.metric("BHK Categories", f"{filtered_df['BHK'].nunique():,}")

    c1, c2 = st.columns(2)

    property_type = (
        filtered_df.groupby("PROPERTY_TYPE", as_index=False)
        .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
             TRANSACTIONS=("TXN_ID", "nunique"))
        .sort_values("SALES_VALUE", ascending=False)
    )
    segment = (
        filtered_df.groupby("SEGMENT", as_index=False)
        .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
        .sort_values("SALES_VALUE", ascending=False)
    )

    with c1:
        chart_card(
            "Sales by Property Type",
            alt.Chart(property_type)
            .mark_bar()
            .encode(
                x=alt.X("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                y=alt.Y("PROPERTY_TYPE:N", sort="-x", title=None),
                tooltip=[
                    alt.Tooltip("PROPERTY_TYPE:N", title="Property Type"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                ],
            ),
        )
    with c2:
        chart_card(
            "Sales by Segment",
            alt.Chart(segment)
            .mark_arc(innerRadius=38)
            .encode(
                theta=alt.Theta("SALES_VALUE:Q"),
                color=alt.Color("SEGMENT:N", title="Segment"),
                tooltip=[
                    alt.Tooltip("SEGMENT:N", title="Segment"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                ],
            ),
        )

    c3, c4 = st.columns(2)

    bhk = (
        filtered_df.groupby("BHK", as_index=False)
        .agg(
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            TRANSACTIONS=("TXN_ID", "nunique"),
        )
        .sort_values("BHK")
    )

    status = (
        filtered_df.groupby("PROJECT_STATUS", as_index=False)
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
        )
        .sort_values("TRANSACTIONS", ascending=False)
    )

    with c3:
        chart_card(
            "Sales by BHK",
            alt.Chart(bhk)
            .mark_bar()
            .encode(
                x=alt.X("BHK:N", title="BHK"),
                y=alt.Y("SALES_VALUE:Q", title="Sales (₹ Lakhs)", axis=alt.Axis(format=",.0f")),
                tooltip=[
                    alt.Tooltip("BHK:N", title="BHK"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                    alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                ],
            ),
        )
    with c4:
        chart_card(
            "Project Status Distribution",
            alt.Chart(status)
            .mark_arc(innerRadius=38)
            .encode(
                theta=alt.Theta("TRANSACTIONS:Q"),
                color=alt.Color("PROJECT_STATUS:N", title="Status"),
                tooltip=[
                    alt.Tooltip("PROJECT_STATUS:N", title="Status"),
                    alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                    alt.Tooltip("SALES_VALUE:Q", title="Sales (₹ Lakhs)", format=",.2f"),
                ],
            ),
        )

