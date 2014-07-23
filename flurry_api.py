# --------------------------------------------------
# Author: Binh Nguyen 
# Email: "binh@misfitwearables.com" or ntbinhptnk@gmail.com
# Feel free to ask me any question.
#
# --------------------------------------------------
#coding=gbk
import sys

from datetime import *
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from optparse import OptionParser
import re
import shutil
import getopt
import gzip
import ast
import os.path
import datetime
import StringIO
import cStringIO
import traceback
import httplib
import traceback
import urllib
import urllib2
import cookielib

FLURRY_LOGIN_EMAIL="<YOUR_FLURRY_LOGIN_EMAIL>"
FLURRY_LOGIN_PASSWORD="<YOUR_FLURRY_LOGIN_PASSWORD>"


def totimestamp(dt, epoch=datetime.datetime(1970,1,1)):
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6
    
def date2str(date):
    return date.strftime("%Y-%m-%d")

def datestr2datetime(datestr):
    temp=re.findall(r'\d+',datestr)
    year=temp[0]
    month=temp[1]
    day=temp[2]
    return datetime.datetime(int(year),int(month),int(day),0,0,0)

def datestr2ending_datetime(datestr):
    temp=re.findall(r'\d+',datestr)
    year=temp[0]
    month=temp[1]
    day=temp[2]
    return datetime.datetime(int(year),int(month),int(day),23,59,59)

def one_week_ago(date):
    one_week_ago_date=date-datetime.timedelta(days=7)
    return date2str(one_week_ago_date)

def one_month_ago(date):
    one_month_ago_date=date-datetime.timedelta(days=30)
    return date2str(one_month_ago_date)

def one_year_ago(date):
    one_year_ago_date=date-datetime.timedelta(days=365)
    return date2str(one_year_ago_date)

def timestamp2datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def add_headers(req):
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36')
    req.add_header('Content-type','application/x-www-form-urlencoded')
    req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    req.add_header('Cache-Control', 'no-cache')
    req.add_header('Connection','Keep-Alive')

class FlurryAPI:
    def __init__(self):
        #create cookiejar to store site cookies
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj));
        urllib2.install_opener(opener)
        #post fields of login form
        self.params = urllib.urlencode({ \
            'loginEmail': FLURRY_LOGIN_EMAIL, \
            'loginPassword': FLURRY_LOGIN_PASSWORD,\
            'rememberMe':'True',\
            '__checkbox_rememberMe':'True'\
            })
        self.login_url = "https://dev.flurry.com/secure/loginAction.do"
        #request for login to flurry
        print "Login to Flurry..."
        req = urllib2.Request(self.login_url, self.params);
        add_headers(req)
        resp = urllib2.urlopen(req);
        resp_info = resp.info()
        page_info = resp.read()
        print "Finish, result code:",resp.getcode()
        print "Set cookies: "
        for idx,cookie in enumerate(cj):
            print "%s -> %s" % (idx,cookie)
        
    def get_list_event_ids(self, project_id):
        download_url="https://dev.flurry.com/analyticsBehavior.do?projectID=%s&versionCut=versionsAll&intervalCut=30Days&segmentID=0&channelID=0&networkId=0" %(project_id)
        try:
            print "Downloading log file from Flurry..."
            #request for downloading csv file
            req2 = urllib2.Request(download_url)
            add_headers(req2)
            resp2 = urllib2.urlopen(req2)
            data = resp2.read()
            
            event_data=data.split('"dataAC" : [')
            event_data=event_data[1].split('"dataSchema')
            event_data="["+event_data[0]

            event_data = event_data.replace(u'\xa0',u' ')
            event_data = event_data.replace(u'\u201d',u'"')
            event_data = event_data.replace(u'\u201c',u'"')
            event_data = event_data.replace(u'\u2018',u"'")
            event_data = event_data.replace(u'\u2019',u"'")
            event_data = re.sub('\r',' ',event_data)
            event_data = re.sub('\t',' ',event_data)
            event_data = re.sub(' ','',event_data)
            event_data = event_data.replace("\t","")
            event_data = event_data.replace("\n","")
            event_data=event_data[:-1]
            
            event_data=event_data.split("}")
            event_data=event_data[:-1]
            all_events=dict()
            for event in event_data:
                event_info=event.split("{")[1]
                event_info=event_info.split(",")
                name=str(event_info[0]).replace('name:"','').replace('"','')
                event_id=str(event_info[1]).replace('id:','')
                if "." not in name:
                    all_events[name]=event_id
            return all_events
        except Exception, e:
            traceback.print_exc()
            
    def get_event_log(self,project_id, event_name, start_day, end_day, file_path, offset):
        list_all_events=self.get_list_event_ids(project_id)
        print list_all_events
        list_event_names=[]
        for key,value in list_all_events.items():
            list_event_names.append(key)
        if event_name not in list_event_names:
            return False
        else:
            eventid=list_all_events[event_name]
            download_url = "https://dev.flurry.com/eventsLogCsv.do?projectID=%s&versionCut=versionsAll&intervalCut=customInterval%s-%s&eventID=%s&stream=true&direction=1&offset=%d" % (project_id,start_day, end_day, eventid, offset)
            try:
        
                print "Downloading log file from Flurry..."
                #request for downloading csv file
                req2 = urllib2.Request(download_url)
                add_headers(req2)
                resp2 = urllib2.urlopen(req2)
                data = resp2.read()
                f_out = open(file_path,"wb")
                f_out.write(data)
                f_out.close()
                print "Finish, save file at", file_path
                return True

            except Exception, e:
                traceback.print_exc()
        
if __name__ == "__main__":
    api=FlurryAPI()
    
    start_day = "2014-07-20"
    end_day = "2014-07-20"
    event_name = "YourEventName"
    project_id="123456"
    offset = 0
    file_path="./"+str(event_name)+"-"+start_day+"-"+end_day+".tsv"
    print api.get_list_event_ids(project_id)
    print api.get_event_log(project_id,event_name, start_day, end_day, file_path, offset)
    
    