import sys
sys.path.append('../')
from datetime import datetime
import pandas as pd
import backtrader as bter
from InitGlobal import stock_global as sg
from Trading import BackTest as bt

sg.init_global()
# =======================================
path_xlsx = "C:\\stockauto\\xlsx\\"
path_xlsx_more = "C:\\stockauto\\xlsx\\more\\"
benefit_total = 0
bene_money_pro_total = 0
fees = 0.0014
buy_persent = 90
money = 10000000
# test_target_stock_list = sg.g_json_trading_config['buy_list']
test_target_stock_list = list(sg.g_market_db.get_stock_info_all().values())
test_stock_amount = len(test_target_stock_list)
comp_count = 0
benefit_OK = 0
benefit_NO = 0

test_days = 30  # day
test_days_day = (test_days * 4)
analysis_data_amount_day = test_days_day // 2
analysis_data_amount_min = (sg.g_one_day_data_amount * test_days) // 3

slow_d_buy = 30
slow_d_sell = 85
is_graph = False
is_graph_code = 'A005930'

def make_test_data(df, chart):

    # chart : 0 -> m
    # chart : 1 -> day

    if df is None:
        sg.g_logger.write_log(f"{stock_name} : data 없음", log_lv=3)
        return None

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

    if chart == 0:
        kurikai = len(df) - analysis_data_amount_min
        analysis_data_amount = analysis_data_amount_min
        slow_d_rolling = sg.g_one_day_data_amount
        if kurikai < 300:
            sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
            return None
    elif chart == 1:
        kurikai = len(df) - analysis_data_amount_day
        analysis_data_amount = analysis_data_amount_day
        slow_d_rolling = 5
        if kurikai < 10:
            sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
            return None
    else:
        return None

    # ===================================================================
    for i in range(1, kurikai):
        end_i = int(analysis_data_amount + i)
        df_back_data = df[i:end_i]
        # print(f"data amount = {len(df_back_data)}")

        macd_stoch_data = sg.g_ets.get_macd_stochastic(df_back_data, slow_d_rolling)

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

    return test_data_df

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
        xlsx_analysis_ascending_true_m = pd.DataFrame()
        xlsx_analysis_ascending_false_m = pd.DataFrame()
        xlsx_analysis_ascending_true_d = pd.DataFrame()
        xlsx_analysis_ascending_false_d = pd.DataFrame()

        for stock_code in test_target_stock_list:
            stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
            df_min = sg.g_market_db.get_past_stock_price(stock_code, test_days)
            df_day = sg.g_market_db.get_past_stock_price(stock_code, test_days_day, chart_type="D")

            df_data_min = make_test_data(df_min, 0)
            if df_data_min is None:
                continue
            df_data_day = make_test_data(df_day, 1)
            if df_data_day is None:
                continue

            df_data_min.to_excel(f"{path_xlsx_more}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{stock_name}_m.xlsx",
                                  sheet_name=f'분석데이터m')
            df_ascending_data_m = df_data_min.sort_values('close', ascending=True)

            xlsx_analysis_ascending_true_m = xlsx_analysis_ascending_true_m.append(df_ascending_data_m.iloc[0])
            xlsx_analysis_ascending_false_m = xlsx_analysis_ascending_false_m.append(df_ascending_data_m.iloc[-1])

            df_data_day.to_excel(f"{path_xlsx_more}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{stock_name}_d.xlsx",
                                  sheet_name=f'분석데이터d')
            df_ascending_data_d = df_data_day.sort_values('close', ascending=True)

            xlsx_analysis_ascending_true_d = xlsx_analysis_ascending_true_d.append(df_ascending_data_d.iloc[0])
            xlsx_analysis_ascending_false_d = xlsx_analysis_ascending_false_d.append(df_ascending_data_d.iloc[-1])

            back_test_arg_list = []
            bt_obj = bt.BackTest

            df_data_min.index = pd.to_datetime(df_data_min['date'])
            df_data_day.index = pd.to_datetime(df_data_day['date'])
            back_test_arg_list.append(sg.g_ets)
            back_test_arg_list.append(df_data_min)
            back_test_arg_list.append(df_data_day)
            back_test_arg_list.append(slow_d_buy)  # __slow_d_buy
            back_test_arg_list.append(slow_d_sell)  # __slow_d_sell

            data = bter.feeds.PandasData(dataname=df_data_min)

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
        xlsx_analysis_ascending_true_m.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_싼순_m.xlsx",
                                              sheet_name=f'분석데이터m')
        xlsx_analysis_ascending_false_m.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_비싼순_m.xlsx",
                                               sheet_name=f'분석데이터m')

        xlsx_analysis_ascending_true_d.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_싼순_d.xlsx",
                                              sheet_name=f'분석데이터d')
        xlsx_analysis_ascending_false_d.to_excel(f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_비싼순_d.xlsx",
                                               sheet_name=f'분석데이터d')

        # benefit_per = (benefit_total / (money * len(sg.g_json_back_test_csv['csv_list']))) * 100
        # sg.g_logger.write_log(f"benefit_total = {benefit_total}, {benefit_per}%", log_lv=2)
        # sg.g_logger.write_log("back_test main end - python console", log_lv=2)
        # sys.exit(0)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured back_test __name__ python console: {str(ex)}", log_lv=5)