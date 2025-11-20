import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_analyzer import DataInspector


st.set_page_config(page_title="PyDataInsight Engine", layout="wide")

st.title("📊 PyDataInsight Engine")


st.markdown("""
**Welcome to PyDataInsight Engine!**  
A no-code platform for exploring and visualizing your data.  
Upload a CSV file to automatically analyze, clean, and visualize your dataset with just a few clicks.
""")


uploaded = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

if uploaded is not None:
    st.sidebar.success("✅ File uploaded successfully!")

    try:
       
        df = pd.read_csv(uploaded)
        inspector = DataInspector(df)

        
        st.subheader("📂 Raw Data Preview")
        st.dataframe(df.head())

       
        st.sidebar.markdown("---")
        st.sidebar.header("🧹 Data Cleaning Controls")

        overview = inspector.dataset_overview()
        duplicates_count = overview["duplicates"]
        missing_summary = overview["missing"]
        missing_cols = [c for c, m in missing_summary.items() if m > 0]

        
        if duplicates_count > 0:
            st.sidebar.warning(f"Found {duplicates_count} duplicate rows.")
            if st.sidebar.button("Remove Duplicates"):
                removed = inspector.remove_duplicated_rows()
                st.sidebar.success(f"Removed {removed} duplicate rows.")
        else:
            st.sidebar.info("No duplicate rows detected.")

       
        if missing_cols:
            st.sidebar.markdown("### Handle Missing Values")
            st.sidebar.write("Columns with missing values:", ", ".join(missing_cols))
            method = st.sidebar.selectbox(
                "Select a filling strategy:",
                ["None", "Mean", "Median", "Mode", "Zero", "Drop"]
            )

            if method != "None":
                if st.sidebar.button(f"Apply {method} Strategy"):
                    strategy_map = {
                        "Mean": "mean", "Median": "median",
                        "Mode": "mode", "Zero": "zero", "Drop": "drop"
                    }
                    inspector.handle_missing(strategy_map[method], selected_cols=missing_cols)
                    st.sidebar.success(f"{method} method applied successfully.")
        else:
            st.sidebar.info("No missing values detected.")

       
        st.markdown("---")
        st.subheader("📊 Data Overview")

        data_info = inspector.dataset_overview()
        st.write("**Dataset Shape:**", data_info["shape"])
        st.write("**Columns:**", ", ".join(data_info["columns"]))
        st.write("**Duplicate Rows:**", data_info["duplicates"])

        st.write("**Missing Values (per column):**")
        st.dataframe(pd.DataFrame.from_dict(data_info["missing"], orient='index', columns=['Count']))

        st.markdown("---")
        st.subheader("📈 Descriptive Statistics")
        st.dataframe(inspector.basic_statistics())

       
        st.markdown("---")
        st.subheader("🎨 Data Visualization Tools")

        columns = inspector.data.columns.tolist()
        num_cols = inspector.data.select_dtypes(include=np.number).columns.tolist()
        cat_cols = inspector.data.select_dtypes(exclude=np.number).columns.tolist()

     
        st.markdown("### 1️⃣ Distribution Charts")
        selected_col = st.selectbox("Select a column:", ["-- Select --"] + columns)
        if selected_col != "-- Select --":
            if selected_col in num_cols:
                bins = st.slider("Number of bins:", 5, 100, 30)
                fig = inspector.numerical_distribution(selected_col, bins=bins)
                if fig:
                    st.pyplot(fig)
            elif selected_col in cat_cols:
                chart_choice = st.radio("Chart Type:", ["Bar", "Pie"], horizontal=True)
                if chart_choice == "Bar":
                    top_n = st.slider("Top Categories:", 5, 30, 15)
                    fig = inspector.categorical_bar_chart(selected_col, top_n=top_n)
                    if fig:
                        st.pyplot(fig)
                else:
                    top_n = st.slider("Top Categories:", 5, 15, 8)
                    fig = inspector.categorical_pie_chart(selected_col, top_n=top_n)
                    if fig:
                        st.pyplot(fig)
            else:
                st.info("Selected column is not suitable for standard plots.")

     
        st.markdown("### 2️⃣ Correlation Heatmap")
        if len(num_cols) > 1:
            heatmap_fig = inspector.correlation_heatmap()
            if heatmap_fig:
                st.pyplot(heatmap_fig)
            else:
                st.info("Could not generate heatmap.")
        else:
            st.info("Need at least two numeric columns for correlation.")

      
        st.markdown("### 3️⃣ Target-Based Correlation Bar Chart")
        if len(num_cols) > 1:
            target = st.selectbox("Select a target numeric column:", ["-- Select --"] + num_cols)
            if target != "-- Select --":
                top_n = st.slider("Top correlated features:", 5, 20, 10)
                bar_fig = inspector.correlation_bar_chart(target, top_n=top_n)
                if bar_fig:
                    st.pyplot(bar_fig)
        else:
            st.info("Need at least two numeric columns to plot correlations.")

        
        st.markdown("### 4️⃣ Grouped Category Chart")
        cat_for_group = st.selectbox("Group by (categorical):", ["-- Select --"] + cat_cols)
        num_for_group = st.selectbox("Value (numeric):", ["-- Select --"] + num_cols)
        agg_method = st.selectbox("Aggregation Method:", ["mean", "sum", "median", "count"])

        if cat_for_group != "-- Select --" and num_for_group != "-- Select --":
            grouped_fig = inspector.grouped_summary_chart(cat_for_group, num_for_group, method=agg_method)
            if grouped_fig:
                st.pyplot(grouped_fig)

    except Exception as err:
        st.error(f"⚠️ An error occurred while processing your file: {err}")

else:
    st.info("Please upload a CSV file using the sidebar to begin your data analysis.")
