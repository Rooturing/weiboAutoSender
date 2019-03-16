# -*- coding: utf-8 -*-
import requests
import time
import rsa
import base64
import re
import json
import binascii
import urllib
import warnings
import sys

from logger import logger
from config import UNAME, PASSWD
from config import WBCLIENT, USER_AGENT
from config import HAS_PROXY, PROXY_URL

warnings.filterwarnings("ignore")

# 设置proxy
if HAS_PROXY == True:
    proxies = {
        "http":PROXY_URL,
        "https":PROXY_URL  
    }
else:
    proxies = {}

# 创建一个session
session = requests.Session()
session.headers['User-Agent'] = USER_AGENT



def pre_login(su):
    
    #获取prelogin参数
    url_prelogin = "https://login.sina.com.cn/sso/prelogin.php"
    pre_params = {
        "entry":"weibo",
        "callback":"sinaSSOController.preloginCallBack",
        "su":su,
        "rsakt":"mod",
        "checkpin":"1",
        "client":"ssologin.js(v1.4.19)",
        "_":int(time.time()*1000)
    }
    
    res = session.get(url_prelogin, params = pre_params, verify = False, proxies=proxies)
    json_obj = re.search(r"\((?P<data>.*)\)",res.text)
    if json_obj is None:
        logger.info("登陆失败，无法获取pubkey")
        sys.exit()
    json_data = json_obj.group("data")
    pre_data = json.loads(json_data) 

    servertime = pre_data["servertime"]
    nonce = pre_data["nonce"]
    pubkey = pre_data["pubkey"]
    rsakv = pre_data["rsakv"]
    return (servertime, nonce, pubkey, rsakv)

def encrypt_pass(password, pubkey, servertime, nonce):
    #对密码进行加密
    rsaPublickey = int(pubkey, 16)
    key = rsa.PublicKey(rsaPublickey, 65537) #2nd argument: exponent parameter of RSA public key, WEIBO uses 0x10001, which is 65537 in Decimal
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
    sp = binascii.b2a_hex(rsa.encrypt(message.encode("utf-8"),key))
    return sp

def login_wb():
    username = UNAME
    password = PASSWD
 
    #用户名base64编码
    su = base64.b64encode(username.encode("UTF-8")).decode("UTF-8")
    #pre_login获取参数
    (servertime, nonce, pubkey, rsakv) = pre_login(su)
    #对密码进行加密
    sp = encrypt_pass(password, pubkey, servertime, nonce)
    #进行登陆操作
    url_login = "https://login.sina.com.cn/sso/login.php"
    postdata = {
        "entry":"weibo",
        "geteway":"1",
        "from":"",
        "qrcode_flag":"false",
        "userticket":"1",
        "vsnf":"1",
        "su":su,
        "service":"miniblog",
        "servertime":servertime,
        "nonce":nonce,
        "pwencode":"rsa2",
        "rsakv":rsakv,
        "sp":sp,
        "sr":"1280*720",
        "encoding":"UTF-8",
        "prelt":"296",
        "url":"https://weibo.com/ajaxlogin.php?framelogin=1",
        "callback":"parent.sinaSSOController.feedBackUrlCallBack",
        "returntype":"META"
    }
    rsp = session.post(url_login,data=postdata, verify = False, proxies=proxies)

    #第一次跳转
    #获得登陆跳转URL
    match_obj = re.search(r'location\.replace\([\"](.*?)[\"]\)',rsp.text)
    #检查是否登陆成功
    if match_obj is None:
        logger.info("登陆失败，找不到跳转链接")
        sys.exit()
    redirect_url = match_obj.group(1)
    r = re.search(r'&r=(.*?)&',redirect_url).group(1)
    login_time = re.search(r'&login_time=(\d+)&',redirect_url).group(1)
    sign = re.search(r'&sign=(.*?)&',redirect_url).group(1)
    sr = re.search(r'&sr=(.*)',redirect_url).group(1)
    params = {
        "action":"login",
        "entry":"weibo",
        "r":urllib.parse.quote(r),
        "login_time":login_time,
        "sign":sign,
        "sr":sr
    }
    headers = {
        "Referer":"https://login.sina.com.cn/crossdomain2.php?action=login&entry=weibo&r="+r+"&login_time="+login_time+"&sign="+sign+"&sr="+sr
    }
    res = session.get("https://login.sina.com.cn/crossdomain2.php", params=params,headers=headers, verify = False, proxies=proxies)

    #第二次跳转
    #获得ticket
    ticket = re.search(r'login\?ticket\=(.*?)\"',res.text).group(1)
    ssosavestate = str(int(re.search(r'\-(\d+)\-',ticket).group(1)) + 3600 * 7)
    second_url = "https://passport.weibo.com/wbsso/crossdomain"
    login_param = {
        "action":"login",
        "callback":"sinaSSOController.doCrossDomainCallBack",
        "scriptId":"ssoscript0",
        "client":"ssologin.js(v1.4.19)",
        "_":int(time.time()*1000)
    }
    res = session.get(second_url, params=login_param, headers=headers, verify = False, proxies=proxies)

    #第三次跳转
    third_url = "https://passport.weibo.com/wbsso/login"
    res = session.get(third_url + "?url=https%3A%2F%2Fweibo.com%2Fajaxlogin.php%3Fframelogin%3D1&ticket=" + ticket + "&retcode=0", headers=headers, verify = False, proxies=proxies)

    # print(res.content.decode("GBK"))
    login_str = re.search(r'\((\{.*\})\)',res.text)
    if login_str is None:
        logger.info("登陆失败，服务器返回结果错误")
        sys.exit()
    login_info = json.loads(login_str.group(1))
    logger.info("登陆成功：[%s]" % str(login_info))
    return


def send_wb(text):
    #发送微博
    url_sendwb = "https://weibo.com/aj/mblog/add?ajwvt=6&__rnd="+str(int(time.time()*1000))
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "User-Agent":"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "X-Requested-With": "XMLHttpRequest",
        "Referer":"https://weibo.com/iacr/home"
    }
    post_wb = {
        "location":"v6_content_home",
        "text":text,
        "appkey":"",
        "style_type":"1",
        "pic_id":"",
        "tid":"",
        "pdetail":"",
        "mid":"",
        "isReEdit":"false",
        "rank":"0",
        "rankid":"",
        "module":"stissue",
        "pub_source":"main_",
        "pub_type":"dialog",
        "_t":"0"
    }
    res = session.post(url_sendwb,headers=headers,data=post_wb, verify = False, proxies=proxies)
    res_obj = re.search(r'\"code\"\:\"100000\"',res.text)
    if res_obj is None:
        logger.info("发送微博失败！")
        sys.exit()
    else:
        logger.info("发送微博成功！内容为[%s]" %text)
        return 

def write_wb(count, rss_list):
    wb_text_list = list()
    for i in range(count):
            wb_text = " "
            title = rss_list[i][0]
            link = rss_list[i][1]
            category = rss_list[i][2]
            detail = rss_list[i][3]
            #判断此则新闻所属种类
            if category == "ePrint Report":
                wb_text = "#ePrint论文更新# "
            elif category == "Job Posting":
                wb_text = "#密码学学术招聘# "
            elif category == "Event Calendar":
                wb_text = "#学术会议征稿# "
            title = title.split(":",1)
            wb_text += title[1].strip() + " " + detail + " " + link
            wb_text_list.append(wb_text)
    return wb_text_list
    
