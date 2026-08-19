import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="E-commerce Sales & Inventory Dashboard",
    page_icon="📦",
    layout="wide"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("retail_cleaned.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = load_data()


# =========================================================
# TITLE
# =========================================================

st.title("📊 E-commerce Sales & Inventory Dashboard")

st.caption(
    "An interactive dashboard analyzing retail sales trends, inventory health, "
    "and stockout risk, with a live reorder-point simulator. "
    "Built with Streamlit, Pandas, and Plotly."
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")


# ---------------------------------------------------------
# DATE RANGE
# ---------------------------------------------------------

date_range = st.sidebar.date_input(
    "Date Range",
    value=(
        df["Date"].min().date(),
        df["Date"].max().date()
    ),
    min_value=df["Date"].min().date(),
    max_value=df["Date"].max().date()
)


# Handle single-date selection
if isinstance(date_range, tuple) and len(date_range) == 2:

    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

else:

    start_date = pd.to_datetime(date_range)
    end_date = start_date


# ---------------------------------------------------------
# CATEGORY
# ---------------------------------------------------------

categories = st.sidebar.multiselect(
    "Category",
    options=sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)


# ---------------------------------------------------------
# REGION
# ---------------------------------------------------------

regions = st.sidebar.multiselect(
    "Region",
    options=sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique())
)


# ---------------------------------------------------------
# STORE
# ---------------------------------------------------------

stores = st.sidebar.multiselect(
    "Store ID",
    options=sorted(df["Store ID"].unique()),
    default=sorted(df["Store ID"].unique())
)


# =========================================================
# APPLY FILTERS
# =========================================================

mask = (
    (df["Date"] >= start_date)
    & (df["Date"] <= end_date)
    & (df["Category"].isin(categories))
    & (df["Region"].isin(regions))
    & (df["Store ID"].isin(stores))
)

filtered_df = df.loc[mask].copy()


# =========================================================
# EMPTY DATA CHECK
# =========================================================

if filtered_df.empty:

    st.warning(
        "No data is available for the selected filters. "
        "Please adjust the filters in the sidebar."
    )

    st.stop()


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📈 Sales Overview",
        "📦 Inventory Health",
        "🔄 Reorder Simulator"
    ]
)


# =========================================================
# TAB 1 — SALES OVERVIEW
# =========================================================

