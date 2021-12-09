import pandas as pd
import time
import urllib.request
import json
from datetime import datetime, timedelta
import utils as ut


class KrakenTrades:
    API_DOMAIN = 'https://api.kraken.com'
    API_PATH = '/0/public/'
    API_METHOD = 'Trades'

    @staticmethod
    def __trades_to_dataframe(_trades):
        df =\
            pd.DataFrame(_trades,
                         columns=['Price', 'Volume', 'Time',
                                  'Buy/Sell', 'Limited/Market', '_'])
        df['Time'] = pd.to_datetime(df['Time'], unit='s')
        df.set_index('Time', inplace=True)
        df.drop(columns=['_', 'Buy/Sell', 'Limited/Market'], inplace=True)
        df = df.astype(float)
        df['Value'] = df['Price'] * df['Volume']

        return df

    def __init__(self, pair):
        self.pair = pair
        self.last_trade = None
        self.first_trade = None
        self.values = pd.DataFrame()

    def __retrive_trades(self, _from, _to=datetime.now()):

        # starting time (_from)
        if self.first_trade:
            self.first_trade = min(_from, self.first_trade)
        else:
            self.first_trade = _from

        # API start
        api_start = f'{_from.timestamp() * 1000000000 + 1000:.0f}'

        # accumulate trades from starting time
        # repeat until objective time (_to) is reached
        _trades = []
        last_timestamp = None
        while True:
            api_data = f'?pair={self.pair}&since={api_start}'
            api_request = urllib.request.Request(
                self.API_DOMAIN + self.API_PATH + self.API_METHOD + api_data)
            try:
                api_data = urllib.request.urlopen(api_request).read()
            except Exception as err:
                print('Receiving error from api: ', err, end='\r')
                time.sleep(3)
                continue

            api_data = json.loads(api_data)

            # Move starting time
            try:
                api_start = api_data["result"]["last"]
            except KeyError:
                print('Waiting', end='\r')
                time.sleep(3)
                continue

            # Accumulate trades
            _trades += api_data['result'][self.pair]
            print('Receiving trades:', len(_trades), end='\r')

            # Check if objective time is reached or no result from last datetime
            last_timestamp = int(api_data['result']['last']) / 1000000000
            if last_timestamp >= _to.timestamp() or \
                    not api_data['result'][self.pair]:
                break

        return (_trades,
                datetime.fromtimestamp(last_timestamp))

    def update_trades(self, _pair, _from):

        # If first time we update --> we have to load from the beginning
        if not self.first_trade:
            _trades, self.last_trade = self.__retrive_trades(_from)
            self.values = self.__trades_to_dataframe(_trades)

        # If no change in crypto / standard currency pair
        # then update from last to now and update last
        elif _pair == self.pair and _from >= self.first_trade:
            _trades, self.last_trade = self.__retrive_trades(self.last_trade)
            self.values = pd.concat([self.values,
                                     self.__trades_to_dataframe(_trades)])
        else:
            print('Recalculando datos...', end='\r')
            self.pair = _pair
            self.values = pd.DataFrame()
            _trades, self.last_trade = self.__retrive_trades(_from)
            self.values = self.__trades_to_dataframe(_trades)

    def __str__(self):
        return \
            f"Pair:    {self.pair} trades" + '\n' + \
            f"- from:  {self.first_trade.strftime('%d/%m/%Y %H:%M:%S')}"\
            + '\n' + \
            f"- to:    {self.last_trade.strftime('%d/%m/%Y %H:%M:%S')}"


