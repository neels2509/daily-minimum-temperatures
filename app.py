
import os
import re
from io import StringIO

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

MODEL_PATH = "manual_sarima_model.joblib"
DATA_FILE = "daily-minimum-temperatures-in-me.csv"

st.set_page_config(
    page_title="Melbourne Min Temperature Forecast",
    page_icon="🌤️",
    layout="wide",
)

# Load the pre-trained SARIMA model
@st.cache_resource
def load_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as input_file:
        lines = []
        for line in input_file:
            if re.match(r'^\s*"?\d{4}-\d{2}-\d{2}"?,', line):
                lines.append(line.replace(',?', ',0'))

    data = StringIO("".join(lines))
    df = pd.read_csv(
        data,
        names=["Date", "Temperature"],
        header=None,
        parse_dates=["Date"],
        index_col="Date",
        quotechar='"',
    )
    df.index = pd.to_datetime(df.index)
    df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
    df.dropna(subset=["Temperature"], inplace=True)
    return df


def forecast_sarima(model, last_date: pd.Timestamp, days: int) -> pd.Series:
    predicted = model.forecast(steps=days)
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq="D")
    return pd.Series(predicted.to_numpy(), index=future_dates)


def render_app():
    model_fit = load_model(MODEL_PATH)
    df_original = load_data(DATA_FILE)

    st.markdown("# 🌤️ Daily Minimum Temperature Forecasting")
    st.markdown(
        "Use the pre-trained SARIMA model to forecast future daily minimum temperatures for Melbourne, Australia. "
        "The dashboard blends historical observations with smooth forecast visuals."
    )

    start_date = df_original.index.min()
    end_date = df_original.index.max()
    total_points = len(df_original)
    last_value = df_original["Temperature"].iloc[-1]

    with st.container():
        col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 1.4])
        col1.metric("Data points", f"{total_points:,}")
        col2.metric("Date range", f"{start_date.date()} → {end_date.date()}")
        col3.metric("Last observed", f"{last_value:.1f}°C")
        col4.metric("Model", "SARIMA")

    with st.expander("Dataset preview", expanded=False):
        st.dataframe(df_original.tail(10).style.format({"Temperature": "{:.1f}"}), height=320)

    forecast_days = st.slider(
        "Forecast horizon (days)",
        min_value=1,
        max_value=365,
        value=30,
        help="Choose how far into the future to forecast daily minimum temperatures.",
    )

    if st.button("Run Forecast", type="primary"):
        forecast_series = forecast_sarima(model_fit, end_date, forecast_days)

        with st.container():
            left, right = st.columns((2, 1))
            with left:
                st.subheader(f"Forecast for the next {forecast_days} days")
                st.dataframe(
                    forecast_series.rename("Forecast (°C)").to_frame(),
                    use_container_width=True,
                    height=360,
                )

            with right:
                st.subheader("Forecast summary")
                st.metric("Forecast start", forecast_series.index[0].strftime("%Y-%m-%d"))
                st.metric("Forecast end", forecast_series.index[-1].strftime("%Y-%m-%d"))
                st.metric("Mean forecast", f"{forecast_series.mean():.1f}°C")
                st.metric("Max forecast", f"{forecast_series.max():.1f}°C")
                st.metric("Min forecast", f"{forecast_series.min():.1f}°C")

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df_original.index, df_original["Temperature"], label="Historical", color="#1f77b4", linewidth=1.5)
        ax.plot(forecast_series.index, forecast_series, label="Forecast", color="#ff7f0e", linewidth=2.5)
        ax.scatter(forecast_series.index, forecast_series, color="#ff7f0e", s=24)
        ax.set_title("Melbourne Daily Minimum Temperature: History and Forecast", fontsize=16, pad=15)
        ax.set_xlabel("Date")
        ax.set_ylabel("Temperature (°C)")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
        st.pyplot(fig)

        st.markdown(
            "---\n"
            "### Insights\n"
            "- The model is trained on historical daily minimum temperature data from 1981 to 1990.\n"
            "- Forecast values are generated from a SARIMA model and shown above.\n"
            "- Use the slider to change the prediction horizon and compare recent patterns with projected values."
        )

    st.sidebar.header("Model details")
    st.sidebar.write("**Forecast engine:** SARIMA")
    st.sidebar.write("**Dataset:** Melbourne daily minimum temperatures, 1981–1990")
    st.sidebar.write("**Source file:** `daily-minimum-temperatures-in-me.csv`")
    st.sidebar.write("**Model file:** `manual_sarima_model.joblib`")
    st.sidebar.markdown("---")
    st.sidebar.write(
        "Built for interactive forecasting and exploratory visualization. If you want, this app can be extended to compare SARIMA with neural forecasting models (LSTM/GRU) as well."
    )


if __name__ == "__main__":
    render_app()
