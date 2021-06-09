import sys
sys.path.append('../')
from datetime import datetime
from InitGlobal import stock_global as sg
from Utility import Tools as tool

if __name__ == '__main__':
    #  7일간의 데이터 개수가 일정개수 이상인 주식만 자동매매 대상으로 할 것
    today = datetime.today().weekday()
    if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
        sg.g_logger.write_log(f"本日は土日または日曜なので株取引プログラムを終了します。", log_lv=2, is_slacker=True)
        sys.exit(0)
    # =======================================
    sg.init_global()
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