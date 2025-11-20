import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")


class DataInspector:

    def __init__(self, dataframe):
        self.data = dataframe.copy()

    
    def dataset_overview(self):
        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "data_types": {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            "missing": self.data.isnull().sum().to_dict(),
            "duplicates": int(self.data.duplicated().sum())
        }

    def basic_statistics(self):
       
        return self.data.describe(include="all")


    def remove_duplicated_rows(self):
        
        before = len(self.data)
        self.data = self.data.drop_duplicates()
        removed = before - len(self.data)
        return removed

    def handle_missing(self, method="mean", selected_cols=None):
        df = self.data.copy()
        if selected_cols is None:
            selected_cols = df.columns.tolist()

        for col in selected_cols:
            if df[col].isnull().any():
                if method == "mean" and np.issubdtype(df[col].dtype, np.number):
                    df[col].fillna(df[col].mean(), inplace=True)
                elif method == "median" and np.issubdtype(df[col].dtype, np.number):
                    df[col].fillna(df[col].median(), inplace=True)
                elif method == "mode":
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col].fillna(mode_val[0], inplace=True)
                elif method == "zero" and np.issubdtype(df[col].dtype, np.number):
                    df[col].fillna(0, inplace=True)
                elif method == "drop":
                    df.dropna(subset=[col], inplace=True)

        self.data = df
        return self.data

   
    def numerical_distribution(self, column, bins=30):
        if column not in self.data.columns or not np.issubdtype(self.data[column].dtype, np.number):
            return None

        clean_series = self.data[column].dropna()
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        sns.histplot(clean_series, bins=bins, color="#4C78A8", ax=axes[0])
        axes[0].set_title(f"{column} - Histogram")
        axes[0].set_xlabel(column)
        axes[0].set_ylabel("Frequency")

        sns.boxplot(y=clean_series, color="#72B7B2", ax=axes[1])
        axes[1].set_title(f"{column} - Box Plot")

        plt.tight_layout()
        return fig

    def categorical_bar_chart(self, column, top_n=15):
        if column not in self.data.columns:
            return None

        series = self.data[column].astype("category").value_counts().dropna()
        if len(series) > top_n:
            series = pd.concat([series[:top_n], pd.Series({"Others": series[top_n:].sum()})])

        fig, ax = plt.subplots(figsize=(10, 6))
        series.sort_values(ascending=True).plot(kind="barh", color="#F58518", ax=ax)
        ax.set_title(f"{column} - Bar Chart")
        ax.set_xlabel("Count")
        ax.set_ylabel(column)
        plt.tight_layout()
        return fig

    def categorical_pie_chart(self, column, top_n=8):
        if column not in self.data.columns:
            return None

        counts = self.data[column].astype("category").value_counts().dropna()
        if len(counts) > top_n:
            counts = pd.concat([counts[:top_n], pd.Series({"Others": counts[top_n:].sum()})])

        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            counts.values,
            labels=counts.index.astype(str),
            autopct="%1.1f%%",
            startangle=120,
            colors=sns.color_palette("pastel")
        )
        ax.set_title(f"{column} - Pie Chart")
        plt.tight_layout()
        return fig

    def correlation_heatmap(self):
        numeric_df = self.data.select_dtypes(include=np.number)
        if numeric_df.shape[1] < 2:
            return None

        corr_matrix = numeric_df.corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, cmap="coolwarm", center=0, linewidths=0.5, ax=ax)
        ax.set_title("Correlation Heatmap")
        plt.tight_layout()
        return fig

    def correlation_bar_chart(self, target_col, top_n=10):
        numeric_df = self.data.select_dtypes(include=np.number)
        if target_col not in numeric_df.columns:
            return None

        corr_values = numeric_df.corr()[target_col].drop(labels=[target_col]).dropna()
        top_corr = corr_values.abs().sort_values(ascending=False).head(top_n)

        fig, ax = plt.subplots(figsize=(10, 6))
        top_corr.sort_values().plot(kind="barh", color="#E45756", ax=ax)
        ax.set_title(f"Top {top_n} Correlations with {target_col}")
        ax.set_xlabel("Absolute Correlation")
        plt.tight_layout()
        return fig

    def grouped_summary_chart(self, category_col, numeric_col, method="mean", top_n=20):
        if category_col not in self.data.columns or numeric_col not in self.data.columns:
            return None

        temp_df = self.data[[category_col, numeric_col]].dropna()
        if temp_df.empty:
            return None

        if method not in ["mean", "sum", "count", "median"]:
            method = "mean"

        grouped = getattr(temp_df.groupby(category_col)[numeric_col], method)()
        grouped = grouped.sort_values(ascending=False)[:top_n]

        fig, ax = plt.subplots(figsize=(10, 6))
        grouped[::-1].plot(kind="barh", color="#54A24B", ax=ax)
        ax.set_title(f"{numeric_col} by {category_col} ({method.capitalize()})")
        plt.tight_layout()
        return fig
