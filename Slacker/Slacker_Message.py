# from slacker import Slacker
import requests
from InitGlobal import stock_global as sg

def post_message(message, channel=None):

    if channel is None:
        channel = sg.g_json_slacker_info['channel_nomal_stock_trading']
    myToken = sg.g_json_slacker_info['myToken']
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+myToken},
        data={"channel": channel,"text": message}
    )
    # print(f"doge message : {response}")