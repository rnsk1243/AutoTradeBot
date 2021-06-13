import sys
sys.path.append('../')
from datetime import datetime
import pandas as pd
import backtrader as bter
from InitGlobal import stock_global as sg
from Trading import BackTest as bt



if __name__ == '__main__':
    try:
        sg.init_global()
        # =======================================
        sg.g_logger.write_log("back_test main end")
        sys.exit(0)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured back_test __name__ : {str(ex)}", log_lv=5)

else:
    try:
        sg.init_global()
        # =======================================
        path_xlsx = "C:\\stockauto\\xlsx\\"
        path_xlsx_more = "C:\\stockauto\\xlsx\\more\\"
        xlsx_analysis_ascending_true = pd.DataFrame()
        xlsx_analysis_ascending_false = pd.DataFrame()
        benefit_total = 0
        bene_money_pro_total = 0
        fees = 0.0014
        buy_persent = 90
        money = 10000000
        test_target_stock_list = sg.g_json_trading_config['test_list']
        test_stock_amount = len(test_target_stock_list)
        comp_count = 0
        benefit_OK = 0
        benefit_NO = 0

        test_days = 18  # day
        analysis_data_amount = sg.g_one_day_data_amount * 5
        macd_long_day = 5  # day
        msd_rolling_day = 30  # // day
        slow_d_buy = 10
        slow_d_sell = 85
        is_graph = False
        is_graph_code = 'A005930'

        for stock_code in test_target_stock_list:
            stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
            df = sg.g_market_db.get_past_stock_price(stock_code, test_days)
            if df is None:
                sg.g_logger.write_log(f"{stock_name} : data 없음", log_lv=3)
                continue
            df_code = []
            df_date = []
            df_week = []
            df_open = []
            df_high = []
            df_low = []
            df_close = []
            df_diff = []
            df_volume = []
            df_macdhist = []
            df_slow_d = []
            # df_hist_inclination_avg = []
            df_macdhist_ave = []

            kurikai = len(df) - analysis_data_amount
            if kurikai < 300:
                sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
                continue

# ===================================================================
            for i in range(1, kurikai):
                end_i = int(analysis_data_amount+i)
                df_back_data = df[i:end_i]
                # print(f"data amount = {len(df_back_data)}")

                macd_stoch_data = sg.g_ets.get_macd_stochastic(df_back_data, (sg.g_one_day_data_amount * macd_long_day))

                macd_stoch_data_df = macd_stoch_data[0]
                macdhist_ave = macd_stoch_data[1]

                # macd_stoch_data_df = sg.g_ets.macd_sec_dpc(macd_stoch_data_df, 1)
                macd_stoch_data_df = macd_stoch_data_df.iloc[-1]
                df_code.append(macd_stoch_data_df['code'])
                df_date.append(macd_stoch_data_df['date'])
                df_week.append(macd_stoch_data_df['week'])
                df_open.append(macd_stoch_data_df['open'])
                df_high.append(macd_stoch_data_df['high'])
                df_low.append(macd_stoch_data_df['low'])
                df_close.append(macd_stoch_data_df['close'])
                df_diff.append(macd_stoch_data_df['diff'])
                df_volume.append(macd_stoch_data_df['volume'])
                df_macdhist.append(macd_stoch_data_df['macdhist'])
                df_slow_d.append(macd_stoch_data_df['slow_d'])
                # df_hist_inclination_avg.append(macd_stoch_data_df['hist_inclination_avg'])
                df_macdhist_ave.append(macdhist_ave)
