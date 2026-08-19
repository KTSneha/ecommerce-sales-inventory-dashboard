import streamlit as st
import pandas as pd
import plotly.express as px

# ---- Page config ----
st.set_page_config(page_title="E-commerce Sales & Inventory Dashboard", page_icon="📦", layout="wide")# ---- Load data ----
@st.cache_data
def load_data():
    df = pd.read_csv("retail_cleaned.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# ---- Title ----
st.title("📊 E-commerce Sales & Inventory Dashboard")

st.caption(
    "An interactive dashboard analyzing retail sales trends, inventory health, and stockout risk, "
    "with a live reorder-point simulator. Built with Streamlit, Pandas, and Plotly."
)

# ---- Sidebar filters ----
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['Date'].min(), df['Date'].max()),
    min_value=df['Date'].min(),
    max_value=df['Date'].max()
)

categories = st.sidebar.multiselect(
    "Category", options=sorted(df['Category'].unique()), default=sorted(df['Category'].unique())
)

regions = st.sidebar.multiselect(
    "Region", options=sorted(df['Region'].unique()), default=sorted(df['Region'].unique())
)

stores = st.sidebar.multiselect(
    "Store ID", options=sorted(df['Store ID'].unique()), default=sorted(df['Store ID'].unique())
)

# ---- Apply filters ----
mask = (
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1])) &
    (df['Category'].isin(categories)) &
    (df['Region'].isin(regions)) &
    (df['Store ID'].isin(stores))
)
filtered_df = df[mask]

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["📈 Sales Overview", "📦 Inventory Health", "🔄 Reorder Simulator"])

