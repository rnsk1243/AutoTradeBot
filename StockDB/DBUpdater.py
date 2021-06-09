import pandas as pd
from datetime import datetime
from InitGlobal import stock_global as sg

class DBUpdater:
    def __init__(self):
        try:
            # self.__logger = sg.g_logger
            # self.__sql = sg.g_json_sql
            # self.__conn = sg.g_conn
            self.__codes = {}  # key:株コード:value:社名

        except FileNotFoundError as e:
            print(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured DBUpdater init : {str(e)}", log_lv=2)

    def update_stock_info(self, dfStockInfo):
        """
        종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장
        株項目一覧をDBに書き込む　
        :param dfStockInfo 株項目DataFrame
        """
        stockInfoNum = len(dfStockInfo)
        with sg.g_conn.cursor() as curs:
            curs.execute(sg.g_json_sql['SELECT_002'])
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                for idx in range(stockInfoNum):
                    code = dfStockInfo.code.values[idx]
                    company = dfStockInfo.company.values[idx]
                    curs.execute(sg.g_json_sql['REPLACE_001'].format(code, company, today))
                    self.__codes[code] = company
                    sg.g_conn.commit()
                sg.g_logger.write_log('株コード commit 完了。', log_lv=2)
            else:
                df = pd.read_sql(sg.g_json_sql['SELECT_001'], sg.g_conn)
                for idx in range(len(df)):
                    self.__codes[df['code'].values[idx]] = df['company'].values[idx]

        sg.g_logger.write_log(f'株情報Update完了。数：【{stockInfoNum}】', log_lv=2)

    def replace_into_db(self, code, df, chartType):
        """
        Creonから取得したChartデータをREPLACE
        :param code: 株式コード(String)
        :param df: DBに入れるデータ(DataFrame)
        :param chartType:(String) Chart区分("D","W","M","m","T")以外の場合Noneをリターンする。
        :return: 件数
        """
        goalAmount = len(df)
        sg.g_logger.write_log(f"DB insert スタート：code:【{code}】、type:【{chartType}】、len:【{goalAmount}】", log_lv=2)
        try:
            with sg.g_conn.cursor() as curs:
                excu_result = 0
                for r in df.itertuples():

                    if chartType == 'T': #tick Chart

                        excu_result += curs.execute(sg.g_json_sql['REPLACE_006'].format(
                            code, r.dailyCount, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'm': #分 Chart

                        excu_result += curs.execute(sg.g_json_sql['REPLACE_005'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'D': #日 Chart

                        excu_result += curs.execute(sg.g_json_sql['REPLACE_004'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'W': #週 Chart

                        excu_result += curs.execute(sg.g_json_sql['REPLACE_003'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'M': #月 Chart

                        excu_result += curs.execute(sg.g_json_sql['REPLACE_002'].format(
                            code, r.date, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    else:
                        sg.g_logger.write_log(f"type:【{chartType}】は扱えません。", log_lv=4)
                        return None
                    sg.g_conn.commit()
                    sg.g_logger.write_log(f"excu_result:【{excu_result}】、type:【{chartType}】、execute:【{r}】", log_lv=1, is_con_print=False)

                return excu_result
                # if goalAmount == excu_result:
                #     sg.g_logger.write_log(f"insert【挿入】。code:【{code}】、type:【{chartType}】、影響がある行数:【{excu_result}】", log_lv=2)
                # else:
                #     sg.g_logger.write_log(f"insert【更新＆挿入】。code:【{code}】、入れようとした行数:【{goalAmount}】、影響がある行数:【{excu_result}】", log_lv=2)

        except Exception as e:
            sg.g_logger.write_log(f"Exception occured __replace_into_db:code:【{code}】、type:【{chartType}】、len:【{goalAmount}】、エラー内容：【{str(e)}】", log_lv=5)
            return None
