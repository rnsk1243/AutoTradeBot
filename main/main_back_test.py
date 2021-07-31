import sys
sys.path.append('../')
from datetime import datetime
import datetime as dt
import math
import random
from datetime import timedelta
import pandas as pd
import backtrader as bter
from InitGlobal import stock_global as sg
from Trading import BackTest as bt
import time
from Utility import Tools as tool
start_time = time.time()

sg.init_global()
# =======================================
path_xlsx = "..\\..\\stockauto\\xlsx\\"
path_xlsx_more = "..\\..\\stockauto\\xlsx\\more\\"
benefit_total = 0
bene_money_pro_total = 0
fees = 0.0014
buy_persent = 90
money = 10000000
# test_target_stock_list = sg.g_json_trading_config['test_list1']
# test_target_stock_list = sg.g_json_trading_config['bought_list']
# test_target_stock_list = sg.g_json_trading_config['buy_list']
test_target_stock_list = sg.g_json_trading_config['all_list']
# test_target_stock_list = list(sg.g_market_db.get_stock_info_all().values())
test_stock_amount = len(test_target_stock_list)
comp_count = 0
benefit_OK = 0
benefit_NO = 0

analysis_data_amount_min = sg.g_json_trading_config['analysis_data_amount_min']
analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
min_rolling = sg.g_json_trading_config['min_rolling']
day_rolling = sg.g_json_trading_config['day_rolling']
kau_list = sg.g_json_trading_config['buy_list']
slow_d_buy = sg.g_json_trading_config['slow_d_buy']
slow_d_sell = sg.g_json_trading_config['slow_d_sell']
larry_constant_K = sg.g_json_trading_config['larry_constant_K']
rieki_persent_break = sg.g_json_trading_config['rieki_persent_break']
test_days = 22  # day
is_graph = False
is_graph_code = '다우데이타'
cur_stock_name = ""

algori = "if macdhist_m < 0 < macdhist_ave_m and macdhist_day < 0 < macdhist_ave_day\
                    and slow_d_day < slow_d_buy and slow_d_m < slow_d_buy"

sg.g_logger.write_log(f"\tanalysis_data_amount_day\t{analysis_data_amount_day}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tanalysis_data_amount_min\t{analysis_data_amount_min}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\ttail_macdhist_d\t{sg.g_json_trading_config['tail_macdhist_d']}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\ttail_macdhist_m\t{sg.g_json_trading_config['tail_macdhist_m']}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tmin_rolling\t{min_rolling}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tday_rolling\t{day_rolling}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tslow_d_buy\t{slow_d_buy}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tslow_d_sell\t{slow_d_sell}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\tlarry_constant_K\t{larry_constant_K}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\trieki_persent_break\t{rieki_persent_break}\t", log_lv=2, is_con_print=False)
sg.g_logger.write_log(f"\t{algori}\t\t", log_lv=2, is_con_print=False)

def make_test_data(df, chart, larry_constant_K=None, arg4_analysis_data_amount_day=None):

    # chart : 0 -> m
    # chart : 1 -> day

    if df is None:
        sg.g_logger.write_log(f"{stock_name} : data 없음", log_lv=3)
        return None

    df_analysis = pd.DataFrame()
    last_time = df.iloc[-1].date

    if chart == 0:  # min
        test_data = df[last_time - timedelta(days=test_days) < df['date']]
        kurikai = len(test_data)

        analysis_data = df[df['date'] >= last_time - timedelta(days=test_days)]
        # analysis_data = df[df['date'] <= last_time - timedelta(days=test_days)]
        # analysis_data = analysis_data[analysis_data.iloc[-1].date - timedelta(days=analysis_data_amount_min) < analysis_data['date']]
        analysis_data_amount = len(analysis_data)

        analysis_amount = ((analysis_data_amount_min * sg.g_one_day_data_amount) * 9) // 14 # 14일중에 9일이 개장
        if kurikai < 0 or analysis_data_amount < analysis_amount:
            sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
            return None
        else:
            return analysis_data
    elif chart == 1:  # day
        test_data = df[last_time - timedelta(days=test_days) < df['date']]
        kurikai = len(test_data)

        # if is_print is False:
        #     sg.g_logger.write_log(f"\ttest기간\t{kurikai}\t\t", log_lv=2, is_con_print=False)
        #     is_print = True
        analysis_data = df[df['date'] <= last_time - timedelta(days=test_days)]
        analysis_data = analysis_data[analysis_data.iloc[-1].date - timedelta(days=arg4_analysis_data_amount_day) < analysis_data['date']]
        analysis_data_amount = len(analysis_data)

        slow_d_rolling = day_rolling
        analysis_amount = (arg4_analysis_data_amount_day * 9) // 14  # 14일중에 9일이 개장
        if kurikai < 0 or analysis_data_amount < analysis_amount:
            sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
            return None
    else:
        return None
    try:
        # ===================================================================
        for i in range(0, kurikai):
            df_back_data = df[i - (analysis_data_amount + kurikai):i - kurikai]
            # df_back_data = df[i - (analysis_data_amount + kurikai):i - kurikai - analysis_data_amount + 30]
            # sg.g_logger.write_log(f"\t{i}\t{df_back_data.iloc[0].date}\t{df_back_data.iloc[-1].date}\t", is_con_print=False, log_lv=2)
            df_back_data_len = len(df_back_data)

            if df_back_data_len < analysis_amount:
                sg.g_logger.write_log(f"{stock_name} : data / {analysis_amount-df_back_data_len} 적음", log_lv=3)
                return None

            # print(f"data amount = {len(df_back_data)}")
            analysis_series = sg.g_ets.get_macd_stochastic(df_back_data, larry_constant_K)
            if len(analysis_series) == 0:
                return None
            df_analysis = df_analysis.append(analysis_series)

        # sg.g_logger.write_log(f"\t테스트데이터\t{df_analysis}\t", is_con_print=False, log_lv=2)
        # for end
        return df_analysis

    except Exception as ex:
        print(f"{ex}")

