# Imports
import dash
from dash import dcc
import plotly.graph_objects as go
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
CONSTANT_NO_WINDOWS = 120

tparams = TimeParams(default_window, default_anchor, CONSTANT_NO_WINDOWS)
currency_pair = 'X'+default_crypto+'Z'+default_currency

# Trades
trades = KrakenTrades(currency_pair)
trades.get_trades_from(tparams.trades_start)

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
                    children="Par de monedas", className="header-title"
                ),
                html.P(
                    children="Display cotizaciones par de monedas en tiempo"
                             " real.",
                    className="header-description",
                ),
            ],
            className="header",
        ),

        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Crypto", className="menu-title"),
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
                        html.Div(children="Currency", className="menu-title"),
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
                        html.Div(children="Window", className="menu-title"),
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
                        html.Div(children="Anchor", className="menu-title"),
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
                        id="graph-ohlc", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="graph-volume", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="graph-instant", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [
        Output("graph-instant", "figure"),
        Output("graph-ohlc", "figure"),
        Output("graph-volume", "figure"),
    ],
    [
        Input("from-crypto", "value"),
        Input("to-currency", "value"),
        Input("window-size", "value"),
        Input("anchor-time", "value"),
    ])
def display(from_crypto, to_currency, window_size, anchor_time):

    # Update values:
    new_pair = 'X'+from_crypto+'Z'+to_currency

    previous_start = tparams.trades_start
    tparams.update_params(window_size, anchor_time, CONSTANT_NO_WINDOWS)

    print('Pair :', new_pair)
    print('Previous start: ', previous_start)
    print('Actual start  : ', tparams.trades_start)

    trades.update_trades(new_pair, tparams.trades_start)
    # Grouped trades
    grouped_trades = GroupedTrades()
    grouped_trades.load_values(trades.values,
                               tparams.frequency,
                               tparams.anchor_time)

    # Graph always 120 (CONSTANT_NO_WINDOWS) windows
    ohlc_data = grouped_trades.ohlc[-(CONSTANT_NO_WINDOWS+1):]
    vwap_data = grouped_trades.vwap[-(CONSTANT_NO_WINDOWS + 1):]
    fig_ohlc = go.Figure()
    fig_ohlc.add_trace(
        go.Candlestick(
            x=ohlc_data.index,
            open=ohlc_data['Open'],
            high=ohlc_data['High'],
            low=ohlc_data['Low'],
            close=ohlc_data['Close']
        )
    )
    fig_ohlc.add_trace(
        go.Scatter(x=vwap_data.index,
                   y=vwap_data.vwap)
    )
    fig_ohlc.update_layout(xaxis_rangeslider_visible=False)

    volume_data = grouped_trades.volume[-(CONSTANT_NO_WINDOWS + 1):]
    fig_volume = go.Figure()
    volume_colors = volume_data.oc_sign.map(lambda x: ut.candles_color.get(x))
    fig_volume.add_trace(
        go.Bar(x=volume_data.index,
               y=volume_data.Value,
               marker_color=volume_colors)
    )

    fig_instant = go.Figure()
    fig_instant.add_trace(
        go.Scatter(x=trades.values.index,
                   y=trades.values.Price)
    )

    return fig_instant, fig_ohlc, fig_volume


if __name__ == "__main__":
    app.run_server(debug=True)
