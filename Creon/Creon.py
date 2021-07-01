import time
import ctypes
import pandas as pd
from datetime import datetime
from datetime import timedelta
from InitGlobal import stock_global as sg

LT_NONTRADE_REQUEST = 1
MAX_REQUEST_NUM = 2221
ONE_DAY_MIN_AMOUNT = 381

class Creon:
    def __init__(self):
        try:
            # self.__creonConfig = sg.g_json_creonConfig
            # self.__cpStatus = sg.g_cpStatus
            # self.__cpTradeUtil = sg.g_cpTradeUtil
            # self.__objCpCodeMgr = sg.g_cpCodeMgr
            # self.__cpOhlc = sg.g_cpOhlc
            # self.__dbu = sg.g_db_updater
            sg.g_logger.write_log('Creon init 成功', log_lv=2)

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured Creon init : {str(e)}", log_lv=2, is_slacker=False)

    def check_creon_system(self):
        """CREONPLUSEシステムつながりチェックする"""
        # 管理者権限で実行したのか
        if not ctypes.windll.shell32.IsUserAnAdmin():
            sg.g_logger.write_log('check_creon_system() : admin user -> FAILED', log_lv=2, is_slacker=False)
            return False

        # 繋げるのか
        if (sg.g_cpStatus.IsConnect == 0):
            sg.g_logger.write_log('check_creon_system() : connect to server -> FAILED', log_lv=2, is_slacker=False)
            return False

        # 注文関連初期化 - 口座関連コードがある場合のみ
        if (sg.g_cpTradeUtil.TradeInit(0) != 0):
            sg.g_logger.write_log('check_creon_system() : init trade -> FAILED', log_lv=2, is_slacker=False)
            return False

        sg.g_logger.write_log('CREONPLUSEシステムつながりチェック True', log_lv=2, is_slacker=False)
        return True

    def __check_and_wait(self, type):
        remainCount = sg.g_cpStatus.GetLimitRemainCount(type)
        sg.g_logger.write_log(f"残り要請Count : {remainCount}", log_lv=1, is_con_print=False)
        if remainCount <= 0:
            sg.g_logger.write_log(f"データ要請待機 : {sg.g_cpStatus.LimitRequestRemainTime/1000}秒", log_lv=2)
            time.sleep(sg.g_cpStatus.LimitRequestRemainTime / 1000)

    def init_cpBalance(self):
        # self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        sg.g_cpTradeUtil.TradeInit()
        acc = sg.g_cpTradeUtil.AccountNumber[0]  # 계좌번호
        accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        sg.g_cpBalance.SetInputValue(0, acc)  # 계좌번호
        sg.g_cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        sg.g_cpBalance.SetInputValue(2, 50)  # 요청 건수(최대 50)
        sg.g_cpBalance.BlockRequest()

    def get_current_cash(self):
        """증거금 100% 주문 가능 금액을 반환한다."""
        self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        sg.g_cpTradeUtil.TradeInit()
        acc = sg.g_cpTradeUtil.AccountNumber[0]  # 계좌번호
        accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        sg.g_cpCash.SetInputValue(0, acc)  # 계좌번호
        sg.g_cpCash.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        sg.g_cpCash.BlockRequest()
        return sg.g_cpCash.GetHeaderValue(9)  # 증거금 100% 주문 가능 금액

    def get_bought_stock_list(self):
        self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        self.init_cpBalance()
        stocks = []
        for i in range(sg.g_cpBalance.GetHeaderValue(7)):
            stock_code = sg.g_cpBalance.GetDataValue(12, i)  # 종목코드
            stock_name = sg.g_cpBalance.GetDataValue(0, i)  # 종목명
            stock_qty = sg.g_cpBalance.GetDataValue(15, i)  # 수량
            stocks.append({'code': stock_code,
                           'name': stock_name,
                           'qty': stock_qty})
        return stocks

    def get_bought_stock_info(self, stock_code):
        """
        return {}
        """
        bought_stock_list = self.get_bought_stock_list()
        result = None
        for stock in bought_stock_list:
            if stock['code'] == stock_code:
                result = stock

        return result

    def notice_current_status(self, is_slacker):
        self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        self.init_cpBalance()

        current_benefit = sg.g_cpBalance.GetHeaderValue(3)
        bought_stock_count = sg.g_cpBalance.GetHeaderValue(7)

        if bought_stock_count == 0:
            sg.g_logger.write_log(f"評価金額: {(current_benefit):,.0f}", log_lv=2, is_slacker=is_slacker,
                                  is_con_print=False)
            sg.g_logger.write_log(f"株種類数: {str(bought_stock_count)}", log_lv=2, is_slacker=is_slacker,
                                  is_con_print=False)
            return

        today_benefit = current_benefit - sg.g_day_start_assets_money
        today_benefit_per = round((today_benefit / sg.g_day_start_assets_money) * 100, 2)
        # sg.g_logger.write_log("↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓", log_lv=2, is_slacker=True, is_con_print=False)
        # sg.g_logger.write_log(f"口座名: {str(sg.g_cpBalance.GetHeaderValue(0))}", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        # sg.g_logger.write_log(f"決済残高収量: {str(sg.g_cpBalance.GetHeaderValue(1))}", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        sg.g_logger.write_log(f"評価金額: {(current_benefit):,.0f}", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        # sg.g_logger.write_log(f"評価損益: {(sg.g_cpBalance.GetHeaderValue(4)):,.0f}", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        sg.g_logger.write_log(f"株種類数: {str(bought_stock_count)}", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        sg.g_logger.write_log(f"本日の利益率: {(today_benefit):,.0f} / 【{today_benefit_per}%】", log_lv=2, is_slacker=is_slacker, is_con_print=False)
        # sg.g_logger.write_log("↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑", log_lv=2, is_slacker=True, is_con_print=False)

        return

    def __transform_data_frame_db(self, df, chartType):
        """
        株価情報をDBに書き込むためにDBテーブルに変換する。
        :param df: 変換対象DataFrame
        :param chartType: Chart区分("D","W","M","m")
        :return: 返還後のDataFrame
        """
        sg.g_logger.write_log(f"chartType = {chartType}", log_lv=1, is_con_print=False)
        f_weekday = lambda x: x.weekday()

        if chartType == "m":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "D":

            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        else:
            return None

    def __set_request_obj(self, code, chartType, requestAmount):
        """
        通信オブジェクトを初期化する。
        :param code 株コード
        :param chartType: グラフタイプ（'M','W','D','m','T'）
        :param requestAmount: 要請数
        :return: 通信オブジェクト
        """

        pType1 = sg.g_json_creonConfig['StockChart']['要請区分']['type']
        pValue1 = sg.g_json_creonConfig['StockChart']['要請区分']['value']
        pType2 = sg.g_json_creonConfig['StockChart']['要請数']['type']
        pValue2 = requestAmount
        pType3 = sg.g_json_creonConfig['StockChart']['要請内容']['type']
        pValue3 = sg.g_json_creonConfig['StockChart']['要請内容']['内容List']
        pType4 = sg.g_json_creonConfig['StockChart']['Chart区分']['type']
        pValue4 = chartType
        pType5 = sg.g_json_creonConfig['StockChart']['ギャップ補正有無']['type']
        pValue5 = sg.g_json_creonConfig['StockChart']['ギャップ補正有無']['value']
        pType6 = sg.g_json_creonConfig['StockChart']['修正株株価適用有無']['type']
        pValue6 = sg.g_json_creonConfig['StockChart']['修正株株価適用有無']['value']
        pType7 = sg.g_json_creonConfig['StockChart']['取引量区分']['type']
        pValue7 = sg.g_json_creonConfig['StockChart']['取引量区分']['value']

        sg.g_logger.write_log(f"code : {code}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請区分 : {pType1}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請区分value : {pValue1}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請数 : {pType2}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請数value : {pValue2}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請内容 : {pType3}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"要請内容value : {pValue3}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"Chart区分 : {pType4}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"Chart区分value : {pValue4}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"ギャップ補正有無 : {pType5}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"ギャップ補正有無value : {pValue5}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"修正株株価適用有無 : {pType6}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"修正株株価適用有無value : {pValue6}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"取引量区分 : {pType7}", log_lv=1, is_con_print=False)
        sg.g_logger.write_log(f"取引量区分value : {pValue7}", log_lv=1, is_con_print=False)
        # code
        sg.g_cpOhlc.SetInputValue(0, code)
        # 要請区分
        sg.g_cpOhlc.SetInputValue(pType1, ord(pValue1))
        # 全要請数
        sg.g_cpOhlc.SetInputValue(pType2, pValue2)
        # 要請内容
        sg.g_cpOhlc.SetInputValue(pType3, pValue3)
        # 'Chart区分
        sg.g_cpOhlc.SetInputValue(pType4, ord(pValue4))
        # ギャップ補正有無
        sg.g_cpOhlc.SetInputValue(pType5, ord(pValue5))
        # 修正株株価適用有無
        sg.g_cpOhlc.SetInputValue(pType6, ord(pValue6))
        # 取引量区分
        sg.g_cpOhlc.SetInputValue(pType7, ord(pValue7))

        return sg.g_cpOhlc

    def request_chart_day(self, code, amount=MAX_REQUEST_NUM):
        """
        月、週データを取得
        :param code: 株コード
        :param is_all:全日 or 一日
        :return: None
        """
        objStockChart = self.__set_request_obj(code, 'D', amount)
        self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

        curRequestedAmount = objStockChart.GetHeaderValue(3)  # 受信した数
        if curRequestedAmount == 0:
            return None

        sg.g_logger.write_log(f"受信数: {curRequestedAmount}", log_lv=1, is_con_print=False)

        stockDateList = []  # 日付
        stockTimeList = []  # 時間
        stockOpenList = []  # Open
        stockHighList = []  # High
        stockLowList = []  # Low
        stockCloseList = []  # Close
        stockDiffList = []  # Diff
        stockVolumeList = []  # Volume

        for i in range(curRequestedAmount):
            stockDateList.append(objStockChart.GetDataValue(0, i))
            stockTimeList.append(objStockChart.GetDataValue(1, i))
            stockOpenList.append(objStockChart.GetDataValue(2, i))
            stockHighList.append(objStockChart.GetDataValue(3, i))
            stockLowList.append(objStockChart.GetDataValue(4, i))
            stockCloseList.append(objStockChart.GetDataValue(5, i))
            stockDiffList.append(objStockChart.GetDataValue(6, i))
            stockVolumeList.append(objStockChart.GetDataValue(7, i))

        # --------------------------end for----------------------------------------

        result = pd.DataFrame({'date': stockDateList,
                               'time': stockTimeList,
                               'open': stockOpenList,
                               'high': stockHighList,
                               'low': stockLowList,
                               'close': stockCloseList,
                               'diff': stockDiffList,
                               'volume': stockVolumeList,
                               })

        result = self.__transform_data_frame_db(result, "D")
        resent_day = result.iloc[0].date.day
        # ------------DB INSERT--------------
        result_amount = sg.g_db_updater.replace_into_db(code, result, "D")
        # ------------DB INSERT--------------

        return result_amount, resent_day

    def request_chart_type(self, code, amount, chartType='m'):
        """
        月、週、分の全日データを取得
        :param code: 株コード
        :param chartType:'M','W','m'
        :return: None
        """
        objStockChart = self.__set_request_obj(code, chartType, amount)
        resent_min = -1
        requestedAmount = 0  # 受信データ数累計
        while amount > requestedAmount:  # 要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

            curRequestedAmount = objStockChart.GetHeaderValue(3)  # 受信した数
            if curRequestedAmount == 0:
                return None

            sg.g_logger.write_log(f"受信数: {curRequestedAmount}", log_lv=1, is_con_print=False)

            stockDateList = []  # 日付
            stockTimeList = []  # 時間
            stockOpenList = []  # Open
            stockHighList = []  # High
            stockLowList = []  # Low
            stockCloseList = []  # Close
            stockDiffList = []  # Diff
            stockVolumeList = []  # Volume

            for i in range(curRequestedAmount):

                stockDateList.append(objStockChart.GetDataValue(0, i))
                stockTimeList.append(objStockChart.GetDataValue(1, i))
                stockOpenList.append(objStockChart.GetDataValue(2, i))
                stockHighList.append(objStockChart.GetDataValue(3, i))
                stockLowList.append(objStockChart.GetDataValue(4, i))
                stockCloseList.append(objStockChart.GetDataValue(5, i))
                stockDiffList.append(objStockChart.GetDataValue(6, i))
                stockVolumeList.append(objStockChart.GetDataValue(7, i))

            # --------------------------end for----------------------------------------

            result = pd.DataFrame({'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   })

            result = self.__transform_data_frame_db(result, chartType)
            resent_min = result.iloc[0].date.time().minute
            # ------------DB INSERT--------------
            requestedAmount += sg.g_db_updater.replace_into_db(code, result, chartType)
            # ------------DB INSERT--------------
        return requestedAmount, resent_min

    def request_day_chart_type(self, code, day_ago, chartType='m'):
        """
        月、週、分の全日データを取得
        :param code: 株コード
        :param chartType:'M','W','m'
        :return:
        """
        result_amount = 0
        resent_min = 0
        amount = 5 * ONE_DAY_MIN_AMOUNT
        today = datetime.today().weekday()
        if today == 0:  # 月曜日の場合、当日のみ取得する。
            day_ago = 0

        ago_date = datetime.today() - timedelta(days=day_ago)
        ago_date_start = ago_date.replace(hour=9, minute=1, second=0, microsecond=0)
        # ago_date_start_str = ago_date_start.strftime("%Y-%m-%d %H:%M:%S")

        objStockChart = self.__set_request_obj(code, chartType, amount)


        is_not_end = True
        while is_not_end:  # 要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

            curRequestedAmount = objStockChart.GetHeaderValue(3)  # 受信した数
            if curRequestedAmount == 0:
                return None

            sg.g_logger.write_log(f"受信数: {curRequestedAmount}", log_lv=1, is_con_print=False)

            stockDateList = []  # 日付
            stockTimeList = []  # 時間
            stockOpenList = []  # Open
            stockHighList = []  # High
            stockLowList = []  # Low
            stockCloseList = []  # Close
            stockDiffList = []  # Diff
            stockVolumeList = []  # Volume

            for i in range(curRequestedAmount):

                stockDateList.append(objStockChart.GetDataValue(0, i))
                stockTimeList.append(objStockChart.GetDataValue(1, i))
                stockOpenList.append(objStockChart.GetDataValue(2, i))
                stockHighList.append(objStockChart.GetDataValue(3, i))
                stockLowList.append(objStockChart.GetDataValue(4, i))
                stockCloseList.append(objStockChart.GetDataValue(5, i))
                stockDiffList.append(objStockChart.GetDataValue(6, i))
                stockVolumeList.append(objStockChart.GetDataValue(7, i))

            # --------------------------end for----------------------------------------

            result = pd.DataFrame({'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   })

            result = self.__transform_data_frame_db(result, chartType)

            for row in result.itertuples():
                if ago_date_start == row[1]:
                    result = result[:(row[0]+1)]
                    is_not_end = False  # while exit
                    break

            if is_not_end is True:
                return None
            else:
                resent_min = result.iloc[0].date.time().minute
                # ------------DB INSERT--------------
                result_amount = sg.g_db_updater.replace_into_db(code, result, chartType)
                # ------------DB INSERT--------------

        return result_amount, resent_min

    def request_stock_info(self):
        """
        株の情報を取得する
        :return:(pandas.DataFrame) 株情報
        """
        stockCodeList = []
        stockNameList = []

        # 株式コードリスト取得
        stockList1 = sg.g_cpCodeMgr.GetStockListByMarket(1)  # 取引マーケット
        stockList2 = sg.g_cpCodeMgr.GetStockListByMarket(2)  # KOSDAQ(コスダック)
        lenStockInfo = len(stockList1) + len(stockList2)

        for i, code in enumerate(stockList1):
            # secondCode = sg.g_cpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            # stdPrice = sg.g_cpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = sg.g_cpCodeMgr.CodeToName(code)  # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            sg.g_logger.write_log(f"code : {code} // company : {name}", log_lv=1, is_con_print=False)

        for i, code in enumerate(stockList2):
            # secondCode = sg.g_cpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            # stdPrice = sg.g_cpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = sg.g_cpCodeMgr.CodeToName(code)  # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            sg.g_logger.write_log(f"code : {code} // company : {name}", log_lv=1, is_con_print=False)

        dfStockInfo = pd.DataFrame({'code': stockCodeList,
                                    'company': stockNameList},
                                   index=[i for i in range(1, lenStockInfo + 1)])

        # ------------DB INSERT--------------
        sg.g_db_updater.update_stock_info(dfStockInfo=dfStockInfo)
        # ------------DB INSERT--------------

        return dfStockInfo

    # def split_df_stock(self, dfStockInfo, threadAmount):
    #     """
    #     thread数で株データframeを分ける
    #     :param dfStockInfo: データframe
    #     :param threadAmount: thread数
    #     :return: 分けたデータframe
    #     """
    #
    #
    #     thread_num = self.__thread_num
    #     splitAmount = (int)(dfStockInfo.shape[0] / threadAmount)
    #
    #     if thread_num == 1:
    #         result = dfStockInfo[:splitAmount]
    #     elif thread_num == threadAmount:
    #         result = dfStockInfo[(thread_num - 1) * splitAmount:]
    #     else:
    #         result = dfStockInfo[(thread_num - 1) * splitAmount:(thread_num) * splitAmount]
    #
    #     return result

    def get_current_price(self, code):
        self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
        """인자로 받은 종목의 현재가, 매수호가, 매도호가를 반환한다."""
        sg.g_cpStock.SetInputValue(0, code)  # 종목코드에 대한 가격 정보
        sg.g_cpStock.BlockRequest()
        item = {}
        item['cur_price'] = sg.g_cpStock.GetHeaderValue(11)  # 현재가
        item['ask'] = sg.g_cpStock.GetHeaderValue(16)  # 매수호가
        item['bid'] = sg.g_cpStock.GetHeaderValue(17)  # 매도호가
        return item['cur_price'], item['ask'], item['bid']

    # 최유리 IOC 매수
    def buy_stock(self, code, money):
        try:
            current_price, ask_price, bid_price = self.get_current_price(code)

            buy_qty = 0  # 매수할 수량 초기화
            if ask_price > 0:  # 매수호가가 존재하면
                buy_qty = money // ask_price
                if buy_qty == 0:
                    sg.g_logger.write_log(f"돈이 부족해서 1주도 못삼. 쓸돈:{money} / 매수호가:{ask_price}", log_lv=2, is_slacker=False)
                    return False
            else:
                sg.g_logger.write_log(f"매수호가 없음:{ask_price}", log_lv=2, is_slacker=False)
                return False

            sg.g_cpTradeUtil.TradeInit()
            acc = sg.g_cpTradeUtil.AccountNumber[0]  # 계좌번호
            accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체,1:주식,2:선물/옵션
            # 최유리 FOK 매수 주문 설정
            sg.g_cpOrder.SetInputValue(0, "2")  # 2: 매수
            sg.g_cpOrder.SetInputValue(1, acc)  # 계좌번호
            sg.g_cpOrder.SetInputValue(2, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
            sg.g_cpOrder.SetInputValue(3, code)  # 종목코드
            sg.g_cpOrder.SetInputValue(4, buy_qty)  # 매수할 수량
            sg.g_cpOrder.SetInputValue(7, "1")  # 주문조건 0:기본, 1:IOC, 2:FOK
            sg.g_cpOrder.SetInputValue(8, "12")  # 주문호가 1:보통, 3:시장가
            # 5:조건부, 12:최유리, 13:최우선
            self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            # 매수 주문 요청
            sg.g_cpOrder.BlockRequest()
            time.sleep(2)

            bought_stocks = self.get_bought_stock_list()
            for stock in bought_stocks:
                if stock['code'] == code:
                    sg.g_logger.write_log(f"注文結果 \n"
                                          f"【{str(stock['name'])}】"
                                          f" : "
                                          f"【{(ask_price):,.0f}"
                                          f" * "
                                          f"{str(stock['qty'])}】株\n"
                                          f"【{(money):,.0f}】won\n"
                                          f"を買いました。", log_lv=2, is_slacker=True)
                    return True

        except Exception as ex:
            sg.g_logger.write_log(f"buy_stock("
                                  f"{str(code)}"
                                  f") -> exception! "
                                  f"{str(ex)}", log_lv=5, is_slacker=False)

    # 최유리 IOC 매수 매도
    def sell_stock(self, code):
        try:
            sg.g_cpTradeUtil.TradeInit()
            acc = sg.g_cpTradeUtil.AccountNumber[0]  # 계좌번호
            accFlag = sg.g_cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
            while True:
                stock_info = self.get_bought_stock_info(code)

                if stock_info is None:
                    return True
                else:
                    sg.g_cpOrder.SetInputValue(0, "1")  # 1:매도, 2:매수
                    sg.g_cpOrder.SetInputValue(1, acc)  # 계좌번호
                    sg.g_cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                    sg.g_cpOrder.SetInputValue(3, stock_info['code'])  # 종목코드
                    sg.g_cpOrder.SetInputValue(4, stock_info['qty'])  # 매도수량
                    sg.g_cpOrder.SetInputValue(7, "1")  # 조건 0:기본, 1:IOC, 2:FOK
                    sg.g_cpOrder.SetInputValue(8, "12")  # 호가 12:최유리, 13:최우선
                    self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
                    # 최유리 IOC 매도 주문 요청
                    sg.g_cpOrder.BlockRequest()
                time.sleep(2)

        except Exception as ex:
            sg.g_logger.write_log(f"sell_all() -> exception! "
                                  f"{str(ex)}", log_lv=5, is_slacker=False)