class GroupedTrades:

    def __init__(self):
        self.frequency = None
        self.anchor = None
        self.last_complete_window = None
        self.values = pd.DataFrame()
        self.ohlc = pd.DataFrame()
        self.vwap = pd.DataFrame()

    def __update_simple_vwap(self):
        self.vwap = self.values[['Value', 'Volume']].copy()
        self.vwap['vwap'] = self.vwap['Value'] / self.vwap['Volume']

    def __update_classic_vwap(self):
        # vwap calculated from anchor time
        selector = (self.values.index >= self.anchor)
        # Calculations for Vwap
        self.vwap = self.values[selector][
            ['Volume', 'High', 'Low', 'Close']].copy()
        self.vwap['Typical_price'] = \
            (self.vwap['High'] + self.vwap['Low'] + self.vwap['Close']) / 3
        self.vwap['Weighed_volume'] = \
            self.vwap['Typical_price'] * self.vwap['Volume']
        self.vwap['Acc_weighed_volume'] = \
            self.vwap['Weighed_volume'].cumsum()
        self.vwap['Acc_volume'] = \
            self.vwap['Volume'].cumsum()
        self.vwap['vwap'] = self.vwap['Acc_weighed_volume'] / \
            self.vwap['Acc_volume']

    def __update_values(self, _trades):
        # Aggregate trades
        self.values = \
            _trades.groupby(pd.Grouper(freq=self.frequency, label='left')). \
            agg(Volume=('Volume', 'sum'), Value=('Value', 'sum'),
                Open=('Price', 'first'), High=('Price', 'max'),
                Low=('Price', 'min'), Close=('Price', 'last'))

        # Calculations for ohlc
        self.values['oc_max'] = self.values[['Open', 'Close']].max(axis=1)
        self.values['oc_min'] = self.values[['Open', 'Close']].min(axis=1)
        self.values['oc_sign'] = \
            (self.values['Close'] - self.values['Open']). \
            map(lambda x: -1 if x < 0 else 1 if x > 0 else 0)

        # Complete structures
        self.ohlc = self.values[['Open', 'High', 'Low', 'Close',
                                 'oc_min', 'oc_max', 'oc_sign']]

        self.volume = self.values[['Value', 'oc_sign']]

        # Calculate vwap from anchor time or simple vwap if not given
        if self.anchor:
            self.__update_classic_vwap()
        else:
            self.__update_simple_vwap()

    def load_values(self, _trades, _frequency, _anchor_time):
        self.frequency = _frequency
        self.anchor = _anchor_time
        self.__update_values(_trades)


class TimeParams:

    def __init__(self, window_size_name, anchor_name, no_windows):
        self.window_size_name = None
        self.window_size = None
        self.frequency = None
        self.anchor_name = None
        self.anchor_gap = None
        self.number_of_windows = None
        self.anchor_time, self.trades_start = (None, None)
        self.update_params(window_size_name, anchor_name, no_windows)

    def update_params(self, window_size_name, anchor_name, no_windows):
        self.window_size_name = window_size_name
        self.window_size = ut.window_size[window_size_name][0]
        self.frequency = ut.window_size[window_size_name][1]
        self.anchor_name = anchor_name
        self.anchor_gap = ut.anchor_time[anchor_name]
        self.number_of_windows = no_windows
        self.anchor_time, self.trades_start = self.__trades_from_time__()

    def __trades_from_time__(self):
        # Considering we divide the hour in different windows
        # get the begining of the last window before now()

        last_window_start = \
            ut.get_time_window_start(datetime.now(),
                                     window=self.window_size)

        # Considering we are showing no_windows number of windows
        # calculate the starting time from the last window start that
        # give us that than number of full windows
        span_interval = \
            ut.get_datime_interval(to_datetime=last_window_start,
                                   window=self.window_size,
                                   number_of_windows=self.number_of_windows)

        # As we are setting an anchor time for calculating the vwap
        # we substract a number of hours from the last window start
        # or we define that there is no anchor
        if self.anchor_gap is not None:
            anchor_time = last_window_start -\
                          timedelta(seconds=self.anchor_gap)
            trades_start = min(anchor_time, span_interval[0])
            # Finally we need trades from the min of the starting time
            # of the graph and the anchor time calculated previously
            return anchor_time, trades_start
        else:
            # Or if no anchor
            return None, span_interval[0]
