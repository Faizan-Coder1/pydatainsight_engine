import streamlit as st
import pandas as pd
import io
import zipfile
import plotly.express as px

from supabase import create_client, Client
from data_analyzer import DataInspector


# ================= SUPABASE =================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "user-files"


# ================= CHART STYLE FIX =================
def style_chart(fig, title):

    fig.update_layout(
        title=dict(text=title, font=dict(size=22, color="#ffffff")),

        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",

        font=dict(color="#ffffff", size=14),

        xaxis=dict(
            title_font=dict(color="#ffffff"),
            tickfont=dict(color="#ffffff"),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.15)"
        ),
        yaxis=dict(
            title_font=dict(color="#ffffff"),
            tickfont=dict(color="#ffffff"),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.15)"
        ),

        legend=dict(font=dict(color="#ffffff")),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # ===== FIX VALUE DISPLAY =====
    for trace in fig.data:
        try:
            # BAR → show rounded values
            if trace.type == "bar":
                trace.update(
                    text=[f"{v:.2f}" for v in trace.y],
                    textposition="outside",
                    textfont=dict(color="#ffffff", size=12)
                )

            # LINE → markers only (no text)
            elif trace.type == "scatter" and "lines" in trace.mode:
                trace.update(mode="lines+markers")

            # SCATTER → remove text
            elif trace.type == "scatter":
                trace.update(mode="markers", text=None)

            # HISTOGRAM → remove text
            elif trace.type == "histogram":
                trace.update(text=None)

            # BOX → show only outliers
            elif trace.type == "box":
                trace.update(
                    boxpoints="outliers",
                    marker=dict(color="#ffffff")
                )

        except:
            pass

    return fig


colors = ["#ff6b6b", "#4dabf7", "#51cf66", "#fcc419", "#b197fc"]


