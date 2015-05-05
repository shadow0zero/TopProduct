#!/usr/bin/env python 
#-*-coding:utf-8-*-

"""This is a web spider for Next(36kr)"""
"""思路：
Url_Q存放请求链接
1.4个线程ThreadHtml从不同时间开始，抓取链接，请求链接，存储页面
2.2个线程ThreadData负责解析页面，存储到相应的队列（4个）
3.人为划分日期界限
4.数据处理的函数
5.Thread的run方法分离式
"""
from bs4 import BeautifulSoup
import requests
import threading
import Queue
from datetime import *
import time

from pymongo import MongoClient 
#引入Mongo数据库存储
client = MongoClient("localhost",27017)
#创建数据库topnext
db = client.topnext
#创建Collection名字prod_next
coll = db.prod_next

#队列列表QL=QueueList
Url_QL = []
Html_QL = []
for i in xrange(20):
    Url_Q = Queue.Queue()#存放请求链接
    Html_Q = Queue.Queue()#存放bs4解析页面
    Url_QL.append(Url_Q)
    Html_QL.append(Html_Q)

_WORKER_THREADHTML_NUM = 1
_WORKER_THREADDATA_NUM = 1 
Internal = 15#一个爬虫间隔链接数
Internal_day = Internal * 3#一个爬虫间隔的日期数(一个链接包括3个日期)
token = None 
#Unique ID
UID = 0

class ThreadHtml(threading.Thread):
    def __init__(self,func, url_q, html_q):
        super(ThreadHtml,self).__init__()
        self.func = func
        self.url_q = url_q
        self.html_q = html_q

    def run(self):
        s = requests.Session()
        self.func(self.url_q,self.html_q,s)

class ThreadData(threading.Thread):
    def __init__(self,func,url_q,html_q,out):
        super(ThreadData,self).__init__()
        self.func = func
        self.url_q = url_q
        self.html_q = html_q
        self.out = out

    def run(self):
        self.func(self.url_q,self.html_q,self.out)

#----存储页面-----
def store_html(url_q,html_q,s):
    global Internal
    j = 0
    while j<Internal:
        if url_q.empty():
            continue
        url = url_q.get()
        print url#test
        global token
        s.headers.update({
            "X-CSRF-Token":token,
            "X-Requested-With":"XMLHttpRequest"
        })
        content = s.get(url).content
        soup = BeautifulSoup(content)
        html_q.put(soup)
        j+=1

#----解析页面-----
def parse_html(url_q,html_q,out):
    global Internal
    
    datas = {}

    j = 0
    while j < Internal:
        if html_q.empty():
            continue
        soup = html_q.get()
        #--------存储下一页链接-------
        load = soup.find_all('a','load-more-notes')
        if not len(load):
            return
        load_url = load[0]['href']
        url = "http://next.36kr.com"+load_url 
        url_q.put(url)#将获取的下一页链接存储
        #--------获取数据---------
        #--------Post日期------------
        dates_tag = soup.find_all(attrs={"class":"date"})
        dates = []
        for date in dates_tag:
            dates.append(date.contents[3].string)
        #--------Post标题和摘要--------
        posts_tag = soup.find_all(class_="post")#EveryDay
        posts = []#EveryDay-product-list
        for post in posts_tag:
            posts.append(post.contents[3])
        i = 0
        titles = []
        summaries = []
        while i <= len(posts)-1:
            #titles:Three days-product-title-list
            #title:Oneday of product title list
            title_tag = posts[i].find_all('a', 'post-url')
            summary_tag = posts[i].find_all('span','post-tagline')
            x = 0
            title = []
            summary = []
            while x < 3:
                title.append(title_tag[x].string) 
                summary.append(summary_tag[x].string)
                x+=1
            titles.append(title)
            summaries.append(summary)
            i+=1
        #--------get token-------------
        global token
        token = soup.find_all('meta',attrs={"name":"csrf-token"})
        #--------print date-title-summary
        global UID
        x = 0
        for date in dates:
            out.write(date.encode('utf-8'))
            out.write('\n')
            title = titles[x]
            summary = summaries[x]
            datas["date"]=date
            datas["title"] = title
            datas["summary"] = summary
            #dates["id"] = UID
            UID += 1
            y = 0 
            while y<3:
                out.write(title[y].encode('utf-8'))
                out.write('\n')
                out.write(summary[y].encode('utf-8'))
                out.write('\n')
                #datas["post"+str(y)] = [title[y],summary[y]]
                y+=1
            x+=1
            #写入数据库
            coll.insert(datas)
        j+=1

def get_url(num):
    global Internal_day
    seed_day = date.today()
    internal_day = timedelta(days=Internal_day)
    i = 0
    next_day = seed_day
    while i < num: 
        next_day = next_day- internal_day 
        i=i+1
    pre_url = 'http://next.36kr.com/posts.html?start_on='
    url = str(pre_url) + str(next_day)
    return url


def main():
    global Url_QL
    global Html_QL
    global _WORKER_THREADHTML_NUM 
    global _WORKER_THREADDATA_NUM 
    #Url_Q.put(url)#将首页放入url队列
    for i in xrange(_WORKER_THREADHTML_NUM):#NUM=4
        #分配队列
        Url_Q = Url_QL[i]
        Html_Q = Html_QL[i]
        url = get_url(i)
        Url_Q.put(url)
        #创建笔记本
        out = open(str(i)+'.txt','w')
        #创建线程
        thread1 = ThreadHtml(store_html,Url_Q,Html_Q)
        thread2 = ThreadData(parse_html,Url_Q,Html_Q,out)
        #开启线程
        thread1.start()
        thread2.start()
    
if __name__ == "__main__":
    main()
