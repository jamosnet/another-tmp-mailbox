import requests
import secrets
import string
import time
import json
import random
from datetime import datetime
from uuid import uuid4

class TempEmailAPI:
    def __init__(self, base_url, domains):
        self.base_url = base_url
        self.domains = domains
        self.uuid = ""
        self.email = ""
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            # "Cookie": "uuid=db048be5",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Content-Length": "0"
        }

    def generate_random_string(self, length):
        letters = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(letters) for _ in range(length))
        return random_string.lower()

    def get_email_address(self, name='', domain=''):
        if domain == '':
            domain = random.choice(self.domains)
        if name == '':
            name = uuid4().hex[::4]

        url = f'{self.base_url}/user/'
        self.headers['Cookie'] = f"uuid={name}"
        response = requests.post(url, headers=self.headers )
        print("POST 请求成功！", response.text,self.headers)
        self.uuid = ''
        if response.status_code == 200:
            #print("POST 请求成功！", response.text)
            self.uuid = response.json()['uuid']
            self.email = f"{self.uuid}@{domain}"
            return self.email
        else:
            print(f"获取邮件地址失败，状态码：{response.status_code}")
            return None

    def get_email_content(self, timeout=120):
        url = f'{self.base_url}/mail/{self.uuid}'
        for i in range((timeout // 10) + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                data = response.json()
                if len(data) > 0:
                    # print(data['results'])
                    return data
                    break
                time.sleep(10)
            except Exception as e:
                pass

        print("请求超时")
        return None

    def delete_email_address(self, email=''):
        url = f'{self.base_url}/user/{self.uuid}'
        response = requests.delete(url)
        if response.status_code == 200:
            print(response.text)
            print("删除邮件地址成功")
        else:
            print(f"删除邮件地址失败，状态码：{response.status_code}")


if __name__ == "__main__":
    # 创建一个 EmailAPIWrapper 实例
    wrapper = TempEmailAPI("http://127.0.0.1:8888", ["aa.com", "bb.com"])

    print("当前时分秒:", datetime.now().strftime("%H:%M:%S"))
    # 获取邮件地址
    email_address = wrapper.get_email_address()
    if email_address:
        print("获取到的邮件地址：", email_address)

    # 获取邮件内容
    if email_address:
        email_content = wrapper.get_email_content(30)
        if email_content:
            print("获取到的邮件内容：", email_content)

    # 删除邮件地址
    if email_address:
        wrapper.delete_email_address(email_address)

    print("当前时分秒:", datetime.now().strftime("%H:%M:%S"))


'''

import os
from datetime import datetime

import tempmailbox

# 创建一个 EmailAPIWrapper 实例
wrapper = tempmailbox.TempEmailAPI("http://127.0.0.1:8888", ["aa.com", "bb.com"])

print("当前时分秒:", datetime.now().strftime("%H:%M:%S"))
# 获取邮件地址
email_address = wrapper.get_email_address()
if email_address:
    print("获取到的邮件地址：", email_address)

    content = wrapper.get_email_content(60)
    print( content )
    
    wrapper.delete_email_address()




'''