import ctypes
import pandas as pd
from datetime import datetime
import time
from InitGlobal import stock_global as sg
from Slacker import Slacker_Message as sm


# def dbgout(message):
#     """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
#     print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
#     strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
#     Slacker_Message.post_message("#nomal-stock-trading", strbuf)

# def sg.g_logger.write_log(message, *args):
#     """인자로 받은 문자열을 파이썬 셸에 출력한다."""
#     print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
 
# 크레온 플러스 공통 OBJECT


def is_send_slacker():
    if sg.g_exception_slacker > 0:
        is_send = True
        sg.g_exception_slacker -= 1
    else:
        is_send = False
    return is_send

def check_creon_system():
    """크레온 플러스 시스템 연결 상태를 점검한다."""
    # 관리자 권한으로 프로세스 실행 여부
    if not ctypes.windll.shell32.IsUserAnAdmin():
        sg.g_logger.write_log('管理者権限失敗', log_lv=5, is_slacker=False)
        return False
 
    # 연결 여부 체크
    if (sg.g_cpStatus.IsConnect == 0):
        sg.g_logger.write_log('creonコネクトエラー', log_lv=5, is_slacker=False)
        return False
 
    # 주문 관련 초기화 - 계좌 관련 코드가 있을 때만 사용
    if (sg.g_cpTradeUtil.TradeInit(0) != 0):
        sg.g_logger.write_log('注文関連失エラー', log_lv=5, is_slacker=False)
        return False
    return True

def init_cpBalance():
    sg.g_cpTradeUtil.TradeInit()
    acc = sg.g_cpTradeUtil.AccountNumber[0]  # 계좌번호
    accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
    sg.g_cpBalance.SetInputValue(0, acc)  # 계좌번호
    sg.g_cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    sg.g_cpBalance.SetInputValue(2, 50)  # 요청 건수(최대 50)
    sg.g_cpBalance.BlockRequest()

def get_current_price(code):
    """인자로 받은 종목의 현재가, 매수호가, 매도호가를 반환한다."""
    sg.g_cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보
    sg.g_cpStock.BlockRequest()
    item = {}
    item['cur_price'] = sg.g_cpStock.GetHeaderValue(11)   # 현재가
    item['ask'] = sg.g_cpStock.GetHeaderValue(16)        # 매수호가
    item['bid'] = sg.g_cpStock.GetHeaderValue(17)        # 매도호가
    return item['cur_price'], item['ask'], item['bid']

def get_ohlc(code, qty):
    """인자로 받은 종목의 OHLC 가격 정보를 qty 개수만큼 반환한다."""
    sg.g_cpOhlc.SetInputValue(0, code)           # 종목코드
    sg.g_cpOhlc.SetInputValue(1, ord('2'))        # 1:기간, 2:개수
    sg.g_cpOhlc.SetInputValue(4, qty)             # 요청개수
    sg.g_cpOhlc.SetInputValue(5, [0, 2, 3, 4, 5]) # 0:날짜, 2~5:OHLC
    sg.g_cpOhlc.SetInputValue(6, ord('D'))        # D:일단위
    sg.g_cpOhlc.SetInputValue(9, ord('1'))        # 0:무수정주가, 1:수정주가
    sg.g_cpOhlc.BlockRequest()
    count = sg.g_cpOhlc.GetHeaderValue(3)   # 3:수신개수
    columns = ['open', 'high', 'low', 'close']
    index = []
    rows = []
    for i in range(count): 
        index.append(sg.g_cpOhlc.GetDataValue(0, i))
        rows.append([sg.g_cpOhlc.GetDataValue(1, i), sg.g_cpOhlc.GetDataValue(2, i),
            sg.g_cpOhlc.GetDataValue(3, i), sg.g_cpOhlc.GetDataValue(4, i)])
    df = pd.DataFrame(rows, columns=columns, index=index) 
    return df

