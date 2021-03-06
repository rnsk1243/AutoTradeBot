import sys
sys.path.append('../')
from pygit2 import Repository
from datetime import datetime
import time
from InitGlobal import stock_global as sg
from Utility import Tools as tool
from requests import get

if __name__ == '__main__':
    try:
        #  7일간의 데이터 개수가 일정개수 이상인 주식만 자동매매 대상으로 할 것
        # =======================================
        sg.init_global()
        # =======================================
        ip = get("https://api.ipify.org").text
        sg.g_logger.write_log(f"My public IP address : \r\n{ip}\r\n", log_lv=2, is_slacker=True)
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
        sg.g_creon.init_cpBalance()  # 내 주식 정보 초기화

        sg.g_day_start_assets_money = sg.g_cpBalance.GetHeaderValue(3)  # 주식을 포함한 총 자산 금액 초기화(아침 시작기준)
        sg.g_day_start_pure_money = sg.g_creon.get_current_cash()  # 주식금액을 제외한 순수 현금자산 금액 초기화(아침 시작기준)
        total_cash = int(sg.g_day_start_pure_money)
        buy_stock_cash_p = sg.g_json_trading_config['buy_stock_cash'] / 100

        cur_bought_count = sg.g_cpBalance.GetHeaderValue(7)  # 구매한 종목 수
        # sg.g_creon.notice_current_status(is_slacker=True)

        if cur_bought_count > 0:
            can_use_cash = sg.g_day_start_assets_money * buy_stock_cash_p
            total_stock_cash = sg.g_day_start_assets_money - total_cash
            cur_can_use_cash = can_use_cash - total_stock_cash
        elif cur_bought_count == 0:
            can_use_cash = total_cash * buy_stock_cash_p
            total_stock_cash = 0
            cur_can_use_cash = int(can_use_cash - total_stock_cash)
        else:
            sg.g_logger.write_log(f"Exception occured triple screen 구매한 종목 개수 이상발생->개수:{cur_bought_count}",
                                  log_lv=5,
                                  is_slacker=True)
            sys.exit(0)

        if sg.g_buy_auto_stock_count_short == 0:
            sg.g_logger.write_log(f"구매 하려는 종목 개수 초기치가 0이므로 매도만 진행합니다.:{sg.g_buy_auto_stock_count_short}",
                                  log_lv=3,
                                  is_slacker=True)
            atari_cash = 0
        else:
            atari_cash = int(cur_can_use_cash // sg.g_buy_auto_stock_count_short)

        sg.g_logger.write_log(f"투자 비율 = {buy_stock_cash_p * 100}%", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"투자 비율에 따른 전체 투자금 = {(can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 사용할 수 있는 돈 = {(cur_can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"종목당 구매 할 돈 = {(atari_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 구매완료종목수/최대구매종목수 = {cur_bought_count}/{sg.g_buy_auto_stock_count_short}", log_lv=2,
                              is_slacker=True)

        buy_list = sg.g_json_trading_config['buy_list']
        analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
        min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']
        kau_list_zenjitu_rieki = []
        try:
            for stock_name in buy_list:
                stock_code = sg.g_market_db.get_stock_code(stock_name)
                if stock_code is not None:
                    analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code,
                                                                               analysis_data_amount_day,
                                                                               chart_type="D")
                    if analysis_data_df_day is not None:
                        analysis_series = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day)
                        if analysis_series is not None and len(analysis_series) > 0:

                            df_yester_day = analysis_series.iloc[-1]
                            recent_rieki_count = df_yester_day.recent_rieki_count
                            recent_not_rieki_count = df_yester_day.recent_not_rieki_count
                            recent_rieki_count_long = df_yester_day.recent_rieki_count_long
                            recent_not_rieki_count_long = df_yester_day.recent_not_rieki_count_long

                            step2 = recent_not_rieki_count_long < recent_rieki_count_long
                            step3 = (recent_not_rieki_count == 0 and min_rieki_amount <= recent_rieki_count)

                            if step2 and step3:
                                kau_list_zenjitu_rieki.append(stock_name)
                        else:
                            sg.g_logger.write_log(f"analysis_series 분석 실패 ：{stock_name}", log_lv=3,
                                                  is_slacker=False)
                else:
                    sg.g_logger.write_log(f"stock_code 검색 실패 ：{stock_name}", log_lv=3,
                                          is_slacker=False)
        except Exception as ex:
            sg.g_logger.write_log(f"Exception occured triple screen 종목 초기화 실패 프로그램 종료.: {str(ex)}",
                                  log_lv=5,
                                  is_slacker=True)

        if len(kau_list_zenjitu_rieki) > 0:
            sg.g_logger.write_log(f"금일 살만한 주식 : {len(kau_list_zenjitu_rieki)} 개\r\n{kau_list_zenjitu_rieki}\r\n",
                                  log_lv=2, is_slacker=True)
        else:
            sg.g_logger.write_log(f"금일 살만한 주식을 찾을 수 없음. 프로그램 종료.", log_lv=2, is_slacker=True)
            sys.exit(0)

        old_min = -1
        is_notice = False
        today_hennka_prices = {}
        while True:
            t_now = datetime.now()
            cur_min = t_now.minute
            if sg.g_t_taiki <= t_now < sg.g_t_start:
                time.sleep(1)
                print("--떡상 기원--")
            elif sg.g_t_start <= t_now < sg.g_t_buy_end:
                if cur_min != old_min:
                    old_min = cur_min
                    bought_list = sg.g_creon.get_bought_stock_list()  # 구매한 주식 불러오기
                    bought_count = len(bought_list)
                    if bought_count < sg.g_buy_auto_stock_count_short:
                        for stock_name in kau_list_zenjitu_rieki:
                            stock_code = sg.g_market_db.get_stock_code(stock_name)
                            if stock_code is None:
                                sg.g_logger.write_log(f"종목코드 못 불러옴:{stock_name}", log_lv=3)
                                continue

                            is_bought = sg.g_creon.get_bought_stock_info(stock_code=stock_code)
                            if is_bought is not None:
                                sg.g_logger.write_log(f"이미 산 종목:{is_bought['name']}", log_lv=2)
                                continue

                            analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code,
                                                                                       analysis_data_amount_day,
                                                                                       chart_type="D")
                            if analysis_data_df_day is None:
                                sg.g_logger.write_log(f"{stock_code} analysis_data_df_min or day is None", log_lv=3,
                                                      is_con_print=False)
                                continue
                            # 살까 말까 계산 처리
                            sg.g_logger.write_log(f"\r\n\t【{stock_name}】...살까 말까 계산 처리...\r\n", log_lv=2)
                            # ===========================
                            analysis_series = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day)
                            if analysis_series is None or len(analysis_series) == 0:
                                sg.g_logger.write_log(
                                    f"{stock_code} / analysis_series get_macd_stochastic의 리턴값이 len = 0"
                                    f" \r\n 거래 정지 되었던 주식일지도?", log_lv=3,
                                    is_slacker=False)
                                continue

                            if stock_code in today_hennka_prices.keys():
                                hennka_price = today_hennka_prices[stock_code]
                            else:
                                hennka_price, today_open = sg.g_creon.get_target_price(code=stock_code)
                                today_hennka_prices[stock_code] = hennka_price

                            current_price, ask_price, bid_price = sg.g_creon.get_current_price(stock_code)

                            if hennka_price is None or current_price is None:
                                continue

                            is_buy = sg.g_ets.is_buy_sell(df_yester_day=analysis_series.iloc[-1],
                                                          hennka_price=hennka_price,
                                                          cur_price=current_price)
                            if is_buy is True:
                                # ============== 산다 ================
                                is_buy_success = sg.g_creon.buy_stock(code=stock_code, money=atari_cash)
                            if is_buy is False:
                                sg.g_logger.write_log(f"매도 하기위해 for문을 빠져나옵니다.", log_lv=2, is_slacker=True)
                                break  # 매도 하기위해 for문을 빠져나옴
                            else:
                                # sg.g_logger.write_log(f"{stock_name}====is_buy_sell 실패.", log_lv=2)
                                continue
                    else:
                        sg.g_logger.write_log(f"\t구매 개수 제한에 걸림... : {bought_count}개\t", log_lv=2,
                                              is_slacker=False)

                    # 2시간마다 알림
                    if (t_now.hour % 2) == 0 and is_notice is False:
                        sg.g_creon.notice_current_status(is_slacker=True)
                        is_notice = True
                    elif (t_now.hour % 2) > 0:
                        is_notice = False

            elif sg.g_t_buy_end <= t_now < sg.g_t_sell_start:
                print("매도 대기중...")
                time.sleep(5)

            elif sg.g_t_sell_start <= t_now < sg.g_t_stock_end:
                bought_list = sg.g_creon.get_bought_stock_list()  # 구매한 주식 불러오기
                for bought_stock in bought_list:
                    stock_code = bought_stock['code']
                    if stock_code in today_hennka_prices.keys():
                        hennka_price = today_hennka_prices[stock_code]
                    else:
                        hennka_price, today_open = sg.g_creon.get_target_price(code=stock_code)
                        today_hennka_prices[stock_code] = hennka_price
                    # ============== 판다 ================
                    is_sell_success = sg.g_creon.sell_stock(stock_code)
                    if is_sell_success is True:
                        current_price, ask_price, bid_price = sg.g_creon.get_current_price(stock_code)
                        bought_list = sg.g_creon.get_bought_stock_list()
                        stock_name_sell = sg.g_market_db.get_stock_name(stock_code)
                        sg.g_logger.write_log(f"매도 했습니다.\r\n"
                                              f"이름 = {stock_name_sell}\r\n"
                                              f"현재가 = {(current_price):,.0f}\r\n"
                                              f"돌파가격 = {(hennka_price):,.0f}\r\n"
                                              f"현재가-돌파가격 = {(current_price - hennka_price):,.0f}\r\n",
                                              log_lv=2, is_slacker=True)

            elif sg.g_t_stock_end <= t_now:
                sg.g_logger.write_log(f"오늘의 주식거래 종료", log_lv=2, is_slacker=True)
                # =======================================
                sys.exit(0)
            else:
                print("시간외...")
                time.sleep(5)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured triple screen __name__ python console: {str(ex)}", log_lv=5,
                              is_slacker=True)

