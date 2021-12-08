import pandas as pd
import time
import urllib.request
import json

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

        # AP start
        api_start = f'{_from.timestamp() * 1000000000 + 1000:.0f}'

        # accumulate trades from starting time
        # repeat until objective time (_to) is reached
        _trades = []
        while True:
            api_data = f'?pair={self.pair}&since={api_start}'
            api_request = urllib.request.Request(
                self.API_DOMAIN + self.API_PATH + self.API_METHOD + api_data)
            try:
                api_data = urllib.request.urlopen(api_request).read()
            except Exception as err:
                print(err)
                time.sleep(3)
                continue

            api_data = json.loads(api_data)

            # Move starting time
            api_start = api_data["result"]["last"]

            # Accumulate trades
            _trades += api_data['result'][self.pair]

            # Check if objective time is reached or no result from last datetime
            last_timestamp = int(api_data['result']['last']) / 1000000000
            if last_timestamp >= _to.timestamp() or \
                    not api_data['result'][self.pair]:
                break

        return (_trades,
                datetime.fromtimestamp(last_timestamp))

    def get_trades_from(self, _from):
        _trades, self.last_trade = self.__retrive_trades(_from)
        self.values = self.__trades_to_dataframe(_trades)
        # while until get end of interval or if no end to last

    def update_trades(self):
        # from last to now and update last
        _trades, self.last_trade = self.__retrive_trades(self.last_trade)
        self.values = pd.concat([self.values,
                                 self.__trades_to_dataframe(_trades)])

    def __str__(self):
        return \
            f"Pair:    {self.pair} trades" + '\n' + \
            f"- from:  {self.first_trade.strftime('%d/%m/%Y %H:%M:%S')}"\
            + '\n' + \
            f"- to:    {self.last_trade.strftime('%d/%m/%Y %H:%M:%S')}"


class GroupedTrades:

    def __init__(self, _frequency, _anchor_time=None):
        self.frequency = _frequency
        self.anchor = _anchor_time
        self.last_complete_window = None
        self.values = pd.DataFrame()
        self.ohlc = pd.DataFrame()
        self.vwap = pd.DataFrame()

    def __update_simple_vwap(self):
        self.vwap = self.values['Value'] / self.values['Volume']

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
            _trades.groupby(pd.Grouper(freq=frequency, label='left')). \
            agg(Volume=('Volume', 'sum'), Value=('Value', 'sum'),
                Open=('Price', 'first'), High=('Price', 'max'),
                Low=('Price', 'min'), Close=('Price', 'last'))

        # Update anchor if not given
        if not self.anchor:
            self.anchor = self.values.index[0]

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
        self.__update_classic_vwap()

        # recibo trades,
        # me quedo con los que son mayores que la última ventana completa
        # calculo el vwap de los trades
        # calculo _temp_last_complete_window
        # Desecho el vwap de la última ventana no completa
        # concateno los nuevos vwap
        # actualizo last_complete_window

    def load_values(self, _trades):
        self.__update_values(_trades)