def get_stock_balance(code):
    """인자로 받은 종목의 종목명과 수량을 반환한다."""
    init_cpBalance()
    if code == 'ALL':
        current_benefit = sg.g_cpBalance.GetHeaderValue(3)
        today_benefit = current_benefit - sg.g_day_start_pure_money
        today_benefit_per = round((today_benefit / sg.g_day_start_pure_money) * 100, 2)
        sm.post_message("↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
        sg.g_logger.write_log(f"口座名: {str(sg.g_cpBalance.GetHeaderValue(0))}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"決済残高収量: {str(sg.g_cpBalance.GetHeaderValue(1))}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"評価金額: {(current_benefit):,.0f}", log_lv=2, is_slacker=True)
        # sg.g_logger.write_log(f"評価損益: {(sg.g_cpBalance.GetHeaderValue(4)):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"株種類数: {str(sg.g_cpBalance.GetHeaderValue(7))}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"本日の利益率: 【{today_benefit_per}%】", log_lv=2, is_slacker=True)
        sm.post_message("↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")
    stocks = []
    for i in range(sg.g_cpBalance.GetHeaderValue(7)):
        stock_code = sg.g_cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = sg.g_cpBalance.GetDataValue(0, i)   # 종목명
        stock_qty = sg.g_cpBalance.GetDataValue(15, i)   # 수량
        if code == 'ALL':
            # ================================================================
            if stock_code == 'A005930' or stock_code == 'A001360':
                continue
            # ================================================================
            sg.g_logger.write_log(f"{str(i+1) + ' ' + stock_code + '(' + stock_name + ')' + ':' + str(stock_qty)}",
                                  log_lv=2,
                                  is_slacker=False)
            stocks.append({'code': stock_code,
                           'name': stock_name,
                           'qty': stock_qty})
        if stock_code == code:  
            return stock_name, stock_qty
    if code == 'ALL':
        return stocks
    else:
        stock_name = sg.g_cpCodeMgr.CodeToName(code)
        return stock_name, 0

def get_current_cash():
    """증거금 100% 주문 가능 금액을 반환한다."""
    sg.g_cpTradeUtil.TradeInit()
    acc = sg.g_cpTradeUtil.AccountNumber[0]    # 계좌번호
    accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    sg.g_cpCash.SetInputValue(0, acc)              # 계좌번호
    sg.g_cpCash.SetInputValue(1, accFlag[0])      # 상품구분 - 주식 상품 중 첫번째
    sg.g_cpCash.BlockRequest()
    return sg.g_cpCash.GetHeaderValue(9) # 증거금 100% 주문 가능 금액

def get_target_price(code):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open 
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]                                      
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * sg.g_json_trading_config['larry_constant_K_buy']
        return target_price
    except Exception as ex:
        sg.g_logger.write_log(f"get_target_price() -> exception! : "
                              f"{str(ex)}", log_lv=5, is_slacker=is_send_slacker())
        return None
    
