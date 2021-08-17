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
test_target_name = 'buy_list'
# test_target_stock_list = sg.g_json_trading_config['test_list1']
# test_target_stock_list = sg.g_json_trading_config['bought_list']
test_target_stock_list = sg.g_json_trading_config[test_target_name]
# test_target_stock_list = sg.g_json_trading_config['all_list']
# test_target_stock_list = list(sg.g_market_db.get_stock_info_all().values())
test_stock_amount = len(test_target_stock_list)
comp_count = 0
benefit_OK = 0
benefit_NO = 0

analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
recent_rieki_count_day_long_end = sg.g_json_trading_config['recent_rieki_count_day_long_end']
kau_list = sg.g_json_trading_config['buy_list']
larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']
rieki_persent_break = sg.g_json_trading_config['rieki_persent_break']
test_days = 5  # day
is_graph = False
is_graph_code = '네이처셀'
cur_stock_name = ""

algori = "if macdhist_m < 0 < macdhist_ave_m and macdhist_day < 0 < macdhist_ave_day\
                    and slow_d_day < slow_d_buy and slow_d_m < slow_d_buy"

# sg.g_logger.write_log(f"\tanalysis_data_amount_day\t{analysis_data_amount_day}\t", log_lv=2, is_con_print=False)
# sg.g_logger.write_log(f"\tlarry_constant_K_anl\t{larry_constant_K_anl}\t", log_lv=2, is_con_print=False)
# sg.g_logger.write_log(f"\trieki_persent_break\t{rieki_persent_break}\t", log_lv=2, is_con_print=False)
# sg.g_logger.write_log(f"\t{algori}\t\t", log_lv=2, is_con_print=False)

