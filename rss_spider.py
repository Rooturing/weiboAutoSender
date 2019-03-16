# -*- coding: utf-8 -*-
import feedparser
import pymysql
import sys
import warnings
import re

from config import RSS_URL
from logger import logger

warnings.filterwarnings("ignore")

rss_url = RSS_URL

def run_spider(conn, cursor):
    #判断feeds表是否存在
    cursor.execute("set names 'utf8'")
    cursor.execute("select table_name from information_schema.tables where table_name='feeds'")
    res = cursor.fetchone()

    #创建feeds表
    if not res:
        try:
            cursor.execute(""" create table if not exists feeds(
                id int(4) primary key not null auto_increment,
                title char(200) not null unique,
                link char(200) not null,
                category char(20) not null,
                detail char(200) not null,
                published char(100) not null)charset=utf8""")
        except Exception as e:
            logger.debug(e)
            logger.info("无法创建feeds表")
            sys.exit()


    #爬虫获取RSS feeds
    feeds = feedparser.parse(rss_url)
    rowLen = len(feeds["entries"])
    count = 0   #总共新增条数
    rss_list = list()   #新增条数列表
    
    for i in range(rowLen):
        title = feeds.entries[i]["title"]
        link = feeds.entries[i]["link"]
        category = feeds.entries[i]["category"]
        summary = feeds.entries[i]["summary"]
        if category == "Event Calendar":
            event_time = re.search(r'<br><i>(.*?)<\/i>', summary).group(1)
            #搜索是否有deadline相关信息
            sub_deadline_obj = re.search(r'(Submission deadline:.*?)<br>', summary)
            if sub_deadline_obj:
                sub_deadline = sub_deadline_obj.group(1)
                detail = event_time + ", " + sub_deadline
            else:
                detail = event_time
        else:
            detail = re.search(r'<br><i>(.*?)<\/i>', summary).group(1)
        published = feeds.entries[i]["published"]
        
        sql = "insert ignore into feeds\
            (title, link, category, detail, published)\
            values('%s', '%s', '%s', '%s', '%s')" % \
            (title, link, category, detail, published)
        try:
            cursor.execute(sql)
        except Exception as e:
            conn.rollback()
            logger.debug(e)
            logger.info("数据插入失败")
            sys.exit()
        #判断是否插入重复条目
        cursor.execute("select row_count()")
        res = cursor.fetchone()[0]
        #当重复条目出现即停止爬行，记录下新增的条目个数
        if res != 0:
            count += res
            conn.commit()
            row = (title, link, category, detail)
            rss_list.append(row)
        else:
            if count >= 1:
                logger.info("成功插入数据，一共%d条" % count)
            else:  
                logger.info("没有新的数据插入")
            return (count, rss_list, conn, cursor)
    #或者循环结束后返回，说明所有条目均为新增
    logger.info("成功插入数据，一共%d条" % count)
    return (count, rss_list, conn, cursor)

