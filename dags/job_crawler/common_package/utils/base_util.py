import json
import os
import sys
import time

from selenium import webdriver

import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '.', 'credentials'))
import data_credential as dc


def get_proxy():
    return requests.get("{}/get/".format(dc.PROXY_ADD)).json().get("proxy")


def delete_proxy(proxy):
    requests.get("{}/delete/?proxy={}".format(dc.PROXY_ADD, proxy))


def generate_cookies(target_job=None):
    driver = webdriver.Chrome()
    driver.get('https://www.zhipin.com/shanghai/')
    time.sleep(60)  # log in manually within 60 seconds
    dict_cookies = driver.get_cookies()
    print(dict_cookies)
    json_cookies = json.dumps(dict_cookies)
    print(json_cookies)
    # sava into local file
    with open("./credentials/cookies_boss%s.json" % ("_for_"+target_job) if target_job else "", "w") as f:
        f.write(json_cookies)
    driver.close()


if __name__ == '__main__':
    generate_cookies('device_design_engineer')
