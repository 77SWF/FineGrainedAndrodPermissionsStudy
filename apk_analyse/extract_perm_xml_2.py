'''
2022年4月14日
先用test_androguard.py get_dir_perm()获取所有uses-permission权限
处理后，存到sqlite

除了3个com.开头的权限(list_com_android_permission)，都只显示android.permission.xxx后面这个xxx
且是从源码里提取的那些权限，不只207个
'''

import os
import re
import sqlite3
import time
from bs4 import BeautifulSoup
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import load_api_specific_resource_module
import gc
import traceback

from download_apk import download_url


find_perm = re.compile(r'android:name="(.*?)"') #use-permission
find_permission = re.compile(r'android:name="(.*?)"') #permission
#40个危险权限 API 1-tiramisu
dangerousPermissionList = ["ACCEPT_HANDOVER","ACCESS_COARSE_LOCATION","ACCESS_FINE_LOCATION","ADD_VOICEMAIL","ANSWER_PHONE_CALLS","BODY_SENSORS","CALL_PHONE","CAMERA","GET_ACCOUNTS","PROCESS_OUTGOING_CALLS","READ_CALENDAR","READ_CALL_LOG","READ_CONTACTS","READ_EXTERNAL_STORAGE","READ_PHONE_NUMBERS","READ_PHONE_STATE","READ_SMS","RECEIVE_MMS","RECEIVE_WAP_PUSH","RECORD_AUDIO","SEND_SMS","USE_SIP","WRITE_CALENDAR","WRITE_CALL_LOG","WRITE_CONTACTS","WRITE_EXTERNAL_STORAGE","ACCEPT_HANDOVER","ACTIVITY_RECOGNITION","ACCESS_BACKGROUND_LOCATION","ACCESS_MEDIA_LOCATION","UWB_RANGING","BLUETOOTH_ADVERTISE","BLUETOOTH_CONNECT","BLUETOOTH_SCAN","BODY_SENSORS_BACKGROUND","NEARBY_WIFI_DEVICES","POST_NOTIFICATIONS","READ_MEDIA_AUDIO","READ_MEDIA_IMAGE","READ_MEDIA_VIDEO"]