with tab1:

    # =====================================================
    # KPI SECTION
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)


    # Total Revenue
    total_revenue = (
        filtered_df["Revenue_After_Discount"].sum()
    )


    # Total Units Sold
    total_units = (
        filtered_df["Units Sold"].sum()
    )


    # Average Revenue per Transaction
    avg_revenue_transaction = (
        filtered_df["Revenue_After_Discount"].mean()
    )


    # Stockout Risk %
    stockout_risk_pct = (
        filtered_df["Stockout_Risk"].mean() * 100
    )


    col1.metric(
        "Total Revenue",
        f"${total_revenue:,.0f}"
    )


    col2.metric(
        "Total Units Sold",
        f"{total_units:,.0f}"
    )


    col3.metric(
        "Avg Revenue / Transaction",
        f"${avg_revenue_transaction:,.2f}"
    )


    col4.metric(
        "Stockout Risk",
        f"{stockout_risk_pct:.2f}%"
    )


    st.divider()


    # =====================================================
    # REVENUE TREND
    # =====================================================

    st.subheader("📈 Revenue Trend")


    # Monthly revenue
    monthly_revenue = (
        filtered_df
        .set_index("Date")
        .resample("MS")["Revenue_After_Discount"]
        .sum()
        .reset_index()
    )


    # -----------------------------------------------------
    # REMOVE INCOMPLETE FINAL MONTH
    # -----------------------------------------------------

    last_data_date = filtered_df["Date"].max()

    last_month = last_data_date.to_period("M")


    if last_data_date.day < last_data_date.days_in_month:

        monthly_revenue = monthly_revenue[
            monthly_revenue["Date"].dt.to_period("M")
            != last_month
        ]


    # -----------------------------------------------------
    # 3-MONTH MOVING AVERAGE
    # -----------------------------------------------------

    monthly_revenue["3-Month Moving Average"] = (
        monthly_revenue["Revenue_After_Discount"]
        .rolling(
            window=3,
            min_periods=1
        )
        .mean()
    )


    # -----------------------------------------------------
    # REVENUE LINE CHART
    # -----------------------------------------------------

    fig_trend = px.line(
        monthly_revenue,
        x="Date",
        y=[
            "Revenue_After_Discount",
            "3-Month Moving Average"
        ],
        title="Monthly Revenue & 3-Month Moving Average",
        labels={
            "Date": "Month",
            "value": "Revenue",
            "variable": ""
        }
    )


    # Make actual revenue line lighter
    fig_trend.update_traces(
        selector=dict(
            name="Revenue_After_Discount"
        ),
        opacity=0.45
    )


    # Make moving average line stronger
    fig_trend.update_traces(
        selector=dict(
            name="3-Month Moving Average"
        ),
        line=dict(width=4)
    )


    fig_trend.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )


    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )


    # =====================================================
    # CATEGORY & REGION ANALYSIS
    # =====================================================

    col5, col6 = st.columns(2)


    # =====================================================
    # REVENUE CONTRIBUTION BY CATEGORY
    # =====================================================

    with col5:

        category_revenue = (
            filtered_df
            .groupby("Category")[
                "Revenue_After_Discount"
            ]
            .sum()
            .reset_index()
        )


        # Calculate percentage contribution
        category_revenue["Revenue Contribution %"] = (
            category_revenue["Revenue_After_Discount"]
            / category_revenue["Revenue_After_Discount"].sum()
            * 100
        )


        category_revenue = category_revenue.sort_values(
            "Revenue Contribution %",
            ascending=False
        )


        fig_category = px.bar(
            category_revenue,
            x="Category",
            y="Revenue Contribution %",
            title="Revenue Contribution by Category",
            text=category_revenue[
                "Revenue Contribution %"
            ].round(1).astype(str) + "%",
        )


        fig_category.update_layout(
            xaxis_title="Category",
            yaxis_title="Revenue Contribution (%)",
            showlegend=False
        )


        fig_category.update_traces(
            textposition="outside"
        )


        st.plotly_chart(
            fig_category,
            use_container_width=True
        )


        # Top category insight
        top_category = category_revenue.iloc[0]


        st.caption(
            f"**{top_category['Category']}** contributes "
            f"**{top_category['Revenue Contribution %']:.1f}%** "
            f"of total revenue."
        )


    # =====================================================
    # REVENUE BY REGION
    # =====================================================

    with col6:

        region_revenue = (
            filtered_df
            .groupby("Region")[
                "Revenue_After_Discount"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "Revenue_After_Discount",
                ascending=False
            )
        )


        fig_region = px.bar(
            region_revenue,
            x="Region",
            y="Revenue_After_Discount",
            title="Revenue by Region",
            text_auto=".2s"
        )


        fig_region.update_layout(
            xaxis_title="Region",
            yaxis_title="Revenue",
            showlegend=False
        )


        st.plotly_chart(
            fig_region,
            use_container_width=True
        )


        # Region insight
        top_region = region_revenue.iloc[0]
        bottom_region = region_revenue.iloc[-1]


        if bottom_region["Revenue_After_Discount"] != 0:

            region_gap = (
                (
                    top_region["Revenue_After_Discount"]
                    - bottom_region["Revenue_After_Discount"]
                )
                / bottom_region["Revenue_After_Discount"]
            ) * 100


            st.caption(
                f"**{top_region['Region']}** leads with "
                f"**{region_gap:.1f}%** more revenue than "
                f"**{bottom_region['Region']}**."
            )


    # =====================================================
    # PROMOTION IMPACT
    # =====================================================

    st.subheader("🎉 Promotion Impact on Revenue")


    promo_impact = (
        filtered_df
        .groupby("Holiday/Promotion")[
            "Revenue_After_Discount"
        ]
        .mean()
        .reset_index()
    )


    promo_impact["Holiday/Promotion"] = (
        promo_impact["Holiday/Promotion"]
        .map(
            {
                0: "No Promotion",
                1: "Promotion"
            }
        )
    )


    # Check if both groups exist
    if len(promo_impact) >= 2:

        no_promo_val = promo_impact.loc[
            promo_impact["Holiday/Promotion"]
            == "No Promotion",
            "Revenue_After_Discount"
        ].values[0]


        promo_val = promo_impact.loc[
            promo_impact["Holiday/Promotion"]
            == "Promotion",
            "Revenue_After_Discount"
        ].values[0]


        if no_promo_val != 0:

            pct_diff = (
                (promo_val - no_promo_val)
                / no_promo_val
            ) * 100

        else:

            pct_diff = 0


        fig_promo = px.bar(
            promo_impact,
            x="Holiday/Promotion",
            y="Revenue_After_Discount",
            title="Average Revenue: Promotion vs No Promotion",
            text_auto=".2s"
        )


        fig_promo.update_layout(
            xaxis_title="Promotion Status",
            yaxis_title="Average Revenue",
            showlegend=False
        )


        st.plotly_chart(
            fig_promo,
            use_container_width=True
        )


        st.caption(
            f"Promotions show a "
            f"**{pct_diff:+.1f}%** difference in "
            f"average revenue per transaction."
        )


    else:

        st.info(
            "Promotion comparison is not available "
            "for the selected filters."
        )


