import sys
sys.path.append('../')
from datetime import datetime
from datetime import timedelta
import pandas as pd
import backtrader as bter
from InitGlobal import stock_global as sg
from Trading import BackTest as bt
import time
from Utility import Tools as tool
import itertools

start_time = time.time()
sg.init_global()
# =======================================
path_xlsx = "..\\..\\stockauto\\xlsx\\"
path_xlsx_more = "..\\..\\stockauto\\xlsx\\more\\"
path_trading_config = "..\\..\\stockauto\\MyJson\\trading_config.json"
benefit_total = 0
bene_money_pro_total = 0
fees = 0.0014
buy_persent = 90
money = 10000000
test_target_name = 'buy_list'
test_target_stock_list = sg.g_json_trading_config[test_target_name]
test_stock_amount = len(test_target_stock_list)
comp_count = 0
benefit_OK = 0
benefit_NO = 0

analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
recent_rieki_count_day_long_end = sg.g_json_trading_config['recent_rieki_count_day_long_end']
test_days = sg.g_json_trading_config['back_test_days']  # day

is_graph = False
is_graph_code = '네이처셀'
cur_stock_name = ""

def silce_data_min(df):

    if df is None:
        sg.g_logger.write_log(f"{stock_name} : data 없음", log_lv=3)
        return None

    last_time = df.iloc[-1].date
    analysis_data = df[df['date'] >= last_time - timedelta(days=test_days)]
    return analysis_data

def silce_data_day(df):

    if df is None:
        sg.g_logger.write_log(f"{stock_name} : data 없음", log_lv=3)
        return None
    last_time = df.iloc[-1].date

    test_data = df[last_time - timedelta(days=test_days) < df['date']]
    kurikai = len(test_data)

    analysis_data = df[df['date'] <= last_time - timedelta(days=test_days)]
    if analysis_data is None or len(analysis_data) == 0:
        return None
    analysis_data = analysis_data[
        analysis_data.iloc[-1].date - timedelta(days=analysis_data_amount_day) < analysis_data['date']]
    analysis_data_amount = len(analysis_data)

    return kurikai, analysis_data_amount

def make_test_data(df, recent_rieki_count_day, recent_rieki_count_day_long, min_rieki_amount=1):

    try:
        df_analysis = pd.DataFrame()
        kurikai, analysis_data_amount = silce_data_day(df)
        # ===================================================================
        for i in range(0, kurikai):
            df_back_data = df[i - (analysis_data_amount + kurikai):i - kurikai]
            analysis_series = sg.g_ets.get_macd_stochastic_back_test(df=df_back_data,
                                                                     recent_rieki_count_day=recent_rieki_count_day,
                                                                     recent_rieki_count_day_long=recent_rieki_count_day_long)
            if len(analysis_series) == 0:
                return None
            df_analysis = df_analysis.append(analysis_series)

        for df_yester_day in df_analysis.itertuples():

            recent_rieki_count = df_yester_day.recent_rieki_count
            recent_not_rieki_count = df_yester_day.recent_not_rieki_count
            recent_rieki_count_long = df_yester_day.recent_rieki_count_long
            recent_not_rieki_count_long = df_yester_day.recent_not_rieki_count_long

            step2 = recent_not_rieki_count_long < recent_rieki_count_long
            step3 = (recent_not_rieki_count == 0 and min_rieki_amount <= recent_rieki_count)

            if step2 and step3:
                return df_analysis

        return None

    except Exception as ex:
        print(f"{ex}")

