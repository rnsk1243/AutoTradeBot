import matplotlib.pyplot as plt
import pandas as pd
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
import math
from InitGlobal import stock_global as sg

class ElderTradeSystem:
    def __init__(self):
        try:
            self.__logger = sg.g_logger

        except FileNotFoundError as e:
            print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=3)

    def print_chart(self, df):

        try:
            df_chart = df
            df_chart['number'] = df.date.map(mdates.date2num)
            ohlc = df_chart[['number', 'open', 'high', 'low', 'close']]

            plt.figure(figsize=(9, 9))
            p1 = plt.subplot(3, 1, 1)
            plt.title('Triple Screen Trading - First Screen MACD')
            plt.grid(True)

            candlestick_ohlc(p1, ohlc.values, width=.6, colorup='red',
                             colordown='blue')
            p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.plot(df_chart.number, df_chart['ema_long'], color='c', label='ema_long')
            plt.legend(loc='best')

            p2 = plt.subplot(3, 1, 2)
            plt.grid(True)
            p2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.bar(df_chart.number, df_chart['macdhist'], color='m', label='MACD-Hist')
            plt.plot(df_chart.number, df_chart['macd'], color='b', label='MACD')
            plt.plot(df_chart.number, df_chart['signal'], 'g--', label='MACD-Signal')
            plt.legend(loc='best')

            p3 = plt.subplot(3, 1, 3)
            plt.grid(True)
            p3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.plot(df.number, df['fast_k'], color='c', label='%K')
            plt.plot(df.number, df['slow_d'], color='k', label='%D')
            plt.plot(df.number, df['hist_inclination_avg'], 'r--', label='MACD-HI-Avg')
            plt.yticks([0, 20, 80, 100])
            plt.legend(loc='best')
            plt.show()

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} print_chart : {str(e)}", log_lv=3)

    def get_macd_stochastic(self, df):
        """
        MACD,ストキャスティクスを抽出
        :param stock_name: 株の名前または株のコード
        :param days_long: 一番長いの何日移動平均か
        :return: df
        """
        try:
            if df is None or len(df) <= 0:
                return None

            rieki_persent = 0
            larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']
            slow_d_rolling = sg.g_json_trading_config['day_rolling']
            recent_rieki_count_day = sg.g_json_trading_config['recent_rieki_count_day']

            hennka_price = df['open'] + (((df['high'] - df['low']).shift()) * larry_constant_K_anl)
            is_hennka_kau = hennka_price < df['high']
            is_hennka_rieki = hennka_price < df['close']
            is_hennka_not_rieki = hennka_price >= df['close']

            is_rieki = is_hennka_kau & is_hennka_rieki
            is_not_rieki = is_hennka_kau & is_hennka_not_rieki
            rieki_count = is_rieki.sum()
            recent_rieki_count = is_rieki.iloc[-recent_rieki_count_day:].sum()
            recent_not_rieki_count = is_not_rieki.iloc[-recent_rieki_count_day:].sum()

            hennka_kau_count = is_hennka_kau.sum()
            if hennka_kau_count > 0:
                rieki_persent = round((rieki_count / hennka_kau_count) * 100)

            ndays_high = df.high.rolling(window=len(df), min_periods=1).max()  # 7日最大値
            ndays_low = df.low.rolling(window=len(df), min_periods=1).min()  # 7日最小値

            high_low = (ndays_high - ndays_low)
            high_low = high_low[high_low != 0]

            fast_k = ((df.close - ndays_low) / high_low) * 100  # 早いK線
            slow_d = fast_k.rolling(window=slow_d_rolling).mean()  # 遅いD線

            df_analysis = df.iloc[[-1]].assign(slow_d=[slow_d.iloc[-1]]).dropna()
            df_analysis = df_analysis.assign(hennka_price=hennka_price,
                                             rieki_persent=rieki_persent,
                                             recent_rieki_count=recent_rieki_count,
                                             recent_not_rieki_count=recent_not_rieki_count).dropna()

            return df_analysis

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} get_MACD : {str(e)}", log_lv=3)
            return None

    def is_buy_sell(self, df_day):
        """
        株を買うか売るか見守るか選択
        :param slow_d_buy:
        :param slow_d_sell:
        :param df_day:
        :param df_min:
        :return: タプル(True=買う,False=売る,None=見守る／点数=高いほど買う)
        """
        try:
            if df_day is None:
                self.__logger.write_log(f"is_buy_sell // df_day is None", log_lv=3)
                return None

            rieki_persent = df_day['rieki_persent']
            slow_d = df_day['slow_d']
            j_rieki_persent_break = sg.g_json_trading_config['rieki_persent_break']
            j_slow_d_buy = sg.g_json_trading_config['slow_d_buy']

            if j_rieki_persent_break < rieki_persent and slow_d < j_slow_d_buy:
                result = True
            else:
                result = None

            return result

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} is_buy_sell : {str(e)}", log_lv=3)
            return None

    def is_buy_sell_nomal(self, slow_d_buy, slow_d_sell, df_day, df_min, df_today, name, rieki_persent_break):
        """
        株を買うか売るか見守るか選択
        :param slow_d_buy:
        :param slow_d_sell:
        :param df_day:
        :param df_min:
        :return: タプル(True=買う,False=売る,None=見守る／点数=高いほど買う)
        """
        try:
            if df_day is None or df_min is None:
                self.__logger.write_log(f"is_buy_sell_nomal // df_day or df_min is None", log_lv=3)
                return None

            slow_d_day = df_day['slow_d']
            h = df_min['date'].hour
            min = df_min['date'].minute

            if h == 15 and min >= 15:
                # print(f"{df_min['date'].day}일 장 종료")
                return False

            larry_constant_K_buy = sg.g_json_trading_config['larry_constant_K_buy']
            hennka_price = df_today.open + ((df_day.high - df_day.low) * larry_constant_K_buy)

            recent_rieki_count = df_day.recent_rieki_count
            recent_not_rieki_count = df_day.recent_not_rieki_count
            rieki_persent = df_day.rieki_persent
            # df_today.hennka_price

            if hennka_price < df_min['close'] and \
               rieki_persent > rieki_persent_break and \
               recent_not_rieki_count == 0 <= recent_rieki_count:
                result = True
            else:
                result = None

            # if hennka_price < df_min['close'] and \
            #    rieki_persent > rieki_persent_break and \
            #    recent_rieki_count >= recent_not_rieki_count:
            #     result = True
            # else:
            #     result = None

            # if hennka_price < df_min['close']:
            #     result = True
            # else:
            #     result = None

            return result

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} is_buy_sell : {str(e)}", log_lv=3)
            return None