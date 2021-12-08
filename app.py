# Imports
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

# User define functions
import utils as ut
from classes import KrakenTrades, GroupedTrades


def plot(_trades, _grouped_trades, _window):

    # Sticks (High / Low)
    sticks = _grouped_trades.ohlc[['Low', 'High']].copy().reset_index()
    sticks['Time'] = sticks['Time'] + timedelta(seconds=_window / 2)
    sticks = sticks.to_numpy()

    # Candle (Close / Open)
    candles = _grouped_trades.ohlc[['oc_min', 'oc_max']].copy()
    candles['oc_color'] = _grouped_trades.ohlc['oc_sign'].\
        map(lambda x: ut.candles_color.get(x))
    candles = candles[['oc_min', 'oc_max', 'oc_color']].\
        reset_index()
    candles['Time'] = candles['Time'] + timedelta(seconds=_window / 2)
    candles = candles.to_numpy()

    # Graph ohlc + vwap
    plt.figure(figsize=(20, 6))
    plt.vlines(sticks[:, 0],
               sticks[:, 1], sticks[:, 2],
               'black', linewidths=1)
    plt.vlines(candles[:, 0],
               candles[:, 1], candles[:, 2],
               candles[:, 3], linewidths=7)

    vwap = _grouped_trades.vwap['vwap'].copy()
    vwap.index = vwap.index + timedelta(seconds=_window / 2)
    plt.plot(vwap)

    # Volumes
    volume = _grouped_trades.volume[['Value']].copy()
    volume['Base'] = 0
    volume['oc_color'] = _grouped_trades.volume['oc_sign'].\
        map(lambda x: ut.candles_color.get(x))
    volume = volume.reset_index()
    volume['Time'] = volume['Time'] + timedelta(seconds=_window / 2)
    volume = volume.to_numpy()

    # Graph volumes
    plt.figure(figsize=(20, 2))
    plt.vlines(volume[:, 0],
               volume[:, 2], volume[:, 1],
               volume[:, 3], linewidths=7)
    _trades.values['Price'].plot()

    # Graph instant
    plt.figure(figsize=(20, 2))
    _trades.values['Price'].plot()


# Execute
interval = '5 min'
time_span = '6 hour'
window = ut.intervals[interval][0]
frequency = ut.intervals[interval][1]
number_of_windows = ut.time_spans[time_span] / window

end_time = datetime.now()

window_start = ut.get_time_window_start(end_time, window=window)
span_interval =\
  ut.get_datime_interval(to_datetime=window_start,
                         window=window,
                         number_of_windows=number_of_windows)
starting_time = span_interval[0]

# Trades
trades = KrakenTrades('XETHZEUR')
trades.get_trades_from(starting_time)

flag = True
while flag:

    trades.update_trades()
    grouped_trades = GroupedTrades(frequency)
    grouped_trades.load_values(trades.values)

    plot(trades, grouped_trades, window)
    plt.show()
    flag = False