if __name__ == '__main__':
    try:
        min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']
        cur_larry_constant_K_buy = sg.g_json_trading_config['larry_constant_K_buy']

        cur_larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']
        cur_recent_rieki_count_day = sg.g_json_trading_config['recent_rieki_count_day']
        cur_recent_rieki_count_day_long = sg.g_json_trading_config['recent_rieki_count_day_long']
        delta_k = 0.1
        delta_day = 1
        delta_day_long = cur_recent_rieki_count_day_long // 10

        kumi_list_0 = [round((cur_larry_constant_K_anl - delta_k * 1), 1),
                       round(cur_larry_constant_K_anl, 1),
                       round((cur_larry_constant_K_anl + delta_k * 1), 1)]
        kumi_list_1 = [cur_recent_rieki_count_day - delta_day * 4,
                       cur_recent_rieki_count_day - delta_day * 2,
                       cur_recent_rieki_count_day - delta_day * 1,
                       cur_recent_rieki_count_day,
                       cur_recent_rieki_count_day + delta_day * 1,
                       cur_recent_rieki_count_day + delta_day * 2,
                       cur_recent_rieki_count_day + delta_day * 4]
        kumi_list_2 = [cur_recent_rieki_count_day_long - delta_day_long * 4,
                       cur_recent_rieki_count_day_long - delta_day_long * 2,
                       cur_recent_rieki_count_day_long - delta_day_long * 1,
                       cur_recent_rieki_count_day_long,
                       cur_recent_rieki_count_day_long + delta_day_long * 1,
                       cur_recent_rieki_count_day_long + delta_day_long * 2,
                       cur_recent_rieki_count_day_long + delta_day_long * 4]

        p = itertools.product(kumi_list_0, kumi_list_1, kumi_list_2)
        sg.g_logger.write_log(f"back test 시작 \r\n"
                              f"kumi_list_k: {kumi_list_0} \r\n"
                              f"kumi_list_day: {kumi_list_1}\r\n"
                              f"kumi_list_day_long: \r\n{kumi_list_2}", log_lv=2, is_slacker=True)
        xlsx_analysis = pd.DataFrame()

        # folder 作成
        folder_name = f"{datetime.today().strftime('%Y-%m')}_테스트결과"
        folder_name_detail = f"{datetime.today().strftime('%Y-%m-%d')}_테스트결과"
        tool.createFolder(f"{path_xlsx}{folder_name}")
        tool.createFolder(f"{path_xlsx}{folder_name}\\{folder_name_detail}")

        for kumi_tuple in p:

            xlsx_analysis_detail = pd.DataFrame()
            larry_constant_K_anl = float(kumi_tuple[0])
            larry_constant_K_buy = round((float(larry_constant_K_anl - cur_larry_constant_K_buy)), 1)
            recent_rieki_count_day = kumi_tuple[1]
            recent_rieki_count_day_long = kumi_tuple[2]

            cumulative_benefit = 0
            cumulative_benefit_ave = 0

            benefit_OK = 0
            benefit_NO = 0

            for stock_code in test_target_stock_list:
                stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
                cur_stock_name = stock_name
                ############# day #############
                df_day = sg.g_market_db.get_past_stock_price(stock_code, analysis_data_amount_day,
                                                             day_ago_end=recent_rieki_count_day_long_end,
                                                             chart_type="D")
                df_data_day = make_test_data(df_day, recent_rieki_count_day=recent_rieki_count_day,
                                             recent_rieki_count_day_long=recent_rieki_count_day_long)
                if df_data_day is None:
                    sg.g_logger.write_log(f"테스트기간중 매매가 발생 하지 않음 : \t{stock_name}\t", log_lv=2, is_slacker=False
                                          , is_con_print=False)
                    continue
                ############# day #############
                ############# min #############
                df_min = sg.g_market_db.get_past_stock_price(stock_code, 20,
                                                             day_ago_end=recent_rieki_count_day_long_end)
                df_data_min = silce_data_min(df_min)
                if df_data_min is None:
                    continue
                ############# min #############

                back_test_arg_list = []
                bt_obj = bt.BackTest
                df_data_min.index = pd.to_datetime(df_data_min['date'])
                df_data_day.index = pd.to_datetime(df_data_day['date'])
                back_test_arg_list.append(sg.g_ets)
                back_test_arg_list.append(df_data_min)
                back_test_arg_list.append(df_data_day)
                back_test_arg_list.append(larry_constant_K_anl)
                back_test_arg_list.append(df_day.iloc[-1].open)
                back_test_arg_list.append(df_data_day.iloc[-1])
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
                sg.g_logger.write_log(f"Result : \t{stock_name}\t{(cur_benefit):,.0f}\t{cur_bene_money_pro}\t KRW",
                                      log_lv=2, is_slacker=False)
                xlsx_analysis_detail = xlsx_analysis_detail.append({"stock_name": stock_name,
                                                                    "cur_benefit": cur_benefit,
                                                                    "cur_bene_money_pro": cur_bene_money_pro},
                                                                   ignore_index=True)

            benefit_OK_NO = benefit_OK + benefit_NO
            if benefit_OK_NO != 0:
                bene_pro = round(((benefit_OK / benefit_OK_NO) * 100), 2)
                syueki = round(((cumulative_benefit / (benefit_OK_NO * money)) * 100), 2)
                cumulative_benefit_ave = round((cumulative_benefit / benefit_OK_NO))
            else:
                bene_pro = 0
                syueki = 0

            result_info = f"【{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}】\r\n" \
                          f"테스트대상-------------【{test_target_name}】\r\n" \
                          f"larry_constant_K_anl-【{larry_constant_K_anl}】\r\n" \
                          f"larry_constant_K_buy-【{larry_constant_K_buy}】\r\n" \
                          f"recent_rieki_count_day-【{recent_rieki_count_day}】\r\n" \
                          f"recent_rieki_count_day_long-【{recent_rieki_count_day_long}】\r\n" \
                          f"min_rieki_amount----【{min_rieki_amount}】\r\n" \
                          f"구매건수-------------【{benefit_OK_NO}】\r\n" \
                          f"수익누계-------------【{(cumulative_benefit):,.0f}】\r\n" \
                          f"수익누계평균----------【{(cumulative_benefit_ave):,.0f}】\r\n" \
                          f"이득확률-------------【{bene_pro}%】\r\n" \
                          f"수익평균-------------【{syueki}%】\r\n" \
                          f"테스트기간-----------【{test_days}일】\r\n" \
                          f"매일 테스트 완료------\r\n"

            xlsx_analysis = xlsx_analysis.append({"larry_constant_K_anl": larry_constant_K_anl,
                                                  "larry_constant_K_buy": larry_constant_K_buy,
                                                  "테스트기간": test_days,
                                                  "구매건수": benefit_OK_NO,
                                                  "cumulative_benefit": cumulative_benefit,
                                                  "수익누계평균": cumulative_benefit_ave,
                                                  "bene_pro": bene_pro,
                                                  "수익평균": syueki,
                                                  "recent_rieki_count_day_long": recent_rieki_count_day_long,
                                                  "recent_rieki_count_day": recent_rieki_count_day,
                                                  "min_rieki_amount": min_rieki_amount}, ignore_index=True)

            xlsx_analysis_detail.to_excel(
                f"{path_xlsx}{folder_name}\\{folder_name_detail}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_상세.xlsx",
                sheet_name=f'결과')

            sg.g_logger.write_log(result_info, log_lv=2, is_slacker=False)
        # ============
        # sort 수익누계 내림차순
        xlsx_analysis = xlsx_analysis.sort_values('cumulative_benefit', ascending=False)

        xlsx_analysis.to_excel(
            f"{path_xlsx}{folder_name}\\{folder_name_detail}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_수익누계_내림차순.xlsx",
            sheet_name=f'결과')
        time.sleep(2)

        xlsx_analysis_top5 = xlsx_analysis.iloc[:5]
        xlsx_analysis_top5 = xlsx_analysis_top5.sort_values('bene_pro', ascending=False)

        xlsx_analysis_top5.to_excel(
            f"{path_xlsx}{folder_name}\\{folder_name_detail}\\{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_테스트결과_top5.xlsx",
            sheet_name=f'결과')

        cur_max_benefit_df = xlsx_analysis_top5.iloc[0]

        if cur_max_benefit_df is not None and len(cur_max_benefit_df) > 0:
            sg.g_logger.write_log("새 분석 결과를 반영합니다.", log_lv=2, is_slacker=True)
            new_larry_constant_K_anl = float(cur_max_benefit_df.larry_constant_K_anl)
            new_recent_rieki_count_day = int(cur_max_benefit_df.recent_rieki_count_day)
            new_recent_rieki_count_day_long = int(cur_max_benefit_df.recent_rieki_count_day_long)
            new_cumulative_benefit = int(cur_max_benefit_df.cumulative_benefit)

            tool.write_json_single(path_trading_config, "larry_constant_K_anl", new_larry_constant_K_anl)
            tool.write_json_single(path_trading_config, "recent_rieki_count_day", new_recent_rieki_count_day)
            tool.write_json_single(path_trading_config, "recent_rieki_count_day_long", new_recent_rieki_count_day_long)

            hennka_k = round((new_larry_constant_K_anl - cur_larry_constant_K_anl), 2)
            hennka_count_day = new_recent_rieki_count_day - cur_recent_rieki_count_day
            hennka_count_day_long = new_recent_rieki_count_day_long - cur_recent_rieki_count_day_long

            sg.g_logger.write_log(f"새 분석 결과 larry_k:\r\n{new_larry_constant_K_anl} / 증감:({hennka_k})", log_lv=2,
                                  is_slacker=True)
            sg.g_logger.write_log(f"새 분석 결과 day:\r\n{new_recent_rieki_count_day} / 증감:({hennka_count_day})", log_lv=2, is_slacker=True)
            sg.g_logger.write_log(f"새 분석 결과 day_long:\r\n{new_recent_rieki_count_day_long} / 증감:({hennka_count_day_long})", log_lv=2, is_slacker=True)
            sg.g_logger.write_log(f"새 누적 수익:\r\n{(new_cumulative_benefit):,.0f}원", log_lv=2, is_slacker=True)
            sg.g_logger.write_log(f"상세 결과 내용:\r\n{cur_max_benefit_df}\r\n", log_lv=2, is_slacker=True)

        else:
            sg.g_logger.write_log(f"분석 결과가 없습니다..cur_max_benefit_df={cur_max_benefit_df}", log_lv=3, is_slacker=True)

        sg.g_logger.write_log(f"작업시간 : {time.time() - start_time}", log_lv=2, is_slacker=False)
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
        cur_larry_constant_K_anl = sg.g_json_trading_config['larry_constant_K_anl']

        for stock_code in test_target_stock_list:
            stock_name = sg.g_market_db.get_stock_name(stock_code=stock_code)
            df_day = sg.g_market_db.get_past_stock_price(stock_code, analysis_data_amount_day,
                                                         recent_rieki_count_day_long_end, chart_type="D")

            df_data_day = make_test_data(df_day, 12, 800)
            if df_data_day is None:
                continue

            df_min = sg.g_market_db.get_past_stock_price(stock_code, 50, day_ago_end=recent_rieki_count_day_long_end)
            df_data_min = silce_data_min(df_min)
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
            back_test_arg_list.append(cur_larry_constant_K_anl)
            back_test_arg_list.append(df_day.iloc[-1].open)
            back_test_arg_list.append(df_data_day.iloc[-1])
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