# ===================================================================
            test_data_df = pd.DataFrame(data={'code': df_code, 'date': df_date, 'week': df_week, 'open': df_open,
                                              'high': df_high, 'low': df_low, 'close': df_close, 'diff': df_diff,
                                              'volume': df_volume, 'macdhist': df_macdhist, 'slow_d': df_slow_d,
                                              'macdhist_ave': df_macdhist_ave},
                                        columns=['code', 'date', 'week', 'open',
                                                 'high', 'low', 'close', 'diff',
                                                 'volume', 'macdhist', 'slow_d', 'macdhist_ave'])

            test_data_df.to_excel(f"{path_xlsx_more}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{stock_name}.xlsx",
                                  sheet_name=f'분석데이터')
            df_ascending_data = test_data_df.sort_values('close', ascending=True)

            xlsx_analysis_ascending_true = xlsx_analysis_ascending_true.append(df_ascending_data.iloc[0])
            xlsx_analysis_ascending_false = xlsx_analysis_ascending_false.append(df_ascending_data.iloc[-1])

            back_test_arg_list = []
            bt_obj = bt.BackTest

            test_data_df.index = pd.to_datetime(test_data_df['date'])
            back_test_arg_list.append(sg.g_ets)
            back_test_arg_list.append(test_data_df)
            back_test_arg_list.append(slow_d_buy)  # __slow_d_buy
            back_test_arg_list.append(slow_d_sell)  # __slow_d_sell

            data = bter.feeds.PandasData(dataname=test_data_df)

            cerebro = bter.Cerebro()
            cerebro.addstrategy(bt_obj, back_test_arg_list)

            cerebro.adddata(data)
            cerebro.broker.setcash(money)
            cerebro.broker.setcommission(commission=fees)
            cerebro.addsizer(bter.sizers.PercentSizer, percents=buy_persent)

            start_money = cerebro.broker.getvalue()

            try:
                cerebro.run()
            except Exception as e:
                sg.g_logger.write_log(f"予測失敗 {str(e)}", log_lv=3)

            end_money = cerebro.broker.getvalue()
            cur_benefit = round(end_money - money)
            if cur_benefit > 0:
                benefit_OK += 1
            elif cur_benefit < 0:
                benefit_NO += 1

            benefit_OK_NO = benefit_OK + benefit_NO
            bene_pro = 0
            if benefit_OK_NO != 0:
                bene_pro = round(((benefit_OK / benefit_OK_NO) * 100), 2)
            benefit_total += cur_benefit

            cur_bene_money_pro = round(((cur_benefit / money) * 100), 2)
            bene_money_pro_total += cur_bene_money_pro
            bene_pro_ave = 0
            if benefit_OK_NO != 0:
                bene_pro_ave = round((bene_money_pro_total / benefit_OK_NO), 2)

            # self.__logger.write_log(f'Final Portfolio Value : {new_money:,.0f} KRW', log_lv=2)
            money = end_money
            comp_count += 1
            sg.g_logger.write_log(f'Result : \t{stock_code}\t{stock_name}\t{(cur_benefit):,.0f}\t KRW', log_lv=2, is_con_print=False)
            comp_pro = round((comp_count / test_stock_amount) * 100, 2)
            print(f"-------------------------------------\r\n"
                  f"이름---------【{stock_name}%】\r\n"
                  f"수익---------【{(cur_benefit):,.0f}】\r\n"
                  f"이득확률------【{bene_pro}%】\r\n"
                  f"수익평균------【{bene_pro_ave}】\r\n"
                  f"완료---------【{comp_pro}%】")
            # ========================================
            if is_graph and stock_code == is_graph_code:
                plot_obj = cerebro
                plot_obj.plot(style='candlestick')
                break
            # ========================================
        xlsx_analysis_ascending_true.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_오름차순.xlsx",
                                              sheet_name=f'분석데이터')
        xlsx_analysis_ascending_false.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_내림차순.xlsx",
                                               sheet_name=f'분석데이터')

        # benefit_per = (benefit_total / (money * len(sg.g_json_back_test_csv['csv_list']))) * 100
        # sg.g_logger.write_log(f"benefit_total = {benefit_total}, {benefit_per}%", log_lv=2)
        # sg.g_logger.write_log("back_test main end - python console", log_lv=2)
        # sys.exit(0)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured back_test __name__ python console: {str(ex)}", log_lv=5)