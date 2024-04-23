# -*- coding: UTF-8 -*-
"""
API
"""
import json
import os
import time
import re
import json
import sys
import http.cookies
import qrcode
from time import sleep
from urllib import request
from urllib.request import Request as Reqtype
from urllib.parse import urlencode
from urllib.error import HTTPError
from geetest import dealCode
from plyer import notification as trayNotify
import pyperclip # 新增剪贴板功能 By FriendshipEnder 4/19


class Api:
    """
    API操作
    """
    def __init__(self,proxies=None,specificID=None,sleepTime=0.15,token=None):
        self.proxies=proxies
        self.specificID=specificID
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.1.4.514 Safari/537.36",
            "Referer":"https://mall.bilibili.com/",
            "Origin":"https://mall.bilibili.com/",
            "Pregma":"no-cache",
            "Cache-Control":"max-age=0",
            "Upgrade-Insecure-Requests":"1",
            "Sec-Fetch-Site":"none",
            "Sec-Fetch-Mode":"navigate",
            "Sec-Fetch-User":"?1",
            "Sec-Fetch-Dest":"document",
            "Cookie":"a=b;",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "",
            "Connection": "keep-alive"
        }
        self.sleepTime = sleepTime
        self.token = token
        self.start_time = time.time()
        self.user_data = {}
        self.user_data["specificID"] = specificID
        self.user_data["username"] = ""
        self.user_data["project_id"] = ""
        # self.user_data["deliver_info"] = ""
        self.user_data["token"] = ""
        self.appName = "BilibiliShow_AutoOrder"
        self.selectedTicketInfo = "未选择"
        # ALL_USER_DATA_LIST = [""]

    def load_cookie(self):
        if not os.path.exists("user_data.json"):
            t =  open("user_data.json","w")
            t.write("{}")
            t.close
        with open("user_data.json","r") as r:
            try:
                j = json.load(r)
            except:
                r.close()
                print("请重新运行login.py登录一次bilibili, 我和2233娘的关系好像有点生冷了 让我重温一次~")
                t =  open("user_data.json","w")
                t.write("{}")
                t.close()
                self.error_handle("")
            if not len(j):
                print("请先运行目录下的login.py登录一次bilibili, 让我抢票姬可以和2233娘好好沟通一下下~")
                t =  open("user_data.json","w")
                t.write("{}")
                t.close()
                self.error_handle("")
            if self.user_data["specificID"]:
                self.user_data["username"],self.headers["Cookie"] = j[self.user_data["specificID"]][0],j[self.user_data["specificID"]][1]
            else:
                j = j[list(j.keys())[0]]
                self.user_data["username"],self.headers["Cookie"] = j[0],j[1]
            
    def _http(self,url,j=False,data=None,raw=False):
        data = data.encode() if type(data) == type("") else data
        try:
            if self.proxies and data:
                opener = request.build_opener(request.ProxyHandler({'http':self.proxies,'https':self.proxies}))
                res = opener.open(Reqtype(url,headers=self.headers,method="POST",data=data),timeout=200)
            elif self.proxies and not data:
                opener = request.build_opener(request.ProxyHandler({'http':self.proxies,'https':self.proxies}))
                res = opener.open(Reqtype(url,headers=self.headers,method="GET"),timeout=200)
            elif data and not self.proxies:
                res = request.urlopen(Reqtype(url,headers=self.headers,method="POST",data=data),timeout=200)
            else:
                res = request.urlopen(Reqtype(url,headers=self.headers,method="GET"),timeout=200)
        except HTTPError as e:
        #     print("请求超时 请检查网络")
        #     print(e)
        #     self.error_handle("ip可能被风控。请求地址: " + url)
            if e.code == 429:
                print("请求太快, 或许是抢票姬触发蜀黍设定的风控咯! 5秒后重试...")
            else:
                print("HTTP请求响应 {} 错误! 5秒后重试...".format(e.code))
            sleep(5)
        # print(res)
        if res.code != 200:
            self.error_handle("抢票姬的IP地址可能被风控咯，都是蜀黍干的好事!!\n可以换个WiFi或热点试试. 请求地址: " + url)
            sleep(5)
        if j:
            return json.loads(res.read().decode("utf-8","ignore"))
        elif raw:
            return res
        else:
            return res.read().decode("utf-8","ignore")

    def getCSRF(self):
        cookie = http.cookies.BaseCookie()
        cookie.load(self.headers["Cookie"])
        return cookie["bili_jct"].value
    
    def orderInfo(self):
        # 获取目标
        self.user_data["project_id"] = re.search(r"id=\d+",self.menu("GET_SHOW")).group().split("=")[1]
        # print(self.user_data["project_id"])
        # exit(0)
        # 获取订单信息
        url = "https://show.bilibili.com/api/ticket/project/get?version=134&id=" + self.user_data["project_id"] + "&project_id="+ self.user_data["project_id"]
        data = self._http(url,True)
        if not data["data"]:
            print(data)
            return 1
        # print(self.menu("GET_ORDER_IF",data["data"]))
        self.setAuthType(data)
        # print(self.user_data["auth_type"])
        self.user_data["screen_id"],self.user_data["sku_id"],self.user_data["pay_money"] = self.menu("GET_ORDER_IF",data["data"])
        if(data["data"]["has_paper_ticket"]):
            a = self.addressInfo()
            fa = a["prov"]+a["city"]+a["area"]+a["addr"]
            self.user_data["deliver_info"] = {}
            self.user_data["deliver_info"]["name"],self.user_data["deliver_info"]["tel"],self.user_data["deliver_info"]["addr_id"],self.user_data["deliver_info"]["addr"] = a["name"],a["phone"],a["id"],fa

        # print("订单信息获取成功")
    
    def getExpressFee(self):
        url = "https://show.bilibili.com/api/ticket/project/get?version=134&id=" + self.user_data["project_id"] + "&project_id="+ self.user_data["project_id"]
        data = self._http(url,True)
        if not data["data"]:
            print(data)
            return 1
        e = data["data"]["express_fee"]
        if(e == -1 or e == -2):
            return 0
        return e

    def setAuthType(self,data):
        if not data:
            self.error_handle("项目不存在咩")
        self.user_data["auth_type"] = ""
        for _ in data["data"]["performance_desc"]["list"]:
            if _["module"] == "base_info":
                for i in _["details"]:
                    if i["title"] == "实名认证" or i["title"] == "实名登记" or i["title"] == "实名":
                        if "一单一证" in i["content"]:
                            self.user_data["auth_type"] = 1
                        elif "一人一证" in i["content"] or "一人一票" in i["content"]:
                            self.user_data["auth_type"] = 2
                if not self.user_data["auth_type"]:
                    self.user_data["auth_type"] = 0

    def buyerinfo(self):
        if self.user_data["auth_type"] == 0:
            self.user_data["buyer_name"], self.user_data["buyer_phone"] = self.menu("GET_NORMAL_INFO")
            self.user_data["user_count"] = self.menu("GET_T_COUNT")
            return
        # 获取购票人
        url = "https://show.bilibili.com/api/ticket/buyer/list?is_default&projectId=" + self.user_data["project_id"]
        data = self._http(url,True)

        self.user_data["buyer"] = self.menu("GET_ID_INFO", data["data"])
        # print(self.user_data["buyer"])
        # exit(0)
        if self.user_data["auth_type"] == 2:
            self.user_data["user_count"] = len(self.user_data["buyer"])
        else:
            self.user_data["user_count"] = self.menu("GET_T_COUNT")

        for i in range(0, len(self.user_data["buyer"])):
            self.user_data["buyer"][i]["isBuyerInfoVerified"] = "true"
            self.user_data["buyer"][i]["isBuyerValid"] = "true"
       
        # self.user_data["buyer"] = data["data"]["list"]
        # print(self.user_data["buyer"])
        # exit()
        # print("购票人信息获取成功")

    def addressInfo(self):
        url = "https://show.bilibili.com/api/ticket/addr/list"
        data = self._http(url,True)
        if(len(data["data"]["addr_list"])<=0):
            self.error_handle("请先前往会员购地址管理添加收货地址, 你要让老姐电报到你家吗?~")
        if data["errno"] != 0:
            print("[会员购地址管理] 失败信息: " + data["msg"])
            return 1
        n = int(self.menu("GET_ADDRESS_LIST",data["data"]))-1
        return data["data"]["addr_list"][n]
        

    def tokenGet(self):
        # 获取token
        url = "https://show.bilibili.com/api/ticket/order/prepare?project_id=" + self.user_data["project_id"]

        payload = "count=" + str(self.user_data["user_count"]) + "&order_type=1&project_id=" + self.user_data["project_id"] + "&screen_id=" + str(self.user_data["screen_id"]) + "&sku_id=" + str(self.user_data["sku_id"]) + "&token=" + "&newRisk=true"
        # payload = "count=1&order_type=1&project_id=73710&screen_id=134762&sku_id=398405&token="       
        
        data = self._http(url,True,payload)
        
        # R.I.P. 旧滑块验证

        # if not data["data"]:
        #     # self.error_handle("获取token失败")
        #     timestr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + ": "
        #     print(timestr+"失败信息: " + data["msg"])
        #     return 1
        # if data["data"]["shield"]["verifyMethod"]:
        #     with open("url","w") as f:
        #         print("需要验证，正在拉取验证码")
        #         f.write(data["data"]["shield"]["naUrl"])
        #     if self.token:
        #         self.end_time = time.time()
        #         if self.end_time - self.start_time > 60:
        #             print(self.end_time - self.start_time)
        #             self.sendNotification("该拉滑块验证码啦！")
        #             self.start_time = self.end_time            
        # self.user_data["token"] = data["data"]["token"]
        # # print(data)
        # # print(self.user_data["user_count"])
        # print("\n购买Token获取成功")

        if data["errno"] == -401:
            _url = "https://api.bilibili.com/x/gaia-vgate/v1/register"
            _payload = urlencode(data["data"]["ga_data"]["riskParams"])
            _data = self._http(_url,True,_payload)
            gt = _data["data"]["geetest"]["gt"]
            challenge = _data["data"]["geetest"]["challenge"]
            token = _data["data"]["token"]
            print("大人, 请“验证”, 老姐是机器人过不了验证~ (失败请退出重新运行脚本)：")
            with open("url","w") as f:
                f.write("file://"+ os.path.abspath('.') + "/geetest-validator/index.html?gt=" + gt + "&challenge=" + challenge)
                f.close()
            dealCode().mult_work() # 新增自动调用接口  By FriendshipEnder 4/19
            validate = pyperclip.paste() # 剪贴板自动粘贴  By FriendshipEnder 4/19
            seccode = validate + "|jordan"
            csrf=self.getCSRF()
            _url = "https://api.bilibili.com/x/gaia-vgate/v1/validate"
            _payload = {
                "challenge": challenge,
                "token": token,
                "seccode": seccode,
                "csrf": csrf,
                "validate": validate
            }
            # print(_payload)
            _data = self._http(_url,True,urlencode(_payload))
            # print(_data)
            if(_data["code"]==-111):
                self.error_handle("csrf校验失败")
            elif _data["code"] == 0:
                print("[极验GeeTest认证] 老姐成功啦, 继续充满活力的帮你抢票咯。")
                return 0
            elif _data["code"]==100001:
                self.error_handle("验证码校验失败。")
            else:
                self.error_handle("极验GeeTest验证失败。")
        else:
            if not data["data"]:
                timestr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + ": "
                print("{}失败信息[{}]: {}".format(timestr,data["code"],data["msg"]))
                return 1
            if data["data"]["token"]:
                self.user_data["token"] = data["data"]["token"]
        return 0

    def orderCreate(self):
        # 创建订单
        # url = "https://show.bilibili.com/api/ticket/order/createV2?project_id=" + config["projectId"]
        url = "https://show.bilibili.com/api/ticket/order/createV2?project_id=" + self.user_data["project_id"]

        try:
            self.user_data["deliver_info"]
        except KeyError:
            if self.user_data["auth_type"] == 0:
                payload = {
                    "buyer": self.user_data["buyer_name"],
                    "tel": self.user_data["buyer_phone"],
                    "count": self.user_data["user_count"],
                    "deviceId": "",
                    "order_type": 1,
                    "pay_money": int(self.user_data["pay_money"]) * int(self.user_data["user_count"]),
                    "project_id": self.user_data["project_id"],
                    "screen_id": self.user_data["screen_id"],
                    "sku_id": self.user_data["sku_id"],
                    "timestamp": int(round(time.time() * 1000)),
                    "token": self.user_data["token"]
                }
            else:
                payload = {
                    "buyer_info": self.user_data["buyer"],
                    "count": self.user_data["user_count"],
                    "deviceId": "",
                    "order_type": 1,
                    "pay_money": int(self.user_data["pay_money"]) * int(self.user_data["user_count"]),
                    "project_id": self.user_data["project_id"],
                    "screen_id": self.user_data["screen_id"],
                    "sku_id": self.user_data["sku_id"],
                    "timestamp": int(round(time.time() * 1000)),
                    "token": self.user_data["token"]
                }
        else:
            if self.user_data["auth_type"] == 0:
                payload = {
                    "buyer": self.user_data["buyer_name"],
                    "tel": self.user_data["buyer_phone"],
                    "count": self.user_data["user_count"],
                    "deviceId": "",
                    "order_type": 1,
                    "pay_money": int(self.user_data["pay_money"]) * int(self.user_data["user_count"]) + self.getExpressFee(),
                    "project_id": self.user_data["project_id"],
                    "screen_id": self.user_data["screen_id"],
                    "sku_id": self.user_data["sku_id"],
                    "timestamp": int(round(time.time() * 1000)),
                    "token": self.user_data["token"],
                    "deliver_info": json.dumps(self.user_data["deliver_info"],ensure_ascii=0)
                }
            else:
                payload = {
                    "buyer_info": self.user_data["buyer"],
                    "count": self.user_data["user_count"],
                    "deviceId": "",
                    "order_type": 1,
                    "pay_money": int(self.user_data["pay_money"]) * int(self.user_data["user_count"]) + self.getExpressFee(),
                    "project_id": self.user_data["project_id"],
                    "screen_id": self.user_data["screen_id"],
                    "sku_id": self.user_data["sku_id"],
                    "timestamp": int(round(time.time() * 1000)),
                    "token": self.user_data["token"],
                    "deliver_info": json.dumps(self.user_data["deliver_info"],ensure_ascii=0)
                }
        timestr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        print(timestr, end=": ")
        data = self._http(url,True,urlencode(payload).replace("%27true%27","true").replace("%27","%22"))
        if data["errno"] == 0:
            print("老姐成功发现一张票! 立即尝试抢票!")
            if self.checkOrder(data["data"]["token"],data["data"]["orderId"]):
                print("老姐成功把票弄到手, 请在10分钟内完成支付.实际成交时间:"+timestr)
                trayNotifyMessage = timestr+"老姐成功把票弄到手, 请在10分钟内完成支付" + "\n" + "购票人："
                # + thisBuyerInfo + self.selectedTicketInfo + "\n"
                # Add buyer info
                if "buyer_info" in payload:
                    for i in range(0, len(payload["buyer_info"])):
                        if self.user_data["auth_type"] == 0:
                            trayNotifyMessage += ['buyer_info'][i][0] + " "
                        else:
                            trayNotifyMessage += payload['buyer_info'][i]["name"] + " "
                elif "buyer" in payload:
                    trayNotifyMessage += payload["buyer"]
                trayNotifyMessage += "\n" + self.selectedTicketInfo
                # check if trayNotifyMessage is too long
                if len(trayNotifyMessage) > 500:
                    trayNotifyMessage = trayNotifyMessage[:500] + "..."
                self.tray_notify("抢票成功", trayNotifyMessage, "./ico/success.ico", timeout=20)
                if self.token:
                    self.sendNotification(trayNotifyMessage)
                return 1
            else:
                print("糟糕，是张假票(同时锁定一张票，但被其他人抢走了)\n老姐立即重新抢nya~")
                self.tray_notify("抢票失败", "糟糕，是张假票(同时锁定一张票，但被其他人抢走了)\n老姐立即重新抢nya~", "./ico/failed.ico", timeout=8)
        elif data["errno"] == 209002: # 统一格式  By FriendshipEnder 4/19
            print("嗯, 未获取到购买人信息")
        elif "10005" in str(data["errno"]):    # Token过期
            print("嗯, Token已过期! 正在重新获取!")
            self.tokenGet()
        elif data["errno"] == 100009:
            print("唉, 现在暂无余票，请耐心等候。")
        elif data["errno"] == 100001:
            print("嘶, 获取频率过快或无票。")
        else:
            print("呃, 错误信息: ["+ str(data["errno"])+ "]", data["msg"])
            # print(data)
        return 0

    def checkOrder(self,_token,_orderId):
        timestr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+":"
        print(timestr+"啊哈! 老姐帮下单成功！正在检查票务状态...请稍等")
        self.tray_notify("啊哈! 老姐帮下单成功", "正在检查票务状态...请稍等", "./ico/info.ico", timeout=5)
        # sleep(5)
        # url = "https://show.bilibili.com/api/ticket/order/list?page=0&page_size=10"
        # data = self._http(url,True)
        # # print(data)
        # if data["errno"] != 0:
        #     print("检测到网络波动，正在重新检查...")
        #     return self.checkOrder()
        # elif not data["data"]["list"]:
        #     return 0
        # elif data['data']['list'][0]['status'] == 1:
        #     return 1
        # else:
        #     return 0
        url = "https://show.bilibili.com/api/ticket/order/createstatus?token="+_token+"&timestamp="+str(int(round(time.time() * 1000)))+"&project_id="+self.user_data["project_id"]+"&orderId="+str(_orderId)
        data = self._http(url,True)
        if(data["errno"] == 0):
            _qrcode = data["data"]["payParam"]["code_url"]
            print("请使用微信/QQ/支付宝扫描二维码完成支付")
            print("请使用微信/QQ/支付宝扫描二维码完成支付")
            print("请使用微信/QQ/支付宝扫描二维码完成支付")
            qr_gen = qrcode.QRCode()
            qr_gen.add_data(_qrcode)
            qr_gen.print_ascii()
            # print(qrcode)
            return 1
        else:
            return 0

    def error_handle(self,msg):
        print(msg)
        os.system("pause")
        sys.exit(0)

    def menu(self,mtype,data=None):
        if mtype == "GET_SHOW":
            i = input("快点给我购票链接并按回车继续! 抢票姬要帮你抢票啦! 范例https://show.bilibili.com/platform/detail.html?id=73711\n=>").strip()
            if "bilibili" not in i or "id" not in i:
                self.error_handle("网址格式错误")
            return i
        elif mtype == "GET_ORDER_IF":
            print("\n演出名称: " + data["name"])
            print("票务状态: " + data["sale_flag"])
            if data["has_eticket"] == 1:
                print("本演出/展览票面为电子票/兑换票。")
            if data["has_paper_ticket"] == 1:
                print("本演出/展览包含纸质票。")
            print("\n请选择场次序号并按回车继续，格式例如 1")
            for i in range(len(data["screen_list"])):
                print(str(i+1) + ":",data["screen_list"][i]["name"])
            date = input("场次序号 =>").strip()
            try:
                date = int(date) - 1
                if date not in [i for i in range(len(data["screen_list"]))]:
                    self.error_handle("请输入正确序号")
            except:
                self.error_handle("请输入正确数字")
            print("已选择：", data["screen_list"][date]["name"])
            print("\n请输入票种并按回车继续，格式例如 1")
            for i in range(len(data["screen_list"][date]["ticket_list"])):
                print(str(i+1) + ":",data["screen_list"][date]["ticket_list"][i]["desc"],"-",data["screen_list"][date]["ticket_list"][i]["price"]//100,"RMB")
            choice = input("票种序号 =>").strip()
            try:
                choice = int(choice) - 1
                if choice not in [i for i in range(len(data["screen_list"][date]["ticket_list"]))]:
                    self.error_handle("请输入正确序号")
            except:
                self.error_handle("请输入正确数字")
            self.selectedTicketInfo = data["name"] + " " + data["screen_list"][date]["name"] + " " + data["screen_list"][date]["ticket_list"][choice]["desc"]+ " " + str(data["screen_list"][date]["ticket_list"][choice]["price"]//100)+ " " +"RMB"
            print("\n已选择：", self.selectedTicketInfo)
            return data["screen_list"][date]["id"],data["screen_list"][date]["ticket_list"][choice]["id"],data["screen_list"][date]["ticket_list"][choice]["price"]
        elif mtype == "GET_ID_INFO":
            if not data:
                self.error_handle("用户信息为空，请登录或先上传身份信息后重试")
            if self.user_data["auth_type"] == 1:
                print("\n此演出为一单一证，只需选择1个购票人，如 1")
                if len(data["list"]) <= 0:
                    self.error_handle("你的账号里一个购票人信息都没填写哦，请前往哔哩哔哩客户端-会员购-个人中心-购票人信息提前填写购票人信息")
                for i in range(len(data["list"])):
                    # 姓名隐私保护  By FriendshipEnder 4/19
                    name_private = str(data["list"][i]["name"]) # 隐私保护  By FriendshipEnder 4/19
                    print(str(i+1) + ":" , "姓名:", "*"*(len(name_private)-1)+ name_private[-1], end = " ")

                    phone_private = str(data["list"][i]["tel"]) # 隐私保护  By FriendshipEnder 4/19
                    print("手机号:" , phone_private[:3]+ "*****"+ phone_private[-3:], end = " ")

                    id_private = str(data["list"][i]["personal_id"]) # 隐私保护  By FriendshipEnder 4/19
                    print("身份证:", id_private[:4]+ "**********"+ id_private[-4:])

                p = input("购票人序号 =>").strip()
                try:
                    t = []
                    name_private = str(data["list"][int(p)-1]["name"]) # 隐私姓名保护  By FriendshipEnder 4/19
                    print("\n已选择: ", "*"*(len(name_private)-1)+ name_private[-1])
                    t.append(data["list"][int(p)-1])
                    return t
                except:
                    self.error_handle("请输入正确序号")
            if self.user_data["auth_type"] == 2:
                if len(data["list"]) <= 0:
                    self.error_handle("你的账号里一个购票人信息都没填写哦，请前往哔哩哔哩客户端-会员购-个人中心-购票人信息提前填写购票人信息")
                print("\n此演出为一人一证，请选择购票人, 全部购票请输入0，其他请输入购票人序号，多个购票请用空格分隔，如 1 2")
                for i in range(len(data["list"])):
                    # 姓名隐私保护  By FriendshipEnder 4/19
                    name_private = str(data["list"][i]["name"]) # 隐私保护  By FriendshipEnder 4/19
                    print(str(i+1) + ":" , "姓名:", "*"*(len(name_private)-1)+ name_private[-1], end = " ")

                    phone_private = str(data["list"][i]["tel"]) # 隐私保护  By FriendshipEnder 4/19
                    print("手机号:" , phone_private[:3]+ "*****"+ phone_private[-3:], end = " ")

                    id_private = str(data["list"][i]["personal_id"]) # 隐私保护  By FriendshipEnder 4/19
                    print("身份证:", id_private[:4]+ "**********"+ id_private[-4:])

                p = input("购票人序号 =>").strip()

                t = []
                if p == "0":
                    print("\n已选择列表中全部购票人")
                    return data["list"]
                elif " " in p:
                    try:
                        print("\n已选择: ",end="") # 隐私姓名保护  By FriendshipEnder 4/19
                        for i in p.split(" "):
                            if i:
                                name_private = str(data["list"][int(i)-1]["name"])
                                print("*"*(len(name_private)-1)+ name_private[-1],end=" ")
                                t.append(data["list"][int(i)-1])
                        print("")
                        return t
                    except:
                        self.error_handle("请输入正确序号")
                else:
                    try:
                        name_private = str(data["list"][int(p)-1]["name"]) # 隐私姓名保护  By FriendshipEnder 4/19
                        print("\n已选择: ", "*"*(len(name_private)-1)+ name_private[-1])
                        t.append(data["list"][int(p)-1])
                        return t
                    except:
                        self.error_handle("请输入正确序号")
        elif mtype == "GET_NORMAL_INFO":
            print("\n此演出无需身份电话信息，请填写姓名和联系方式后按回车")
            name = input("姓名 =>").strip()
            tel = input("电话 =>").strip()
            if not re.match(r"^\d{9,14}$",tel):
                self.error_handle("请输入正确格式的电话号码")
            return name, tel

        elif mtype == "GET_T_COUNT":
            print("\n请输入购买数量")
            n = input("=>").strip()
            if not re.match(r"^\d{1,2}$",n):
                self.error_handle("请输入正确的数量")
            return n
        elif mtype == "GET_ADDRESS_LIST":
            print("\n请选择实体票发货地址(仅单地址)")
            for i in range(len(data["addr_list"])):
                print(str(i+1) + ":" , data["addr_list"][i]["prov"]+data["addr_list"][i]["city"]+data["addr_list"][i]["area"]+data["addr_list"][i]["addr"], end=" ")
                name_private = str(data["addr_list"][i]["name"]) # 隐私保护  By FriendshipEnder 4/19
                print("收件人:", "*"*(len(name_private)-1)+ name_private[-1], end = " ")
                phone_private = str(data["addr_list"][i]["phone"]) # 隐私保护  By FriendshipEnder 4/19
                print(phone_private[:3]+ "*****"+ phone_private[-3:])
            p = input("收货地址序号 =>").strip()
            return p

    def sendNotification(self,msg):
        data = {
            "token": self.token,
            "title": "抢票通知",
            "content": msg,
        }
        url = "http://www.pushplus.plus/send"
        self._http(url,data=urlencode(data),j=True)

    def tray_notify(self, title, msg, iconPath, timeout=10):  # windows系统托盘通知（部分功能可能只在Win10及之后版本有效）
        if not iconPath.endswith(".ico"):
            raise ValueError(f"iconPath must be a .ico file or icon doesn't exist. Your icon path: {iconPath}")
        trayNotify.notify(
            title = title,
            message = msg,
            app_name= self.appName,
            app_icon = iconPath,
            timeout = timeout,
        )

    def start(self):
        print("欢迎使用抢票娘 (Bilibili_show_ticket_auto_order) 版本1.8.2  只能抢B站会员购的票票哦~")
        print("是由 fengx1a0、Just-Prog 等大佬编写, 由 FriendshipEnder(CN小影) 精心优化修改后的版本")
        print("!!!!!老娘完全免费开源! 切勿外传(bushi)、切勿用于商业用途、切勿落入黄牛(nmsl)之手!!!!!")
        print("有问题去 https://github.com/fsender/Bilibili_show_ticket_auto_order 提issue 点star")
        # 加载登录信息
        self.load_cookie()
        # 加载演出信息
        self.orderInfo()
        # while True:
            # try:
                # sleep(1.7)
                # if not self.orderInfo():
                    # break
            # except Exception as e:
            #     pass
        # 加载购买人信息
        self.buyerinfo()
        # 获取购票token
        while True:
            sleep(self.sleepTime)
            if self.tokenGet() == 0:
                break
        # 购票
        while True:
            # i = 1+i # 次数显示集成在抢票函数里了 节省输出 By FriendshipEnder 4/19
            sleep(self.sleepTime)
            # print("正在尝试第: %d次抢票"%i) 
            # if self.tokenGet():
                # continue
            if self.orderCreate():
                # open("url","w").write("https://show.bilibili.com/orderlist")
                os.system("pause")
                break

    def test(self):
        self.load_cookie()
        self.checkOrder()


if __name__ == '__main__':
    Api("127.0.0.1:8080").start()