from dash import Dash, html, dcc, Output, Input
import pandas as pd
import plotly.express as px
from flask import request
from collections import defaultdict
import requests
import logging
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from flask_instance import server
import os


class LimitExeededError(Exception):
    pass


KEY = os.getenv("WEATHER_API_KEY")
URL = "https://api.weatherapi.com/v1/forecast.json?key={KEY}&q={PLACE}&days=1&aqi=no&alerts=no"

logger = logging.getLogger("Weather app")
logging.basicConfig(level="INFO")
N_THRESHOLD = 2 * 10**5
NOTIFICATION_PERCENT = 0.8
if __name__ == "__main__":
    URL_BASE_PATHNAME = None
else:
    URL_BASE_PATHNAME = "/apps/weather/"

app = Dash(__name__, server=server, url_base_pathname=URL_BASE_PATHNAME)
access_counts = defaultdict(int)
app.title = "Weather App"
app.layout = dmc.NotificationsProvider(
    html.Div(
        [
            html.Div(id="notifications-container"),
            html.H1(
                children="My Weather App",
                style={
                    "textAlign": "center",
                    "color": "#fff",
                    "font-size": "3vw",  # Adjust font size using vw (viewport width)
                },
            ),
            dcc.Input(
                placeholder="Write the name of the place",
                id="input-place",
                type="text",
                style={
                    "fontSize": "1.5vw",  # Adjust font size using vw (viewport width)
                    "color": "#fff",  # Text color (white for contrast)
                    "backgroundColor": "rgba(255, 255, 255, 0.1)",  # Semi-transparent white background
                    "border": "2px solid #fff",  # White border
                    "padding": "12px 15px",  # Padding around the input field
                    "borderRadius": "10px",  # Rounded corners
                    # "width": "300px",  # Width of the input field
                    "boxShadow": "2px 2px 5px rgba(0, 0, 0, 0.1)",  # Box shadow for depth
                    "transition": "all 0.3s ease",  # Smooth transition effect
                    # "position": "fixed",  # Fixed position
                    # "top": "20px",  # Distance from the top
                    "right": "5px",  # Distance from the left
                    "margin-right": "2rem",  # Right margin
                    # "margin-bottom": "2rem",  # Bottom margin
                    # "padding": "2rem",  # Padding
                },
            ),
            html.Div(id="temp-stats", style={"textAlign": "center", "color": "white"}),
            dcc.Graph(
                id="graph-content",
                style={
                    # "margin-top": "5rem",
                    "height": "60vh",
                },
            ),
        ],
        style={
            "textAlign": "Right",
            "position": "sticky",
            "margin-top": "0rem",
            # "width": "100%",
            "height": "100vh",
            "background": "linear-gradient(to top, #f5ed95, #0E86D4)",
            "padding": "10px",
        },
    ),
    position="top-right",
)


def register_client_ip():
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        addr = request.environ["REMOTE_ADDR"]
    else:
        addr = request.environ["HTTP_X_FORWARDED_FOR"]  # if behind a proxy

    access_counts[addr] += 1
    logger.info(access_counts)


def get_data(place):
    """This function gets the data from API using HTTP GET method"""
    if place is None:
        raise ValueError("Please specify a valid place parameter")

    resp = requests.get(URL.format(KEY=KEY, PLACE=place))
    resp.raise_for_status()
    dct_resp = resp.json()
    name = dct_resp["location"]["name"]
    region = dct_resp["location"]["region"]
    country = dct_resp["location"]["country"]
    forecast = dct_resp["forecast"]["forecastday"][0]["hour"]
    time = []
    temp_c = []
    for i in forecast:
        time.append(i["time"])
        temp_c.append(i["temp_c"])

    df = pd.DataFrame(
        {"Time [h]": time, "Temperature [C]": temp_c, "place": len(time) * [place]}
    )
    output_body = {
        "name": name,
        "region": region,
        "country": country,
        "df": df,
        "status_code": resp.status_code,
    }
    return output_body


def monitor_access_count():
    access_count = sum(access_counts.values())
    state = {}
    if access_count > N_THRESHOLD:
        state["notification"] = dmc.Notification(
            title="Hey there!",
            id="simple-notify",
            action="show",
            message=r"You have reached the 100 % of access limit! You can try next month.",
            icon=DashIconify(icon="ic:round-celebration"),
            style={"align-items": "top"},
        )
        state["state"] = "error"
    elif access_count > NOTIFICATION_PERCENT * N_THRESHOLD:
        state["notification"] = dmc.Notification(
            title="Hey there!",
            id="simple-notify",
            action="show",
            message=r"You have reached the 80 % of access limit!",
            icon=DashIconify(icon="ic:round-celebration"),
            style={"align-items": "top"},
        )
        state["state"] = "warning"
    else:
        state["notification"] = None
        state["state"] = "success"
    return state


def figure_design(fig):
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",  # Set plot background to transparent
        paper_bgcolor="rgba(0, 0, 0, 0)",  # Set paper background to transparent
        font_color="white",
        autosize=True,  # Enable autosizing
        margin=dict(l=0, r=30, t=40, b=30),
        xaxis=dict(
            gridcolor="grey",
            linecolor="white",
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="grey",
            linecolor="white",
            zeroline=False,
            showgrid=True,
        ),
    )


@app.callback(
    [
        Output("graph-content", "figure"),
        Output("notifications-container", "children"),
        Output("temp-stats", "children"),
    ],  # New Output for temperature statistics
    Input("input-place", "value"),
)
def update_graph(value):
    try:
        register_client_ip()
        state = monitor_access_count()
        if state["state"] == "error":
            raise LimitExeededError("You have exceeded the access limit")
        output = get_data(value)
        df = output["df"]
        name = output["name"]
        region = output["region"]
        country = output["country"]
        max_temp_time = df.loc[df["Temperature [C]"].idxmax()]["Time [h]"]
        min_temp_time = df.loc[df["Temperature [C]"].idxmin()]["Time [h]"]
        max_temp = df["Temperature [C]"].max()  # Calculate max temperature
        min_temp = df["Temperature [C]"].min()  # Calculate min temperature
        fig = px.line(
            df,
            x="Time [h]",
            y="Temperature [C]",
            title=f"Temperature Over Time in {name}, {region}, {country}",
        )
        fig.update_xaxes(nticks=12)
        fig.update_traces(
            line=dict(color="rgb(0, 49, 101)"),
        )
        figure_design(fig)

        # Create text for temperature statistics with beautiful styling
        temp_stats_text = html.Div(
            [
                html.Div(
                    f"Max Temperature: {max_temp}°C at {max_temp_time[-5:]}",
                    style={
                        "color": "#12476C",
                        "font-size": "1.5vw",
                        "font-weight": "bold",
                    },
                ),
                html.Div(
                    f"Min Temperature: {min_temp}°C at {min_temp_time[-5:]}",
                    style={
                        "color": "#12476C",
                        "font-size": "1.5vw",
                        "font-weight": "bold",
                    },
                ),
            ]
        )

        return fig, state["notification"], temp_stats_text
    except (requests.exceptions.HTTPError, ValueError):
        # Return an empty graph initially or handle the default behavior
        fig = px.line()
        figure_design(fig)
        return fig, state["notification"], html.Div("")
    except Exception:
        logger.exception("Something went wrong")
        fig = px.line()
        figure_design(fig)
        return fig, state["notification"], html.Div("")


if __name__ == "__main__":
    app.run_server(debug=False)