# =========================
# TAB 1: SALES OVERVIEW
# =========================
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    total_revenue = filtered_df['Revenue_After_Discount'].sum()
    total_units = filtered_df['Units Sold'].sum()
    avg_order_value = filtered_df['Revenue_After_Discount'].mean()
    avg_discount = filtered_df['Discount'].mean()

    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Units Sold", f"{total_units:,.0f}")
    col3.metric("Avg Order Value", f"${avg_order_value:,.2f}")
    col4.metric("Avg Discount", f"{avg_discount:.1f}%")

    st.divider()

    revenue_trend = filtered_df.groupby('Date')['Revenue_After_Discount'].sum().reset_index()
    fig_trend = px.line(revenue_trend, x='Date', y='Revenue_After_Discount', title="Revenue Trend Over Time")
    st.plotly_chart(fig_trend, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        revenue_by_category = filtered_df.groupby('Category')['Revenue_After_Discount'].sum().reset_index().sort_values('Revenue_After_Discount', ascending=False)
        fig_cat = px.bar(revenue_by_category, x='Category', y='Revenue_After_Discount', title="Revenue by Category", text_auto='.2s')
        fig_cat.update_yaxes(range=[revenue_by_category['Revenue_After_Discount'].min() * 0.9, revenue_by_category['Revenue_After_Discount'].max() * 1.05])
        st.plotly_chart(fig_cat, use_container_width=True)
        top_cat = revenue_by_category.iloc[0]
        bottom_cat = revenue_by_category.iloc[-1]
        gap_pct = ((top_cat['Revenue_After_Discount'] - bottom_cat['Revenue_After_Discount']) / bottom_cat['Revenue_After_Discount']) * 100
        st.caption(f"**{top_cat['Category']}** leads with **{gap_pct:.1f}%** more revenue than the lowest category, **{bottom_cat['Category']}**.")

    with col6:
        revenue_by_region = filtered_df.groupby('Region')['Revenue_After_Discount'].sum().reset_index().sort_values('Revenue_After_Discount', ascending=False)
        fig_region = px.bar(revenue_by_region, x='Region', y='Revenue_After_Discount', title="Revenue by Region", text_auto='.2s')
        fig_region.update_yaxes(range=[revenue_by_region['Revenue_After_Discount'].min() * 0.9, revenue_by_region['Revenue_After_Discount'].max() * 1.05])
        st.plotly_chart(fig_region, use_container_width=True)
        top_reg = revenue_by_region.iloc[0]
        bottom_reg = revenue_by_region.iloc[-1]
        gap_pct_reg = ((top_reg['Revenue_After_Discount'] - bottom_reg['Revenue_After_Discount']) / bottom_reg['Revenue_After_Discount']) * 100
    st.caption(f"**{top_reg['Region']}** leads with **{gap_pct_reg:.1f}%** more revenue than the lowest region, **{bottom_reg['Region']}**.")

    st.subheader("🎉 Promotion Impact on Revenue")
promo_impact = filtered_df.groupby('Holiday/Promotion')['Revenue_After_Discount'].mean().reset_index()
promo_impact['Holiday/Promotion'] = promo_impact['Holiday/Promotion'].map({0: 'No Promotion', 1: 'Promotion'})

no_promo_val = promo_impact.loc[promo_impact['Holiday/Promotion'] == 'No Promotion', 'Revenue_After_Discount'].values[0]
promo_val = promo_impact.loc[promo_impact['Holiday/Promotion'] == 'Promotion', 'Revenue_After_Discount'].values[0]
pct_diff = ((promo_val - no_promo_val) / no_promo_val) * 100

fig_promo = px.bar(
    promo_impact, x='Holiday/Promotion', y='Revenue_After_Discount',
    title="Avg Revenue: Promotion vs No Promotion",
    text_auto='.2s'
)
fig_promo.update_yaxes(range=[min(no_promo_val, promo_val) * 0.9, max(no_promo_val, promo_val) * 1.1])
st.plotly_chart(fig_promo, use_container_width=True)

st.caption(
    f"Promotions show a **{pct_diff:+.1f}%** difference in average revenue per transaction — "
    f"a negligible effect in this dataset, suggesting promotions here don't meaningfully drive higher order value."
)

# =========================
# TAB 2: INVENTORY HEALTH
# =========================
with tab2:
    col1, col2, col3, col4 = st.columns(4)

    stockout_count = filtered_df['Stockout_Risk'].sum()
    stockout_pct = filtered_df['Stockout_Risk'].mean() * 100
    avg_days_stock = filtered_df.loc[filtered_df['Days_of_Stock'] != float('inf'), 'Days_of_Stock'].mean()
    total_inventory = filtered_df['Inventory Level'].sum()

    col1.metric("Stockout Risk Count", f"{stockout_count:,.0f}")
    col2.metric("Stockout Risk %", f"{stockout_pct:.2f}%")
    col3.metric("Avg Days of Stock", f"{avg_days_stock:.1f}")
    col4.metric("Total Inventory Units", f"{total_inventory:,.0f}")

    st.divider()

    # Top 10 products at highest stockout risk (lowest days of stock)
    st.subheader("⚠️ Top 10 Products at Stockout Risk")
    at_risk = filtered_df[filtered_df['Stockout_Risk'] == True].sort_values('Days_of_Stock').head(10)
    st.dataframe(
        at_risk[['Date', 'Product ID', 'Category', 'Region', 'Store ID',
                 'Inventory Level', 'Demand Forecast', 'Days_of_Stock']],
        use_container_width=True
    )

    col7, col8 = st.columns(2)
    with col7:
        risk_by_category = filtered_df.groupby('Category')['Stockout_Risk'].sum().reset_index().sort_values('Stockout_Risk', ascending=False)
        fig_risk_cat = px.bar(risk_by_category, x='Category', y='Stockout_Risk', title="Stockout Risk Count by Category")
        st.plotly_chart(fig_risk_cat, use_container_width=True)
    with col8:
        risk_by_region = filtered_df.groupby('Region')['Stockout_Risk'].sum().reset_index().sort_values('Stockout_Risk', ascending=False)
        fig_risk_region = px.bar(risk_by_region, x='Region', y='Stockout_Risk', title="Stockout Risk Count by Region")
        st.plotly_chart(fig_risk_region, use_container_width=True)

    # Inventory vs Demand scatter
    st.subheader("📉 Inventory Level vs Demand Forecast")
    sample = filtered_df.sample(min(3000, len(filtered_df)), random_state=42)  # sample for performance
    fig_scatter = px.scatter(
        sample, x='Demand Forecast', y='Inventory Level', color='Stockout_Risk',
        title="Inventory vs Demand (colored by Stockout Risk)",
        color_discrete_map={True: 'red', False: 'blue'},
        opacity=0.5
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# =========================
# TAB 3: REORDER SIMULATOR
# =========================
with tab3:
    st.subheader("🔄 What-If Reorder Point Simulator")
    st.write("Select a product and store, then adjust assumptions to calculate a suggested reorder point.")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        selected_product = st.selectbox("Select Product ID", sorted(df['Product ID'].unique()))
        selected_store = st.selectbox("Select Store ID", sorted(df['Store ID'].unique()))
        lead_time = st.slider("Lead Time (days)", min_value=1, max_value=30, value=7)
        safety_stock_pct = st.slider("Safety Stock Buffer (%)", min_value=0, max_value=100, value=20)

    # Filter to this specific product + store (ignore sidebar filters, as planned)
    product_df = df[(df['Product ID'] == selected_product) & (df['Store ID'] == selected_store)].sort_values('Date')

    avg_daily_sales = product_df['Units Sold'].mean()
    max_inventory_seen = product_df['Inventory Level'].max()
    base_reorder_point = avg_daily_sales * lead_time
    safety_stock_units = base_reorder_point * (safety_stock_pct / 100)
    suggested_reorder_point = base_reorder_point + safety_stock_units

    with col_a:
        st.metric("Avg Daily Sales", f"{avg_daily_sales:.1f} units")
        st.metric("Suggested Reorder Point", f"{suggested_reorder_point:.0f} units")
        if suggested_reorder_point > max_inventory_seen:
            st.warning(
                f"⚠️ This reorder point exceeds the highest inventory level ever "
                f"recorded ({max_inventory_seen:.0f} units) for this product/store — "
                f"current stocking practice may not support this lead time + buffer."
            )

    with col_b:
        fig_product = px.line(
            product_df, x='Date', y='Inventory Level',
            title=f"Inventory Trend — {selected_product} @ {selected_store}"
        )
        fig_product.add_hline(
            y=suggested_reorder_point, line_dash="dash", line_color="red",
            annotation_text="Suggested Reorder Point", annotation_position="top left"
        )
        st.plotly_chart(fig_product, use_container_width=True)

    st.caption(
        f"Formula: Reorder Point = (Avg Daily Sales × Lead Time) + Safety Stock Buffer "
        f"= ({avg_daily_sales:.1f} × {lead_time}) + {safety_stock_pct}% = {suggested_reorder_point:.0f} units"
    )