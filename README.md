# 📊 E-commerce Sales & Inventory Dashboard

An interactive dashboard analyzing retail sales trends, inventory health, and stockout risk — with a live what-if reorder-point simulator.

🔗 **Live app:** https://ecommerce-sales-inventory-dashboard-nnmdzfjgybhqtwsltm6mfe.streamlit.app/

## Features
- **Sales Overview**: revenue trends, category/region breakdown, promotion impact analysis
- **Inventory Health**: stockout risk detection, top at-risk products, inventory-vs-demand visualization
- **Reorder Simulator**: interactive what-if tool to calculate suggested reorder points based on lead time and safety stock assumptions

## Tech Stack
- Python, Pandas
- Streamlit
- Plotly

## Dataset
73,100 records of daily retail sales and inventory data across 5 stores, 20 products, and 4 regions (2022–2024).

## Key Insights
- 3.54% of records show stockout risk (inventory below forecasted demand)
- [Add your Category/Region revenue gap findings here once you check the updated captions]
- Promotions show a negligible (~X%) effect on average revenue per transaction in this dataset

## Run Locally
\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`