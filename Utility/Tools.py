from itertools import combinations
import numpy as np
import json
from InitGlobal import stock_global as sg
import win32gui, win32con
import re
SC_MONITORPOWER = 0xF170

def get_stock_combination(target_list, split_target_list, combi_r):
    """
    listをsplit_target_list数に分けて、分けたリストでcombi_r数分抽出の全場合の数をリターンする。
    :param target_list:ターゲットリスト
    :param split_target_list:リスト分割数
    :param combi_r:分割リストから何個抽出するか
    :return:全場合の数 List[tuple]
    """

    stock_list = list(np.array_split(target_list, split_target_list))
    combination_list = []
    for tmp_list in stock_list:
        combination_list.append(list(combinations(tmp_list, combi_r)))

    return combination_list

def json_clean(path, path2):
    null_json = {path2:{}}
    with open(path, 'w', encoding='utf-8') as clean_json:
        json.dump(null_json, clean_json, indent="\t")

def write_json(path, path2, naiyou):
    try:
        if type(naiyou) is not dict:
            print(f"naiyouはdict typeを使ってください。 type:{type(naiyou)}")
            return

        with open(path, 'r', encoding='utf-8') as my_read_json:
            open_json = json.load(my_read_json)
            update_json = open_json[path2]
            update_json.update(**naiyou)
            open_json[path2] = update_json

        with open(path, 'w', encoding='utf-8') as my_write_json:
            json.dump(open_json, my_write_json, indent="\t", ensure_ascii=False)

    except FileNotFoundError as e:
        sg.g_logger.write_log(f"{path}ファイルを見つかりません。 {str(e)}", log_lv=3)

    except Exception as e:
        sg.g_logger.write_log(f"Exception occured : {str(e)}", log_lv=5)

def powersave():
    # wmic = wmi.WMI()
    # Put the monitor to Off.
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND, SC_MONITORPOWER, 2)
    # Get the monitor states
    # print([monitor.Availability for monitor in wmic.Win32_DesktopMonitor()])
    sg.g_logger.write_log(f"ディスプレイ電源をオフにします", log_lv=2, is_slacker=True)

def date_normalization(date):
    """
    年月日をDBで使える形に正規化する。(YYYY-MM-DD)
    :param date: "4桁の年に"
    :return: 正常：正規化した日付(string) 、異常：None
    """
    if type(date) is not str:
        return date

    date_split = re.split('\D+', date)
    if date[0] == '':
        date_split = date_split[1:]
    year = int(date_split[0])
    month = int(date_split[1])
    day = int(date_split[2])
    if year < 1900 or year > 2200:
        sg.g_logger.write_log(f"ValueError: start_year({year:d}) is wrong.", log_lv=3)
        return
    if month < 1 or month > 12:
        sg.g_logger.write_log(f"ValueError: start_month({month:d}) is wrong.", log_lv=3)
        return
    if day < 1 or day > 31:
        sg.g_logger.write_log(f"ValueError: start_day({day:d}) is wrong.", log_lv=3)
        return
    normal_date = f"{year:04d}-{month:02d}-{day:02d}"
    return normal_date
