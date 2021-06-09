import sys
sys.path.append('../')
from InitGlobal import stock_global as sg
from Creon import CreonLogin as cl
from Slacker import Slacker_Message as sm
from Trading import AutoTrade as at
from Utility import Tools as tool
import time


if __name__ == '__main__':
    try:
        sg.init_global()
        # =======================================
        sm.post_message("가즈아!!!!!!!!!!!!!(console main start)")
        myCreon = cl.CreonLogin()
        if myCreon.check_login_creon() is False:
            myCreon.LoginCreon()
        time.sleep(30)
        sg.init_win32com_client()
        tool.powersave()  # モニター電源オフ

        # ++++++++++++++++++++++++++++++
        at.update_money()
        # ++++++++++++++++++++++++++++++

        sm.post_message("main end")
        sys.exit(0)

    except Exception as ex:
        sm.post_message(f"console main.py error : {ex}")

else:
    try:
        sg.init_global()
        # =======================================
        sm.post_message("가즈아!!!!!!!!!!!!!(python console main start)")
        myCreon = cl.CreonLogin()
        if myCreon.check_login_creon() is False:
            myCreon.LoginCreon()
        time.sleep(30)
        sg.init_win32com_client()
        tool.powersave()  # モニター電源オフ

        # ++++++++++++++++++++++++++++++
        at.update_money()
        # ++++++++++++++++++++++++++++++

        sm.post_message("main end")
        sys.exit(0)

    except Exception as ex:
        sm.post_message(f"console main.py error : {ex}")