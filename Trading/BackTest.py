import backtrader as bt
from datetime import datetime
from InitGlobal import stock_global as sg

class BackTest(bt.Strategy):
    def __init__(self, arg_list):
        try:
            self.__ets = arg_list[0]
            self.__macd_stoch_data = arg_list[1] # macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
            self.__slow_d_buy = arg_list[2]
            self.__slow_d_sell = arg_list[3]
            self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)
            self.__buy_price = 0

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=5)

    def notify_order(self, order):  # ①
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:  # ②
             if order.isbuy():
                 self.buyprice = order.executed.price
                 # if self.__buy_price != self.buyprice:
                 #    sg.g_logger.write_log(f"backTest.py 가격 다름 :"
                 #                          f"self.buyprice = {self.buyprice} "
                 #                          f"self.__buy_price = {self.__buy_price}", log_lv=3)
                 self.buycomm = order.executed.comm
             self.bar_executed = len(self)
        elif order.status in [order.Canceled]:
             sg.g_logger.write_log('ORDER CANCELD', log_lv=2)
        elif order.status in [order.Margin]:
             sg.g_logger.write_log('ORDER MARGIN', log_lv=2)
        elif order.status in [order.Rejected]:
             sg.g_logger.write_log('ORDER REJECTED', log_lv=2)

        self.order = None

    def next(self):
        # '2021-06-03 09:05:00'
        now_year = self.datas[0].datetime.date(0).year
        now_month = self.datas[0].datetime.date(0).month
        now_day = self.datas[0].datetime.date(0).day

        now_hour = self.datas[0].datetime.time(0).hour
        now_minute = self.datas[0].datetime.time(0).minute
        now_second = self.datas[0].datetime.time(0).second

        now_data = datetime(now_year, now_month, now_day,
                            now_hour, now_minute, now_second)

        if now_data in self.__macd_stoch_data.index:
            # sg.g_logger.write_log(f"now_data = {now_data}", log_lv=2)
            temp_df = self.__macd_stoch_data.loc[now_data]

            macdhist = temp_df['macdhist']
            hist_inclination_avg = temp_df['hist_inclination_avg']
            slow_d = temp_df['slow_d']

            # 買う；True　売る；False 何もしない；None
            is_buy_sell = self.__ets.is_buy_sell_nomal(macdhist=macdhist,
                                                       slow_d=slow_d,
                                                       slow_d_buy=self.__slow_d_buy,
                                                       slow_d_sell=self.__slow_d_sell)

            if not self.position:
                if is_buy_sell is True:
                    self.__buy_price = temp_df['close']
                    self.order = self.buy()
            else:
                if is_buy_sell is False:
                    self.order = self.sell()

            # if not self.position:
            #     if is_buy_sell is True and self.rsi < 30:
            #         self.order = self.buy()
            # else:
            #     if is_buy_sell is False and self.rsi > 70:
            #         self.order = self.sell()

        else:
            # sg.g_logger.write_log(f"index No = {now_data}", log_lv=3)
            return

    def log(self, txt, dt=None):  # ③
        dt = self.datas[0].datetime.date(0)
        sg.g_logger.write_log(f'[{dt.isoformat()}] {txt}', log_lv=2)