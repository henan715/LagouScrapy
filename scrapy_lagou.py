# -*- encoding:utf-8 -*-

import urllib2
import json
import re
import time
import datetime
import socket
from bs4 import BeautifulSoup

#解决'ascii' codec can't decode问题
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#导入pandas库
import pandas as pd
from pandas import DataFrame,Series

#对输入的关键字进行预先处理
def processKeyWord(keyword):
    keywordbyte=keyword.encode('utf-8')
    keywordindex=str(keywordbyte).replace(r'\x','%').replace(r"'","")
    keywordindex=re.sub('^b','',keywordindex)
    return keywordindex

#获取指定关键字搜索结果的总页数
def getSearchPageNumber(keyword):
    overview_url='http://www.lagou.com/jobs/positionAjax.json?px=default&first=true&kd='+processKeyWord(keyword)+'&pn=1'
    data=urllib2.urlopen(overview_url).read()
    urlcount=int(json.loads(str(data))["content"]["totalPageCount"])
    return urlcount

def getJobDatas(keyword):
    i=0
    type='true'

    for i in list(range(0,getSearchPageNumber(keyword))):python 写入excel 不覆盖
        #合法性检验
        if i==0:
            type='true'
        else:
            type='false'

        #基本参数
        overview_url='http://www.lagou.com/jobs/positionAjax.json?px=default&first='+type+'&kd='+processKeyWord(keyword)+'&pn='+str(i+1)
        data=urllib2.urlopen(overview_url).read()
        urlcount=int(json.loads(str(data))["content"]["totalPageCount"])


def lagou_spider(keyword):
    keywordbyte=keyword.encode('utf-8')
    keywordindex=str(keywordbyte).replace(r'\x','%').replace(r"'","")
    keywordindex=re.sub('^b','',keywordindex)

    #get search page numbers
    i=0
    type='true'
    overview_url='http://www.lagou.com/jobs/positionAjax.json?px=default&first='+type+'&kd='+keywordindex+'&pn='+str(i+1)
    data=urllib2.urlopen(overview_url).read()
    urlcount=int(json.loads(str(data))["content"]["totalPageCount"])
    #print "查询到到网页页数为："+str(urlcount)

    for i in list(range(0,urlcount)):
        #合法性检验
        if i==0:
            type='true'
        else:
            type='false'

        #基本参数
        overview_url='http://www.lagou.com/jobs/positionAjax.json?px=default&first='+type+'&kd='+keywordindex+'&pn='+str(i+1)
        data=urllib2.urlopen(overview_url).read()
        urlcount=int(json.loads(str(data))["content"]["totalPageCount"])

        #轮询获取数据
        try:
            jsondata=json.loads(str(data))["content"]['result']
            for t in list(range(len(jsondata))):
                jsondata[t]['companyLabelList2']=','.join(jsondata[t]['companyLabelList'])  #合并公司福利标签

                #将每一行数据作成series，之后再合并？？？
                if t==0:
                    rdata=DataFrame(Series(data=jsondata[t])).T
                    #print rdata
                else:
                    rdata=pd.concat([rdata,DataFrame(Series(data=jsondata[t])).T])  #.T代表交换行列次序
                    #print rdata

                #重新给rdata编码
#from urllib2 import Request
#import urllib.request
                rdata.index=range(1,len(rdata)+1)
                rdata['keyword']=keyword
                rdata['salarymin']=0
                rdata['salarymax']=0
                rdata['url']=''
                rdata['jd']=''  #职位描述
                rdata['handle_prec']='' #简历处理及时律
                rdata['handle_day']=''  #简历处理平均完成天数

                for klen in list(range(len(rdata['salary']))):
                    rdata.ix[klen+1,'salarymin']=re.search('^(\d*?)k',rdata['salary'].iloc[klen]).group(1)

                    #如果工资的最大值没有填写则默认为空
                    if re.search('-(\d*?)k$',rdata['salary'].iloc[klen])!=None:
                        rdata.ix[klen+1,'salarymax']=re.search('-(\d*?)k$',rdata['salary'].iloc[klen]).group(1)
                    else:
                        #增加一列，便于后续抓取内容
                        rdata.ix[klen+1,'salarymax']=''

                    rdata.ix[klen+1,'url']='http://www.lagou.com/jobs/%s.html'% rdata.ix[klen+1,'positionId']
                    sp_req=urllib2.Request(rdata.ix[klen+1,'url'])

                    with urllib2.urlopen(sp_req) as f:
                        data_url=f.read()
                        soup_url=BeautifulSoup(data_url,'html5lib')
                        strings_url=soup_url.find('dd',{"class":"job_bt"}).strings
                        rdata.ix[klen+1,'jd']=''.join(strings_url).encode('gb2312','ignore').decode('gb2312','ignore').replace(' ','')
                        temp=soup_url.find_all('span',{"class":"data"})
                        if re.search('>(\w*%)<',str(temp[0]))==None:
                            rdata.ix[klen+1,'handle_perc']=''
                        else:
                            rdata.ix[klen+1,'handle_prec']=re.search('>(\w*%)<',str(temp[1])).group(1).replace('天','')
        except Exception,e:
            print(e)
            continue

        if i==0:
            totaldata=rdata
        else:
            totaldata.index=range(1,len(totaldata)+1)
        print('正在抓取搜索页面第%d页,时间是%s，还剩下%d页'%(i+1,datetime.datetime.now(),urlcount-i-1))
         #开始写入数据库
        totaldata.to_excel('lagou.xls',sheet_name='Sheet1')


lagou_spider("python")