'''
2022年4月9日
先用test_androguard.py get_dir_manifest_xml()获取文件
从xml文件提取权限数据，存到sqlite
'''

import os
import re
import sqlite3
from bs4 import BeautifulSoup
from androguard.misc import AnalyzeAPK
from androguard.core.bytecodes import apk
from androguard.core.androconf import load_api_specific_resource_module
from lxml import etree
import datetime


find_perm = re.compile(r'android:name="(.*?)"')

def get_appname_exist_perms():
    '''获取数据表中已有perms的app_name列表'''
    db = sqlite3.connect("../data/db_LDA.db")
    print("Opened database successfully.")
    c = db.cursor()

    names = c.execute('''select app_name from perms_declare;''')
    list_names = [row[0] for row in names]
    return list_names
    # print([row[0] for row in names])


def get_dir_manifest_xml(apkpath):
    '''取apk文件夹所有apk,提取xml,返回[apkfile,xml]列表'''
    files = []
    filename_list=os.listdir(apkpath)
    filename_list.sort()

    list_appname_exist_perms = get_appname_exist_perms()

    for filename in filename_list:
        app_name = filename.split('.')[0]
        #文件夹下列出的是文件，且该apk还没有在数据库里存入perms
        if os.path.isfile(os.path.join(apkpath, filename)) and (app_name not in list_appname_exist_perms) :
            files.append(filename)

    list_filename_xml = []
    num_apks = len(files)
    num = 0
    for apkfile in files:
        try:
            num += 1
            print("提取xml %d/%d:%s..."% (num,num_apks,apkfile),end="")
            a = apk.APK(apkpath + '/' + apkfile) 
            xml = a.get_android_manifest_xml() #返回xml解码字符串,class 'bytes'
            xml = str(etree.tostring(xml),'utf-8')
            list_filename_xml.append([apkfile,xml])
            print("over")
        except:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d')
            with open('extract_perm_xml_log.txt','a',encoding='utf-8') as f_log:
                f_log.write(now_time)
                f_log.write('//')
                f_log.write('%d/%d:%s 的Androidmanifest.xml解析失败,可能是apk文件无效.'%(num,num_apks,apkfile))
                f_log.write('\n')
            # return list_filename_xml
            continue
    return list_filename_xml


if __name__ == '__main__':
    ''' 从apk直接取xml'''
    ##################################################################
    apkpath = r"D:/apk"
    list_filename_xml = get_dir_manifest_xml(apkpath)

    info_apps = []
    num_xmls = len(list_filename_xml)
    num = 0
    for filename,xml in list_filename_xml:
        num += 1
        perms = "" #每个应用的系统权限

        app_name = filename.split('.')[0]
        print('分析xml %d/%d: %s...'%(num,num_xmls,app_name),end="\t")

        # uses-permission下的权限
        soup = BeautifulSoup(xml,"xml")
        items_uses_perm = soup.find_all('uses-permission')
        for item in items_uses_perm:
            item = str(item)
            perm = re.findall(find_perm,item)[0]

            #保留系统权限(Android 12):698个android.开头/11个com.android.开头(从清单文件)
            #去掉自定义权限(本APP/其他APP)
            if perm.startswith('android.permission.') or perm.startswith('com.android.permission.'):
                perms = perms + perm +";"

        info_apps.append([app_name,perms])
        print("over")
    ##################################################################

    '''xml保存为文件后，下面读文件'''
    # ##################################################################
    # dir = r'./output_xml'  # 所有文件名
    # filenames = []
    # filenames = os.listdir(dir)

    # info_apps = []
    # for filename in filenames:
    #     perms = "" #每个应用的系统权限

    #     app_name = filename.split('.')[0]
    #     print('提取',app_name,'...')

    #     filepath = dir + '/' +filename
    #     with open(filepath,'r',encoding="utf-8") as f:
    #         xml = f.read()
    #         soup = BeautifulSoup(xml,"xml")

    #         # uses-permission下的权限
    #         items_uses_perm = soup.find_all('uses-permission')
    #         for item in items_uses_perm:
    #             item = str(item)
    #             perm = re.findall(find_perm,item)[0]

    #             #保留系统权限(Android 12):698个android.开头/11个com.android.开头(从清单文件)
    #             #去掉自定义权限(本APP/其他APP)
    #             if perm.startswith('android') or perm.startswith('com.android.'):
    #                 perms = perms + perm +";"
    #     info_apps.append([app_name,perms])
    # ##################################################################

    '''连接数据库'''
    db = sqlite3.connect("../data/db_LDA.db")
    print("Opened database successfully.")
    c = db.cursor()

    for app_name,perms in info_apps:
        # print(app_name)
        sql = '''
        insert into perms_declare(app_name,perms_declare)\
            values("{0}","{1}");
        '''.format(app_name,perms)
        c.execute(sql)
    
    db.commit()
    db.close()
    print("Close database successfully.")

        



