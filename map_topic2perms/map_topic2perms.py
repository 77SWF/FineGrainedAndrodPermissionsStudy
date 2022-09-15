import json
import re
import sqlite3
import  os
import copy
from xmlrpc.client import FastParser
from bs4 import BeautifulSoup
from pyltp import Segmentor
import little_mallet_wrapper as lmw
import sys
from androguard.core.bytecodes import apk

sys.path.append('../')
from huawei_appstore.huawei_appdescrip_spider import word_cut
# from apk_analyse.extract_perm_xml_2 import get_apk_declare_perms

path_to_mallet = 'C:/mallet/bin/mallet'  # CHANGE THIS TO YOUR MALLET PATH
#41个危险权限
list_dangerous_perms = ["ACCEPT_HANDOVER","ACCESS_COARSE_LOCATION","ACCESS_FINE_LOCATION","ADD_VOICEMAIL","ANSWER_PHONE_CALLS","BODY_SENSORS","CALL_PHONE","CAMERA","GET_ACCOUNTS","PROCESS_OUTGOING_CALLS","READ_CALENDAR","READ_CALL_LOG","READ_CONTACTS","READ_EXTERNAL_STORAGE","READ_PHONE_NUMBERS","READ_PHONE_STATE","READ_SMS","RECEIVE_MMS","RECEIVE_WAP_PUSH","RECORD_AUDIO","SEND_SMS","USE_SIP","WRITE_CALENDAR","WRITE_CALL_LOG","WRITE_CONTACTS","WRITE_EXTERNAL_STORAGE","ACCEPT_HANDOVER","ACTIVITY_RECOGNITION","ACCESS_BACKGROUND_LOCATION","ACCESS_MEDIA_LOCATION","UWB_RANGING","BLUETOOTH_ADVERTISE","BLUETOOTH_CONNECT","BLUETOOTH_SCAN","BODY_SENSORS_BACKGROUND","NEARBY_WIFI_DEVICES","POST_NOTIFICATIONS","READ_MEDIA_AUDIO","READ_MEDIA_IMAGE","READ_MEDIA_VIDEO","READ_CELL_BROADCASTS"]
find_permission = re.compile(r'android:name="(.*?)"') #permission
find_protectionLevel = re.compile(r'android:protectionLevel="(.*?)"') #保护级别
find_desctag = re.compile(r'android:description="(.*?)"') #保护级别



#LDA的概率阈值选取
threshold = 0.005 #原本0.05/0.01
if threshold == 0.01:
    threshold_str = "" #相关文件后缀
else:
    threshold_str = '_' + str(threshold).replace('.',"")

'''从db topic_vector_90_3(_90的模型损坏了)
读取所有属于topic_x的(应用名，P)到appAndP_belong2topicx/app_topic_x.txt
只取有声明权限/代码权限8980个
'''
def get_appList_of_topic_x():
    print('-'*20,'running get_appList_of_topic_x','-'*20)

    db = sqlite3.connect('../data/db_LDA.db')
    c = db.cursor()
    print("open database successfully...")

    '''选取有apk分析数据的APP(主题数据)'''
    sql = '''
    select topic_vector_90_3%s.app_name,topics,probilities from topic_vector_90_3%s inner join perms_code\
        on topic_vector_90_3%s.app_name = perms_code.app_name;
    '''%(threshold_str,threshold_str,threshold_str)
    rows = c.execute(sql)
    list_appdata = [] #[(app_name,topics_list,probilities_list),...]
    # temp = []
    for row in rows:#每个app的[app_name,topics_str,probilities_str]
        try:
            list_topic = row[1].split(',')
            list_probility = row[2].split(',')
        except:
            print(row[0],list_topic,list_probility)

        if "" in list_topic:
            list_topic.remove("")
        if "" in list_probility:
            list_probility.remove("")

        list_appdata.append((row[0],list_topic,list_probility))
        # temp.append(row[3])
        # if row[0] not in temp:
        #     temp.append(row[0])
        # else:
        #     print(row[0])
    print("read data of %d apps successfully..." % len(list_appdata))

    # for i in range(1,8981):
    #     if i not in temp:
    #         print(i,list_appdata[i-1])
    # print("len(temp)=",len(temp))

    appList_path = 'appAndP_belong2topicx%s'%threshold_str
    if not os.path.isdir(appList_path):
        os.mkdir(appList_path)
        print('create directory \'%s\' successfully...'%appList_path)
    else:
        print('directory \'%s\' exists...'%appList_path)


    dict_topic2app = {}
    for i in range(90):
        dict_topic2app[str(i)] = ""
    print("init dict_topic2app successfully...")

    for app_name,list_topic,list_probility in list_appdata: #遍历每个app
        for topic,probility in zip(list_topic,list_probility):
            # with open(appList_path+'/appList_topic%d' % topic,'a',encoding='utf-8'):
            dict_topic2app[str(topic)] += app_name + '\t' + str(probility) + '\n' 
    print("get dict_topic2app successfully...")


    with open('num_app_belong2topicx%s.txt'%threshold_str,'a',encoding='utf-8') as f2:
        f2.write("topic\tnum_app\n")
        
    for i in range(90):
        data = dict_topic2app[str(i)].strip()
        list_data = data.split('\n')
        try:
            list_data.remove("")
        except :
            pass
        num = len(list_data)
        with open(appList_path+'/app_topic_%d.txt'%i,'w',encoding='utf-8') as f:
            f.write(data) #属于topic i的所有应用与P字符串，一个app一行
        with open('num_app_belong2topicx%s.txt'%threshold_str,'a',encoding='utf-8') as f2:
            f2.write("%d\t%d\n"%(i,num))
    print("write directory \'%s\' over."%appList_path)