if __name__ == '__main__':
    try:
        args = sys.argv
        kuriae = int(args[1])
        arg2_min_slow_d = int(args[2])
        arg3_max_slow_d = int(args[3])
        arg4_min_rieki = int(args[4])
        arg5_max_rieki = int(args[5])
        arg6_analysis_data_amount_day = int(args[6])
        print(f"kuriae : {kuriae}")
        print(f"slow_d : {arg2_min_slow_d}～{arg3_max_slow_d}")
        print(f"rieki : {arg4_min_rieki}～{arg5_max_rieki}")

        # folder 作成
        if arg6_analysis_data_amount_day == -1:
            folder_name = f"{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_random_day"
        else:
            folder_name = f"{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_{arg6_analysis_data_amount_day}"

        print(f"folder_name:{folder_name}")
        tool.createFolder(f"{path_xlsx}{folder_name}")

        xlsx_analysis = pd.DataFrame()

        for i in range(1, kuriae):
            slow_d_buy = random.randint(arg2_min_slow_d, arg3_max_slow_d)
            rieki_persent_break = random.randint(arg4_min_rieki, arg5_max_rieki)
            lck = 0.48  # round(random.uniform(0.45, 0.55), 2)

            if arg6_analysis_data_amount_day == -1:
                arg6_analysis_data_amount_day = round(random.randint(60, 180), -1)

            cumulative_benefit = 0
            cumulative_benefit_ave = 0

            benefit_OK = 0
            benefit_NO = 0

            for stock_code in test_target_stock_list:
                stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
                cur_stock_name = stock_name
                df_min = sg.g_market_db.get_past_stock_price(stock_code, 360)
                df_day = sg.g_market_db.get_past_stock_price(stock_code, 720, chart_type="D")

                df_data_day = make_test_data(df_day, 1, lck, arg6_analysis_data_amount_day)
                if df_data_day is None:
                    continue
                df_data_min = make_test_data(df_min, 0)
                if df_data_min is None:
                    continue

                back_test_arg_list = []
                bt_obj = bt.BackTest
                df_data_min.index = pd.to_datetime(df_data_min['date'])
                df_data_day.index = pd.to_datetime(df_data_day['date'])
                back_test_arg_list.append(sg.g_ets)
                back_test_arg_list.append(df_data_min)
                back_test_arg_list.append(df_data_day)
                back_test_arg_list.append(slow_d_buy)  # __slow_d_buy
                back_test_arg_list.append(slow_d_sell)  # __slow_d_sell
                back_test_arg_list.append(stock_name)
                back_test_arg_list.append(rieki_persent_break)

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
                    print(f"予測失敗 {str(e)}")
                    continue

                end_money = cerebro.broker.getvalue()
                cur_benefit = round(end_money - money)

                cumulative_benefit += cur_benefit
                if cur_benefit > 0:
                    benefit_OK += 1
                elif cur_benefit < 0:
                    benefit_NO += 1

                cur_bene_money_pro = round(((cur_benefit / money) * 100), 2)
                print(f"Result : \t{stock_name}\t{(cur_benefit):,.0f}\t{cur_bene_money_pro}\t KRW")
                # ========================================
                if is_graph and stock_code == is_graph_code:
                    plot_obj = cerebro
                    plot_obj.plot(style='candlestick')
                    break
                # ========================================

            benefit_OK_NO = benefit_OK + benefit_NO
            if benefit_OK_NO != 0:
                bene_pro = round(((benefit_OK / benefit_OK_NO) * 100), 2)
                syueki = round(((cumulative_benefit / (benefit_OK_NO*money)) * 100), 2)
                cumulative_benefit_ave = round((cumulative_benefit / benefit_OK_NO))
            else:
                bene_pro = 0
                syueki = 0

            print(f"--------------------------------------\r\n"
                  f"slow_d_buy----------【{slow_d_buy}】\r\n"
                  f"rieki_persent_break-【{rieki_persent_break}】\r\n"
                  f"larry_constant_K----【{lck}】\r\n"
                  f"arg6_analysis_data_amount_day----【{arg6_analysis_data_amount_day}】\r\n"
                  f"구매건수-------------【{benefit_OK_NO}】\r\n"
                  f"수익누계-------------【{(cumulative_benefit):,.0f}】\r\n"
                  f"수익누계평균----------【{(cumulative_benefit_ave):,.0f}】\r\n"
                  f"이득확률-------------【{bene_pro}%】\r\n"
                  f"수익평균-------------【{syueki}】\r\n"
                  f"완료----------------【{round((i/kuriae)*100)}%】\r\n"
                  f"--------------------------------------\r\n")

            xlsx_analysis = xlsx_analysis.append({"slow_d_buy": slow_d_buy,
                                                  "rieki_persent_break": rieki_persent_break,
                                                  "larry_constant_K": lck,
                                                  "arg6_analysis_data_amount_day": arg6_analysis_data_amount_day,
                                                  "day_rolling": day_rolling,
                                                  "테스트기간": test_days,
                                                  "구매건수": benefit_OK_NO,
                                                  "수익누계": cumulative_benefit,
                                                  "수익누계평균": cumulative_benefit_ave,
                                                  "이득확률": bene_pro,
                                                  "수익평균": syueki}, ignore_index=True)

            xlsx_analysis.to_excel(f"{path_xlsx}{folder_name}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과.xlsx",
                                   sheet_name=f'결과')
        print("작업시간 : ", time.time() - start_time)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured 【back_test.bat】: {str(ex)} \r\n 【{cur_stock_name}】", log_lv=5)