else:

    try:
        #  7일간의 데이터 개수가 일정개수 이상인 주식만 자동매매 대상으로 할 것
        # =======================================
        sg.init_global()
        # =======================================
        ip = get("https://api.ipify.org").text
        sg.g_logger.write_log(f"My public IP address : \r\n{ip}\r\n", log_lv=2, is_slacker=True)
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
        sg.g_creon.init_cpBalance()  # 내 주식 정보 초기화

        sg.g_day_start_assets_money = sg.g_cpBalance.GetHeaderValue(3)  # 주식을 포함한 총 자산 금액 초기화(아침 시작기준)
        sg.g_day_start_pure_money = sg.g_creon.get_current_cash()  # 주식금액을 제외한 순수 현금자산 금액 초기화(아침 시작기준)
        total_cash = int(sg.g_day_start_pure_money)
        buy_stock_cash_p = sg.g_json_trading_config['buy_stock_cash'] / 100

        cur_bought_count = sg.g_cpBalance.GetHeaderValue(7)  # 구매한 종목 수
        # sg.g_creon.notice_current_status(is_slacker=True)

        if cur_bought_count > 0:
            can_use_cash = sg.g_day_start_assets_money * buy_stock_cash_p
            total_stock_cash = sg.g_day_start_assets_money - total_cash
            cur_can_use_cash = can_use_cash - total_stock_cash
        elif cur_bought_count == 0:
            can_use_cash = total_cash * buy_stock_cash_p
            total_stock_cash = 0
            cur_can_use_cash = int(can_use_cash - total_stock_cash)
        else:
            sg.g_logger.write_log(f"Exception occured triple screen 구매한 종목 개수 이상발생->개수:{cur_bought_count}",
                                  log_lv=5,
                                  is_slacker=True)
            sys.exit(0)

        if sg.g_buy_auto_stock_count_short == 0:
            sg.g_logger.write_log(f"구매 하려는 종목 개수 초기치가 0이므로 매도만 진행합니다.:{sg.g_buy_auto_stock_count_short}",
                                  log_lv=3,
                                  is_slacker=True)
            atari_cash = 0
        else:
            atari_cash = int(cur_can_use_cash // sg.g_buy_auto_stock_count_short)

        sg.g_logger.write_log(f"투자 비율 = {buy_stock_cash_p * 100}%", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"투자 비율에 따른 전체 투자금 = {(can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 사용할 수 있는 돈 = {(cur_can_use_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"종목당 구매 할 돈 = {(atari_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"현재 구매완료종목수/최대구매종목수 = {cur_bought_count}/{sg.g_buy_auto_stock_count_short}", log_lv=2,
                              is_slacker=True)

        buy_list = sg.g_json_trading_config['buy_list']
        analysis_data_amount_day = sg.g_json_trading_config['analysis_data_amount_day']
        min_rieki_amount = sg.g_json_trading_config['min_rieki_amount']
        kau_list_zenjitu_rieki = []
        try:
            for stock_name in buy_list:
                stock_code = sg.g_market_db.get_stock_code(stock_name)
                if stock_code is not None:
                    analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code,
                                                                               analysis_data_amount_day,
                                                                               chart_type="D")
                    if analysis_data_df_day is not None:
                        analysis_series = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day)
                        if analysis_series is not None and len(analysis_series) > 0:

                            df_yester_day = analysis_series.iloc[-1]
                            recent_rieki_count = df_yester_day.recent_rieki_count
                            recent_not_rieki_count = df_yester_day.recent_not_rieki_count
                            recent_rieki_count_long = df_yester_day.recent_rieki_count_long
                            recent_not_rieki_count_long = df_yester_day.recent_not_rieki_count_long

                            step2 = recent_not_rieki_count_long < recent_rieki_count_long
                            step3 = (recent_not_rieki_count == 0 and min_rieki_amount <= recent_rieki_count)

                            if step2 and step3:
                                kau_list_zenjitu_rieki.append(stock_name)
                        else:
                            sg.g_logger.write_log(f"analysis_series 분석 실패 ：{stock_name}", log_lv=3,
                                                  is_slacker=False)
                else:
                    sg.g_logger.write_log(f"stock_code 검색 실패 ：{stock_name}", log_lv=3,
                                          is_slacker=False)
        except Exception as ex:
            sg.g_logger.write_log(f"Exception occured triple screen 종목 초기화 실패 프로그램 종료.: {str(ex)}",
                                  log_lv=5,
                                  is_slacker=True)

        if len(kau_list_zenjitu_rieki) > 0:
            sg.g_logger.write_log(f"금일 살만한 주식 : {len(kau_list_zenjitu_rieki)} 개\r\n{kau_list_zenjitu_rieki}\r\n",
                                  log_lv=2, is_slacker=True)
        else:
            sg.g_logger.write_log(f"금일 살만한 주식을 찾을 수 없음. 프로그램 종료.", log_lv=2, is_slacker=True)
            sys.exit(0)

        old_min = -1
        is_notice = False
        today_hennka_prices = {}
        while True:
            t_now = datetime.now()
            cur_min = t_now.minute
            if sg.g_t_taiki <= t_now < sg.g_t_start:
                time.sleep(1)
                print("--떡상 기원--")
            elif sg.g_t_start <= t_now < sg.g_t_buy_end:
                if cur_min != old_min:
                    old_min = cur_min
                    bought_list = sg.g_creon.get_bought_stock_list()  # 구매한 주식 불러오기
                    bought_count = len(bought_list)
                    if bought_count < sg.g_buy_auto_stock_count_short:
                        for stock_name in kau_list_zenjitu_rieki:
                            stock_code = sg.g_market_db.get_stock_code(stock_name)
                            if stock_code is None:
                                sg.g_logger.write_log(f"종목코드 못 불러옴:{stock_name}", log_lv=3)
                                continue

                            is_bought = sg.g_creon.get_bought_stock_info(stock_code=stock_code)
                            if is_bought is not None:
                                sg.g_logger.write_log(f"이미 산 종목:{is_bought['name']}", log_lv=2)
                                continue

                            analysis_data_df_day = sg.g_market_db.get_past_stock_price(stock_code,
                                                                                       analysis_data_amount_day,
                                                                                       chart_type="D")
                            if analysis_data_df_day is None:
                                sg.g_logger.write_log(f"{stock_code} analysis_data_df_min or day is None", log_lv=3,
                                                      is_con_print=False)
                                continue
                            # 살까 말까 계산 처리
                            sg.g_logger.write_log(f"\r\n\t【{stock_name}】...살까 말까 계산 처리...\r\n", log_lv=2)
                            # ===========================
                            analysis_series = sg.g_ets.get_macd_stochastic(df=analysis_data_df_day)
                            if analysis_series is None or len(analysis_series) == 0:
                                sg.g_logger.write_log(
                                    f"{stock_code} / analysis_series get_macd_stochastic의 리턴값이 len = 0"
                                    f" \r\n 거래 정지 되었던 주식일지도?", log_lv=3,
                                    is_slacker=False)
                                continue

                            if stock_code in today_hennka_prices.keys():
                                hennka_price = today_hennka_prices[stock_code]
                            else:
                                hennka_price, today_open = sg.g_creon.get_target_price(code=stock_code)
                                today_hennka_prices[stock_code] = hennka_price

                            current_price, ask_price, bid_price = sg.g_creon.get_current_price(stock_code)

                            if hennka_price is None or current_price is None:
                                continue

                            is_buy = sg.g_ets.is_buy_sell(df_yester_day=analysis_series.iloc[-1],
                                                          hennka_price=hennka_price,
                                                          cur_price=current_price)
                            if is_buy is True:
                                # ============== 산다 ================
                                is_buy_success = sg.g_creon.buy_stock(code=stock_code, money=atari_cash)
                            if is_buy is False:
                                sg.g_logger.write_log(f"매도 하기위해 for문을 빠져나옵니다.", log_lv=2, is_slacker=True)
                                break  # 매도 하기위해 for문을 빠져나옴
                            else:
                                # sg.g_logger.write_log(f"{stock_name}====is_buy_sell 실패.", log_lv=2)
                                continue
                    else:
                        sg.g_logger.write_log(f"\t구매 개수 제한에 걸림... : {bought_count}개\t", log_lv=2,
                                              is_slacker=False)

                    # 2시간마다 알림
                    if (t_now.hour % 2) == 0 and is_notice is False:
                        sg.g_creon.notice_current_status(is_slacker=True)
                        is_notice = True
                    elif (t_now.hour % 2) > 0:
                        is_notice = False

            elif sg.g_t_buy_end <= t_now < sg.g_t_sell_start:
                print("매도 대기중...")
                time.sleep(5)

            elif sg.g_t_sell_start <= t_now < sg.g_t_stock_end:
                bought_list = sg.g_creon.get_bought_stock_list()  # 구매한 주식 불러오기
                for bought_stock in bought_list:
                    stock_code = bought_stock['code']
                    if stock_code in today_hennka_prices.keys():
                        hennka_price = today_hennka_prices[stock_code]
                    else:
                        hennka_price, today_open = sg.g_creon.get_target_price(code=stock_code)
                        today_hennka_prices[stock_code] = hennka_price
                    # ============== 판다 ================
                    is_sell_success = sg.g_creon.sell_stock(stock_code)
                    if is_sell_success is True:
                        current_price, ask_price, bid_price = sg.g_creon.get_current_price(stock_code)
                        bought_list = sg.g_creon.get_bought_stock_list()
                        stock_name_sell = sg.g_market_db.get_stock_name(stock_code)
                        sg.g_logger.write_log(f"매도 했습니다.\r\n"
                                              f"이름 = {stock_name_sell}\r\n"
                                              f"현재가 = {(current_price):,.0f}\r\n"
                                              f"돌파가격 = {(hennka_price):,.0f}\r\n"
                                              f"현재가-돌파가격 = {(current_price - hennka_price):,.0f}\r\n",
                                              log_lv=2, is_slacker=True)

            elif sg.g_t_stock_end <= t_now:
                sg.g_logger.write_log(f"오늘의 주식거래 종료", log_lv=2, is_slacker=True)
                # =======================================
                sys.exit(0)
            else:
                print("시간외...")
                time.sleep(5)

    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured triple screen __name__ python console: {str(ex)}", log_lv=5,
                              is_slacker=True)