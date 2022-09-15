# -*- coding: utf-8 -*-
import ssl
import re
import urllib2
import os
from bs4 import BeautifulSoup
import xlwt
import html5lib

def main():
    #创建excel,第一列是className，第二列是方法，第三列是tag信息
    file = open('permissionList.xls',"w")
    book = xlwt.Workbook() #创建一个Excel
    sheet1 = book.add_sheet('mapping') #在其中创建一个名为mapping的sheet
    #循环处理每一个类
    f = open("urlList.txt","r")
    content = f.readlines()
    f.close()
    i = 0
    
    
    while i < len(content):
        url = content[i]
        print i 
        print url
        '''
        try:
            extractUrl(url,i,sheet1)
        except:
            pass
        '''
        extractUrl(url,i,sheet1)
        i += 1
    #创建保存文件
    book.save(file)
    file.close()
    #extractUrl("https://developer.android.com/reference/android/hardware/camera2/CaptureResult.Key",1)

def findClassName(soup,classCount):
    metaTag = soup.find_all("meta",attrs={"itemprop": "name"})[0]
    className = metaTag.get("content")
    addclassName = str(className) + "--" +str(classCount)
    os.mkdir("results" + "/" + addclassName )
    return addclassName


def extractUrl(url,classCount,sheet1):
    context = ssl._create_unverified_context()
    content = urllib2.urlopen(url, context=context).read()
    soup = BeautifulSoup(content, 'html5lib')
    className = findClassName(soup,classCount)
        
    #写入类名
    #sheet1.write(classCount,0,className.split("--")[0])
    list = soup.find_all("div",attrs={"data-version-added": re.compile("\d")})
    methodCount = 0
    for tag in list:
        
        try:
            if  tag.h3["id"][0].isupper() :
                continue
            else:
                extractPermission(tag,className,methodCount,sheet1)
        except:
            pass
        methodCount += 1
        
       
        
    map = {}
    count = 1
    

methodSeq = 0

def extractPermission(tag,className,methodCount,sheet1):
    global methodSeq 
    method = tag.h3["id"].split("(")[0]
    methodName = str(method) + str(methodCount)
    path = "results" + "/" + className + "/"+methodName
    os.mkdir(path)
    #print  method
    
    #print "============================================start====================================================="
    
    temp = []
    totolPermisionList = []
    children = tag.children
    
    for child in children:
        if "permission" in str(child):  
            temp.append(child)
            #print child
            logPath ="results"+  "/" +className + "/"+ methodName+ "/"+"permission.txt"
            f = open(logPath, "w")
            f.write(str(child))
            f.close()
            
            permissionSet = compareDangerousPermission(child)
        
            totolPermisionList = addToPermisionList(totolPermisionList,permissionSet)
           
    sheet1.write(methodSeq,0,className)
    sheet1.write(methodSeq,1,methodName)
    if temp:
        sheet1.write(methodSeq,2,str(temp))
    if totolPermisionList:
        sheet1.write(methodSeq,3,str(totolPermisionList))

    methodSeq += 1
    map[method] = temp
    #print "==============================================end======================================================"


def compareDangerousPermission(child):
    dangerousPermissionList = ["ACCEPT_HANDOVER","ACCESS_COARSE_LOCATION","ACCESS_FINE_LOCATION","ADD_VOICEMAIL","ANSWER_PHONE_CALLS","BODY_SENSORS","CALL_PHONE","CAMERA","GET_ACCOUNTS","PROCESS_OUTGOING_CALLS","READ_CALENDAR","READ_CALL_LOG","READ_CONTACTS","READ_EXTERNAL_STORAGE","READ_PHONE_NUMBERS","READ_PHONE_STATE","READ_SMS","RECEIVE_MMS","RECEIVE_WAP_PUSH","RECORD_AUDIO","SEND_SMS","USE_SIP","WRITE_CALENDAR","WRITE_CALL_LOG","WRITE_CONTACTS","WRITE_EXTERNAL_STORAGE"]
    matchList = set()
    for dangerousPermission in  dangerousPermissionList:
        if dangerousPermission in str(child):
            matchList.add(dangerousPermission)
    return matchList
    


def addToPermisionList(totolPermisionList,permissionSet):
    for p in permissionSet:
        if p not in totolPermisionList:
            totolPermisionList.append(p)
    return totolPermisionList


if __name__ == "__main__":
    main()

        
    

