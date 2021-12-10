# Imports
import dash
from dash import dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html
from dash.dependencies import Output, Input

# User define functions
import utils as ut
from classes import KrakenTrades, GroupedTrades, TimeParams

# Default params:
default_crypto = 'ETH'
default_currency = 'EUR'
default_window = '5 min'
default_anchor = '-6 hours'
CONSTANT_NO_WINDOWS = 90

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Cotizaciones crypto"
server = app.server

app.layout = html.Div(
    children=[

        html.Div(
            children=[
                html.H1(
                    children="Crypto price", className="header-title"
                ),
                html.P(
                    children="Crypto price .vs. standard currency",
                    className="header-description",
                ),
            ],
            className="header",
        ),

        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="From crypto", className="menu-title"),
                        dcc.Dropdown(
                            id="from-crypto",
                            options=[
                                {"label": crypto, "value": crypto}
                                for crypto in ['ETH', 'XBT']
                            ],
                            value=default_crypto,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="To currency", className="menu-title"),
                        dcc.Dropdown(
                            id="to-currency",
                            options=[
                                {"label": currency, "value": currency}
                                for currency in ['EUR', 'USD']
                            ],
                            value=default_currency,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(children="Time window", className="menu-title"),
                        dcc.Dropdown(
                            id="window-size",
                            options=[
                                {"label": window, "value": window}
                                for window in ut.window_size.keys()
                            ],
                            value=default_window,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Anchor (for Vwap calc)", className="menu-title"),
                        dcc.Dropdown(
                            id="anchor-time",
                            options=[
                                {"label": anchor, "value": anchor}
                                for anchor in ut.anchor_time.keys()
                            ],
                            value=default_anchor,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="graph", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(

    Output("graph", "figure"),
    [
        Input("from-crypto", "value"),
        Input("to-currency", "value"),
        Input("window-size", "value"),
        Input("anchor-time", "value"),
    ])
def display(from_crypto, to_currency, window_size, anchor_time):

    # Update params and time values:
    new_pair = 'X'+from_crypto+'Z'+to_currency
    tparams.update_params(window_size, anchor_time, CONSTANT_NO_WINDOWS)

    # update trades
    trades.update_trades(new_pair, tparams.trades_start)

    # group trades
    grouped_trades = GroupedTrades()
    grouped_trades.load_values(trades.values,
                               tparams.frequency,
                               tparams.anchor_time)

    # Control data to show in the window
    # Graph always 120 (CONSTANT_NO_WINDOWS) windows
    ohlc_data = grouped_trades.ohlc[-(CONSTANT_NO_WINDOWS+1):]
    vwap_data = grouped_trades.vwap[-(CONSTANT_NO_WINDOWS + 1):]
    volume_data = grouped_trades.volume[-(CONSTANT_NO_WINDOWS + 1):]
    window_time_start = ohlc_data.index[0]
    # instant_data = trades.values[trades.values.index >= window_time_start]

    # make graphs
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Candlestick(
            x=ohlc_data.index,
            open=ohlc_data['Open'],
            high=ohlc_data['High'],
            low=ohlc_data['Low'],
            close=ohlc_data['Close'],
            name='Ohlc'
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=vwap_data.index,
                   y=vwap_data.vwap,
                   line=dict(color='rgb(57, 105, 172)', width=2),
                   name='Vwap'),
        secondary_y=False,
    )
    # fig.add_trace(
    #     go.Scatter(x=instant_data.index,
    #                y=instant_data.Price, opacity=.75,
    #                line=dict(color='gray', width=2),
    #                name='Instant price'),
    #     secondary_y=False,
    # )
    fig.add_trace(
        go.Bar(x=volume_data.index,
               y=volume_data.Value,
               marker_color='rgb(47, 138, 196)',
               marker_line_color='#1f77b4',
               opacity=0.25,
               marker_line_width=1.5,
               name='Traded volume'),
        secondary_y=True,
    )
    fig.update_layout(xaxis_rangeslider_visible=False)

    fig.update_layout(
        title={
            'text': f"from {from_crypto} to {to_currency}"
                    f" (starting at "
                    f"{window_time_start.strftime('%d/%m/%Y %H:%M:%S')})",

            'y': 0.9,
            'x': 0.05,
            'xanchor': 'left',
            'yanchor': 'top'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1),
    )

    fig.update_xaxes(
        title_text="<b>UTC Time</b>",
        titlefont=dict(
            size=12,
            color="gray"),
        showline=True,
        linewidth=1,
        linecolor='gray',
        tickfont=dict(size=11))

    fig.update_yaxes(
        title_text=f"<b>Price</b> ({to_currency})",
        titlefont=dict(
            size=12,
            color="gray"),
        ticks="outside",
        ticklen=10,
        tickcolor='rgba(0,0,0,0)',
        tickfont=dict(size=11),
        secondary_y=False)
    fig.update_yaxes(
        title_text=f"<b>Traded volume</b> ({to_currency})",
        titlefont=dict(
            size=12,
            color="gray"),
        ticks="outside",
        ticklen=10,
        tickcolor='rgba(0,0,0,0)',
        tickfont=dict(size=11),
        showgrid=False,
        secondary_y=True)

    fig.update_layout(
        autosize=True,
        height=500,
        margin=dict(
            l=100,
            r=50,
            b=100,
            t=100,
            pad=1,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


if __name__ == "__main__":

    tparams = TimeParams(default_window, default_anchor, CONSTANT_NO_WINDOWS)
    currency_pair = 'X' + default_crypto + 'Z' + default_currency

    # Init KrakenTrades class
    trades = KrakenTrades(currency_pair)
    trades.update_trades(currency_pair, tparams.trades_start)

    app.run_server(debug=True)
