
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
# Re-run the full dashboard every 60 seconds so newly loaded
# Snowflake records appear automatically after Snowpipe/tasks finish.
st_autorefresh(interval=60_000, key="real_estate_auto_refresh")

st.set_page_config(
    page_title="Real Estate Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PROFESSIONAL DASHBOARD STYLING
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f8fa;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #6b7280;
    }

    [data-testid="stMetricValue"] {
        font-size: 22px;
        font-weight: 700;
        line-height: 1.15;
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
        word-break: keep-all;
    }

    [data-testid="stMetric"] {
        min-width: 0;
    }

    [data-testid="stMetricLabel"] {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .dashboard-subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-top: -12px;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .status-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    footer {
        visibility: hidden;
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

conn = st.connection("snowflake")
session = conn.session()

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

df = session.sql(QUERY).to_pandas()

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
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("Real Estate Analytics")
st.sidebar.caption("Management Analytics Platform")

page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Summary",
        "City Insights",
        "Developer Performance",
        "Property Explorer",
    ],
)

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

# ============================================================
# SIDEBAR FILTERS
# ============================================================

min_date = df["TXN_DATE"].min()
max_date = df["TXN_DATE"].max()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

cities = sorted(df["CITY_NAME"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect(
    "City",
    cities,
    default=cities,
)

regions = sorted(df["REGION"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Region",
    regions,
    default=regions,
)

city_classes = sorted(df["CITY_CLASS"].dropna().unique().tolist())
selected_city_classes = st.sidebar.multiselect(
    "City Class",
    city_classes,
    default=city_classes,
)

developers = sorted(df["DEVELOPER_NAME"].dropna().unique().tolist())
selected_developers = st.sidebar.multiselect(
    "Developer",
    developers,
    default=developers,
)

segments = sorted(df["SEGMENT"].dropna().unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Segment",
    segments,
    default=segments,
)

property_types = sorted(df["PROPERTY_TYPE"].dropna().unique().tolist())
selected_property_types = st.sidebar.multiselect(
    "Property Type",
    property_types,
    default=property_types,
)

project_statuses = sorted(df["PROJECT_STATUS"].dropna().unique().tolist())
selected_project_statuses = st.sidebar.multiselect(
    "Project Status",
    project_statuses,
    default=project_statuses,
)

sales_channels = sorted(df["SALES_CHANNEL"].dropna().unique().tolist())
selected_sales_channels = st.sidebar.multiselect(
    "Sales Channel",
    sales_channels,
    default=sales_channels,
)

txn_statuses = sorted(df["TXN_STATUS"].dropna().unique().tolist())
selected_txn_statuses = st.sidebar.multiselect(
    "Transaction Status",
    txn_statuses,
    default=txn_statuses,
)

# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["TXN_DATE"] >= date_range[0])
        & (filtered_df["TXN_DATE"] <= date_range[1])
    ]

if selected_cities:
    filtered_df = filtered_df[
        filtered_df["CITY_NAME"].isin(selected_cities)
    ]

if selected_regions:
    filtered_df = filtered_df[
        filtered_df["REGION"].isin(selected_regions)
    ]

if selected_city_classes:
    filtered_df = filtered_df[
        filtered_df["CITY_CLASS"].isin(selected_city_classes)
    ]

if selected_developers:
    filtered_df = filtered_df[
        filtered_df["DEVELOPER_NAME"].isin(selected_developers)
    ]

if selected_segments:
    filtered_df = filtered_df[
        filtered_df["SEGMENT"].isin(selected_segments)
    ]

if selected_property_types:
    filtered_df = filtered_df[
        filtered_df["PROPERTY_TYPE"].isin(selected_property_types)
    ]

if selected_project_statuses:
    filtered_df = filtered_df[
        filtered_df["PROJECT_STATUS"].isin(selected_project_statuses)
    ]

if selected_sales_channels:
    filtered_df = filtered_df[
        filtered_df["SALES_CHANNEL"].isin(selected_sales_channels)
    ]

if selected_txn_statuses:
    filtered_df = filtered_df[
        filtered_df["TXN_STATUS"].isin(selected_txn_statuses)
    ]

# ============================================================
# COMMON KPI CALCULATIONS
# ============================================================

total_transactions = filtered_df["TXN_ID"].nunique()
total_sales = filtered_df["SALE_PRICE_LAKHS"].sum()
total_net_sales = filtered_df["NET_SALE_PRICE"].sum()
avg_sale_price = filtered_df["SALE_PRICE_LAKHS"].mean()
avg_discount = filtered_df["DISCOUNT_PCT"].mean()

cancelled_transactions = (
    filtered_df["TXN_STATUS"]
    .astype(str)
    .str.upper()
    .eq("CANCELLED")
    .sum()
)

cancellation_rate = (
    cancelled_transactions / total_transactions * 100
    if total_transactions > 0
    else 0
)

# ============================================================
# PAGE 1 - EXECUTIVE SUMMARY
# ============================================================

if page == "Executive Summary":

    st.title("Real Estate Analytics")
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Executive performance overview across cities, developers and property segments"
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    st.markdown('<div class="section-title">Key Performance Indicators</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns([1, 1.30, 1.05, 1, 1])

    with k1:
        st.metric("Transactions", f"{total_transactions:,}")

    with k2:
        st.metric("Total Sales Value", format_kpi_sales(total_sales))

    with k3:
        st.metric("Avg Sale Price", format_price(avg_sale_price))

    with k4:
        st.metric("Avg Discount", format_pct(avg_discount))

    with k5:
        st.metric("Cancellation Rate", format_pct(cancellation_rate))

    st.caption(
        f"Showing {len(filtered_df):,} transaction rows after applying the selected filters."
    )

    st.divider()

    # --------------------------------------------------------
    # SALES TREND
    # --------------------------------------------------------

    # Adaptive trend grain keeps the chart executive-friendly:
    # <=31 days: daily | 32-180 days: weekly | >180 days: monthly.
    trend_source = filtered_df.copy()
    trend_source["TXN_DATE_DT"] = pd.to_datetime(trend_source["TXN_DATE"])

    if trend_source["TXN_DATE_DT"].notna().any():
        date_span_days = (
            trend_source["TXN_DATE_DT"].max() - trend_source["TXN_DATE_DT"].min()
        ).days
    else:
        date_span_days = 0

    if date_span_days <= 31:
        trend_grain = "Daily"
        trend_source["TREND_DATE"] = trend_source["TXN_DATE_DT"].dt.floor("D")
        trend_title = "Transaction Date"
        tooltip_title = "Date"
        tooltip_format = "%d %b %Y"
    elif date_span_days <= 180:
        trend_grain = "Weekly"
        trend_source["TREND_DATE"] = (
            trend_source["TXN_DATE_DT"].dt.to_period("W-MON").dt.start_time
        )
        trend_title = "Week"
        tooltip_title = "Week Starting"
        tooltip_format = "%d %b %Y"
    else:
        trend_grain = "Monthly"
        trend_source["TREND_DATE"] = (
            trend_source["TXN_DATE_DT"].dt.to_period("M").dt.start_time
        )
        trend_title = "Month"
        tooltip_title = "Month"
        tooltip_format = "%b %Y"

    trend = (
        trend_source.groupby("TREND_DATE", as_index=False)
        .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
        .sort_values("TREND_DATE")
    )

    st.markdown(
        f'<div class="section-title">Sales Performance Trend '
        f'<span style="font-size:0.65em;font-weight:500;color:#64748b;">({trend_grain})</span></div>',
        unsafe_allow_html=True,
    )

    if not trend.empty:
        # Nearest-point selection makes the tooltip appear when the user
        # moves the mouse across the chart, rather than requiring a click.
        hover = alt.selection_point(
            name="hover",
            nearest=True,
            on="pointerover",
            fields=["TREND_DATE"],
            empty=False,
        )

        base = alt.Chart(trend).encode(
            x=alt.X(
                "TREND_DATE:T",
                title=trend_title,
                axis=alt.Axis(
                    format=(
                        "%b %Y"
                        if trend_grain == "Monthly"
                        else ("%d %b" if trend_grain == "Daily" else "%d %b")
                    )
                ),
            ),
            y=alt.Y(
                "SALES_VALUE:Q",
                title="Sales Value (₹ Lakhs)",
                axis=alt.Axis(format=",.0f"),
            ),
        )

        # Subtle area fill gives the trend more visual weight.
        area = base.mark_area(opacity=0.12)

        # Clean line with points so the trend remains easy to follow.
        line = base.mark_line(strokeWidth=3)

        points = base.mark_circle(size=55).encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0))
        ).add_params(hover)

        # Persistent tooltip follows the nearest monthly/weekly/daily point.
        tooltip_layer = base.mark_circle(size=180, opacity=0).encode(
            tooltip=[
                alt.Tooltip(
                    "TREND_DATE:T",
                    title=tooltip_title,
                    format=tooltip_format,
                ),
                alt.Tooltip(
                    "SALES_VALUE:Q",
                    title="Sales Value",
                    format=",.2f",
                ),
            ]
        ).transform_filter(hover)

        trend_chart = (
            alt.layer(area, line, points, tooltip_layer)
            .properties(height=360)
        )

        st.altair_chart(trend_chart, width="stretch")

    st.divider()

    # --------------------------------------------------------
    # TOP CITIES + SEGMENT MIX
    # --------------------------------------------------------

    left, right = st.columns(2)

    with left:
        st.markdown(
            '<div class="section-title">Top Cities by Sales Value</div>',
            unsafe_allow_html=True,
        )

        city_sales = (
            filtered_df.groupby("CITY_NAME", as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
            .sort_values("SALES_VALUE", ascending=False)
            .head(10)
        )

        if not city_sales.empty:
            chart = (
                alt.Chart(city_sales)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    y=alt.Y(
                        "CITY_NAME:N",
                        sort="-x",
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip("CITY_NAME:N", title="City"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=330)
            )
            st.altair_chart(chart, width="stretch")

    with right:
        st.markdown(
            '<div class="section-title">Sales Mix by Segment</div>',
            unsafe_allow_html=True,
        )

        segment_sales = (
            filtered_df.groupby("SEGMENT", as_index=False)
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
            .sort_values("SALES_VALUE", ascending=False)
        )

        if not segment_sales.empty:
            chart = (
                alt.Chart(segment_sales)
                .mark_arc(innerRadius=65)
                .encode(
                    theta=alt.Theta("SALES_VALUE:Q"),
                    color=alt.Color("SEGMENT:N", title="Segment"),
                    tooltip=[
                        alt.Tooltip("SEGMENT:N", title="Segment"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=330)
            )
            st.altair_chart(chart, width="stretch")

    st.divider()

    # --------------------------------------------------------
    # TRANSACTION STATUS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Transaction Status Overview</div>',
        unsafe_allow_html=True,
    )

    status_summary = (
        filtered_df.groupby("TXN_STATUS", as_index=False)
        .agg(TRANSACTIONS=("TXN_ID", "nunique"))
        .sort_values("TRANSACTIONS", ascending=False)
    )

    if not status_summary.empty:
        status_chart = (
            alt.Chart(status_summary)
            .mark_bar()
            .encode(
                x=alt.X("TRANSACTIONS:Q", title="Transactions"),
                y=alt.Y("TXN_STATUS:N", sort="-x", title=None),
                tooltip=[
                    alt.Tooltip("TXN_STATUS:N", title="Status"),
                    alt.Tooltip("TRANSACTIONS:Q", title="Transactions"),
                ],
            )
            .properties(height=250)
        )
        st.altair_chart(status_chart, width="stretch")

    with st.expander("View Transaction Data"):
        st.dataframe(
            filtered_df.sort_values("TXN_DATE", ascending=False),
            width="stretch",
            hide_index=True,
        )

# ============================================================
# PAGE 2 - CITY INSIGHTS
# ============================================================

elif page == "City Insights":

    st.title("🏙️ City Insights")
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Compare market performance across cities, regions and city classes"
        "</div>",
        unsafe_allow_html=True,
    )

    city_performance = (
        filtered_df.groupby(
            ["CITY_NAME", "REGION", "CITY_CLASS"],
            as_index=False,
        )
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            AVG_SALE_PRICE=("SALE_PRICE_LAKHS", "mean"),
        )
        .sort_values("SALES_VALUE", ascending=False)
    )

    if not city_performance.empty:
        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric("Cities in View", f"{city_performance['CITY_NAME'].nunique():,}")

        with k2:
            st.metric("Leading City", city_performance.iloc[0]["CITY_NAME"])

        with k3:
            st.metric(
                "Leading City Sales",
                format_lakhs(city_performance.iloc[0]["SALES_VALUE"]),
            )

        st.divider()

        st.markdown(
            '<div class="section-title">City Performance</div>',
            unsafe_allow_html=True,
        )

        display_city = city_performance.rename(
            columns={
                "CITY_NAME": "City",
                "REGION": "Region",
                "CITY_CLASS": "City Class",
                "TRANSACTIONS": "Transactions",
                "SALES_VALUE": "Sales Value",
                "AVG_SALE_PRICE": "Avg Sale Price",
            }
        )

        display_city = clean_numeric_columns(display_city)

        st.dataframe(
            display_city,
            width="stretch",
            hide_index=True,
        )

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="section-title">Sales by City</div>',
                unsafe_allow_html=True,
            )

            chart = (
                alt.Chart(city_performance.head(10))
                .mark_bar()
                .encode(
                    x=alt.X(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    y=alt.Y("CITY_NAME:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("CITY_NAME:N", title="City"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=350)
            )
            st.altair_chart(chart, width="stretch")

        with right:
            st.markdown(
                '<div class="section-title">Sales by Region</div>',
                unsafe_allow_html=True,
            )

            region_sales = (
                filtered_df.groupby("REGION", as_index=False)
                .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
                .sort_values("SALES_VALUE", ascending=False)
            )

            chart = (
                alt.Chart(region_sales)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    y=alt.Y("REGION:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("REGION:N", title="Region"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=350)
            )
            st.altair_chart(chart, width="stretch")

        st.markdown(
            '<div class="section-title">Segment Mix by City</div>',
            unsafe_allow_html=True,
        )

        segment_city = (
            filtered_df.groupby(
                ["CITY_NAME", "SEGMENT"],
                as_index=False,
            )
            .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
        )

        chart = (
            alt.Chart(segment_city)
            .mark_bar()
            .encode(
                x=alt.X("CITY_NAME:N", title="City"),
                y=alt.Y(
                    "SALES_VALUE:Q",
                    title="Sales Value (₹ Lakhs)",
                    axis=alt.Axis(format=",.0f"),
                ),
                color=alt.Color("SEGMENT:N", title="Segment"),
                tooltip=[
                    alt.Tooltip("CITY_NAME:N", title="City"),
                    alt.Tooltip("SEGMENT:N", title="Segment"),
                    alt.Tooltip(
                        "SALES_VALUE:Q",
                        title="Sales Value",
                        format=",.2f",
                    ),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(chart, width="stretch")

# ============================================================
# PAGE 3 - DEVELOPER PERFORMANCE
# ============================================================

elif page == "Developer Performance":

    st.title("🏢 Developer Performance")
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Measure developer sales contribution, transaction volume and market focus"
        "</div>",
        unsafe_allow_html=True,
    )

    developer_kpi = (
        filtered_df.groupby("DEVELOPER_NAME", as_index=False)
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            AVG_SALE_PRICE=("SALE_PRICE_LAKHS", "mean"),
        )
        .sort_values("SALES_VALUE", ascending=False)
    )

    if not developer_kpi.empty:

        # Use a wider middle card so long developer names remain readable.
        k1, k2, k3 = st.columns([1, 1.65, 1])

        with k1:
            st.metric(
                "Developers in View",
                f"{developer_kpi['DEVELOPER_NAME'].nunique():,}",
            )

        with k2:
            st.metric(
                "Top Developer",
                str(developer_kpi.iloc[0]["DEVELOPER_NAME"]),
            )

        with k3:
            st.metric(
                "Top Developer Sales",
                format_lakhs(developer_kpi.iloc[0]["SALES_VALUE"]),
            )

        st.divider()

        st.markdown(
            '<div class="section-title">Developer Performance</div>',
            unsafe_allow_html=True,
        )

        display_dev = developer_kpi.rename(
            columns={
                "DEVELOPER_NAME": "Developer",
                "TRANSACTIONS": "Transactions",
                "SALES_VALUE": "Sales Value",
                "AVG_SALE_PRICE": "Avg Sale Price",
            }
        )

        display_dev = clean_numeric_columns(display_dev)

        st.dataframe(
            display_dev,
            width="stretch",
            hide_index=True,
        )

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="section-title">Top Developers by Sales Value</div>',
                unsafe_allow_html=True,
            )

            chart = (
                alt.Chart(developer_kpi.head(10))
                .mark_bar()
                .encode(
                    x=alt.X(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    y=alt.Y(
                        "DEVELOPER_NAME:N",
                        sort="-x",
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "DEVELOPER_NAME:N",
                            title="Developer",
                        ),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=350)
            )
            st.altair_chart(chart, width="stretch")

        with right:
            st.markdown(
                '<div class="section-title">Top Developers by Transaction Volume</div>',
                unsafe_allow_html=True,
            )

            volume_df = (
                developer_kpi
                .sort_values("TRANSACTIONS", ascending=False)
                .head(10)
            )

            chart = (
                alt.Chart(volume_df)
                .mark_bar()
                .encode(
                    x=alt.X("TRANSACTIONS:Q", title="Transactions"),
                    y=alt.Y(
                        "DEVELOPER_NAME:N",
                        sort="-x",
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "DEVELOPER_NAME:N",
                            title="Developer",
                        ),
                        alt.Tooltip(
                            "TRANSACTIONS:Q",
                            title="Transactions",
                        ),
                    ],
                )
                .properties(height=350)
            )
            st.altair_chart(chart, width="stretch")

        st.markdown(
            '<div class="section-title">Project Status Mix</div>',
            unsafe_allow_html=True,
        )

        status_mix = (
            filtered_df.groupby("PROJECT_STATUS", as_index=False)
            .agg(
                TRANSACTIONS=("TXN_ID", "nunique"),
                SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            )
            .sort_values("SALES_VALUE", ascending=False)
        )

        status_display = status_mix.rename(
            columns={
                "PROJECT_STATUS": "Project Status",
                "TRANSACTIONS": "Transactions",
                "SALES_VALUE": "Sales Value",
            }
        )

        status_display = clean_numeric_columns(status_display)

        st.dataframe(
            status_display,
            width="stretch",
            hide_index=True,
        )

# ============================================================
# PAGE 4 - PROPERTY EXPLORER
# ============================================================

elif page == "Property Explorer":

    st.title("🏘️ Property Explorer")
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Explore property demand and sales across type, segment, BHK and project status"
        "</div>",
        unsafe_allow_html=True,
    )

    property_summary = (
        filtered_df.groupby(
            [
                "PROPERTY_TYPE",
                "SEGMENT",
                "BHK",
                "PROJECT_STATUS",
                "DEVELOPER_NAME",
                "CITY_NAME",
            ],
            as_index=False,
        )
        .agg(
            TRANSACTIONS=("TXN_ID", "nunique"),
            SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
            AVG_SALE_PRICE=("SALE_PRICE_LAKHS", "mean"),
        )
        .sort_values("SALES_VALUE", ascending=False)
    )

    if not property_summary.empty:

        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric(
                "Property Types",
                f"{filtered_df['PROPERTY_TYPE'].nunique():,}",
            )

        with k2:
            st.metric(
                "Segments",
                f"{filtered_df['SEGMENT'].nunique():,}",
            )

        with k3:
            st.metric(
                "BHK Categories",
                f"{filtered_df['BHK'].nunique():,}",
            )

        st.divider()

        st.markdown(
            '<div class="section-title">Property Performance</div>',
            unsafe_allow_html=True,
        )

        property_display = property_summary.rename(
            columns={
                "PROPERTY_TYPE": "Property Type",
                "SEGMENT": "Segment",
                "BHK": "BHK",
                "PROJECT_STATUS": "Project Status",
                "DEVELOPER_NAME": "Developer",
                "CITY_NAME": "City",
                "TRANSACTIONS": "Transactions",
                "SALES_VALUE": "Sales Value",
                "AVG_SALE_PRICE": "Avg Sale Price",
            }
        )

        property_display = clean_numeric_columns(property_display)

        st.dataframe(
            property_display,
            width="stretch",
            hide_index=True,
        )

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="section-title">Sales by Property Type</div>',
                unsafe_allow_html=True,
            )

            property_type_sales = (
                filtered_df.groupby("PROPERTY_TYPE", as_index=False)
                .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
                .sort_values("SALES_VALUE", ascending=False)
            )

            chart = (
                alt.Chart(property_type_sales)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    y=alt.Y(
                        "PROPERTY_TYPE:N",
                        sort="-x",
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "PROPERTY_TYPE:N",
                            title="Property Type",
                        ),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, width="stretch")

        with right:
            st.markdown(
                '<div class="section-title">Sales by Segment</div>',
                unsafe_allow_html=True,
            )

            segment_sales = (
                filtered_df.groupby("SEGMENT", as_index=False)
                .agg(SALES_VALUE=("SALE_PRICE_LAKHS", "sum"))
                .sort_values("SALES_VALUE", ascending=False)
            )

            chart = (
                alt.Chart(segment_sales)
                .mark_arc(innerRadius=60)
                .encode(
                    theta=alt.Theta("SALES_VALUE:Q"),
                    color=alt.Color("SEGMENT:N", title="Segment"),
                    tooltip=[
                        alt.Tooltip("SEGMENT:N", title="Segment"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, width="stretch")

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="section-title">Sales by BHK</div>',
                unsafe_allow_html=True,
            )

            bhk_sales = (
                filtered_df[filtered_df["BHK"].notna()].groupby("BHK", as_index=False)
                .agg(
                    SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
                    TRANSACTIONS=("TXN_ID", "nunique"),
                )
                .sort_values("BHK")
            )

            chart = (
                alt.Chart(bhk_sales)
                .mark_bar()
                .encode(
                    x=alt.X("BHK:N", title="BHK", sort="ascending"),
                    y=alt.Y(
                        "SALES_VALUE:Q",
                        title="Sales Value (₹ Lakhs)",
                        axis=alt.Axis(format=",.0f"),
                    ),
                    tooltip=[
                        alt.Tooltip("BHK:N", title="BHK"),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                        alt.Tooltip(
                            "TRANSACTIONS:Q",
                            title="Transactions",
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, width="stretch")

        with right:
            st.markdown(
                '<div class="section-title">Project Status Distribution</div>',
                unsafe_allow_html=True,
            )

            property_status = (
                filtered_df.groupby("PROJECT_STATUS", as_index=False)
                .agg(
                    TRANSACTIONS=("TXN_ID", "nunique"),
                    SALES_VALUE=("SALE_PRICE_LAKHS", "sum"),
                )
                .sort_values("TRANSACTIONS", ascending=False)
            )

            chart = (
                alt.Chart(property_status)
                .mark_bar()
                .encode(
                    x=alt.X("TRANSACTIONS:Q", title="Transactions"),
                    y=alt.Y(
                        "PROJECT_STATUS:N",
                        sort="-x",
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "PROJECT_STATUS:N",
                            title="Project Status",
                        ),
                        alt.Tooltip(
                            "TRANSACTIONS:Q",
                            title="Transactions",
                        ),
                        alt.Tooltip(
                            "SALES_VALUE:Q",
                            title="Sales Value",
                            format=",.2f",
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, width="stretch")

# ============================================================
# FOOTER / REFRESH INFORMATION
# ============================================================

st.sidebar.divider()
st.sidebar.caption(
    "Data source: SEMANTIC.VW_TRANSACTION_ANALYTICS"
)
st.sidebar.caption(
    f"Source rows available: {len(df):,}"
)
