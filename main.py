# -*- coding: utf-8 -*-
import pymysql
import sys
import time
from wb_robot import login_wb, send_wb, write_wb
from rss_spider import run_spider
from logger import logger

from config import DB_UNAME, DB_PASSWD, DB_NAME, WAIT_TIME

db_uname = DB_UNAME
db_passwd = DB_PASSWD
db_name = DB_NAME
wait_time = WAIT_TIME

if __name__ == "__main__":
    
    # 连接数据库
    try:
        conn = pymysql.connect(host="127.0.0.1", user=db_uname, passwd=db_passwd, db=db_name)
        cursor = conn.cursor()
    except Exception as e:
        logger.debug(e)
        logger.info("无法连接数据库")
        sys.exit()
    #爬取RSS页面，并返回更新条数
    (count, rss_list, conn, cursor) = run_spider(conn, cursor)
    
    if count >= 1:
        wb_text_list = write_wb(count, rss_list)
    cursor.close()
    conn.close()   
    
    login_wb()
    for i in range(count):
        send_wb(wb_text_list[i])
        time.sleep(wait_time)
    



  