def get_movingaverage(code, window):
    """인자로 받은 종목에 대한 이동평균가격을 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()         
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        sg.g_logger.write_log(f"get_movingavrg("
                              f"{str(window)}"
                              f") -> exception! "
                              f"{str(ex)}", log_lv=5, is_slacker=is_send_slacker())
        return None

def buy_stock(code):
    """인자로 받은 종목을 최유리 지정가 FOK 조건으로 매수한다."""
    try:
        if code in sg.g_bought_short_list or code in sg.g_bought_long_list: # 매수 완료 종목이면 더 이상 안 사도록 함수 종료
            #sg.g_logger.write_log('code:', code, 'in', sg.g_bought_short_list)
            return False
        current_price, ask_price, bid_price = get_current_price(code)
        target_price = get_target_price(code)    # 매수 목표가
        ma5_price = get_movingaverage(code, 5)   # 5일 이동평균가
        ma10_price = get_movingaverage(code, 10) # 10일 이동평균가
        buy_qty = 0        # 매수할 수량 초기화
        if ask_price > 0:  # 매수호가가 존재하면   
            buy_qty = sg.g_buy_amount // ask_price
        if buy_qty == 0:
            return False
        stock_name, stock_qty = get_stock_balance(code)  # 종목명과 보유수량 조회
        #sg.g_logger.write_log('sg.g_bought_short_list:', sg.g_bought_short_list, 'len(sg.g_bought_short_list):',
        #    len(sg.g_bought_short_list), 'buy_auto_stock_count_short:', buy_auto_stock_count_short)
        if current_price > target_price and current_price > ma5_price \
            and current_price > ma10_price:  
            sg.g_logger.write_log(f"{stock_name}'('{str(code)}')': 【{str(buy_qty)}】株 * 【{str(current_price)}】 買収条件を満たす", log_lv=2, is_slacker=False)
            sg.g_cpTradeUtil.TradeInit()
            acc = sg.g_cpTradeUtil.AccountNumber[0]      # 계좌번호
            accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1) # -1:전체,1:주식,2:선물/옵션
            # 최유리 FOK 매수 주문 설정
            sg.g_cpOrder.SetInputValue(0, "2")        # 2: 매수
            sg.g_cpOrder.SetInputValue(1, acc)        # 계좌번호
            sg.g_cpOrder.SetInputValue(2, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            sg.g_cpOrder.SetInputValue(3, code)       # 종목코드
            sg.g_cpOrder.SetInputValue(4, buy_qty)    # 매수할 수량
            sg.g_cpOrder.SetInputValue(7, "2")        # 주문조건 0:기본, 1:IOC, 2:FOK
            sg.g_cpOrder.SetInputValue(8, "12")       # 주문호가 1:보통, 3:시장가
                                                 # 5:조건부, 12:최유리, 13:최우선 
            # 매수 주문 요청
            ret = sg.g_cpOrder.BlockRequest()
            sg.g_logger.write_log(f"株取引注文のFoK（최유리） 買収 【{stock_name}】【{code}】【{buy_qty}】 -> 【{ret}】", log_lv=2, is_slacker=False)
            if ret == 4:
                remain_time = sg.g_cpStatus.LimitRequestRemainTime
                sg.g_logger.write_log(f"주의: 연속 주문 제한에 걸림. 대기 시간: {remain_time / 1000}", log_lv=2, is_slacker=False)
                time.sleep(remain_time/1000) 
                return False
            time.sleep(2)
            sg.g_logger.write_log(f"現金注文 可能金額 : {(sg.g_buy_amount):,.0f}", log_lv=2, is_slacker=False)
            stock_name, bought_qty = get_stock_balance(code)
            sg.g_logger.write_log(f"注文結果：【{stock_name}】【{bought_qty}】株", log_lv=2, is_slacker=False)
            if bought_qty > 0:
                sg.g_bought_short_list.append(code)
                bought_num = len(sg.g_bought_short_list)
                can_buy_num = sg.g_buy_auto_stock_count_short - bought_num
                sg.g_logger.write_log(f"注文結果 \n"
                                      f"【{str(stock_name)}】"
                                      f" : "
                                      f"【{(ask_price):,.0f}"
                                      f" * "
                                      f"{str(bought_qty)}】株\n"
                                      f"【{(sg.g_buy_amount):,.0f}】won\n"
                                      f"を買いました。\n"
                                      f"買収数:【{bought_num}】", log_lv=2, is_slacker=True)
                sg.g_logger.write_log(f"残り買収株数 : 【{can_buy_num}】", log_lv=2, is_slacker=True)
    except Exception as ex:
        sg.g_logger.write_log(f"buy_stock("
                              f"{str(code)}"
                              f") -> exception! "
                              f"{str(ex)}", log_lv=5, is_slacker=is_send_slacker())

def sell_all():
    """보유한 모든 종목을 최유리 지정가 IOC 조건으로 매도한다."""
    try:
        sg.g_cpTradeUtil.TradeInit()
        acc = sg.g_cpTradeUtil.AccountNumber[0]       # 계좌번호
        accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        while True:    
            stocks = get_stock_balance('ALL') 
            total_qty = 0 
            for s in stocks:
                total_qty += s['qty'] 
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:                  
                    sg.g_cpOrder.SetInputValue(0, "1")         # 1:매도, 2:매수
                    sg.g_cpOrder.SetInputValue(1, acc)         # 계좌번호
                    sg.g_cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                    sg.g_cpOrder.SetInputValue(3, s['code'])   # 종목코드
                    sg.g_cpOrder.SetInputValue(4, s['qty'])    # 매도수량
                    sg.g_cpOrder.SetInputValue(7, "1")   # 조건 0:기본, 1:IOC, 2:FOK
                    sg.g_cpOrder.SetInputValue(8, "12")  # 호가 12:최유리, 13:최우선
                    # 최유리 IOC 매도 주문 요청
                    ret = sg.g_cpOrder.BlockRequest()
                    sg.g_logger.write_log(f"株取引注文のIOC（최유리） 売買 {s['name']}, {s['qty']}, {ret}", log_lv=2, is_slacker=True)
                    if ret == 4:
                        remain_time = sg.g_cpStatus.LimitRequestRemainTime
                        sg.g_logger.write_log(f"주의: 연속 주문 제한, 대기시간:, {remain_time / 1000}", log_lv=2, is_slacker=False)
                time.sleep(2)
            time.sleep(30)
    except Exception as ex:
        sg.g_logger.write_log(f"sell_all() -> exception! "
                              f"{str(ex)}", log_lv=5, is_slacker=is_send_slacker())

def update_json_config():
    # 오늘 사려는 것 개수 = 전체 단타 개수 - 이미 산 단타 개수
    buy_stock_amount = sg.g_buy_auto_stock_count_short - len(sg.g_bought_short_list)
    if buy_stock_amount == 0:
        buy_stock_amount = 1
    buy_percent = (1 / buy_stock_amount) - 0.003
    total_cash = int(get_current_cash())  # 100% 증거금 주문 가능 금액 조회
    sg.g_buy_amount = buy_percent * total_cash # 종목별 주문 금액 계산

    return buy_percent, total_cash

def execut_periodic(t_now, min_update_json, min_slacker):

    if (t_now.minute % min_update_json) == 0 and 0 <= t_now.second <= 5:  # 買収時間に毎1分ごとにjsonを再読み込む。
        sg.init_json()
        update_json_config()
        time.sleep(1)
    if (t_now.minute % min_slacker) == 0 and 0 <= t_now.second <= 10:  # 毎30分ごとに状況を送る
        get_stock_balance('ALL')
        if sg.g_exception_slacker < 5:
            sg.g_exception_slacker += 1  # 毎30分ごとにメッセージ送信回数回復
        time.sleep(1)

def update_money():
    try:
        # ================================================================
        # sg.g_bought_short_list = ['A005930', 'A001360']     # 매수 완료된 종목 리스트
        # ================================================================
        init_cpBalance()  # init해야 새로운값을 받아올 수 있음
        sg.g_day_start_pure_money = sg.g_cpBalance.GetHeaderValue(3)
        sg.g_logger.write_log(f"check_creon_system() : {check_creon_system()}", log_lv=2, is_slacker=False)  # 크레온 접속 점검
        get_stock_balance('ALL')      # 보유한 모든 종목 조회

        buy_percent, total_cash = update_json_config()

        sg.g_logger.write_log(f"100% 証拠金注文可能金額 : {(total_cash):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"項目別注文比率 : {buy_percent}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"項目別注文金額 : {(sg.g_buy_amount):,.0f}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"買収株のmax数 : {sg.g_buy_auto_stock_count_short}", log_lv=2, is_slacker=True)
        sg.g_logger.write_log(f"スタート時刻 : {datetime.now().strftime('%m/%d %H:%M:%S')}", log_lv=2, is_slacker=True)

        soldout = False
        while True:
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            # t_buy_am = t_now.replace(hour=11, minute=59, second=59, microsecond=0)
            t_buy = t_now.replace(hour=14, minute=45, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            today = datetime.today().weekday()
            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                sg.g_logger.write_log(f"本日は土日または日曜なので株取引プログラムを終了します。", log_lv=2, is_slacker=True)
                return
            if t_9 < t_now < t_start and soldout is False:
                soldout = True
                sell_all()
            if t_start < t_now < t_buy:  # AM 09:05 ~ PM 15:15 : 株買収時間
                for sym in sg.g_symbol_list:
                    if len(sg.g_bought_short_list) < sg.g_buy_auto_stock_count_short:
                        buy_stock(sym)
                        time.sleep(1)
                    execut_periodic(t_now, 1, 30)
            if t_buy < t_now < t_sell:
                execut_periodic(t_now, 1, 30)
            if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
                if sell_all() == True:
                    sg.g_logger.write_log(f"全株を売買しました。プログラムを終了します。",
                                          log_lv=2, is_slacker=True)
                    return
            if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
                sg.g_logger.write_log(f"株取引時間外なのでプログラムを終了します。",
                                      log_lv=2, is_slacker=True)
                return
            time.sleep(3)
    except Exception as ex:
        sg.g_logger.write_log(f"update_money() exception! "
                              f"{str(ex)}", log_lv=5, is_slacker=is_send_slacker())