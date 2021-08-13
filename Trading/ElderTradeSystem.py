import matplotlib.pyplot as plt
import pandas as pd
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from datetime import datetime
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
            rieki_persent = 0
            larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']
            recent_rieki_count_day = sg.g_json_trading_config['recent_rieki_count_day']
            recent_rieki_count_day_long = sg.g_json_trading_config['recent_rieki_count_day_long']

            if df is None or len(df) <= recent_rieki_count_day_long:
                return None

            df_shift = df.shift().dropna()
            hennka_price = df['open'] + ((df_shift['high'] - df_shift['low']) * larry_constant_K_anl)
            hennka_price_pulse = ((df_shift['high'] - df_shift['low']) * larry_constant_K_anl)
            df = df.assign(hennka_price=hennka_price)
            df = df.assign(hennka_price_pulse=hennka_price_pulse)
            df = df.dropna()
            df = df[df['hennka_price_pulse'] > 0]

            is_hennka_kau = df['hennka_price'] < df['high']
            is_hennka_rieki = df['hennka_price'] < df['close']
            is_hennka_not_rieki = df['hennka_price'] >= df['close']

            is_rieki = is_hennka_kau & is_hennka_rieki
            is_not_rieki = is_hennka_kau & is_hennka_not_rieki
            rieki_count = is_rieki.sum()
            recent_rieki_count = is_rieki.iloc[-recent_rieki_count_day:].sum()
            recent_not_rieki_count = is_not_rieki.iloc[-recent_rieki_count_day:].sum()
            recent_rieki_count_long = is_rieki.iloc[-recent_rieki_count_day_long:].sum()
            recent_not_rieki_count_long = is_not_rieki.iloc[-recent_rieki_count_day_long:].sum()
            hennka_kau_count = is_hennka_kau.sum()
            if hennka_kau_count > 0:
                rieki_persent = round((rieki_count / hennka_kau_count) * 100)

            df_analysis = df.iloc[[-1]].assign(rieki_persent=rieki_persent,
                                               recent_rieki_count=recent_rieki_count,
                                               recent_not_rieki_count=recent_not_rieki_count,
                                               recent_rieki_count_long=recent_rieki_count_long,
                                               recent_not_rieki_count_long=recent_not_rieki_count_long).dropna()

            return df_analysis

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} get_MACD : {str(e)}", log_lv=3)
            return None

    def is_buy_sell(self, df_yester_day, hennka_price, cur_price):
        """
        株を買うか売るか見守るか選択
        :param df_day:
        :param df_min:
        :return: タプル(True=買う,False=売る,None=見守る／点数=高いほど買う)
        """
        try:
            if df_yester_day is None or len(df_yester_day) <= 0:
                self.__logger.write_log(f"is_buy_sell // df_yester_day is None", log_lv=3)
                return None

            t_now = datetime.now()
            cur_h = t_now.hour
            cur_min = t_now.minute

            if cur_h == 9 and cur_min < 5:
                return None
            elif (cur_h == 9 and cur_min >= 5) or (9 < cur_h <= 14) or (cur_h == 14 and cur_min < 60):
                min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']

                recent_rieki_count_long = df_yester_day.recent_rieki_count_long
                recent_not_rieki_count_long = df_yester_day.recent_not_rieki_count_long
                recent_not_rieki_count = df_yester_day.recent_not_rieki_count
                recent_rieki_count = df_yester_day.recent_rieki_count

                if hennka_price < cur_price < (hennka_price * 1.003) and \
                   recent_not_rieki_count_long < recent_rieki_count_long and \
                   recent_not_rieki_count == 0 and min_rieki_amount <= recent_rieki_count:
                    result = True
                else:
                    result = None
            elif cur_h == 15 and 15 <= cur_min < 20:
                # print(f"{df_min['date'].day}일 장 종료")
                return False
            else:
                return None

            return result

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} is_buy_sell : {str(e)}", log_lv=3)
            return None

    def is_buy_sell_nomal(self, df_day, df_min, df_today):
        """
        株を買うか売るか見守るか選択
        :param df_day:
        :param df_min:
        :return: タプル(True=買う,False=売る,None=見守る／点数=高いほど買う)
        """
        try:
            if df_day is None or df_min is None:
                self.__logger.write_log(f"is_buy_sell_nomal // df_day or df_min is None", log_lv=3)
                return None

            h = df_min['date'].hour
            min = df_min['date'].minute

            if h == 15 and min >= 15:
                # print(f"{df_min['date'].day}일 장 종료")
                return False

            min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']
            larry_constant_K_buy = sg.g_json_trading_config['larry_constant_K_buy']
            hennka_price = df_today.open + ((df_day.high - df_day.low) * larry_constant_K_buy)

            recent_rieki_count = df_day.recent_rieki_count
            recent_not_rieki_count = df_day.recent_not_rieki_count
            recent_rieki_count_long = df_day.recent_rieki_count_long
            recent_not_rieki_count_long = df_day.recent_not_rieki_count_long
            # rieki_persent = df_day.rieki_persent

            if hennka_price < df_min['close'] and \
               recent_not_rieki_count_long < recent_rieki_count_long and \
               recent_not_rieki_count == 0 and min_rieki_amount <= recent_rieki_count:
                result = True
            else:
                result = None

            return result

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} is_buy_sell : {str(e)}", log_lv=3)
            return None