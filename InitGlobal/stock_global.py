import win32com.client
import pymysql
from socket import gethostname
from Logging import MyLogging as mylog
from StockDB import DBUpdater as dbu
from StockDB import MarketDB as md
from Creon import CreonLogin as cl
from Creon import Creon as co
from Trading import ElderTradeSystem as ets
from datetime import datetime
import json

global g_json_logging
global g_json_creonConfig
global g_json_update_price_stock_config
global g_json_sql
global g_json_dbInfo
global g_json_trade_stock_list
global g_json_trading_config
global g_json_back_test_csv
global g_json_slacker_info
global g_symbol_list
global g_logger
global g_creon
global g_ets
global g_market_db
global g_creon_login
global g_bought_short_list
global g_buy_amount
global g_exception_slacker
global g_day_start_pure_money
global g_day_start_assets_money
global g_buy_auto_stock_count_short

global g_cpStockCode
global g_cpStatus
global g_cpTradeUtil
global g_cpStock
global g_cpOhlc
global g_cpBalance
global g_cpCash
global g_cpOrder
global g_cpCodeMgr
global g_path_update_price_stock_config_json
global g_conn
global g_db_updater
# global g_test_data_amount
global g_one_day_data_amount
global g_host_name
global g_t_taiki
global g_t_start
global g_t_buy_end
global g_t_sell_start
global g_t_stock_end
global g_t_stock_end_30
global g_t_0

def init_json():
    try:
        with open("..\\..\\stockauto\\MyJson\\logging.json",      'r', encoding='utf-8') as logging_json, \
             open("..\\..\\stockauto\\MyJson\\creonConfig.json",  'r', encoding='utf-8') as creonConfig_json, \
             open("..\\..\\stockauto\\MyJson\\update_price_stock_config.json", 'r', encoding='utf-8') as update_price_stock_config_json, \
             open("..\\..\\stockauto\\MyJson\\sql.json", 'r', encoding='utf-8') as sql_json, \
             open("..\\..\\stockauto\\MyJson\\dbInfo.json", 'r', encoding='utf-8') as dbInfo_json, \
             open("..\\..\\stockauto\\MyJson\\trade_stock_list.json", 'r', encoding='utf-8') as trade_stock_list_json, \
             open("..\\..\\stockauto\\MyJson\\trading_config.json", 'r', encoding='utf-8') as trading_config_json, \
             open("..\\..\\stockauto\\MyJson\\back_test_csv.json", 'r', encoding='utf-8') as back_test_csv_json, \
             open("..\\..\\stockauto\\MyJson\\slacker_info.json", 'r', encoding='utf-8') as slacker_info_json:
            global g_json_logging
            global g_json_creonConfig
            global g_json_update_price_stock_config
            global g_json_sql
            global g_json_dbInfo
            global g_json_trade_stock_list
            global g_json_trading_config
            global g_json_back_test_csv
            global g_json_slacker_info
            global g_symbol_list
            global g_buy_auto_stock_count_short

            g_json_logging = json.load(logging_json)
            g_json_creonConfig = json.load(creonConfig_json)
            g_json_update_price_stock_config = json.load(update_price_stock_config_json)
            g_json_sql = json.load(sql_json)
            g_json_dbInfo = json.load(dbInfo_json)
            g_json_trade_stock_list = json.load(trade_stock_list_json)
            g_json_trading_config = json.load(trading_config_json)
            g_json_back_test_csv = json.load(back_test_csv_json)
            g_json_slacker_info = json.load(slacker_info_json)
            g_symbol_list = g_json_trade_stock_list['trade_stock']['symbol_list']
            g_buy_auto_stock_count_short = g_json_trading_config['buy_auto_stock_count_short']  # 매수할 종목 수

            print("init_json end")

    except FileNotFoundError as e:
        print(f"LoadJson jsonファイルを見つかりません。 {str(e)}")
        # self.__logger.error(f"\\StockBot\\Logging\\logging.jsonファイルを見つかりません。: {str(e)}")

    except Exception as e:
        print(f"Exception occured LoadJson __init__ : {str(e)}")

def init_global():
    try:
        init_json()
        global g_logger
        global g_conn
        global g_db_updater
        global g_market_db
        global g_creon_login
        global g_creon
        global g_ets
        global g_bought_short_list # 구매한 단타 개수
        global g_buy_amount
        global g_exception_slacker
        global g_path_update_price_stock_config_json
        # global g_test_data_amount
        global g_one_day_data_amount
        global g_day_start_pure_money
        global g_day_start_assets_money
        global g_host_name
        global g_t_taiki
        global g_t_start
        global g_t_buy_end
        global g_t_sell_start
        global g_t_stock_end
        global g_t_stock_end_30
        global g_t_0

        g_logger = mylog.MyLogging()
        # =============================================
        host = g_json_dbInfo['host']
        user = g_json_dbInfo['user']
        password = g_json_dbInfo['password']
        dbName = g_json_dbInfo['db']
        charset = g_json_dbInfo['charset']
        g_conn = pymysql.connect(host=host, user=user, password=password, db=dbName, charset=charset)

        g_db_updater = dbu.DBUpdater()
        g_market_db = md.MarketDB()
        g_creon_login = cl.CreonLogin()
        g_creon = co.Creon()
        g_ets = ets.ElderTradeSystem()
        # =============================================
        g_bought_short_list = []
        g_buy_amount = 0  # 단타 항목당 구매가능 금액
        g_exception_slacker = 5
        g_day_start_pure_money = 0
        g_day_start_assets_money = 0
        g_path_update_price_stock_config_json ="..\\..\\stockauto\\MyJson\\update_price_stock_config.json"
        g_one_day_data_amount = 381
        g_host_name = gethostname()
        # g_test_data_amount = g_one_day_data_amount * 5
        # =============================================
        g_t_0 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        g_t_taiki = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        g_t_start = datetime.now().replace(hour=9, minute=5, second=0, microsecond=0)
        g_t_buy_end = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        g_t_sell_start = datetime.now().replace(hour=15, minute=15, second=0, microsecond=0)
        g_t_stock_end = datetime.now().replace(hour=15, minute=20, second=0, microsecond=0)
        g_t_stock_end_30 = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        # =============================================
        if g_host_name == host:
            init_win32com_client()

        print("stock_global init end")

    except FileNotFoundError as e:
        print(f"LoadJson jsonファイルを見つかりません。 {str(e)}")
        # self.__logger.error(f"\\StockBot\\Logging\\logging.jsonファイルを見つかりません。: {str(e)}")

    except Exception as e:
        print(f"Exception occured LoadJson __init__ : {str(e)}")

def init_win32com_client():
# Creonにログイン状態で呼ぶこと。

    global g_cpStockCode
    global g_cpStatus
    global g_cpTradeUtil
    global g_cpStock
    global g_cpOhlc
    global g_cpBalance
    global g_cpCash
    global g_cpOrder
    global g_cpCodeMgr

    g_cpStockCode = win32com.client.Dispatch('CpUtil.CpStockCode')
    g_cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
    g_cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
    g_cpStock = win32com.client.Dispatch('DsCbo1.StockMst')
    g_cpOhlc = win32com.client.Dispatch('CpSysDib.StockChart')
    g_cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
    g_cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
    g_cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')
    g_cpCodeMgr = win32com.client.Dispatch('CpUtil.CpCodeMgr')