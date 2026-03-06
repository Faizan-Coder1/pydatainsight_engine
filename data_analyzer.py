import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")


class DataInspector:

    def __init__(self, dataframe):
        self.data = dataframe.copy()

    # ================= DATA QUALITY =================
    def data_quality_score(self):
        missing = self.data.isnull().sum().sum()
        total = self.data.size
        duplicates = self.data.duplicated().sum()

        missing_percent = (missing / total) * 100 if total else 0
        duplicate_percent = (duplicates / len(self.data)) * 100 if len(self.data) else 0

        score = max(0, 100 - (missing_percent + duplicate_percent))
        return round(score, 2), missing_percent, duplicate_percent

    # ================= CLEANING =================
    def remove_duplicated_rows(self):
        self.data = self.data.drop_duplicates()

    def handle_missing(self, method="mean"):
        for col in self.data.columns:
            if self.data[col].isnull().any():
                if np.issubdtype(self.data[col].dtype, np.number):
                    self.data[col].fillna(self.data[col].mean(), inplace=True)
                else:
                    self.data[col].fillna(self.data[col].mode()[0], inplace=True)

    # ================= INSIGHTS =================
    def generate_insights(self):
        insights = []
        for col in self.data.select_dtypes(include=np.number).columns:
            insights.append(f"{col} Mean: {round(self.data[col].mean(),2)}")
            insights.append(f"{col} Max: {self.data[col].max()}")
        return insights

    # ================= OUTLIERS =================
    def detect_outliers(self, column):
        if column not in self.data.columns:
            return 0

        if not np.issubdtype(self.data[column].dtype, np.number):
            return 0

        Q1 = self.data[column].quantile(0.25)
        Q3 = self.data[column].quantile(0.75)
        IQR = Q3 - Q1

        outliers = self.data[
            (self.data[column] < (Q1 - 1.5 * IQR)) |
            (self.data[column] > (Q3 + 1.5 * IQR))
        ]

        return len(outliers)

    # ================= BAR CHART =================
    def grouped_summary_chart(self, cat_col, num_col):
        try:
            grouped = self.data.groupby(cat_col, as_index=False)[num_col].sum()

            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=grouped, x=cat_col, y=num_col, ax=ax)
            plt.xticks(rotation=45)

            return fig, grouped

        except Exception as e:
            print(e)
            return None, None

    # ================= HISTOGRAM =================
    def histogram(self, col):
        fig, ax = plt.subplots()
        sns.histplot(self.data[col].dropna(), kde=True, ax=ax)
        return fig

    # ================= BOXPLOT =================
    def boxplot(self, col):
        fig, ax = plt.subplots()
        sns.boxplot(y=self.data[col], ax=ax)
        return fig

    # ================= HEATMAP =================
    def heatmap(self):
        num_df = self.data.select_dtypes(include=np.number)
        if num_df.empty:
            return None

        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(num_df.corr(), annot=True, cmap="coolwarm", ax=ax)
        return fig

    # ================= PIE =================
    def pie_chart(self, col):
        data = self.data[col].value_counts().head(5)

        fig, ax = plt.subplots()
        ax.pie(data, labels=data.index, autopct="%1.1f%%")
        return fig
