import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- SAYFA AYARI ---
st.set_page_config(
    page_title="Supply Chain Dashboard",
    page_icon="🚚",
    layout="wide"
)

# --- VERİ ---
@st.cache_data
def load_data():
    df = pd.read_csv("DataCoSupplyChainDataset.csv", encoding="latin-1")
    drop_cols = ["Order Zipcode", "Product Description", "Customer Email",
                 "Customer Password", "Product Image", "Product Status"]
    df.drop(columns=drop_cols, inplace=True)
    df["Customer Lname"].fillna("Unknown", inplace=True)
    df["order date (DateOrders)"] = pd.to_datetime(df["order date (DateOrders)"])
    df["shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"])
    df["shipping_delay"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]
    return df

df = load_data()

# --- BAŞLIK ---
st.title("🚚 Supply Chain Analytics Dashboard")
st.markdown("**DataCo Global** verisi üzerinde uçtan uca tedarik zinciri analizi")
st.divider()

# --- FİLTRELER (Sidebar) ---
st.sidebar.header("🔍 Filtrele")
markets = st.sidebar.multiselect(
    "Pazar Seç",
    options=df["Market"].unique(),
    default=df["Market"].unique()
)
segments = st.sidebar.multiselect(
    "Müşteri Segmenti",
    options=df["Customer Segment"].unique(),
    default=df["Customer Segment"].unique()
)

df_filtered = df[
    (df["Market"].isin(markets)) &
    (df["Customer Segment"].isin(segments))
]

# --- KPI KARTI ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📦 Toplam Sipariş", f"{len(df_filtered):,}")
with col2:
    late_rate = round(df_filtered["Late_delivery_risk"].mean() * 100, 1)
    st.metric("🚨 Geç Teslimat Oranı", f"%{late_rate}", delta=f"%{late_rate - 54.8:.1f}", delta_color="inverse")
with col3:
    total_sales = df_filtered["Sales"].sum()
    st.metric("💰 Toplam Satış", f"${total_sales/1e6:.1f}M")
with col4:
    avg_profit = df_filtered["Benefit per order"].mean()
    st.metric("📈 Ortalama Kâr/Sipariş", f"${avg_profit:.1f}")

st.divider()

# --- GRAFİKLER ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Teslimat Durumu Dağılımı")
    delivery = df_filtered["Delivery Status"].value_counts().reset_index()
    delivery.columns = ["Durum", "Adet"]
    fig1 = px.pie(delivery, values="Adet", names="Durum",
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  hole=0.4)
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig1, use_container_width=True)

with row1_col2:
    st.subheader("Pazara Göre Toplam Satış")
    market_sales = df_filtered.groupby("Market")["Sales"].sum().reset_index()
    market_sales.columns = ["Pazar", "Satış"]
    market_sales = market_sales.sort_values("Satış", ascending=True)
    fig2 = px.bar(market_sales, x="Satış", y="Pazar", orientation="h",
                  color="Satış", color_continuous_scale="Blues")
    fig2.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Kategoriye Göre Ortalama Kâr (Top 10)")
    cat_profit = df_filtered.groupby("Category Name")["Benefit per order"].mean()\
                 .sort_values(ascending=False).head(10).reset_index()
    cat_profit.columns = ["Kategori", "Ort. Kâr"]
    fig3 = px.bar(cat_profit, x="Ort. Kâr", y="Kategori", orientation="h",
                  color="Ort. Kâr", color_continuous_scale="Greens")
    fig3.update_layout(yaxis={"categoryorder": "total ascending"},
                       coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

with row2_col2:
    st.subheader("Teslimat Gecikmesi Dağılımı")
    fig4 = px.histogram(df_filtered, x="shipping_delay", nbins=7,
                        color_discrete_sequence=["#e67e22"],
                        labels={"shipping_delay": "Gecikme (gün)"})
    fig4.update_layout(bargap=0.1)
    st.plotly_chart(fig4, use_container_width=True)

# --- ZAMAN SERİSİ ---
st.divider()
st.subheader("📅 Aylık Satış Trendi")
df_filtered["YearMonth"] = df_filtered["order date (DateOrders)"].dt.to_period("M").astype(str)
monthly = df_filtered.groupby("YearMonth")["Sales"].sum().reset_index()
fig5 = px.line(monthly, x="YearMonth", y="Sales",
               labels={"YearMonth": "Ay", "Sales": "Satış ($)"},
               color_discrete_sequence=["#2980b9"])
fig5.update_traces(mode="lines+markers")
st.plotly_chart(fig5, use_container_width=True)

st.caption("Kaynak: DataCo Global Supply Chain Dataset | Elif Kurt")
