import sys
sys.path.append('../')
from pygit2 import Repository
from datetime import datetime
from InitGlobal import stock_global as sg
from Utility import Tools as tool

if __name__ == '__main__':
    try:
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
        if sg.g_creon_login.check_login_creon() is False:
            sg.g_creon_login.LoginCreon()
        sg.init_win32com_client()
        # =======================================
        tool.powersave()  # モニター電源オフ
        # =======================================

        sg.g_logger.write_log(f"종목 분데이터 수집 시작", log_lv=2, is_slacker=True)
        dfStockInfo = sg.g_creon.request_stock_info()
        for row in dfStockInfo.itertuples():
            sg.g_creon.request_day_chart_type(row[1], 1)
        sg.g_logger.write_log(f"종목 분데이터 수집 완료 = {len(dfStockInfo)}개", log_lv=2, is_slacker=True)
        # =======================================
        sys.exit(0)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured main_db_update __name__ python console: {str(ex)}", log_lv=5, is_slacker=True)
else:
    try:
        # =======================================
        sg.init_global()
        # =======================================
        # =======================================
        # =======================================
        if sg.g_creon_login.check_login_creon() is False:
            sg.g_creon_login.LoginCreon()
        sg.init_win32com_client()
        # =======================================
        # =======================================
        test_target_stock_list = sg.g_json_trading_config['buy_list']
        for row in test_target_stock_list:
            stock_code = sg.g_market_db.get_stock_code(row)
            sg.g_creon.request_day_chart_type(stock_code, 0)
        sg.g_logger.write_log(f"종목 분데이터 수집 완료 = {len(test_target_stock_list)}개", log_lv=2, is_slacker=False)
        # =======================================
        sys.exit(0)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured main_db_update __name__ python console: {str(ex)}", log_lv=5, is_slacker=True)