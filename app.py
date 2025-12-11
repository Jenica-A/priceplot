# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Quality vs Price", layout="wide")

st.title("📊 Product Quality vs List Price")

# -------------------------------------------------------------------
# 1. Load data
# -------------------------------------------------------------------
# Option A: load from a CSV (replace with actual file/path)
# df_plot = pd.read_csv("your_file.csv")

# Option B (recommended for flexibility): upload in the UI
uploaded_file = st.file_uploader("Upload your data file (CSV with df_plot structure)", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV to see the interactive bubble chart.")
    st.stop()

df_plot = pd.read_csv(uploaded_file)

# -------------------------------------------------------------------
# 2. Build the figure 
# -------------------------------------------------------------------
def build_figure(df_plot: pd.DataFrame):
    # --- prep a clean working copy ---
    df_plot2 = df_plot.copy()

    # Ensure date is a formatted string (avoids datetime + numeric dtype issues)
    df_plot2["On_Sale_Date_str"] = (
        pd.to_datetime(df_plot2["On_Sale_Date"], errors="coerce")
        .dt.strftime("%Y-%m-%d")
    )

    # Make sure numeric fields are truly numeric
    num_cols = [
        "List_Price",
        "qual_score",
        "avg_annual_units",
        "Page_Count",
        "Title_Age",
        "amazonaveragerating",
        "amazontotalreviews",
        "2024_units",
        "2025_units",
    ]
    for c in num_cols:
        if c in df_plot2.columns:
            df_plot2[c] = pd.to_numeric(df_plot2[c], errors="coerce")

    # --- main scatter: all but last row ---
    # Treat last row as the reference title
    df_main = df_plot2.iloc[:-1].copy()
    ref = df_plot2.iloc[-1]

    # Optional: filter controls in the sidebar
    with st.sidebar:
        st.header("Filters")
        # Filter by position category
        if "Suggested Position Category" in df_main.columns:
            all_cats = sorted(df_main["Suggested Position Category"].dropna().unique())
            selected_cats = st.multiselect(
                "Suggested Position Category",
                options=all_cats,
                default=all_cats,
            )
            if selected_cats:
                df_main = df_main[
                    df_main["Suggested Position Category"].isin(selected_cats)
                ]

        # Price range filter
        if "List_Price" in df_main.columns:
            min_price = float(df_main["List_Price"].min())
            max_price = float(df_main["List_Price"].max())
            price_range = st.slider(
                "List Price range",
                min_value=round(min_price, 2),
                max_value=round(max_price, 2),
                value=(round(min_price, 2), round(max_price, 2)),
            )
            df_main = df_main[
                (df_main["List_Price"] >= price_range[0])
                & (df_main["List_Price"] <= price_range[1])
            ]

    # --- main Plotly scatter ---
    fig = px.scatter(
        df_main,
        x="List_Price",
        y="qual_score",
        size="avg_annual_units",
        color="Suggested Position Category",
        hover_name="hover_label",
        hover_data={
            "List_Price": ":.2f",
            "avg_annual_units": ":,.0f",
            "Page_Count": ":.0f",
            "Title_Age": ":.0f",
            "amazonaveragerating": ":.1f",
            "amazontotalreviews": ":.0f",
            "On_Sale_Date_str": True,  # already formatted as text
            "2024_units": ":,.0f",
            "2025_units": ":,.0f",
        },
        title="📊 Product Quality vs List Price",
        labels={
            "Page_Count": "Page Count",
            "List_Price": "List Price ($)",
            "avg_annual_units": "Annual Unit Sales Average",
            "On_Sale_Date_str": "Pub Date",
            "amazonaveragerating": "Amazon Rating",
            "amazontotalreviews": "Amazon Review Count",
            "2024_units": "Units Sold in 2024",
            "2025_units": "YTD Unit Sales",
            "qual_score": "Quality Score",
        },
        size_max=40,
        height=900
    )

    # --- reference point: fixed-size marker 
    if len(fig.data) > 0 and hasattr(fig.data[0].marker, "sizeref"):
        sizeref = fig.data[0].marker.sizeref
    else:
        # Fallback if for some reason no sizeref present
        sizeref = 2.0

    fig.add_trace(
        go.Scatter(
            x=[ref["List_Price"]],
            y=[ref["qual_score"]],
            mode="markers",
            marker=dict(
                size=[ref["avg_annual_units"]],
                color="black",
                sizemode="area",
                sizeref=sizeref,
                sizemin=4,
                line=dict(width=1, color="white"),
            ),
            hovertext=[ref["hover_label"]],
            hoverinfo="text",
            name="Reference Marker Size: 15k Units",
        )
    )

    # --- layout tweaks ---
    fig.update_layout(
        xaxis=dict(tickprefix="$"),
        yaxis=dict(tickformat=".1f"),
        legend_title_text="Position Category",
    )

    return fig


# -------------------------------------------------------------------
# 3. Build and show chart
# -------------------------------------------------------------------
fig = build_figure(df_plot)
st.plotly_chart(fig, use_container_width=True)