else:
    try:
        xlsx_analysis_ascending_true_m = pd.DataFrame()
        xlsx_analysis_ascending_false_m = pd.DataFrame()
        xlsx_analysis_ascending_true_d = pd.DataFrame()
        xlsx_analysis_ascending_false_d = pd.DataFrame()

        for stock_code in test_target_stock_list:
            stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
            df_min = sg.g_market_db.get_past_stock_price(stock_code, 360)
            df_day = sg.g_market_db.get_past_stock_price(stock_code, 2000, chart_type="D")

            df_data_day = make_test_data(df_day, 1)
            if df_data_day is None:
                continue
            df_data_min = make_test_data(df_min, 0)
            if df_data_min is None:
                continue

            # df_data_min.to_excel(f"{path_xlsx_more}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{stock_name}_m.xlsx",
            #                       sheet_name=f'분석데이터m')
            # df_ascending_data_m = df_data_min.sort_values('close', ascending=True)
            #
            # xlsx_analysis_ascending_true_m = xlsx_analysis_ascending_true_m.append(df_ascending_data_m.iloc[0])
            # xlsx_analysis_ascending_false_m = xlsx_analysis_ascending_false_m.append(df_ascending_data_m.iloc[-1])
            #
            # df_data_day.to_excel(f"{path_xlsx_more}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{stock_name}_d.xlsx",
            #                       sheet_name=f'분석데이터d')
            # df_ascending_data_d = df_data_day.sort_values('close', ascending=True)
            #
            # xlsx_analysis_ascending_true_d = xlsx_analysis_ascending_true_d.append(df_ascending_data_d.iloc[0])
            # xlsx_analysis_ascending_false_d = xlsx_analysis_ascending_false_d.append(df_ascending_data_d.iloc[-1])

            back_test_arg_list = []
            bt_obj = bt.BackTest
            df_data_min.index = pd.to_datetime(df_data_min['date'])
            df_data_day.index = pd.to_datetime(df_data_day['date'])
            back_test_arg_list.append(sg.g_ets)
            back_test_arg_list.append(df_data_min)
            back_test_arg_list.append(df_data_day)
            back_test_arg_list.append(slow_d_buy)  # __slow_d_buy
            back_test_arg_list.append(slow_d_sell)  # __slow_d_sell
            back_test_arg_list.append(stock_name)
            back_test_arg_list.append(rieki_persent_break)

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
            comp_count += 1
            sg.g_logger.write_log(f'Result : \t{stock_code}\t{stock_name}\t{(cur_benefit):,.0f}\t KRW', log_lv=2,
                                  is_con_print=False)
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
        # xlsx_analysis_ascending_true_m.to_excel(
        #     f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_싼순_m.xlsx",
        #     sheet_name=f'분석데이터m')
        # xlsx_analysis_ascending_false_m.to_excel(
        #     f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_비싼순_m.xlsx",
        #     sheet_name=f'분석데이터m')
        #
        # xlsx_analysis_ascending_true_d.to_excel(
        #     f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_싼순_d.xlsx",
        #     sheet_name=f'분석데이터d')
        # xlsx_analysis_ascending_false_d.to_excel(
        #     f"{path_xlsx}{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_비싼순_d.xlsx",
        #     sheet_name=f'분석데이터d')
        # benefit_per = (benefit_total / (money * len(sg.g_json_back_test_csv['csv_list']))) * 100
        # sg.g_logger.write_log(f"benefit_total = {benefit_total}, {benefit_per}%", log_lv=2)
        # sg.g_logger.write_log("back_test main end - python console", log_lv=2)
        # sys.exit(0)
        print("작업시간 : ", time.time() - start_time)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured back_test __name__ python console: {str(ex)}", log_lv=5)