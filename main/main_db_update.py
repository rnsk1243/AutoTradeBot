import sys
sys.path.append('../')
import time
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
        is_login_success = False
        while is_login_success is False:
            try:
                is_login_success = sg.g_creon_login.check_login_creon()
                if is_login_success is False:
                    sg.g_creon_login.LoginCreon()
            except Exception as ex:
                sg.g_logger.write_log(f"Exception occured triple screen g_creon_login 크레온 로그인 실패 5초뒤 재시도 합니다.: {str(ex)}", log_lv=5,
                                      is_slacker=True)
                time.sleep(5)
        sg.init_win32com_client()
        # =======================================
        tool.powersave()  # モニター電源オフ
        # =======================================

        sg.g_logger.write_log(f"종목 분데이터 수집 시작", log_lv=2, is_slacker=True)
        dfStockInfo = sg.g_creon.request_stock_info()
        for row in dfStockInfo.itertuples():
            result = sg.g_creon.request_day_chart_type(row[1], 1)
            up_amount = result[0]
            up_min = result[1]
            sg.g_logger.write_log(f"【{row[0]}/{len(dfStockInfo)}】 {row[2]} / up_amount = {up_amount} / up_min = {up_min}", log_lv=2, is_slacker=False)
        sg.g_logger.write_log(f"종목 분데이터 수집 완료 = {len(dfStockInfo)}개", log_lv=2, is_slacker=True)
        # =======================================
        sys.exit(0)
    except Exception as ex:
        sg.g_logger.write_log(f"Exception occured main_db_update __name__ python console: {str(ex)}", log_lv=5, is_slacker=True)