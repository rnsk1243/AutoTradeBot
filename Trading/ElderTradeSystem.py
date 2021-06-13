import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
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

    def get_macd_stochastic(self, df, days_long):
        """
        MACD,ストキャスティクスを抽出
        :param stock_name: 株の名前または株のコード
        :param days_long: 一番長いの何日移動平均か
        :return: df
        """
        try:
            days_middle = round(days_long*0.46) # 130日:60日:45日の比率で63:(63*0.46):(63*0.35)に決め
            days_short = round(days_long*0.35)

            ema_middle = df.close.ewm(span=days_middle).mean()  # close days_middle 移動平均
            ema_long = df.close.ewm(span=days_long).mean()  # close days_long 移動平均
            macd = ema_middle - ema_long  # MACD線
            signal = macd.ewm(span=days_short).mean()  # シグナル
            macdhist = macd - signal # MACD ヒストグラム
            macdhist_ave = macdhist.sum() // len(macdhist)

            ndays_high = df.high.rolling(window=len(df), min_periods=1).max()  # 7日最大値
            ndays_low = df.low.rolling(window=len(df), min_periods=1).min()  # 7日最小値

            high_low = (ndays_high - ndays_low)
            high_low.replace(0, 0.1)

            fast_k = ((df.close - ndays_low) / high_low) * 100  # 早いK線
            slow_d = fast_k.rolling(window=sg.g_one_day_data_amount // 3).mean()  # 遅いD線

            df = df.assign(ema_long=ema_long, ema_middle=ema_middle, macd=macd, signal=signal,
                           macdhist=macdhist, fast_k=fast_k, slow_d=slow_d).dropna()

            return df, macdhist_ave

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} get_MACD : {str(e)}", log_lv=3)


    def macd_sec_dpc(self, df, rolling_day):
        """
        MACDヒストグラムの増加率平均を救う。
        :param df: macdヒストグラムカラムがあるDataframe
        :param days: いつから計算するか
        :return:　df
        """
        try:
            if 'macdhist' in df.columns:
                df_days_hist = df['macdhist']  # silce
                df_days_hist_shift = df_days_hist.shift(sg.g_one_day_data_amount*3)  # 60だけずらす
                delta_hist = df_days_hist - df_days_hist_shift  # どのくらい変化か
                delta_hist.iloc[0] = 0
                delta_hist_sec_dpc = (delta_hist / df_days_hist.abs()) * 100 # 変化率

                hist_inclination_avg = delta_hist_sec_dpc.rolling(window=rolling_day).mean()  # 変化率平均

                df = df.assign(delta_hist_sec_dpc=delta_hist_sec_dpc,
                               hist_inclination_avg=hist_inclination_avg).dropna()

                return df
            else:
                return None

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} macd_sec_dpc : {str(e)}", log_lv=3)


    def is_buy_sell_nomal(self, macdhist_ave, macdhist, slow_d, slow_d_buy, slow_d_sell):
        """
        株を買うか売るか見守るか選択
        :param macd_sec_dpc:
        :param slow_d:
        :return: タプル(True=買う,False=売る,None=見守る／点数=高いほど買う)
        """
        try:
            if macdhist is None or slow_d is None:
                self.__logger.write_log(f"is_buy_sell_nomal macdhist or slow_d is None", log_lv=3)
                return None
            if -350 < macdhist_ave < 0 and macdhist < -320 and slow_d <= slow_d_buy:
                # self.__logger.write_log(f"\t산다\tdate \t{print_info_list[1]}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tcode \t{print_info_list[0]}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tmacd_sec_dpc \t{macd_sec_dpc}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tslow_d \t{slow_d}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tclose \t{print_info_list[2]}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tdelta_hist \t{print_info_list[3]}\t", log_lv=2)
                # self.__logger.write_log(f"\t산다\tmacd_sec_dpc \t{print_info_list[4]}\t", log_lv=2)
                # self.__logger.write_log(f"------------------------------------", log_lv=2)
                result = True
            elif macdhist_ave > 0 and macdhist > 280 and slow_d >= slow_d_sell:
                # self.__logger.write_log(f"\t판다\tdate \t{print_info_list[1]}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tcode \t{print_info_list[0]}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tmacd_sec_dpc \t{macd_sec_dpc}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tslow_d \t{slow_d}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tclose \t{print_info_list[2]}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tdelta_hist \t{print_info_list[3]}\t", log_lv=2)
                # self.__logger.write_log(f"\t판다\tmacd_sec_dpc \t{print_info_list[4]}\t", log_lv=2)
                # self.__logger.write_log(f"------------------------------------", log_lv=2)
                result = False
            else:
                result = None

            return result

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} is_buy_sell : {str(e)}", log_lv=3)
