import pandas as pd
import json
from datetime import datetime
from datetime import timedelta
import numpy as np
from InitGlobal import stock_global as sg
from Utility import Tools as tool


class MarketDB:
    def __init__(self):
        try:
            """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
            self.__codes = {}
            self.__get_comp_info()

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured MarketDB init : {str(e)}", log_lv=5)

    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        sg.g_conn.close()

    def __get_comp_info(self):
        """company_info 테이블에서 읽어와서 codes에 저장"""
        krx = pd.read_sql(sg.g_json_sql['SELECT_001'], sg.g_conn)
        for idx in range(len(krx)):
            self.__codes[krx['code'].values[idx]] = krx['company'].values[idx]
        self.__codes_keys = list(self.__codes.keys())
        self.__codes_values = list(self.__codes.values())

    # def __index_to_datetime(self, df):
    #     """dataframeのインデックスをdatetime64[ns]型にする
    #         - df : daily_priceテーブルからselect結果のdataframe
    #     """
    #     df['date'] = pd.to_datetime(df['date'])
    #     df.set_index('date', inplace=True)
    #     df['date'] = df.index
    #
    #     if 'week' in df.columns:
    #         df = df[['code', 'date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
    #     else:
    #         df = df[['code', 'date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
    #
    #     return df

    def __set_search_default(self, chart_type):
        """
        検索をかけるdefault日付を決める
        :param chart_type: Chart区分("D","W","M","m")
        :return: タプル（sql,start_date） 異常:None
        """

        if chart_type == "D":
            sql = 'SELECT_004'
            start_date = datetime.today() - timedelta(days=365)
            is_sort = False
            method_name = 'section_daily_day_all'
        elif chart_type == "m":
            sql = 'SELECT_005'
            start_date = datetime.today() - timedelta(days=7)
            is_sort = False
            method_name = 'section_m'
        elif chart_type == "M":
            sql = 'SELECT_006'
            start_date = datetime.today() - timedelta(days=365 * 30)
            is_sort = False
            method_name = 'section_M'
        elif chart_type == "T":
            sql = 'SELECT_007'
            start_date = datetime.today() - timedelta(days=1)
            is_sort = False
            method_name = 'section_T'
        elif chart_type == "W":
            sql = 'SELECT_008'
            start_date = datetime.today() - timedelta(days=365 * 10)
            is_sort = True
            method_name = 'section_W'
        else:
            sg.g_logger.write_log(f"ValueError: chart_type({chart_type}) doesn't exist.", log_lv=3)
            return None
        # sg.g_logger.write_log(f"start_date is initialized to {start_date.strftime('%Y-%m-%d %H:%M:%S')}", log_lv=1)
        return sql, start_date, is_sort, method_name

    # def __df_week_sort(self, df):
    #     """
    #     date,weekを昇順に整列する。
    #     :param df: 整列対象のデータプライム
    #     :return: 正常：dataframe、異常：None
    #     """
    #     if df is None:
    #         return None
    #     if 'week' in df.columns and 'date' in df.columns:
    #         df = df.sort_values(['date', 'week'])
    #         df = df.reset_index(drop=True)
    #     else:
    #         sg.g_logger.write_log(f"up_downカラムが無いので、株価チェックできない。", log_lv=3)
    #         return None
    #
    #     return df

    def check_stock_price(self, stock_name, chart_type, df):
        """
        株価をチェックする。
        株価分割、株価併合が発生したか
        :param stock_name: 株名前
        :param chart_type: Chart区分("D","W","M","m")
        :param df: stock dataframe
        :return: True:株価正常 False:株価分割併合発生 None:異常
        """
        if df is None:
            return None
        if 'up_down' in df.columns:
            for row in df.itertuples(name='stock'):
                if np.absolute(row.up_down) > 30:  # 変化率30％超えたか
                    stock_code = self.get_stock_code(stock_name=stock_name)
                    if stock_code is None:
                        sg.g_logger.write_log(f"株価異常です。株名前：{stock_name} "
                                              f"内容：【{row}】"
                                              f"/ json追記失敗（株名前異常）", log_lv=4)
                        return False
                    try:
                        with open(sg.g_path_update_price_stock_config_json, 'r', encoding='utf-8') as upsc_json:
                            upsc = json.load(upsc_json)
                            def_val = self.__set_search_default(chart_type=chart_type)
                            method_name = def_val[3]
                            update_stock_list = upsc[method_name]['update_stock_list']
                            update_stock_list.append(stock_code)
                            upsc[method_name]['update_stock_list'] = update_stock_list

                        with open(sg.g_path_update_price_stock_config_json, 'w', encoding='utf-8') as w_upsc_json:
                            json.dump(upsc, w_upsc_json, indent="\t")
                            sg.g_logger.write_log(f"株価異常です。株名前：{stock_name} "
                                                    f"内容：【{row}】"
                                                    f"json追記完了", log_lv=3)
                            return False
                    except FileNotFoundError as e:
                        sg.g_logger.write_log(f"update_price_stock_configファイルを見つかりません。 {str(e)}", log_lv=4)

                    except Exception as e:
                        sg.g_logger.write_log(f"Exception occured check_stock_price : {str(e)}", log_lv=5)
                        return False
            # sg.g_logger.write_log(f"株価正常 株名前：{stock_name}、chart区分：{chart_type}", log_lv=1)
            return True
        else:
            sg.g_logger.write_log(f"up_downカラムが無いので、株価チェックできない。", log_lv=3)
            return None

    def get_stock_name(self, stock_code):
        """
        株の名前で株コードを取得する。
        :param stock_code: 株のcode - A005930
        :return: 正常：株コード(string) or 異常：None
        """
        if stock_code in self.__codes_keys:
            idx = self.__codes_keys.index(stock_code)
            stock_name = self.__codes_values[idx]
            return stock_name
        elif stock_code in self.__codes_values:
            return stock_code
        else:
            sg.g_logger.write_log(f"ValueError: stock_code({stock_code}) doesn't exist.", log_lv=3)
            return None

    def get_stock_code(self, stock_name):
        """
        株の名前で株コードを取得する。
        :param stock_name: 株のハングル名前
        :return: 正常：株コード(string) or 異常：None
        """
        if stock_name in self.__codes_keys:
            return stock_name
        elif stock_name in self.__codes_values:
            idx = self.__codes_values.index(stock_name)
            code = self.__codes_keys[idx]
        else:
            sg.g_logger.write_log(f"ValueError: stock_name({stock_name}) doesn't exist.", log_lv=3)
            return None
        return code

    def get_stock_info_all(self):
        return self.__codes

    def add_diff(self, df):
        """
        diffカラムを追加＆更新する。closeカラムが必要です。
        :param df: 株価データプライム
        :return: 株価データプライム（dataframe） 異常：None
        """
        if df is None:
            return None
        if 'close' in df.columns:
            df['diff'] = df['close'].diff(1).fillna(0).astype(int)
        else:
            sg.g_logger.write_log(f"カラム（close）が無い", log_lv=3)
            return None

        return df

    def add_up_down(self, df):
        """
        up_downカラムを追加＆更新する。close,diffカラムが必要です。
        :param df: 株価データプライム
        :return: 株価データプライム（dataframe） 異常：None
        """

        try:
            if df is None or (len(df) == 0):
                return None
            if 'close' in df.columns and 'diff' in df.columns:
                diff_val = df['diff'].values
                close_val = df['close'].values
                if diff_val.shape == close_val.shape:
                    diff_val = np.roll(diff_val, -1)  # 1個ずらす。
                    up_down_ndarray = ((diff_val / close_val) * 100).round(1)  # 上がり下がり%値
                    up_down_ndarray = np.roll(up_down_ndarray, 1)  # ずらしたことを元通りにする。
                    up_down_ndarray[0] = 0.0
                    df['up_down'] = up_down_ndarray
                else:
                    sg.g_logger.write_log(f"shapeが合わないため、分けられません。"
                                            f"diffのshape{diff_val.shape},"
                                            f"closeのshape{close_val.shape}", log_lv=3)
                    return None
            else:
                sg.g_logger.write_log(f"カラム（close, diff）が無い", log_lv=3)
                return None

            return df

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured check_stock_price : {str(e)}", log_lv=5)
            sg.g_logger.write_log(f"Exception occured check_stock_price : {str(df)}", log_lv=5)
            return None

    def get_past_stock_price(self, code, day_ago, chart_type="m"):
        """
        株価を取得する。
        :param code: 株コードまたは株の名前
        :param chart_type: Chart区分("D","W","M","m") デフォルト値："D"
        :param start_date: 検索スタート日　デフォルト：本日から1年前 (※4桁年)
        :param end_date: 検索End日　デフォルト：本日 (※4桁年)
        :return: dataframe
        """
        def_val = self.__set_search_default(chart_type=chart_type)
        sql_str = def_val[0]
        # is_sort = def_val[2]

        ago_date = datetime.today() - timedelta(days=day_ago)
        ago_date_start = ago_date.replace(hour=9, minute=1, second=0, microsecond=0)
        end_date = datetime.today() - timedelta(days=0)
        ago_date_end = end_date.replace(hour=15, minute=30, second=0, microsecond=0)

        if code in self.__codes_keys:
            pass
        else:
            code = self.get_stock_code(stock_name=code)

        df = pd.read_sql(sg.g_json_sql[sql_str].format(code, ago_date_start, ago_date_end), sg.g_conn)
        df = self.add_up_down(df)
        check_result = self.check_stock_price(stock_name=code, chart_type=chart_type, df=df)

        if check_result is None:
            sg.g_logger.write_log(f"株価取得異常発生", log_lv=4)
            return None
        elif check_result is False:
            sg.g_logger.write_log(f"株コード：{code}は分割または併合発生のため、アップデート必要", log_lv=3)
            return None
        else:
            # sg.g_logger.write_log(f"【正常】株コード：{code} / 取得完了。取得件数：{len(df)}", log_lv=1)
            return df

    def get_cur_stock_price(self, code, day_ago, chart_type="m"):
        """
        株価を取得する。
        :param code: 株コードまたは株の名前
        :param chart_type: Chart区分("D","W","M","m") デフォルト値："D"
        :param start_date: 検索スタート日　デフォルト：本日から1年前 (※4桁年)
        :param end_date: 検索End日　デフォルト：本日 (※4桁年)
        :return: dataframe
        """

        if code in self.__codes_keys:
            pass
        else:
            code = self.get_stock_code(stock_name=code)

        df_recent = pd.read_sql(sg.g_json_sql["SELECT_012"].format(code), sg.g_conn)
        start_date = df_recent.date[0] - timedelta(days=day_ago)

        df = pd.read_sql(sg.g_json_sql["SELECT_013"].format(code, start_date), sg.g_conn)
        df = self.add_up_down(df)
        check_result = self.check_stock_price(stock_name=code, chart_type=chart_type, df=df)

        if check_result is None:
            sg.g_logger.write_log(f"株価取得異常発生", log_lv=4)
            return None
        elif check_result is False:
            sg.g_logger.write_log(f"株コード：{code}は分割または併合発生のため、アップデート必要", log_lv=3)
            return None
        else:
            # sg.g_logger.write_log(f"【正常】株コード：{code} / 取得完了。取得件数：{len(df)}", log_lv=1)
            return df

    # def get_stock_close(self, code, start_date=None, end_date=None):
    #     """
    #     start_dateと end_dateの
    #     close株価を取得する。
    #     :param code: 株コードまたは株の名前
    #     :param start_date: 検索スタート日　デフォルト：30日前 (※4桁年)
    #     :param end_date: 検索End日　デフォルト：本日 (※4桁年)
    #     :return: list['code', 'company', 'old_price', 'new_price', 'returns']
    #     """
    #     if start_date is None:
    #         start_date = datetime.today() - timedelta(days=30)
    #
    #     stock_price = self.get_stock_price(code, "D", start_date, end_date)
    #
    #     if stock_price is not None:
    #         stock_code = self.get_stock_code(code)
    #         stock_name = self.__codes[stock_code]
    #         stock_old_price = stock_price.iloc[0]['close']
    #         stock_new_price = stock_price.iloc[len(stock_price) - 1]['close']
    #         stock_returns = (stock_new_price / stock_old_price - 1) * 100
    #
    #         return [stock_code, stock_name, stock_old_price, stock_new_price, stock_returns]
    #
    #     else:
    #         sg.g_logger.write_log(f"【異常】メソッド：【get_stock_close】失敗", log_lv=1)
    #         return None