def make_test_data(df, chart):

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

        analysis_amount = ((1 * sg.g_one_day_data_amount) * 9) // 14 # 14일중에 9일이 개장
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
        if analysis_data is None or len(analysis_data) == 0:
            return None
        arg4_analysis_data_amount_day = analysis_data_amount_day
        analysis_data = analysis_data[analysis_data.iloc[-1].date - timedelta(days=arg4_analysis_data_amount_day) < analysis_data['date']]
        analysis_data_amount = len(analysis_data)

        # analysis_amount = (arg4_analysis_data_amount_day * 9) // 14  # 14일중에 9일이 개장
        # if kurikai < 0 or analysis_data_amount < analysis_amount:
        #     sg.g_logger.write_log(f"{stock_name} : data / {kurikai} 적음", log_lv=3)
        #     return None
    else:
        return None
    try:
        # ===================================================================
        for i in range(0, kurikai):
            df_back_data = df[i - (analysis_data_amount + kurikai):i - kurikai]
            # df_back_data = df[i - (analysis_data_amount + kurikai):i - kurikai - analysis_data_amount + 30]
            # sg.g_logger.write_log(f"\t{i}\t{df_back_data.iloc[0].date}\t{df_back_data.iloc[-1].date}\t", is_con_print=False, log_lv=2)
            # df_back_data_len = len(df_back_data)

            # if df_back_data_len < analysis_amount:
            #     sg.g_logger.write_log(f"{stock_name} : data / {analysis_amount-df_back_data_len} 적음", log_lv=3)
            #     return None

            # print(f"data amount = {len(df_back_data)}")
            analysis_series = sg.g_ets.get_macd_stochastic(df_back_data)
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
        kuriae = 2
        # arg4_min_rieki = int(args[2])
        # arg5_max_rieki = int(args[3])
        arg6_analysis_data_amount_day = analysis_data_amount_day
        print(f"kuriae : {kuriae}")
        # print(f"rieki : {arg4_min_rieki}～{arg5_max_rieki}")
        is_analysis_random = False
        recent_rieki_count_day = sg.g_json_trading_config['recent_rieki_count_day']
        recent_rieki_count_day_long = sg.g_json_trading_config['recent_rieki_count_day_long']
        min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']

        # folder 作成
        folder_name = f"{datetime.today().strftime('%Y-%m')}_테스트결과"
        folder_name_detail = f"{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과"

        print(f"folder_name:{folder_name}")
        tool.createFolder(f"{path_xlsx}{folder_name}")
        tool.createFolder(f"{path_xlsx}{folder_name}\\{folder_name_detail}")

        xlsx_analysis = pd.DataFrame()
        xlsx_analysis_detail = pd.DataFrame()

        sg.g_logger.write_log(f"\r\n back test 시작 \r\n", log_lv=2, is_slacker=True)

        for i in range(1, kuriae):
            # rieki_persent_break = random.randint(arg4_min_rieki, arg5_max_rieki)
            larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']
            larry_constant_K_buy = sg.g_json_trading_config['larry_constant_K_buy']

            if is_analysis_random is True:
                arg6_analysis_data_amount_day = round(random.randint(180, 400), -1)

            cumulative_benefit = 0
            cumulative_benefit_ave = 0

            benefit_OK = 0
            benefit_NO = 0

            for stock_code in test_target_stock_list:
                stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
                cur_stock_name = stock_name
                df_min = sg.g_market_db.get_past_stock_price(stock_code, 50, day_ago_end=recent_rieki_count_day_long_end)
                df_day = sg.g_market_db.get_past_stock_price(stock_code, analysis_data_amount_day, recent_rieki_count_day_long_end, chart_type="D")

                df_data_day = make_test_data(df_day, 1)
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
                # back_test_arg_list.append(stock_name)
                # back_test_arg_list.append(rieki_persent_break)

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
                xlsx_analysis_detail = xlsx_analysis_detail.append({"stock_name":stock_name,
                                                                    "cur_benefit":cur_benefit,
                                                                    "cur_bene_money_pro":cur_bene_money_pro},
                                                                   ignore_index=True)
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

            result_info = f"【{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}】\r\n" \
                          f"테스트대상-------------【{test_target_name}】\r\n" \
                          f"larry_constant_K_anl-【{larry_constant_K_anl}】\r\n"\
                          f"larry_constant_K_buy-【{larry_constant_K_buy}】\r\n" \
                          f"recent_rieki_count_day-【{recent_rieki_count_day}】\r\n"\
                          f"recent_rieki_count_day_long-【{recent_rieki_count_day_long}】\r\n" \
                          f"min_rieki_amount----【{min_rieki_amount}】\r\n" \
                          f"구매건수-------------【{benefit_OK_NO}】\r\n"\
                          f"수익누계-------------【{(cumulative_benefit):,.0f}】\r\n"\
                          f"수익누계평균----------【{(cumulative_benefit_ave):,.0f}】\r\n"\
                          f"이득확률-------------【{bene_pro}%】\r\n"\
                          f"수익평균-------------【{syueki}%】\r\n"\
                          f"테스트기간-----------【{test_days}일】\r\n"\
                          f"매일 테스트 완료------\r\n"

            print(result_info)

            xlsx_analysis = xlsx_analysis.append({"rieki_persent_break": rieki_persent_break,
                                                  "larry_constant_K_anl": larry_constant_K_anl,
                                                  "larry_constant_K_buy": larry_constant_K_buy,
                                                  "arg6_analysis_data_amount_day": arg6_analysis_data_amount_day,
                                                  "테스트기간": test_days,
                                                  "구매건수": benefit_OK_NO,
                                                  "수익누계": cumulative_benefit,
                                                  "수익누계평균": cumulative_benefit_ave,
                                                  "이득확률": bene_pro,
                                                  "수익평균": syueki,
                                                  "recent_rieki_count_day_long": recent_rieki_count_day_long,
                                                  "recent_rieki_count_day": recent_rieki_count_day,
                                                  "min_rieki_amount": min_rieki_amount}, ignore_index=True)

            xlsx_analysis.to_excel(f"{path_xlsx}{folder_name}\\{folder_name_detail}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과.xlsx",
                                   sheet_name=f'결과')
            xlsx_analysis_detail.to_excel(f"{path_xlsx}{folder_name}\\{folder_name_detail}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_상세.xlsx",
                                   sheet_name=f'결과')

            sg.g_logger.write_log(result_info, log_lv=2, is_slacker=True)

        print("작업시간 : ", time.time() - start_time)
        # =======================================
        sys.exit(0)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured 【main_back_test】: {str(ex)} \r\n 【{cur_stock_name}】", log_lv=5, is_slacker=True)

else:
    try:
        xlsx_analysis_ascending_true_m = pd.DataFrame()
        xlsx_analysis_ascending_false_m = pd.DataFrame()
        xlsx_analysis_ascending_true_d = pd.DataFrame()
        xlsx_analysis_ascending_false_d = pd.DataFrame()

        for stock_code in test_target_stock_list:
            stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
            df_min = sg.g_market_db.get_past_stock_price(stock_code, 50, day_ago_end=recent_rieki_count_day_long_end)
            df_day = sg.g_market_db.get_past_stock_price(stock_code, analysis_data_amount_day,
                                                         recent_rieki_count_day_long_end, chart_type="D")

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