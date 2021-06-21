from pywinauto import application
import time
import os, json
import win32com.client
from InitGlobal import stock_global as sg

class CreonLogin:
    def __init__(self):
        try:
            # self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
            sg.g_logger.write_log('CreonLogin init 成功', log_lv=2)

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured CreonLogin init : {str(e)}", log_lv=5, is_slacker=True)

    def check_login_creon(self):
        """
        creonにログインされているか確認
        :return: True:ログイン状態 False:非ログイン状態
        """
        if sg.g_cpStatus.IsConnect == 0:
            sg.g_logger.write_log('creonにログインされていないのでログインします。', log_lv=2)
            return False
        else:
            sg.g_logger.write_log('creon에 이미 로그인 되어있습니다.', log_lv=2)
            return True

    def LoginCreon(self):
        """
        Creonログインする。
        :return:
        """
        try:
            with open('C:\stockauto\MyJson\creonInfo.json', 'r', encoding='utf-8') as creonInfo_json:
                creonInfo = json.load(creonInfo_json)

                os.system('taskkill /IM coStarter* /F /T')
                os.system('taskkill /IM CpStart* /F /T')
                os.system('wmic process where "name like \'%coStarter%\'" call terminate')
                os.system('wmic process where "name like \'%CpStart%\'" call terminate')
                time.sleep(5)

                app = application.Application()
                app.start(f"{creonInfo['path']} /prj:cp /id:{creonInfo['id']} /pwd:{creonInfo['pwd']} /pwdcert:{creonInfo['pwdcert']} /autostart")
                time.sleep(60)
                sg.init_win32com_client()
                sg.g_logger.write_log('Creonログイン完了', log_lv=2, is_slacker=True)

        except FileNotFoundError as e:
            sg.g_logger.write_log(f"C:\\StockBot\\creonInfo.jsonファイルを見つかりません。 {str(e)}", log_lv=4, is_slacker=True)
        except Exception as e:
            sg.g_logger.write_log(f"Exception occured LoginCreon : {str(e)}", log_lv=5, is_slacker=True)