'''get_appList_of_topic_x的结果读到json
json.load(“json文件”)得dict={app:概率,...}
'''
def read_txt2json():
    print('-'*20,'running read_txt2json','-'*20)
    json_dir = 'appAndP_belong2topicx_json%s'%threshold_str
    if not os.path.isdir(json_dir):
        os.mkdir(json_dir)
        print('create directory \'%s\' successfully...'%json_dir)
    else:
        print('directory \'%s\' exists...'%json_dir)

    txt_dir = 'appAndP_belong2topicx%s'%threshold_str
    for i in range(90):
        f_json = open(json_dir+'/app_topic_%d.json'%i,'w',encoding='utf-8')
        f_json.write('{\n')

        with open(txt_dir+'/app_topic_%d.txt'%i,'r',encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines: #遍历topic下所有APP
            line = line.strip()
            list_app_P = line.split('\t')

            if line == lines[-1]:
                f_json.write("    \"%s\":%s\n" % (list_app_P[0],list_app_P[1]))
            else:  
                f_json.write("    \"%s\":%s,\n" % (list_app_P[0],list_app_P[1]))
        
        f_json.write('}')
    print("write directory \'%s\' over."%json_dir)



'''读取源码里的711个权限'''
def get_list_allPerms():
    allpermList = []
    path_txt_allpermList_sourceCode = r'../data/allpermList_sourceCode.txt'
    with open(path_txt_allpermList_sourceCode,'r',encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            allpermList.append(line.strip()) #默认空格或换行符
    print('perms from android source code：',len(allpermList)) #689个
    return allpermList



'''读取源码里的危险个权限'''
def get_list_dangerousPerms():
    dangerousPermissionList = ["ACCEPT_HANDOVER","ACCESS_COARSE_LOCATION","ACCESS_FINE_LOCATION","ADD_VOICEMAIL","ANSWER_PHONE_CALLS","BODY_SENSORS","CALL_PHONE","CAMERA","GET_ACCOUNTS","PROCESS_OUTGOING_CALLS","READ_CALENDAR","READ_CALL_LOG","READ_CONTACTS","READ_EXTERNAL_STORAGE","READ_PHONE_NUMBERS","READ_PHONE_STATE","READ_SMS","RECEIVE_MMS","RECEIVE_WAP_PUSH","RECORD_AUDIO","SEND_SMS","USE_SIP","WRITE_CALENDAR","WRITE_CALL_LOG","WRITE_CONTACTS","WRITE_EXTERNAL_STORAGE","ACCEPT_HANDOVER","ACTIVITY_RECOGNITION","ACCESS_BACKGROUND_LOCATION","ACCESS_MEDIA_LOCATION","UWB_RANGING","BLUETOOTH_ADVERTISE","BLUETOOTH_CONNECT","BLUETOOTH_SCAN","BODY_SENSORS_BACKGROUND","NEARBY_WIFI_DEVICES","POST_NOTIFICATIONS","READ_MEDIA_AUDIO","READ_MEDIA_IMAGE","READ_MEDIA_VIDEO","READ_CELL_BROADCASTS"]

    return dangerousPermissionList


'''写入每个topic对应json：权限->该topic下的支持度
参数C/D；默认声明权限D
'''
def get_perm_suprate_of_topics(code_or_declare = "D"):
    print('-'*20,'running get_perm_suprate_of_topics','-'*20)
    
    dict_app2declperms = {} #所有APP，{"APP名"：list, "APP名"：list, ...}
    dict_topic2ratedict = {} #所有topic，{"topic数字"：dict, "topic数字":dict, ...}，dict为权限->支持度

    list_allperms = get_list_allPerms() #所有权限771个

    db = sqlite3.connect('../data/db_LDA.db')
    c = db.cursor()
    print("open database successfully...")
    
    '''dict_app2declperms：app->声明权限list'''
    if code_or_declare=="D":#声明权限
        sql_declare = '''
        select app_name,perms_declare from perms_declare_2 where id < 38217;
        '''
    else:#代码权限
        sql_declare = '''
        select app_name,perms_code from perms_code where id < 38217;
        '''
    rows = c.execute(sql_declare)
    num_app = 0
    for row in rows:#遍历每个APP        
        num_app +=1
        list_perms_declare = row[1].split(';')
        if "" in list_perms_declare:
            list_perms_declare.remove("")

        dict_app2declperms[row[0]] = list_perms_declare
    print("read declared perms of %d apps..."%num_app)

    json_dir = 'appAndP_belong2topicx_json%s'%threshold_str
    # for i in range(1):#测试topic 0
    for i in range(90):#遍历每个topic
        print("="*80)
        print("analysing topic %d..."%i)

        dict_topic_perm2rate = {} #每个topic {"权限":支持度, "权限":支持度,...}
        for perm in list_allperms:
            dict_topic_perm2rate[perm] = 0
        print("initiate dict_topic_perm2rate...")

        with open(json_dir+'/app_topic_%d.json'%i,'r',encoding='utf-8') as f_json:
            dict_app2probility = json.load(f_json)
        print("totally %d apps in topic %d..."%(len(dict_app2probility),i))

        #支持度分母
        probility_sum = 0
        for probility in dict_app2probility.values():
            probility_sum += probility
        # print("probility_sum(topic %d) = %d"%(i,probility_sum))
        
        #支持度分子
        for app_name,probility in dict_app2probility.items():
            list_perms_declare = dict_app2declperms[app_name]
            for perm in list_allperms:#遍历所有711个权限
                if perm in list_perms_declare:#这个APP有该权限(这里已经不管数据库里的权限有没有写重复)
                    dict_topic_perm2rate[perm] +=  probility

        #支持度=分子/分母
        for app_name in dict_topic_perm2rate.keys():
            dict_topic_perm2rate[app_name] = dict_topic_perm2rate[app_name]/probility_sum
        
        #按支持度大到小排序 list内元素是item=[权限,支持度]
        list_sorted_dict = sorted(dict_topic_perm2rate.items(),key = lambda x:x[1],reverse = True)
        dict_topic2ratedict[str(i)] = list_sorted_dict#topic->权限支持度dict


        '''写入json'''
        if code_or_declare=="D":
            json_dir_rate = 'topic2supportRate_json%s'%threshold_str
        else:
            json_dir_rate = 'topic2supportRate_code_json%s'%threshold_str
        if not os.path.isdir(json_dir_rate):
            os.mkdir(json_dir_rate)
            print('create directory \'%s\' successfully...'%json_dir_rate)
        else:
            print('directory \'%s\' exists...'%json_dir_rate)

        f_json = open(json_dir_rate+'/app_topic_%d.json'%i,'w',encoding='utf-8')
        f_json.write('{\n')

        cnt_perm = 0
        list_sorted_dict_not0 = [item for item in list_sorted_dict if item[1]]
        for item in list_sorted_dict_not0:
            cnt_perm+=1
            # print(item)
            if item == list_sorted_dict_not0[-1]:
                f_json.write("    \"%s\":%s\n" % (item[0],item[1]))
            else:  
                f_json.write("    \"%s\":%s,\n" % (item[0],item[1]))

        f_json.write('}')
        print('write app_topic_%d.json over: totally %d perms.'%(i,cnt_perm))
            


'''为app描述(descrip)分词'''
def cut_words(descrip):
    LTP_DATA_DIR = r'..\huawei_appstore\ltp_data'  # ltp模型目录的路径
    cws_model_path = os.path.join(LTP_DATA_DIR, 'cws.model')  # 分词模型路径，模型名称为`cws.model`

    segmentor = Segmentor()  # 初始化实例
    segmentor.load(cws_model_path)  # 加载模型
    words = segmentor.segment(descrip)  # 分词
    segmentor.release()  # 释放模型

    return words



'''输入app描述list/LDA模型/类数
返回[["主题","概率"],...]，其中P>threshold
'''
def satisfy_app(testing_data,output_directory_path,num_topics):
    '''
        testing_data：app描述文本处理后的list["words"]

        output_directory_path：使用的模型所在文件夹

        num_topics：该模型划分类数

        return：data = [["主题","概率"],...]，其中P>0.05
    '''
    print("start analysing %d docs..."%len(testing_data))
    #数据输出路径：该模型下test文件夹
    if not os.path.isdir(output_directory_path + '/test'):
        os.makedirs(output_directory_path + '/test')
    path_to_testing_data           = output_directory_path + '/testing.txt'
    path_to_formatted_testing_data = output_directory_path + '/mallet.testing'
    path_to_tested_topic_distributions     = output_directory_path + '/mallet.test.topic_distributions.' + str(num_topics)

    #模型路径
    path_to_model = output_directory_path + '/mallet.model.' + str(num_topics)

    '''导入测试数据'''
    #参数：exe/txt文件/txt格式化输出/输入txt的list
    lmw.import_data(path_to_mallet,
                    path_to_testing_data,
                    path_to_formatted_testing_data,
                    testing_data,
                    use_pipe_from=output_directory_path + '/mallet.training') #该模型的格式化训练数据

    '''待测数据输入模型，输出结果'''
    lmw.infer_topics(path_to_mallet,
                    path_to_model,
                    path_to_formatted_testing_data, #放新的目标数据集
                    path_to_tested_topic_distributions) #结果输出路径

    topic_distributions_test = lmw.load_topic_distributions(path_to_tested_topic_distributions)


    '''doc主题向量大到小排序，主题向量indexs_max_p_all=[(主题,概率),()]'''
    num_max_p_topics =  num_topics #取每个doc最可能的topic个数

    indexs_max_p_all = [] #存所有doc的主题向量，主题向量=[(主题,概率),()]

    for i in range(len(testing_data)): #遍历所有doc(1个)
        p_topics = copy.deepcopy(topic_distributions_test[i]) #每个doc的概率list
        indexs_max_p = [] #存1个doc最可能的topic下标

        for j in range(num_max_p_topics): #大到小排列indexs_max_p=[概率从大到小的(topic,p)]
            max_p = max(p_topics)#概率的最大值
            index_max_p = p_topics.index(max_p) #是在第几个topic取该最大值

            # indexs_max_p.append((index_max_p,max_p)) #(主题下标，概率) 
            indexs_max_p.append((index_max_p,round(max_p,4))) #(主题下标，概率) topic加入
            # indexs_max_p.append((index_max_p,round(max_p,4)*100)) #(主题下标，概率) 概率单位%
            p_topics[index_max_p] = -1 #最大值改0

        indexs_max_p_all.append(indexs_max_p)

    # print(indexs_max_p_all)


    '''indexs_max_p_all只返回P>0.05的前几个元组,data=[["主题","概率"],...]'''
    
    list_data = []#所以doc的主题向量=[[(topic,p),(topic,p)],[...],...]
    maxnum = len(indexs_max_p_all) #doc个数(1个)
    for i in range(maxnum): #遍历每个doc
        data = [] #每个doc的主题向量
        topic_vector = copy.deepcopy(indexs_max_p_all[i]) #遍历每个app的主题向量=[(主题,概率),()]

        for j in range(num_topics): #遍历主题向量内每个元组，共num_topics个
            temp = []
            if topic_vector[j][1] <= threshold: 
                topic_vector = topic_vector[:j]
                break
            else:
                temp.append(topic_vector[j][0])
                temp.append(topic_vector[j][1])

            data.append(temp)
            # print(j,temp)

        list_data.append(data)
        # print(data)
    print("over")

    # print(list_data)
    
    return list_data



'''输入app名字、描述信息，返回LDA结果：zip(list_app_name,list_topic_p)
修改num_topics、output_directory_path可改变类数与所用模型
flag_test：是否测试(非测试时无限读取直至ctrl+C)'''
def LDA_input(flag_test = False):
    end_flag = "end"
    next_app_flag = 'next'
    # while True:
    '''输入数据'''
    # flag_test = False #是否测试(非测试时无限读取直至ctrl+C)
    print("Note: 1.end flag = 'end';2.next app flag = 'next'\n") #end_flag默认

    testing_data = []
    list_app_name = []
    list_perms_declare =[]#总空

    app_name = input("Input No.1 app name: ")
    data = input("Input No.1 app description:\n ")

    list_app_name.append(app_name)
    list_perms_declare.append([])


    cnt = 0#doc计数
    while data.strip() != end_flag:#未输入end
        cnt+=1
        descrip = "" #一个app的描述
        while data.strip() != next_app_flag and data.strip() != end_flag: #一个app的描述输入未停止
            descrip = descrip + " " + data.strip()
            data = input()

        # 输入next/end后,处理这个数据
        #测试数据文本处理(不去除低频错误词 需要总文本作为依据，训练数据才去除)
        words = cut_words(descrip) #分词
        words = word_cut.rm_stopwords(words) #去除停用词：4常用+重清洗2
        testing_data.append(words)#加入一个app的描述
        print("--------------------------------------------------------------------")
        if data.strip() != end_flag: #输入next
            data = input("Input No.%d app name or input 'end' to start satisfying: "%(cnt+1))

            if data.strip() != 'end':
                list_app_name.append(data)
                list_perms_declare.append([])
                data = input("Input No.%d app description:\n "%(cnt+1))
    
    num_topics = 90
    output_directory_path = '../huawei_appstore/LDA/huawei_LDA-output-分' + str(num_topics) + '类-重清洗-4-3'#使用的模型所在文件夹
    back = output_directory_path.split('重清洗-4-')[-1]
    temp = str(num_topics) + ("" if back.startswith("huawei") else "_"+back)

    list_topic_p = satisfy_app(testing_data,output_directory_path,num_topics)
    '''分类结果写入txt文件'''
    temp_path = "test" if flag_test else "run"
    with open( 'result_%sLDA_%s%s.txt'%(temp_path,temp,threshold_str),'a' if not flag_test else 'w',encoding='utf-8') as f:
        for name,doc,data in zip(list_app_name,testing_data,list_topic_p):
            f.write("app name: %s\n"%name)
            f.write("description: %s\n"%doc)
            f.write("topic vector: %s\n\n"%str(data))

    print()
    for name,doc,data in zip(list_app_name,testing_data,list_topic_p):
        print("app name: %s"%name,end="\t")
        print("topic vector：%s" % str(data))

    return cnt,zip(list_app_name,list_topic_p,list_perms_declare)#list_perms_declare空



'''测试一个APP，推荐权限/声明权限对比，超出推荐权限的权限的支持度
参数：大于阈值的权限，写入文件句柄，大于0的权限与支持度，声明权限
'''
def test(list_perms_recommend,f_test,list_sorted_dict_not0,perms_declare):
    # print(list_sorted_dict_not0)
    list_perms_declare = perms_declare.split(';')
    if '' in list_perms_declare:
        list_perms_declare.remove('')

    list_perms_declare_rmsame = [] #perms_declare去重
    rmsame = []
    for perm in list_perms_declare:
        if perm not in list_perms_declare_rmsame:
            list_perms_declare_rmsame.append(perm)
        # else: #可注释，只是看一下什么重复了
        #     if perm not in rmsame:
        #         rmsame.append(perm)
        #         print(perm)

    print("\n推荐权限个数：%d"%len(list_perms_recommend))
    print('声明权限个数：%d\n'%len(list_perms_declare_rmsame))
    f_test.write("\n推荐权限个数：%d\n"%len(list_perms_recommend))
    f_test.write('声明权限个数：%d\n'%len(list_perms_declare_rmsame))

    print("声明权限里超出的：")
    f_test.write("\n声明权限里超出的：\n")
    cnt_1 = 0
    cnt_1_dangerous = 0
    perms_recommend_dangerous = []
    for perm in list_perms_declare_rmsame:#遍历每个声明权限
        if perm not in list_perms_recommend:#若不在推荐列表
            # print(perm,"超出")
            cnt_1+=1
            #查超出的权限的支持度
            for perm_,rate_ in list_sorted_dict_not0:
                if perm == perm_:
                    if perm in list_dangerous_perms:#超出推荐权限，且为dangerous
                        cnt_1_dangerous+=1
                        print("(dangerous)%-30s\t%-20s"%(perm,str(rate_)))
                        f_test.write("(dangerous)%-30s\t%-20s\n"%(perm,str(rate_)))
                    else:#超出推荐权限，非dangerous
                        print("%-30s\t%-20s"%(perm,str(rate_)))
                        f_test.write("%-30s\t%-20s\n"%(perm,str(rate_)))
                    break
    f_test.write("共%d个，其中dangerous%d个\n"%(cnt_1,cnt_1_dangerous))
    print("共%d个，其中dangerous%d个"%(cnt_1,cnt_1_dangerous))

    return cnt_1,cnt_1_dangerous #超出推荐权限的危险权限数量
    

'''获取APK的声明权限：1）源码有的 2）源码无的'''
def get_apk_declare_perms(a):
    '''a:APK对象
    提取APK的manifest.xml里的uses-permission权限str,按;隔开(按字母排序)
    '''    
    list_perm = a.get_permissions() # 所有uses-permission权限
    list_perm_new = []
    # list_all_perm = get_all_perms() #改成全局list allpermList
    
    allpermList =get_list_allPerms()
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
        if perm in list_dangerous_perms:#危险权限
            str_perms_dangerous = str_perms_dangerous + perm + ";"
        str_perms = str_perms + perm + ";"
    return str_perms,str_perms_delete,str_perms_dangerous


'''从源码提取危险权限->权限描述'''
def get_json_dangerPerm2desc():
    dict_dangerPerm2desc = {}
    
    source_code_path = "../data/manifests_source_code/AndroidManifest-Android12.xml"
    source_code_string_path = "../data/manifests_source_code/strings-Android12.xml"

    with open(source_code_path,'r',encoding="utf-8") as f:
        xml = f.read()
    soup = BeautifulSoup(xml,"xml")
    with open(source_code_string_path,'r',encoding="utf-8") as f:
        xml2 = f.read()
    soup2 = BeautifulSoup(xml2,"xml")

    items_perm = soup.find_all('permission')#permission标签 整个

    cnt=0
    for item in items_perm:
        
        item = str(item)
        protectionLevel = re.findall(find_protectionLevel,item)[0]
        if "dangerous" in protectionLevel:#是危险权限
            cnt+=1
            perm = re.findall(find_permission,item)[0]
            perm = perm.split('.')[-1] #权限名(最后一段)
            tag_desc = re.findall(find_desctag,item)[0]
            tag_desc = tag_desc.split('/')[-1]
            # print(tag_desc)
            
            find_desc_item = re.compile(tag_desc)
            find_desc = re.compile(r'>"(.*?)"</string>')

            items_desc = soup2.find_all(attrs={"name":find_desc_item})
            # print(item_desc)
            if len(items_desc)==1:
                item_desc = items_desc[0]
                str_item_desc = str(item_desc)
                desc = re.findall(find_desc,str_item_desc)[0]
            else:#多个，product=tv/tablet/default
                for item_desc in items_desc:
                    str_item_desc = str(item_desc)
                    if "default" in str_item_desc:
                        desc = re.findall(find_desc,str_item_desc)[0]
                        break

            dict_dangerPerm2desc[perm] = desc
    print("extract %d dangerous permissons..."%cnt)

    f = open('map_dangerPerm2desc.json','w',encoding='utf-8')
    f.write('{\n')
    cnt2=0
    for perm,desc in dict_dangerPerm2desc.items():
        cnt2+=1
        if cnt2<cnt:
            f.write("    \"%s\":\"%s\",\n" % (perm,desc))
        else:
            f.write("    \"%s\":\"%s\"\n" % (perm,desc))
    f.write('}')
    print("write map_dangerPerm2desc.json over.")









if __name__ == '__main__':
    # get_appList_of_topic_x()      #写入每个topic对应txt：app_name->probility
    # read_txt2json()               #上述txt转换成json文件，json.load()可转成dict
    # get_perm_suprate_of_topics("D")  #写入每个topic对应json：声明权限->该topic下的支持度
    # get_perm_suprate_of_topics("C")  #写入每个topic对应json：声明权限->该topic下的支持度
    # get_json_dangerPerm2desc()

    #测试ID
    start_id_testapp =  8987 #8987 工信部
    startID = 0 #非工信部
    endID = 100
    #测试选项 True False
    flag_test = True #测试：单个应用，记录到test_results：推荐的危险权限与支持度、声明权限/推荐权限对比、所有权限-支持度数据
    flag_gongxinbu = True #测试的是否工信部APP
    
    #阈值
    threshold_suprate = 0.1 #0.1/0.005
    threshold_suprate_code = 0.2 #0.1/0.005

    threshold_suprate_str = str(threshold_suprate).replace('.',"")
    threshold_suprate_str_code = str(threshold_suprate_code).replace('.',"")
    json_dir_rate = 'topic2supportRate_json%s'%threshold_str
    json_dir_rate_code = 'topic2supportRate_code_json%s'%threshold_str

    #打印选项
    flag_print_dangerous = False #终端是否打印“推荐权限中的危险权限信息”(perm,rate,total num)
    flag_print_recAPI = True #终端是否打印推荐权限信息
    
    #测试结果输出路径
    if flag_gongxinbu and flag_test:#工信部app测试
        path_results_recommended_perms = 'test_工信部APP/%s_%s/recommended_perms'%(threshold_suprate_str,threshold_suprate_str_code)
        dir_results = 'test_工信部APP/%s_%s/output'%(threshold_suprate_str,threshold_suprate_str_code)
        path_results_recommended_APIs = 'test_工信部APP/%s_%s/overdeclare_APIs'%(threshold_suprate_str,threshold_suprate_str_code)
    elif flag_test:#非工信部APP测试
        path_results_recommended_perms = 'test_otherApp/%s_%s/recommended_perms_%d-%d'%(threshold_suprate_str,threshold_suprate_str_code,startID,endID)
        dir_results = 'test_otherApp/%s_%s/output_%d-%d'%(threshold_suprate_str,threshold_suprate_str_code,startID,endID)
        path_results_recommended_APIs = 'test_otherApp/%s_%s/overdeclare_APIs'%(threshold_suprate_str,threshold_suprate_str_code)
    else:#非测试
        path_results_recommended_perms = 'run_results/%s_%s/recommended_perms'%(threshold_suprate_str,threshold_suprate_str_code)
        path_results_recommended_APIs = 'run_results/%s_%s/overdeclare_APIs'%(threshold_suprate_str,threshold_suprate_str_code)



    list_allperms = get_list_allPerms()


    
    while True:
        '''输入N个APP名字+描述：LDA->主题向量'''
        if not flag_test: #终端输入应用名描述文本
            print()
            print('-'*20,'running LDA','-'*20)
            num_app_input,zip_appname_topicvector_permsdeclare = LDA_input() #默认run，结果txt为'a'形式写入,list_topic_p = [[86, 0.7883], [77, 0.0522]]；permsdeclare为空，为了符合test时候格式
            # print('-'*20,'LDA over','-'*20)
        else:# 测试数据（改应用名list_name_）
            # 根据应用名自动查找输入数据
            db = sqlite3.connect('../data/db_LDA.db')
            c = db.cursor()
            print("open database successfully...")

            #据APP名字查数据
            list_name_ = []
            if flag_gongxinbu:#工信部APP测试
                sql_name = '''select app_name from perms_declare_2\
                    where id>{0}'''.format(start_id_testapp)
            else:#非工信部APP测试
                sql_name = '''select app_name from perms_declare_2\
                    where id>={0} and id<={1}'''.format(startID,endID)
            rows_app_name = c.execute(sql_name)
            cnt_app_name=0
            for row_app_name in rows_app_name:
                cnt_app_name+=1
                list_name_.append(row_app_name[0].strip())
            # print("%d个app："%cnt_app_name,list_name_)            

            list_perms_declare = []#所有应用的声明权限
            # list_perms_code = []#所有应用的代码权限
            list_vector_ = []
            
            cnt_app = 0
            for name_ in list_name_:#遍历每个应用
                cnt_app+=1
                print("getting data of No.%d/%d %s..."%(cnt_app,len(list_name_),name_))

                list_topics = []#该应用的主题向量信息
                list_probilities = [] 

                # 主题向量数据
                sql_vector = '''select topics,probilities from topic_vector_90_3_0005\
                    where app_name = "{0}"'''.format(name_)
                rows_vector = c.execute(sql_vector)
                for topics_,probilities_ in rows_vector:#该应用的主题、概率
                    for topic2,probility2 in zip(topics_.split(','),probilities_.split(',')):
                        list_topics.append(topic2)
                        list_probilities.append(probility2)

                # 声明权限数据，检测模型效果，只看声明权限
                sql_perms_declare = '''select perms_declare from perms_declare_2\
                    where app_name = "{0}"'''.format(name_)
                rows_perms_declare = c.execute(sql_perms_declare)
                perms_declare = rows_perms_declare.fetchone()[0]
                list_perms_declare.append(perms_declare)

                # 综合topic、概率到vector
                vector_ = []
                for topic_,pro_ in zip(list_topics,list_probilities):
                    if topic_:
                        vector_.append([topic_,pro_])
                list_vector_.append(vector_)

            zip_appname_topicvector_permsdeclare=zip(list_name_,list_vector_,list_perms_declare) #测试LDA分类 0.005

            db.close()


        '''遍历每个APP：根据功能向量->权限支持度->推荐权限

        每个APP的全部推荐权限：temp_all
        推荐的危险权限：temo_all_dangerous
        查支持度：for perm_,rate_ in list_sorted_dict_not0_+list_temp_all_dict:
        非test时，rate也可直接查询输出文件
        '''
        cnt_app_analyse = 0
        num_app = len(list_name_) if flag_test else num_app_input

        for app_name,list_topic_p,perms_declare in zip_appname_topicvector_permsdeclare:#遍历每个APP与其LDA结果，为其推荐权限
            cnt_app_analyse += 1
            print()
            print('-'*20,"analysing No.%d/%d %s..."%(cnt_app_analyse,num_app,app_name),'-'*20)
            

            '''计算权限支持度'''
            #一个APP的所有权限的支持度，{"权限":支持度, ...}
            dict_app_perm2rate = {} #声明权限支持度
            dict_app_perm2rate_code = {} #代码权限支持度

            for perm in list_allperms:
                dict_app_perm2rate[perm] = 0
                dict_app_perm2rate_code[perm] = 0
            print("initiate dict_app_perm2rate,dict_app_perm2rate_code...")

            #遍历该APP的每个topic，据topic下权限支持度->APP权限支持度
            for topic,probility in list_topic_p:
                # 声明权限
                with open(json_dir_rate+'/app_topic_%s.json'%topic,'r',encoding='utf-8') as f_json:
                    dict_topic2rate = json.load(f_json)
                for k_perm,v_rate in dict_topic2rate.items():
                    # print(type(v_rate),type(probility))
                    dict_app_perm2rate[k_perm] += v_rate * float(probility)

                #代码权限
                with open(json_dir_rate_code+'/app_topic_%s.json'%topic,'r',encoding='utf-8') as f_json:
                    dict_topic2rate_code = json.load(f_json)
                for k_perm,v_rate in dict_topic2rate_code.items():
                    # print(type(v_rate),type(probility))
                    dict_app_perm2rate_code[k_perm] += v_rate * float(probility)


            '''推荐权限：取阈值以上的权限'''
            #声明权限：按支持度排序，list=[[权限,支持度],...]
            list_sorted_dict = sorted(dict_app_perm2rate.items(),key = lambda x:x[1],reverse = True) #所有权限，权限+支持度
            list_sorted_dict_not0 = [item for item in list_sorted_dict if item[1]] #支持度非0的，权限+支持度
            # list_sorted_perms_not0 = [item[0] for item in list_sorted_dict if item[1]]#有声明的权限列表
            list_sorted_dict_not0_ = [item for item in list_sorted_dict if item[1]>=threshold_suprate] #支持度非0的，权限+支持度
            temp = [item[0] for item in list_sorted_dict_not0 if item[1]>=threshold_suprate]  #支持度>阈值，权限名


            #代码权限：按支持度排序，list=[[权限,支持度],...]
            list_sorted_dict_code = sorted(dict_app_perm2rate_code.items(),key = lambda x:x[1],reverse = True) #所有权限，权限+支持度
            list_sorted_dict_not0_code = [item for item in list_sorted_dict_code if item[1]] #支持度非0的，权限+支持度
            #阈值有问题 普遍偷用的话？改成和声明权限不同的阈值
            #需要该权限有在
            temp_code = [item[0] for item in list_sorted_dict_not0_code if item[1]>=threshold_suprate_code]  #支持度>阈值，权限名
            temp_code_rate = [item[1] for item in list_sorted_dict_not0_code if item[1]>=threshold_suprate_code]

            #综合推荐权限(不看支持度)
            temp_all = copy.deepcopy(temp)
            list_temp_all_dict = []#类似list_sorted_dict_not0，放声明里没有，代码里有的(not0)
            for perm,rate in zip(temp_code,temp_code_rate):
                if perm not in temp:
                    temp_all.append(perm)
                    list_temp_all_dict.append([perm,rate])

            #写入综合推荐权限(不区分从代码权限/声明权限映射关系得来)
            if not os.path.isdir(path_results_recommended_perms):
                os.makedirs(path_results_recommended_perms)
            with open('%s/%s_recPerms.txt'%(path_results_recommended_perms,app_name),'w',encoding='utf-8') as f_r:
                for perm in temp_all:#遍历推荐的每个权限
                    sign_code_declare = "(from coded perms)" if perm not in temp else "" #该推荐权限是否从代码权限的映射得来的
                    #查该权限的支持度
                    for perm_,rate_ in list_sorted_dict_not0_+list_temp_all_dict:  
                        if perm == perm_:
                            f_r.write("%-30s\t%-20s\t%s\n"%(perm,str(rate_),sign_code_declare))
            print("\nRecommend %d permissons in %s/%s_recPerms.txt!" % (len(temp_all),path_results_recommended_perms,app_name))
                    

            '''测试与危险权限推荐'''
            #测试单个应用，对比综合推荐权限/声明权限，写入txt
            cnt_overdeclare_dangerous = 0 #过度声明权限中的危险权限个数
            if flag_test:
                if not os.path.isdir(dir_results):
                    os.makedirs(dir_results)
                f_test_name = '%s/%s.txt'%(dir_results,app_name)
                f_test = open(f_test_name,'w',encoding='utf-8')    
                #对比：声明权限/从声明权限得到的推荐清单 
                cnt_over_declared,cnt_overdeclare_dangerous = test(temp_all,f_test,list_sorted_dict_not0+list_temp_all_dict,perms_declare)#对比声明权限、推荐权限，写入对比结果


            #综合推荐的危险权限、支持度，1.终端；2.测试结果文件；3.推荐结果文件
            f_r_d = open('%s/%s_recDangerPerms.txt'%(path_results_recommended_perms,app_name),'w',encoding='utf-8')
            if flag_print_dangerous:
                print("\n推荐权限中的危险权限：")
            cnt_recommend_dangerous = 0
            if flag_test:
                f_test.write("\n推荐权限中的危险权限：\n")
            temp_all_dangerous = []#推荐的危险权限 备用
            for perm in temp_all:
                if perm in list_dangerous_perms:#推荐的是危险权限
                    temp_all_dangerous.append(perm)
                    cnt_recommend_dangerous+=1
                    sign_code_declare = "(from coded perms)" if perm not in temp else "" #该推荐权限是否从代码权限的映射得来的
                    #查该权限的支持度
                    for perm_,rate_ in list_sorted_dict_not0_+list_temp_all_dict:  
                        if perm == perm_:
                            #输出到文件：推荐的所有危险权限
                            f_r_d.write("%-30s\t%-20s\t%s\n"%(perm,str(rate_),sign_code_declare))
                            #打印在终端
                            if flag_print_dangerous:
                                print("%-30s\t%-20s\t%s"%(perm,str(rate_),sign_code_declare))
                            #测试时 输出到测试文件
                            if flag_test:
                                f_test.write("%-30s\t%-20s\t%s\n"%(perm,str(rate_),sign_code_declare))
                            break
            f_r_d.close()
            print("Recommend %d dangerous permissons in %s/%s_recDangerPerms.txt!" % (cnt_recommend_dangerous,path_results_recommended_perms,app_name))


            if flag_print_dangerous:
                print("共%d个"%cnt_recommend_dangerous)
            if flag_test:
                f_test.write("共%d个\n"%cnt_recommend_dangerous)
            
            #全部权限支持度信息写入
            if flag_test:
                f_test.write("\n（从声明权限）所有权限-支持度：\n")
                for item in list_sorted_dict_not0:
                    f_test.write("%-30s\t%-20s\n"%(str(item[0]),str(item[1])))
                
                f_test.write("\n（从代码权限）所有权限-支持度：\n")
                for item in list_sorted_dict_not0_code:
                    f_test.write("%-30s\t%-20s\n"%(str(item[0]),str(item[1])))

                f_test.close()
            
                #重命名test输出文件
                if cnt_overdeclare_dangerous > 0: #过度声明权限中的危险权限个数
                    f_test_name_new = '%s/_%s.txt'%(dir_results,app_name)
                    os.rename(f_test_name,f_test_name_new)#重命名文件为_开头
                if cnt_over_declared == 0:#没有越权权限
                    f_test_name_new = '%s/0%s.txt'%(dir_results,app_name)
                    os.rename(f_test_name,f_test_name_new)#重命名文件为_开头
        

            '''推荐的危险权限//声明权限->需要控制的API'''
            #查询
            print("\nextract declared permissions of %s "%app_name,end='')
            list_decperm_dangerous = []#APK声明的危险权限

            db = sqlite3.connect('../data/db_LDA.db')
            c = db.cursor()

            sql_dec_perm = '''select perms_declare_dangerous from perms_declare_2\
                where app_name = "{0}"'''.format(app_name)
            rows = c.execute(sql_dec_perm)
            if rows:
                print("from database...")
                for row in rows:
                    str_perms_dangerous = row[0]
            else:
                print("from apk...")
                path_apk = 'D:/%s.apk'%app_name
                a= apk.APK(path_apk)
                str_apk_perms,str_perms_delete,str_perms_dangerous = get_apk_declare_perms(a) 

            list_decperm_dangerous = str_perms_dangerous.split(';')
            if "" in list_decperm_dangerous:
                list_decperm_dangerous.remove("")

            #越权危险权限->API
            list_recAPI = []
            with open('map_perm2API.json','r',encoding='utf-8') as f_json:
                dict_perm2api = json.load(f_json)
            with open('map_dangerPerm2desc.json','r',encoding='utf-8') as f_json:
                dict_dangerPerm2desc = json.load(f_json)

            dict_api2perm = {}
            dict_api2permdsec = {}
            for perm in list_decperm_dangerous:
                #声明的危险权限，不在推荐列表
                if perm not in temp_all_dangerous:
                    list_API = dict_perm2api[perm]#该权限对应API
                    if list_API:
                        for api in list_API:
                            if api not in list_recAPI:#之前还没这个api
                                list_recAPI.append(api)
                                dict_api2perm[api] = perm
                                try:
                                    dict_api2permdsec[api] = dict_dangerPerm2desc[perm]
                                except:
                                    dict_api2permdsec[api] = "暂无权限描述。"
                            else:#已经有其他权限有这个API
                                dict_api2perm[api]+=";"+perm
                                try:
                                    dict_api2permdsec[api] += ";"+dict_dangerPerm2desc[perm]
                                except:
                                    dict_api2permdsec[api] += ";"+"暂无权限描述。"
                    else:#没有对应API
                        if "no API: %s"%perm not in list_recAPI:
                            list_recAPI.append("no API: %s"%perm)
                        dict_api2perm["no API: %s"%perm] = perm
                        try:
                            dict_api2permdsec["no API: %s"%perm]=dict_dangerPerm2desc[perm]
                        except:
                            dict_api2permdsec["no API: %s"%perm] = "暂无权限描述。"


            #写入：要控制的API->对应权限
            if not os.path.isdir(path_results_recommended_APIs):
                os.makedirs(path_results_recommended_APIs)
            path_recAPIs = '%s/%s.txt'%(path_results_recommended_APIs,app_name)
            f_recAPIs = open(path_recAPIs,'w',encoding='utf-8')

            if flag_print_recAPI:
                print("\nRecommend controlling APIs & dangerous permissions as follows:")
            for api in list_recAPI:
                #每行：API  权限;权限  权限描述;权限描述
                str_api2perms = dict_api2perm[api]#API对应的该APP声明了的权限
                str_api2permdescs = dict_api2permdsec[api]#对应权限描述
                f_recAPIs.write("%-65s\t%-25s\t%s\n"%(api,str_api2perms,str_api2permdescs))
                if flag_print_recAPI:
                    print("%-65s\t%-25s\t%s"%(api,str_api2perms,str_api2permdescs))
            f_recAPIs.close()   
            print("Recommend controlling %d APIs in %s/%s!"%(len(list_recAPI),path_results_recommended_APIs,app_name))             

            if flag_test:
                #重命名test的API输出文件
                if cnt_overdeclare_dangerous > 0: #过度声明权限中的危险权限个数
                    path_recAPIs_new =  '%s/_%s.txt'%(path_results_recommended_APIs,app_name)
                    os.rename(path_recAPIs,path_recAPIs_new)#重命名文件为_开头(其他文件是不需控制API的：有越权的普通权限/无越权权限)

        #若非测试，可再次输入描述信息，继续分析
        if flag_test: 
            break