'''get_all_perms()的结果从txt读取（另加 安卓13 tiramisu 的几个权限）'''
allpermList = []
path_txt_allpermList_sourceCode = r'..\data\allpermList_sourceCode.txt'
with open(path_txt_allpermList_sourceCode,'r',encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        allpermList.append(line.strip()) #默认空格或换行符
print('源码里权限个数：',len(allpermList)) #689个


'''从源码12版本清单文件提取所有权限：689个；要另加 安卓13 tiramisu 的几个权限（txt有）'''
def get_all_perms():
    '''从源码12版本清单文件提取所有权限：689个'''
    allpermList = []
    source_code_path = "../data/manifests_source_code/AndroidManifest-Android12.xml"
    with open(source_code_path,'r',encoding="utf-8") as f:
        xml = f.read()
        soup = BeautifulSoup(xml,"xml")
        items_perm = soup.find_all('permission')
        for item in items_perm:
            item = str(item)
            perm = re.findall(find_permission,item)[0]

            perm = perm.split('.')[-1]
            allpermList.append(perm)

            #发现没必要分什么开头了
            # if perm.startswith("com.android."):
            #     allpermList.append(perm)
            # else:
            #     perm = perm.split('.')[-1]
            #     allpermList.append(perm)

    print('源码里权限个数：',len(allpermList)) #689个
    return allpermList


'''获取数据表中已有perms的app_name列表'''
def get_appname_exist_perms():
    '''获取数据表中已有perms的app_name列表'''
    db = sqlite3.connect("../data/db_LDA.db")
    # print("Opened database successfully.")
    c = db.cursor()

    names = c.execute('''select app_name from perms_declare_2;''')
    list_names = [row[0] for row in names]
    db.close()
    return list_names


'''获取目录dirpath下所有文件的路径list'''
def get_dir_filepaths(dirpath):
    '''获取目录dirpath下所有文件的路径list'''
    list_file_path = [] #
    filename_list=os.listdir(dirpath)
    filename_list.sort()

    #数据表中已有perms的app_name列表
    list_appname_exist_perms = get_appname_exist_perms()

    cnt = 0
    for filename in filename_list:
        app_name = filename.split('.')[0]
        #文件夹下列出的是文件，且该apk还没有在数据库里存入perms
        file_path = os.path.join(dirpath, filename)
        if os.path.isfile(file_path) and (app_name not in list_appname_exist_perms) :
            list_file_path.append(file_path)

        # #删除已经分析过的apk文件
        # if os.path.isfile(file_path) and (app_name in list_appname_exist_perms) :
        #     cnt+=1
        #     os.remove(file_path)
        #     print("remove file No.%d %s"%(cnt,app_name))
    return list_file_path


'''获取APK的声明权限：1）源码有的 2）源码无的'''
def get_apk_declare_perms(a):
    '''a:APK对象
    提取APK的manifest.xml里的uses-permission权限str,按;隔开(按字母排序)
    '''    
    list_perm = a.get_permissions() # 所有uses-permission权限
    list_perm_new = []
    # list_all_perm = get_all_perms() #改成全局list allpermList

    str_perms_delete = "" #自定义权限另存一表 不按序排了

    temp = [] #声明权限去重判断
    for perm in list_perm: 
        if perm.split('.')[-1] in allpermList:#只存最后一串
            perm = perm.split('.')[-1]
            if perm not in temp:
                temp.append(perm)
                list_perm_new.append(perm)
        elif perm.startswith("android.permission.") or perm.startswith("com.android."): #可能是其他废弃的系统权限
            str_perms_delete = str_perms_delete + perm+";"

    list_perm_new.sort()

    str_perms = ""
    str_perms_dangerous = ""
    for perm in list_perm_new:
        if perm in dangerousPermissionList:#危险权限
            str_perms_dangerous = str_perms_dangerous + perm + ";"
        str_perms = str_perms + perm + ";"
    return str_perms,str_perms_delete,str_perms_dangerous


'''用permmap映射dx对象的所有API->API、权限、危险权限(str)'''
def map_apk_api2perms(dx,permmap):
    ''' 从APK提取API对应权限到output_api_premission/apkname__api_perm(最新到API 28)
    返回code_infos=[code_info],每个APK的：[应用名，API的str，权限的str]
    '''
    #每个APK的信息，写入数据表
    # code_info = [] #[应用名，API的str，权限的str]
    str_APIs = ""
    str_perms = ""
    str_perms_dangerous = ""
    list_APIs = []
    list_perms = []

    # 遍历所有class的每个method，提取需要权限的API
    # result="" #API->权限结果
    cnt_meth = 0
    num_meth = len(list(dx.get_methods()))
    for meth_analysis in dx.get_methods(): #返回MethodAnalysis对象（一个dex文件一个对象）的列表(迭代器) 而不是直接method的list
        cnt_meth += 1
        print("\r---perm No.%d/%d"%(cnt_meth,num_meth),end="")
        meth = meth_analysis.get_method() #str(meth)如：Landroid/app/Activity;->navigateUpTo(Landroid/content/Intent;)Z
                                            #即 class;->method 描述符
        
        #改成map表的API格式，eg.android.net.wifi.WifiManager.WifiLock.isHeld
        meth_class_name = meth.get_class_name()
        meth_class_name =  meth_class_name[1:-1].replace('/','.').replace('$','.') #去掉L和末尾的; 改成android.net.wifi.WifiManager.WifiLock class形式
        meth_name = meth.get_name()
        name = meth_class_name + '.' + meth_name #android.net.wifi.WifiManager.WifiLock.isHeld形式

        if name in ['android.net.wifi.aware.WifiAwareManager.attach','android.telephony.TelephonyManager.getImei']:
            meth_descriptor = meth.get_descriptor()
            temp_desc = re.findall(re.compile(r'(\(.*?\))'),meth_descriptor)[0]
            temp_desc = temp_desc[1:-1].replace(' ',';')
            temp_list = temp_desc.split(';')
            if "" in temp_list:
                temp_list.remove("")
            name = name + "-" + str(len(temp_list))
            
        for key,value in permmap.items():  #key函数 value权限的list
            if name  == key:  #函数在map文件
                if name not in list_APIs:
                    list_APIs.append(name)
                    str_APIs = str_APIs+name+';'
                for perm in value:
                    if perm not in list_perms:
                        list_perms.append(perm)
                        str_perms = str_perms + perm + ";" #
                        if perm in dangerousPermissionList: 
                            str_perms_dangerous = str_perms_dangerous + perm + ";"

    # print("")
    return str_APIs,str_perms,str_perms_dangerous


def main():
    url = ''
    savename = ''
    apk_dir = r"D:/apk"

    if url:
        download_url(url,savename,apk_dir)

    list_file_path = get_dir_filepaths(apk_dir)
    # list_file_path = [r'D:\\apk\\迅雷直播.apk'] #测试

    '''连接数据库'''
    db = sqlite3.connect("../data/db_LDA.db")
    print("Opened database successfully...")
    c = db.cursor()

    info_apps_declare = [] #声明权限：源码有 [app_name,perms,危险权限]
    info_apps_delete = [] #声明权限：源码无 [app_name,perms]
    info_apps_API = [] #代码权限 [app_name,API,perms,危险权限]

    # dict {函数名:权限list}、可以取permissions_25.json//自己增加permission_32.json文件(从表api2perm_map_2读取)
    permmap = load_api_specific_resource_module('api_permission_mappings',api=32) 
    print("get mapping json file...\n")

    #处理每个apk
    num_apks = len(list_file_path)
    count = 0
    for apk_path in list_file_path:
        count+=1
        # if count <=3:
        #     continue
        app_name = apk_path.split('\\')[-1].split('.apk')[0]
        
        print("analyse APK %d/%d: %s..."% (count,num_apks,app_name),flush=True)
        
        time_start=time.time()
        try: #解析成功    
            a,dx = AnalyzeAPK(apk_path)
        except Exception:#apk解析失败 记录失败traceback 继续下一个
            print("failed\n")
            # traceback.print_exc()
            with open("fail_AnalyzeAPK.txt",'a',encoding='utf-8') as f:
                f.write("%s\t"%(app_name))
                f.write('\n')
                traceback.print_exc(file=f)#异常traceback写入文件

            print("next apk...")
            continue #下一个apk

        time_end1=time.time()
        cost_time1=(time_end1-time_start)/60 #分组
        print("\tAnalyse time = %s mins"%str(round(cost_time1,1)),flush=True)

        # a,dx = AnalyzeAPK(apk_path)
        # print("successfully")

        '''提取声明/代码权限'''
        ##############################################################
        ''' 从apk提取声明权限'''
        print("extract declared perms...",end="",flush=True)
        str_apk_perms,str_perms_delete,str_perms_dangerous = get_apk_declare_perms(a) 
        # info_apps_declare.append([app_name,str_apk_perms,str_perms_dangerous])
        # info_apps_delete.append([app_name,str_perms_delete])
        print("over")
        ##############################################################


        ##############################################################
        ''' 从apk解析method、API映射到'''
        # print("")#换行
        print("extract coded perms...",flush=True)
        str_APIs,str_perms_code,str_perms_code_dangerous = map_apk_api2perms(dx,permmap)
        # info_apps_API.append([app_name,str_APIs,str_perms_code,str_perms_code_dangerous])
        print("...over")
        ##############################################################


        ##############################################################
        ''' （每个APK存一下）存储 从apk提取的声明权限'''
        print("save2db: declared perms...",flush=True)
        # for app_name,perms,perms_dangerous in info_apps_declare:##声明的权限里，源码里有的权限
        sql_1 = '''
        insert into perms_declare_2(app_name,perms_declare,perms_declare_dangerous)\
            values("{0}","{1}","{2}");
        '''.format(app_name,str_apk_perms,str_perms_dangerous)
        c.execute(sql_1)

        # for app_name,perms in info_apps_delete:#声明的权限里，源码里没有的权限
        sql_2 = '''
        insert into perms_declare_del(app_name,perms_declare)\
            values("{0}","{1}");
        '''.format(app_name,str_perms_delete)
        c.execute(sql_2)
        ##############################################################


        ##############################################################
        ''' （每个APK存一下）存储 从apk解析的API、代码权限'''
        print("save2db: coded perms...",end="",flush=True)
        # for app_name,API,perms,perms_dangerous in info_apps_API:#[应用名，API，API映射的权限]
        sql_3 = '''
        insert into perms_code(app_name,API,perms_code,perms_code_dangerous)\
            values("{0}","{1}","{2}","{3}");
        '''.format(app_name,str_APIs,str_perms_code,str_perms_code_dangerous)
        c.execute(sql_3)
        ##############################################################
        db.commit() #提交
        time_end2=time.time()
        cost_time2 = (time_end2-time_start)/60
        print("\tRunning time = %s mins"%str(round(cost_time2,1)),flush=True)

        os.remove(apk_path)#删除该文件
        print("remove file %s"%apk_path.split('\\')[-1])

        del dx
        del a
        gc.collect()
        print("-")


    '''一次性保存到数据库'''
    # print("\n\n")#换行 下面开始保存
    # ##############################################################
    # ''' 存储 从apk提取的声明权限'''

    # print("save2db: declared perms...")
    # for app_name,perms,perms_dangerous in info_apps_declare:##声明的权限里，源码里有的权限
    #     sql = '''
    #     insert into perms_declare_2(app_name,perms_declare,perms_declare_dangerous)\
    #         values("{0}","{1}","{2}");
    #     '''.format(app_name,perms,perms_dangerous)
    #     c.execute(sql)

    # for app_name,perms in info_apps_delete:#声明的权限里，源码里没有的权限
    #     sql = '''
    #     insert into perms_declare_del(app_name,perms_declare)\
    #         values("{0}","{1}");
    #     '''.format(app_name,perms)
    #     c.execute(sql)

    # ##############################################################

    # ##############################################################
    # ''' 存储 从apk解析的API、代码权限'''

    # print("save2db: coded perms...")
    # for app_name,API,perms,perms_dangerous in info_apps_API:#[应用名，API，API映射的权限]
    #     sql = '''
    #     insert into perms_code(app_name,API,perms_code,perms_code_dangerous)\
    #         values("{0}","{1}","{2}","{3}");
    #     '''.format(app_name,API,perms,perms_dangerous)
    #     c.execute(sql)
    # ##############################################################

    '''关闭数据库'''
    db.commit()
    db.close()
    print("\nClose database successfully.")


if __name__ == '__main__':
    main()

        