# ================= UI =================
st.set_page_config(page_title="PyDataInsight Pro", layout="wide")

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #020617, #0f172a);}
h1, h2, h3 {color: #e2e8f0;}

.glow {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    color: white;
    text-shadow: 0 0 10px #6366f1, 0 0 20px #9333ea;
}

.card {
    background: rgba(30,41,59,0.6);
    padding: 20px;
    border-radius: 18px;
    backdrop-filter: blur(15px);
}

.metric-box {
    background: linear-gradient(135deg, #6366f1, #9333ea);
    padding: 20px;
    border-radius: 14px;
    color: white;
    text-align: center;
}

div.stButton > button {
    background: linear-gradient(135deg, #6366f1, #ec4899);
    color: white;
    border-radius: 12px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a);
}
</style>
""", unsafe_allow_html=True)


# ================= SESSION =================
if "user" not in st.session_state:
    st.session_state.user = None


# ================= STORAGE HELPERS =================
def get_file_path(username):
    return f"{username}/data.csv"


def upload_to_storage(file, username):
    path = get_file_path(username)

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            path,
            file.getvalue(),
            {"content-type": "text/csv"}
        )
    except Exception:
        supabase.storage.from_(BUCKET_NAME).update(
            path,
            file.getvalue(),
            {"content-type": "text/csv"}
        )

    supabase.table("users").update({
        "last_file": file.name
    }).eq("username", username).execute()

    st.sidebar.success(f"Uploaded: {file.name}")


def load_from_storage(username):
    try:
        path = get_file_path(username)
        res = supabase.storage.from_(BUCKET_NAME).download(path)
        return pd.read_csv(io.BytesIO(res))
    except:
        return None


def get_last_file(username):
    try:
        res = supabase.table("users").select("last_file").eq("username", username).execute()
        if res.data and res.data[0]["last_file"]:
            return res.data[0]["last_file"]
    except:
        return None
    return None


# ================= AUTH =================
def login_user(username, password):
    res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    return res.data


def signup_user(username, password):
    supabase.table("users").insert({
        "username": username,
        "password": password
    }).execute()


# ================= LOGIN =================
if st.session_state.user is None:

    st.markdown("<div class='glow'>🔐 PyDataInsight Pro</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(user, pwd):
                st.session_state.user = user
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        new_user = st.text_input("New Username")
        new_pwd = st.text_input("New Password", type="password")

        if st.button("Signup"):
            signup_user(new_user, new_pwd)
            st.success("Account created")

    st.stop()


# ================= MAIN =================
st.markdown("<div class='glow'>🚀 PyDataInsight Dashboard</div>", unsafe_allow_html=True)
st.caption(f"User: {st.session_state.user}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()


uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

last_file = get_last_file(st.session_state.user)

if last_file:
    st.sidebar.success(f"📂 Last File: {last_file}")


df = None

if uploaded:
    if last_file == uploaded.name:
        st.sidebar.info("Same file loaded ✔")
    else:
        upload_to_storage(uploaded, st.session_state.user)

    df = pd.read_csv(uploaded)

else:
    df = load_from_storage(st.session_state.user)
    if df is not None:
        st.sidebar.info("Loaded last saved file ✔")


# ================= IF DATA =================
if df is not None:

    df = df.round(2)   # 🔥 FIX DECIMALS

    inspector = DataInspector(df)

    st.sidebar.header("🧹 Data Cleaning")

    if st.sidebar.button("Clean Data"):
        inspector.remove_duplicated_rows()
        inspector.handle_missing()
        df = inspector.data

        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)

        try:
            supabase.storage.from_(BUCKET_NAME).update(
                get_file_path(st.session_state.user),
                buffer.getvalue(),
                {"content-type": "text/csv"}
            )
        except:
            pass

        st.sidebar.success("Data cleaned and saved ✔")


    st.sidebar.header("🎛 Filters")
    cols = df.columns.tolist()

    if cols:
        filter_col = st.sidebar.selectbox("Filter Column", cols)
        values = df[filter_col].dropna().unique()
        selected = st.sidebar.multiselect("Values", values, default=values)

        if selected:
            df = df[df[filter_col].isin(selected)]


    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Data",
        "📊 Insights",
        "📈 Visualization",
        "📤 Export"
    ])


    with tab1:
        st.dataframe(df.head())

        score, miss, dup = inspector.data_quality_score()

        c1, c2, c3 = st.columns(3)
        c1.metric("Quality", score)
        c2.metric("Missing", round(miss, 2))
        c3.metric("Duplicates", round(dup, 2))

        st.download_button("Download Clean Data", df.to_csv(index=False), "clean_data.csv")


    with tab2:
        for i in inspector.generate_insights():
            st.success(i)


    with tab3:

        st.subheader("📊 Visualization Dashboard")

        num_cols = df.select_dtypes(include='number').columns.tolist()

        if num_cols:

            mode = st.radio("Mode", ["Single Chart", "Dashboard"])

            if mode == "Dashboard":

                x = st.selectbox("X-axis", df.columns)
                y = st.selectbox("Y-axis", num_cols)

                grouped = df.groupby(x, as_index=False)[y].sum()

                st.plotly_chart(style_chart(px.bar(grouped, x=x, y=y, color_discrete_sequence=[colors[0]]), f"{y} by {x}"), use_container_width=True)
                st.plotly_chart(style_chart(px.line(grouped, x=x, y=y, color_discrete_sequence=[colors[1]]), "Trend Analysis"), use_container_width=True)
                st.plotly_chart(style_chart(px.scatter(df, x=y, y=y, color_discrete_sequence=[colors[2]]), "Scatter Plot"), use_container_width=True)
                st.plotly_chart(style_chart(px.histogram(df, x=y, color_discrete_sequence=[colors[3]]), "Distribution"), use_container_width=True)
                st.plotly_chart(style_chart(px.box(df, y=y, color_discrete_sequence=[colors[4]]), "Outlier Detection"), use_container_width=True)

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as z:
                    z.writestr("chart_data.csv", grouped.to_csv(index=False))
                    z.writestr("instructions.txt", f"Use {x} as X-axis and {y} as Y-axis")

                st.download_button("Download Power BI Package", zip_buffer.getvalue(), "powerbi.zip")

            else:

                chart = st.selectbox("Chart", ["Bar", "Line", "Histogram"])

                if chart == "Bar":
                    x = st.selectbox("X", df.columns)
                    y = st.selectbox("Y", num_cols)
                    grouped = df.groupby(x, as_index=False)[y].sum()
                    st.plotly_chart(style_chart(px.bar(grouped, x=x, y=y, color_discrete_sequence=[colors[0]]), f"{y} by {x}"), use_container_width=True)

                elif chart == "Line":
                    x = st.selectbox("X", df.columns)
                    y = st.selectbox("Y", num_cols)
                    grouped = df.groupby(x, as_index=False)[y].sum()
                    st.plotly_chart(style_chart(px.line(grouped, x=x, y=y, color_discrete_sequence=[colors[1]]), "Trend"), use_container_width=True)

                elif chart == "Histogram":
                    col = st.selectbox("Column", num_cols)
                    st.plotly_chart(style_chart(px.histogram(df, x=col, color_discrete_sequence=[colors[2]]), "Distribution"), use_container_width=True)


    with tab4:
        st.download_button("Download CSV", df.to_csv(index=False), "data.csv")

else:
    st.info("Upload CSV to start")