# =========================================================
# TAB 2 — INVENTORY HEALTH
# =========================================================

with tab2:

    # =====================================================
    # INVENTORY KPIs
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)


    # Stockout count
    stockout_count = (
        filtered_df["Stockout_Risk"].sum()
    )


    # Stockout percentage
    stockout_pct = (
        filtered_df["Stockout_Risk"].mean()
        * 100
    )


    # Days of stock
    finite_stock = filtered_df.loc[
        filtered_df["Days_of_Stock"] != float("inf"),
        "Days_of_Stock"
    ]


    if not finite_stock.empty:

        avg_days_stock = (
            finite_stock.mean()
        )

    else:

        avg_days_stock = 0


    # Total inventory
    total_inventory = (
        filtered_df["Inventory Level"].sum()
    )


    col1.metric(
        "Stockout Risk Count",
        f"{stockout_count:,.0f}"
    )


    col2.metric(
        "Stockout Risk %",
        f"{stockout_pct:.2f}%"
    )


    col3.metric(
        "Avg Days of Stock",
        f"{avg_days_stock:.1f}"
    )


    col4.metric(
        "Total Inventory Units",
        f"{total_inventory:,.0f}"
    )


    st.divider()


    # =====================================================
    # TOP 10 STOCKOUT RISK PRODUCTS
    # =====================================================

    st.subheader(
        "⚠️ Top 10 Products at Stockout Risk"
    )


    at_risk = (
        filtered_df[
            filtered_df["Stockout_Risk"] == True
        ]
        .sort_values(
            "Days_of_Stock"
        )
        .head(10)
    )


    if not at_risk.empty:

        st.dataframe(
            at_risk[
                [
                    "Date",
                    "Product ID",
                    "Category",
                    "Region",
                    "Store ID",
                    "Inventory Level",
                    "Demand Forecast",
                    "Days_of_Stock"
                ]
            ],
            use_container_width=True
        )

    else:

        st.success(
            "No products are currently at stockout risk "
            "for the selected filters."
        )


    # =====================================================
    # STOCKOUT RISK BY CATEGORY & REGION
    # =====================================================

    col7, col8 = st.columns(2)


    # =====================================================
    # STOCKOUT RISK BY CATEGORY
    # =====================================================

    with col7:

        risk_by_category = (
            filtered_df
            .groupby("Category")[
                "Stockout_Risk"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "Stockout_Risk",
                ascending=False
            )
        )


        fig_risk_cat = px.bar(
            risk_by_category,
            x="Category",
            y="Stockout_Risk",
            title="Stockout Risk Count by Category",
            text_auto=True
        )


        fig_risk_cat.update_layout(
            xaxis_title="Category",
            yaxis_title="Stockout Risk Count",
            showlegend=False
        )


        st.plotly_chart(
            fig_risk_cat,
            use_container_width=True
        )


    # =====================================================
    # STOCKOUT RISK BY REGION
    # =====================================================

    with col8:

        risk_by_region = (
            filtered_df
            .groupby("Region")[
                "Stockout_Risk"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "Stockout_Risk",
                ascending=False
            )
        )


        fig_risk_region = px.bar(
            risk_by_region,
            x="Region",
            y="Stockout_Risk",
            title="Stockout Risk Count by Region",
            text_auto=True
        )


        fig_risk_region.update_layout(
            xaxis_title="Region",
            yaxis_title="Stockout Risk Count",
            showlegend=False
        )


        st.plotly_chart(
            fig_risk_region,
            use_container_width=True
        )


    # =====================================================
    # INVENTORY VS DEMAND
    # =====================================================

    st.subheader(
        "📉 Inventory Level vs Demand Forecast"
    )


    sample = filtered_df.sample(
        min(3000, len(filtered_df)),
        random_state=42
    )


    fig_scatter = px.scatter(
        sample,
        x="Demand Forecast",
        y="Inventory Level",
        color="Stockout_Risk",
        title="Inventory vs Demand — Stockout Risk Highlighted",
        color_discrete_map={
            True: "red",
            False: "blue"
        },
        opacity=0.5
    )


    fig_scatter.update_layout(
        xaxis_title="Demand Forecast",
        yaxis_title="Inventory Level"
    )


    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )


# =========================================================
# TAB 3 — REORDER SIMULATOR
# =========================================================

with tab3:

    # =====================================================
    # INTRODUCTION
    # =====================================================

    st.subheader(
        "🔄 What-If Reorder Point Simulator"
    )


    st.write(
        "Select a product and store, then adjust assumptions "
        "to calculate a suggested reorder point."
    )


    # =====================================================
    # INPUTS
    # =====================================================

    col_a, col_b = st.columns([1, 2])


    with col_a:

        selected_product = st.selectbox(
            "Select Product ID",
            sorted(
                df["Product ID"].unique()
            )
        )


        selected_store = st.selectbox(
            "Select Store ID",
            sorted(
                df["Store ID"].unique()
            )
        )


        lead_time = st.slider(
            "Lead Time (days)",
            min_value=1,
            max_value=30,
            value=7
        )


        safety_stock_pct = st.slider(
            "Safety Stock Buffer (%)",
            min_value=0,
            max_value=100,
            value=20
        )


    # =====================================================
    # FILTER PRODUCT + STORE
    # =====================================================

    product_df = (
        df[
            (df["Product ID"] == selected_product)
            & (df["Store ID"] == selected_store)
        ]
        .sort_values("Date")
    )


    # =====================================================
    # REORDER POINT CALCULATION
    # =====================================================

    avg_daily_sales = (
        product_df["Units Sold"].mean()
    )


    max_inventory_seen = (
        product_df["Inventory Level"].max()
    )


    base_reorder_point = (
        avg_daily_sales
        * lead_time
    )


    safety_stock_units = (
        base_reorder_point
        * (safety_stock_pct / 100)
    )


    suggested_reorder_point = (
        base_reorder_point
        + safety_stock_units
    )


    # =====================================================
    # SIMULATOR METRICS
    # =====================================================

    with col_a:

        st.metric(
            "Avg Daily Sales",
            f"{avg_daily_sales:.1f} units"
        )


        st.metric(
            "Suggested Reorder Point",
            f"{suggested_reorder_point:.0f} units"
        )


        # Warning
        if suggested_reorder_point > max_inventory_seen:

            st.warning(
                f"⚠️ This reorder point exceeds the highest "
                f"inventory level ever recorded "
                f"({max_inventory_seen:.0f} units) for this "
                f"product/store. Current stocking practice may "
                f"not support this lead time + buffer."
            )


    # =====================================================
    # INVENTORY TREND
    # =====================================================

    with col_b:

        fig_product = px.line(
            product_df,
            x="Date",
            y="Inventory Level",
            title=(
                f"Inventory Trend — "
                f"{selected_product} @ {selected_store}"
            )
        )


        # Reorder point line
        fig_product.add_hline(
            y=suggested_reorder_point,
            line_dash="dash",
            line_color="red",
            annotation_text="Suggested Reorder Point",
            annotation_position="top left"
        )


        fig_product.update_layout(
            xaxis_title="Date",
            yaxis_title="Inventory Level"
        )


        st.plotly_chart(
            fig_product,
            use_container_width=True
        )


    # =====================================================
    # FORMULA
    # =====================================================

    st.caption(
        f"**Formula:** Reorder Point = "
        f"(Avg Daily Sales × Lead Time) + Safety Stock "
        f"= ({avg_daily_sales:.1f} × {lead_time}) + "
        f"{safety_stock_pct}% "
        f"= **{suggested_reorder_point:.0f} units**"
    )