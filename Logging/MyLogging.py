import logging.handlers
from requests import get
from InitGlobal import stock_global as sg
from datetime import datetime
from Slacker import Slacker_Message as sm

class MyLogging:
    def __init__(self):
        """
        :param class_name: 呼び出すクラスの名前（class.__name__）
        """
        try:
            self.__set_logger()

        except Exception as e:
            print(f"Exception occured MyLogging __init__ : {str(e)}")

    def __set_logger(self):
        """
        Logging初期化
        使うためにはlogging.jsonファイルに"[クラス名]"で定義が必要です。
        :return:
        """
        try:
            self.__logger = logging.getLogger('logInfo')
            self.__logger.setLevel(logging.DEBUG)
            timeFH = logging.handlers.TimedRotatingFileHandler(
                filename=sg.g_json_logging['logInfo']['logFileNameArray'],
                interval=1, backupCount=30, encoding='utf-8', when='MIDNIGHT')
            timeFH.setLevel(sg.g_json_logging['logInfo']['logLevel']['SET_VALUE'])
            timeFH.setFormatter(logging.Formatter(sg.g_json_logging['formatters']['logFileFormatter']['format']))
            self.__logger.addHandler(timeFH)

        except Exception as e:
            print(f"Exception occured MyLogging __set_logger : 【{str(e)}】")


    def write_log(self, naiyou, log_lv, is_slacker=False, is_con_print=True):
        """
        logを記録する。
        :param naiyou: 記録内容
        :param log_lv: 2:info, 3:warning, 4:error, 5:critical, その他:debug
        :return:
        """
        tmp = f"log内容：\n【{naiyou}】"

        if log_lv == 1:
            self.__logger.debug(tmp)
        elif log_lv == 2:
            self.__logger.info(tmp)
        elif log_lv == 3:
            self.__logger.warning(tmp)
        elif log_lv == 4:
            self.__logger.error(tmp)
        elif log_lv == 5:
            ip = get("https://api.ipify.org").text
            tmp = tmp + f"\r\nMy public IP address : {ip}"
            self.__logger.critical(tmp)
        else:
            self.__logger.debug(tmp)

        if is_slacker is True:
            sm.post_message(tmp)

        if is_con_print is True:
            tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
            print(f"【{tmnow}】：{tmp}")
