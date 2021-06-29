import sys
sys.path.append('../')
from pygit2 import Repository
from datetime import datetime
import time
from InitGlobal import stock_global as sg
from Utility import Tools as tool

# def set_format(today_buy_list, today_sell_list, bought_stock_list):
#
#     today_d = datetime.now().day
#     record_date = datetime.now().strftime('%Y-%m-%d')
#
#     if today_d == 1:
#         month_money, cur_bought_count = sg.g_creon.notice_current_status(is_slacker=False)
#         today_money = month_money
#     else:
#         month_money = sg.g_json_my_legend_life['my_legend_life'][record_date]['month_money']
#         today_money, cur_bought_count = sg.g_creon.notice_current_status(is_slacker=False)
#
#     return_pro = round((today_money / month_money) * 100, 2)
#     naiyou = {record_date: {
#                             "return_pro": return_pro,
#                             "month_money": month_money,
#                             "today_money": today_money,
#                             "today_buy_list": today_buy_list,
#                             "today_sell_list": today_sell_list,
#                             "bought_stock_list": bought_stock_list
#                            }
#              }
#     return naiyou

if __name__ == '__main__':
    try:
        #  7일간의 데이터 개수가 일정개수 이상인 주식만 자동매매 대상으로 할 것
        # =======================================
        sg.init_global()
        # =======================================
        branch_name = Repository('.').head.shorthand
        if branch_name != "master":
            sg.g_logger.write_log(f"gitブランチがマスターではないため、実行できません。ブランチ名：{branch_name}", log_lv=2, is_slacker=True)
            sys.exit(0)
        else:
            sg.g_logger.write_log(f"実行ブランチ名：{branch_name}", log_lv=2, is_slacker=True)
        # =======================================
        today = datetime.today().weekday()
        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
            sg.g_logger.write_log(f"本日は土日または日曜なので株取引プログラムを終了します。", log_lv=2, is_slacker=True)
            sys.exit(0)
        # =======================================
        is_login_success = False
        try:
            is_login_success = sg.g_creon_login.check_login_creon()
            if is_login_success is False:
                sg.g_creon_login.LoginCreon()
        except Exception as ex:
            sg.g_logger.write_log(f"Exception occured triple screen g_creon_login 크레온 로그인 실패 프로그램 종료.: {str(ex)}",
                                  log_lv=5,
                                  is_slacker=True)
            sys.exit(0)
        # =======================================
        tool.powersave()  # モニター電源オフ
        # =======================================
        sg.g_day_start_money = sg.g_creon.get_current_cash()
        total_cash = int(sg.g_day_start_money)
        buy_stock_cash_p = sg.g_json_trading_config['buy_stock_cash'] / 100
        total_property = sg.g_cpBalance.GetHeaderValue(3)
        cur_bought_count = sg.g_cpBalance.GetHeaderValue(7)
        sg.g_creon.notice_current_status(is_slacker=True)

        if cur_bought_count != 0:
            can_use_cash = total_property * buy_stock_cash_p
            total_stock_cash = total_property - total_cash
            cur_can_use_cash = can_use_cash - total_stock_cash
            max_buy_stock_count = sg.g_buy_auto_stock_count_short
        else:
            can_use_cash = total_cash * buy_stock_cash_p
            total_stock_cash = 0
            cur_can_use_cash = can_use_cash - total_stock_cash
            max_buy_stock_count = sg.g_buy_auto_stock_count_short

        if max_buy_stock_count == 0:
            max_buy_stock_count = 1
            sg.g_logger.write_log(f"살수 있는 종목 수 초기화 실패", log_lv=5, is_slacker=True)
        atari_cash = can_use_cash // max_buy_stock_count

        sg.g_logger.write_log(f"투자 비율 = {buy_stock_cash_p*100}%", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"투자 비율에 따른 전체 투자금 = {(can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 사용할 수 있는 돈 = {(cur_can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"종목당 구매 할 돈 = {(atari_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 구매완료종목수/전체 = {cur_bought_count}/{max_buy_stock_count}", log_lv=2, is_slacker=True)

        analysis_data_amount_min = sg.g_json_trading_config['analysis_data_amount_min']
        analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
        day_rolling = sg.g_json_trading_config['day_rolling']
        kau_list = sg.g_json_trading_config['buy_list']

        t_taiki = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        t_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        t_stock_end = datetime.now().replace(hour=15, minute=20, second=0, microsecond=0)

        if t_start < datetime.now() < t_stock_end:
            bought_list = sg.g_creon.get_bought_stock_list()
            for bought_stock in bought_list:
                stock_code = bought_stock['code']
                result = sg.g_creon.request_day_chart_type(stock_code, 0)
                if result is None:
                    sg.g_logger.write_log(f"Creon으로부터 데이터 받기 실패 구매한 주식임으로 대처가 필요! :{stock_code}", log_lv=5, is_slacker=True)
                    continue
            sg.g_logger.write_log(f"오전9시 이후 실행 되었기 때문에 데이터를 다시 받았습니다.", log_lv=2, is_slacker=True)

        old_min = -1
        is_notice = False
        while True:
            t_now = datetime.now()
            cur_min = t_now.minute
            if t_taiki <= t_now < t_start:
                time.sleep(1)
                print("--떡상 기원--")
            elif t_start <= t_now < t_stock_end:
                if cur_min != old_min:
                    old_min = cur_min
                    bought_list = sg.g_creon.get_bought_stock_list()
                    bought_count = len(bought_list)

                    for bought_stock in bought_list:
                        stock_code = bought_stock['code']
                        db_update_result = sg.g_creon.request_chart_type(stock_code, 20)
                        if db_update_result is None:
                            sg.g_logger.write_log(f"Creon으로부터 데이터 받기 실패 :{stock_code}", log_lv=5, is_slacker=True)
                            continue
                        if db_update_result[0] > 0 and (db_update_result[1] >= cur_min or cur_min == 59):
                            analysis_data_df_min = sg.g_market_db.get_cur_stock_price(stock_code, day_ago=analysis_data_amount_min)
                            analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code, analysis_data_amount_day, chart_type="D")
                            if analysis_data_df_min is None or analysis_data_df_day is None:
                                sg.g_logger.write_log(f"{stock_code} analysis_data_df_min or day is None", log_lv=5)
                                continue
                            # 팔까 말까 계산 처리
                            sg.g_logger.write_log(f"{stock_code}===============팔까 말까 계산 처리...Start", log_lv=2)
                            # ===========================
                            macd_stoch_data_day = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day, slow_d_rolling=day_rolling)
                            macd_stoch_data_df_day = macd_stoch_data_day[0]
                            if len(macd_stoch_data_df_day) == 0:
                                sg.g_logger.write_log(f"{stock_code} / macd_stoch_data_df_day get_macd_stochastic의 리턴값이 len = 0"
                                                      f" \r\n 거래 정지 되었던 주식일지도?", log_lv=5, is_slacker=True)
                                continue
                            macdhist_ave_day = macd_stoch_data_day[1]
                            macd_stoch_data_df_day = macd_stoch_data_df_day.iloc[-1]
                            # ===========================
                            macd_stoch_data_min = sg.g_ets.get_macd_stochastic(df=analysis_data_df_min, slow_d_rolling=sg.g_one_day_data_amount)
                            macd_stoch_data_df_min = macd_stoch_data_min[0]
                            if len(macd_stoch_data_df_min) == 0:
                                sg.g_logger.write_log(f"{stock_code} / macd_stoch_data_df_min get_macd_stochastic의 리턴값이 len = 0"
                                                      f" \r\n 거래 정지 되었던 주식일지도?", log_lv=5, is_slacker=True)
                                continue
                            macdhist_ave_m = macd_stoch_data_min[1]
                            macd_stoch_data_df_min = macd_stoch_data_df_min.iloc[-1]
                            # ===========================
                            is_sell = sg.g_ets.is_buy_sell(df_day=macd_stoch_data_df_day,
                                                          macdhist_ave_day=macdhist_ave_day,
                                                          df_min=macd_stoch_data_df_min,
                                                          macdhist_ave_m=macdhist_ave_m)
                            if is_sell is False:
                                # ============== 판다 ================
                                is_sell_success = sg.g_creon.sell_stock(stock_code)
                                if is_sell_success is True:
                                    current_price, ask_price, bid_price = sg.g_creon.get_current_price(stock_code)
                                    bought_list = sg.g_creon.get_bought_stock_list()
                                    bought_count = len(bought_list)
                                    sg.g_logger.write_log(f"매도 했습니다.\r\n"
                                                          f"stock_code = {stock_code}\r\n"
                                                          f"1주 가격 = {current_price}\r\n"
                                                          f"이제 {max_buy_stock_count-bought_count}개 살 수 있습니다.", log_lv=2, is_slacker=True)

                            sg.g_logger.write_log(f"{stock_code}===============팔까 말까 계산 처리...E N D", log_lv=2)
                        else:
                            sg.g_logger.write_log(f"Creon 으로 데이터를 받지 못 했습니다. DB 업뎃 실패\r\n"
                                                  f"stock_code = {stock_code}\r\n"
                                                  f"db_update_result[0] = {db_update_result[0]}\r\n"
                                                  f"db_update_result[1] = {db_update_result[1]}\r\n"
                                                  f"cur_min = {cur_min}", log_lv=3,  is_slacker=True)

                    if bought_count < max_buy_stock_count:
                        for stock_name in kau_list:
                            stock_code = sg.g_market_db.get_stock_code(stock_name)
                            if stock_code is None:
                                sg.g_logger.write_log(f"종목코드 못 불러옴:{stock_name}", log_lv=3)
                                continue

                            is_bought = sg.g_creon.get_bought_stock_info(stock_code=stock_code)
                            if is_bought is not None:
                                sg.g_logger.write_log(f"이미 산 종목:{is_bought['name']}", log_lv=2)
                                continue

                            db_update_result = sg.g_creon.request_day_chart_type(stock_code, 0)  # 당일 9시 이후 데이터를 받아옴
                            if db_update_result is None:
                                sg.g_logger.write_log(f"Creon으로부터 데이터 받기 실패 :{stock_name}", log_lv=3)
                                continue

                            if db_update_result[0] > 0 and (db_update_result[1] >= cur_min or cur_min == 59):
                                analysis_data_df_min = sg.g_market_db.get_cur_stock_price(stock_code, day_ago=analysis_data_amount_min)
                                analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code,
                                                                                           analysis_data_amount_day,
                                                                                           chart_type="D")
                                if analysis_data_df_min is None or analysis_data_df_day is None:
                                    sg.g_logger.write_log(f"{stock_code} analysis_data_df_min or day is None", log_lv=3,
                                                          is_con_print=False)
                                    continue
                                limt_min_amount = ((analysis_data_amount_min * 4) // 7) * sg.g_one_day_data_amount
                                limt_day_amount = (analysis_data_amount_day * 4) // 7
                                if len(analysis_data_df_min) < limt_min_amount or len(analysis_data_df_day) < limt_day_amount:
                                    sg.g_logger.write_log(f"{stock_code} >> data amount = \r\n"
                                                          f"min:{len(analysis_data_df_min)}\r\n"
                                                          f"day:{len(analysis_data_df_day)}\r\n"
                                                          f"continue", log_lv=3)
                                    continue
                                # 살까 말까 계산 처리
                                sg.g_logger.write_log(f"===============살까 말까 계산 처리...Start", log_lv=2)
                                # ===========================
                                macd_stoch_data_day = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day,
                                                                                   slow_d_rolling=day_rolling)
                                macd_stoch_data_df_day = macd_stoch_data_day[0]
                                if len(macd_stoch_data_df_day) == 0:
                                    sg.g_logger.write_log(f"{stock_code} / macd_stoch_data_df_day get_macd_stochastic의 리턴값이 len = 0"
                                                          f" \r\n 거래 정지 되었던 주식일지도?", log_lv=3,
                                                          is_slacker=False)
                                    continue
                                macdhist_ave_day = macd_stoch_data_day[1]
                                macd_stoch_data_df_day = macd_stoch_data_df_day.iloc[-1]
                                # ===========================
                                macd_stoch_data_min = sg.g_ets.get_macd_stochastic(df=analysis_data_df_min,
                                                                                   slow_d_rolling=sg.g_one_day_data_amount)
                                macd_stoch_data_df_min = macd_stoch_data_min[0]
                                if len(macd_stoch_data_df_min) == 0:
                                    sg.g_logger.write_log(f"{stock_code} / macd_stoch_data_df_min get_macd_stochastic의 리턴값이 len = 0"
                                                          f" \r\n 거래 정지 되었던 주식일지도?", log_lv=3,
                                                          is_slacker=False)
                                    continue
                                macdhist_ave_m = macd_stoch_data_min[1]
                                macd_stoch_data_df_min = macd_stoch_data_df_min.iloc[-1]
                                # ===========================
                                is_buy = sg.g_ets.is_buy_sell(df_day=macd_stoch_data_df_day,
                                                              macdhist_ave_day=macdhist_ave_day,
                                                              df_min=macd_stoch_data_df_min,
                                                              macdhist_ave_m=macdhist_ave_m)
                                if is_buy is True:
                                    # ============== 산다 ================
                                    is_buy_success = sg.g_creon.buy_stock(code=stock_code, money=atari_cash)
                                sg.g_logger.write_log(f"===============살까 말까 계산 처리...E N D", log_lv=2)
                            else:
                                sg.g_logger.write_log(f"Creon 으로 데이터를 받지 못 했습니다. DB 업뎃 실패\r\n"
                                                      f"stock_name = {stock_name}"
                                                      f"db_update_result[0] = {db_update_result[0]}"
                                                      f"db_update_result[1] = {db_update_result[1]}"
                                                      f"cur_min = {cur_min}", log_lv=3, is_slacker=False)

                    # if (cur_min % 30) <= 5 and is_notice is False:
                    #     sg.g_creon.notice_current_status(is_slacker=True)
                    #     is_notice = True
                    # elif (cur_min % 30) > 5:
                    #     is_notice = False

            elif t_stock_end <= t_now:
                sg.g_creon.notice_current_status(is_slacker=True)
                sg.g_logger.write_log(f"오늘의 주식거래 종료", log_lv=2, is_slacker=True)
                # =======================================
                sys.exit(0)
            else:
                print("시간외...")
                time.sleep(5)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured triple screen __name__ python console: {str(ex)}", log_lv=5, is_slacker=True)