from functools import partial
from threading import Thread
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import sys

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

sys.path.append('../../')
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



'''初始化数据'''
start_id_testapp =  8987 #8987 工信部
startID = 0 #非工信部
endID = 100

#阈值
threshold_suprate = 0.1 #0.1/0.005
threshold_suprate_code = 0.2 #0.1/0.005

threshold_suprate_str = str(threshold_suprate).replace('.',"")
threshold_suprate_str_code = str(threshold_suprate_code).replace('.',"")
json_dir_rate = '../topic2supportRate_json%s'%threshold_str
json_dir_rate_code = '../topic2supportRate_code_json%s'%threshold_str

#打印选项
flag_print_dangerous = False #终端是否打印“推荐权限中的危险权限信息”(perm,rate,total num)
flag_print_recAPI = False #终端是否打印推荐权限信息

#测试结果输出路径
path_results_recommended_perms = 'run_results/%s_%s/recommended_perms'%(threshold_suprate_str,threshold_suprate_str_code)
path_results_recommended_APIs = 'run_results/%s_%s/overdeclare_APIs'%(threshold_suprate_str,threshold_suprate_str_code)

'''读取源码里的711个权限'''
def get_list_allPerms():
    allpermList = []
    path_txt_allpermList_sourceCode = r'../../data/allpermList_sourceCode.txt'
    with open(path_txt_allpermList_sourceCode,'r',encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            allpermList.append(line.strip()) #默认空格或换行符
    print('perms from android source code：',len(allpermList)) #689个
    return allpermList

list_allperms = get_list_allPerms()
print("initiate analysing data...")









'''全局变量'''
testing_data = []
list_app_name = []
list_perms_declare =[]#总空
apk_path = ""
src_apk = ":/icon/apk.png"

dict_result_1 = {} #3个tab的输出结果暂存
dict_result_2 = {}
dict_result_3 = {}

index_now_1 = 0
index_now_2 = 0
index_now_3 = 0

class Ui_MainWindow_(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self,w, parent=None):
        super(Ui_MainWindow_, self).__init__(parent)
        self.setupUi(w)

        self.button_next.clicked.connect(self.button_next_clicked)
        self.button_end.clicked.connect(self.button_end_clicked)
        self.button_clear.clicked.connect(self.button_clear_clicked)

        self.botton_previous_1.clicked.connect(partial(self.botton_previous_clicked,1))
        self.botton_previous_2.clicked.connect(partial(self.botton_previous_clicked,2))
        self.botton_previous_3.clicked.connect(partial(self.botton_previous_clicked,3))

        self.botton_next_1.clicked.connect(partial(self.botton_next_clicked,1))
        self.botton_next_2.clicked.connect(partial(self.botton_next_clicked,2))
        self.botton_next_3.clicked.connect(partial(self.botton_next_clicked,3))

    def button_next_clicked(self):
        print("click button_next...")

        '''添加测试数据'''
        app_name = self.input_app_name.text().strip()
        apk_path = self.input_apk_path.text().strip()
        descrip = self.input_description.toPlainText().strip()

        if not app_name or not apk_path or not descrip:
            QMessageBox.about(Mainwindow,"Error","Please input valid data!")
            return

        words = self.cut_words(descrip) #分词
        words = word_cut.rm_stopwords(words) #去除停用词：4常用+重清洗2

        list_app_name.append(app_name)
        testing_data.append(words)#加入一个app的描述
        list_perms_declare.append([])

        listModel = QtGui.QStandardItemModel()
        for app_name in list_app_name:#显示待分析apk
            item =  QtGui.QStandardItem(QtGui.QIcon(src_apk),app_name)
            listModel.appendRow(item)
        self.listView_app_to_analyse.setModel(listModel)

        self.input_app_name.setText("")
        self.input_description.setText("")

        print("add app: %s"%app_name)


    def button_clear_clicked(self):
        global dict_result_1
        global dict_result_2
        global dict_result_3
        print("click button_clear...")

        testing_data.clear()
        list_app_name.clear()
        list_perms_declare.clear()
        self.input_app_name.setText("")
        self.input_description.setText("")

        dict_result_1 = {} #3个tab的输出结果咱厝
        dict_result_2 = {}
        dict_result_3 = {}

        tableModel = QtGui.QStandardItemModel()#推荐所有权限
        self.tableView.setModel(tableModel)#默认显示第一个APP结果
        self.tableView_2.setModel(tableModel)
        self.tableView_3.setModel(tableModel)

        self.label_output_app_name_1.setText("")
        self.label_output_app_name_2.setText("")
        self.label_output_app_name_3.setText("")


        listModel = QtGui.QStandardItemModel()
        self.listView_app_to_analyse.setModel(listModel)



    def button_end_clicked(self):
        print("click button_end...")

        self.button_end.setText('analysing')  # 主页面按钮点击后更新按钮文本
        self.button_end.setEnabled(False)  # 将按钮设置为不可点击
            
        global index_now_1
        global index_now_2
        global index_now_3

        '''若有新输入数据'''
        app_name = self.input_app_name.text().strip()
        apk_path = self.input_apk_path.text().strip()
        descrip = self.input_description.toPlainText().strip()

        if app_name and apk_path and descrip and (app_name not in list_app_name):
            words = self.cut_words(descrip) #分词
            words = word_cut.rm_stopwords(words) #去除停用词：4常用+重清洗2

            list_app_name.append(app_name)
            testing_data.append(words)#加入一个app的描述
            list_perms_declare.append([])

            listModel = QtGui.QStandardItemModel()
            for app_name in list_app_name:#显示待分析apk
                item =  QtGui.QStandardItem(QtGui.QIcon(src_apk),app_name)
                listModel.appendRow(item)
            self.listView_app_to_analyse.setModel(listModel)

            print("add app(end): %s"%app_name)
        
        self.input_app_name.setText("")
        self.input_description.setText("")


        # thread_LDA = Runthread(self)
        # thread_LDA._signal.connect(self.set_results)#进程连接传回函数
        # thread_LDA.start()
        thread = Thread(target=runLDA,args=(self,))
        thread.start()        


    def set_results(self,dict_result_1,dict_result_2,dict_result_3):
        # list_topic_p = satisfy_app(testing_data,output_directory_path,num_topics)
        
        index_now_1 = 0
        index_now_2 = 0
        index_now_3 = 0
        self.tableView.setModel(dict_result_1[list_app_name[index_now_1]])#默认显示第一个APP结果
        self.tableView_2.setModel(dict_result_2[list_app_name[index_now_2]])
        self.tableView_3.setModel(dict_result_3[list_app_name[index_now_3]])


        self.label_output_app_name_1.setText(list_app_name[index_now_1])
        self.label_output_app_name_2.setText(list_app_name[index_now_2])
        self.label_output_app_name_3.setText(list_app_name[index_now_3])

        #水平方向标签拓展剩下的窗口部分，填满表格
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView_2.horizontalHeader().setStretchLastSection(True)
        self.tableView_3.horizontalHeader().setStretchLastSection(True)

        # 水平方向，表格大小拓展到适当的尺寸   
        # self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableView_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableView_3.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # 据内容自适应宽度
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        # self.tableView_2.resizeColumnsToContents()
        # self.tableView_3.resizeColumnsToContents()

            
    def botton_previous_clicked(self,tabId):
        print("click botton_previous...")
        global index_now_1
        global index_now_2
        global index_now_3
        global dict_result_1
        global dict_result_2
        global dict_result_3
        if tabId == 1:
            if index_now_1==0:#跳到最后一个
                index_now_1 = len(list_app_name)-1 
            else:
                index_now_1 = index_now_1-1
            self.tableView.setModel(dict_result_1[list_app_name[index_now_1]])#默认显示第一个APP结果
            self.tableView.horizontalHeader().setStretchLastSection(True)
            self.tableView.resizeColumnsToContents()
            # self.tableView.resizeRowsToContents()
            self.label_output_app_name_1.setText(list_app_name[index_now_1])
        elif tabId == 2:
            if index_now_2==0:#跳到最后一个
                index_now_2 = len(list_app_name)-1 
            else:
                index_now_2 = index_now_2 - 1
            self.tableView_2.setModel(dict_result_2[list_app_name[index_now_2]])#默认显示第一个APP结果
            self.tableView_2.horizontalHeader().setStretchLastSection(True)
            self.tableView_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.label_output_app_name_2.setText(list_app_name[index_now_2])
        elif tabId == 3:
            if index_now_3==0:#跳到最后一个
                index_now_3 = len(list_app_name)-1 
            else:
                index_now_3 = index_now_3 - 1
            self.tableView_3.setModel(dict_result_3[list_app_name[index_now_3]])#默认显示第一个APP结果
            self.tableView_3.horizontalHeader().setStretchLastSection(True)
            self.tableView_3.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.label_output_app_name_3.setText(list_app_name[index_now_3])
            


    def botton_next_clicked(self,tabId):
        print("click botton_next...")
        global index_now_1
        global index_now_2
        global index_now_3
        global dict_result_1
        global dict_result_2
        global dict_result_3
        if tabId == 1:
            if index_now_1==len(list_app_name)-1 :#跳到第一个
                index_now_1 = 0
            else:
                index_now_1 += 1
            self.tableView.setModel(dict_result_1[list_app_name[index_now_1]])#默认显示第一个APP结果
            self.tableView.horizontalHeader().setStretchLastSection(True)
            self.tableView.resizeColumnsToContents()
            # self.tableView.resizeRowsToContents()
            self.label_output_app_name_1.setText(list_app_name[index_now_1])
        elif tabId == 2:
            if index_now_2==len(list_app_name)-1 :#跳到第一个
                index_now_2 = 0
            else:
                index_now_2 += 1
            self.tableView_2.setModel(dict_result_2[list_app_name[index_now_2]])#默认显示第一个APP结果
            self.tableView_2.horizontalHeader().setStretchLastSection(True)
            self.label_output_app_name_2.setText(list_app_name[index_now_2])
            self.tableView_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        elif tabId == 3:
            if index_now_3==len(list_app_name)-1 :#跳到第一个
                index_now_3 = 0
            else:
                index_now_3 += 1
            self.tableView_3.setModel(dict_result_3[list_app_name[index_now_3]])#默认显示第一个APP结果
            self.tableView_3.horizontalHeader().setStretchLastSection(True)
            self.label_output_app_name_3.setText(list_app_name[index_now_3])
            self.tableView_3.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      

    '''为app描述(descrip)分词'''
    def cut_words(self,descrip):
        LTP_DATA_DIR = r'..\..\huawei_appstore\ltp_data'  # ltp模型目录的路径
        cws_model_path = os.path.join(LTP_DATA_DIR, 'cws.model')  # 分词模型路径，模型名称为`cws.model`

        segmentor = Segmentor()  # 初始化实例
        segmentor.load(cws_model_path)  # 加载模型
        words = segmentor.segment(descrip)  # 分词
        segmentor.release()  # 释放模型

        return words



def runLDA(ui):
    global dict_result_1
    global dict_result_2
    global dict_result_3
    '''运行LDA'''
    print('-'*20,"running LDA model",'-'*20)
    num_topics = 90
    output_directory_path = '../../huawei_appstore/LDA/huawei_LDA-output-分' + str(num_topics) + '类-重清洗-4-3'#使用的模型所在文件夹
    back = output_directory_path.split('重清洗-4-')[-1]
    temp = str(num_topics) + ("" if back.startswith("huawei") else "_"+back)

    list_topic_p = satisfy_app(testing_data,output_directory_path,num_topics)


    '''分类结果写入txt文件'''
    temp_path =  "run"
    with open( 'result_%sLDA_%s%s.txt'%(temp_path,temp,threshold_str),'a',encoding='utf-8') as f:
        for name,doc,data in zip(list_app_name,testing_data,list_topic_p):
            f.write("app name: %s\n"%name)
            f.write("description: %s\n"%doc)
            f.write("topic vector: %s\n\n"%str(data))

    print()
    for name,doc,data in zip(list_app_name,testing_data,list_topic_p):
        print("app name: %s"%name,end="\t")
        print("topic vector：%s" % str(data))

    cnt = len(list_app_name)
    zip_return = zip(list_app_name,list_topic_p,list_perms_declare)#list_perms_declare空
    num_app_input,zip_appname_topicvector_permsdeclare = cnt,zip_return

    # #测试
    # num_app_input, = 1,
    # zip_appname_topicvector_permsdeclare = zip(['5G拨号v2.1','360手机卫士v8.9.2'],[[[7, 0.7599], [77, 0.1259], [76, 0.0417]],[[35, 0.2401], [17, 0.2375], [69, 0.0842], [39, 0.0816], [9, 0.0814], [82, 0.0164], [81, 0.0133], [74, 0.0127], [77, 0.0105], [86, 0.0104], [11, 0.0079], [20, 0.0077], [21, 0.0077], [14, 0.0073], [2, 0.0062], [5, 0.0058], [1, 0.0051]]],[[],[]])
    # list_app_name.append('5G拨号v2.1')
    # list_app_name.append('360手机卫士v8.9.2')



    '''遍历每个APP：根据功能向量->权限支持度->推荐权限

    每个APP的全部推荐权限：temp_all
    推荐的危险权限：temo_all_dangerous
    查支持度：for perm_,rate_ in list_sorted_dict_not0_+list_temp_all_dict:
    非test时，rate也可直接查询输出文件
    '''
    cnt_app_analyse = 0
    num_app = num_app_input
    print('-'*20,"start analysing",'-'*20)
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

        #temp_all改成按rate排序
        l = list_temp_all_dict+list_sorted_dict_not0_
        l = sorted(l,key=lambda x:x[1],reverse=True)
        temp_all = [item[0] for item in l]

        #写入综合推荐权限(不区分从代码权限/声明权限映射关系得来)
        tableModel_2 = QtGui.QStandardItemModel()#推荐所有权限
        tableModel_2.setHorizontalHeaderLabels(['recAllPerms','surpportRate','source'])

        if not os.path.isdir(path_results_recommended_perms):
            os.makedirs(path_results_recommended_perms)
        with open('%s/%s_recPerms.txt'%(path_results_recommended_perms,app_name),'w',encoding='utf-8') as f_r:
            for perm in temp_all:#遍历推荐的每个权限
                sign_code_declare = "(from coded perms)" if perm not in temp else "" #该推荐权限是否从代码权限的映射得来的
                #查该权限的支持度
                for perm_,rate_ in list_sorted_dict_not0_+list_temp_all_dict:  
                    if perm == perm_:
                        f_r.write("%-30s\t%-20s\t%s\n"%(perm,str(rate_),sign_code_declare))
                        tableModel_2.appendRow([QtGui.QStandardItem(perm),QtGui.QStandardItem(str(rate_)),QtGui.QStandardItem(sign_code_declare)])

        dict_result_2[app_name] = tableModel_2
        print("\nRecommend %d permissons in %s/%s_recPerms.txt!" % (len(temp_all),path_results_recommended_perms,app_name))
                

        '''危险权限推荐'''
        #综合推荐的危险权限、支持度，1.终端；2.测试结果文件；3.推荐结果文件
        f_r_d = open('%s/%s_recDangerPerms.txt'%(path_results_recommended_perms,app_name),'w',encoding='utf-8')
        if flag_print_dangerous:
            print("\n推荐权限中的危险权限：")

        cnt_recommend_dangerous = 0
        temp_all_dangerous = []#推荐的危险权限 备用

        #self.tableView_3：推荐的危险权限与支持度
        tableModel_3 = QtGui.QStandardItemModel()#推荐危险权限
        tableModel_3.setHorizontalHeaderLabels(['recDangerPerms','surpportRate','source'])


        for perm in temp_all:#推荐的所有权限
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
                        tableModel_3.appendRow([QtGui.QStandardItem(perm),QtGui.QStandardItem(str(rate_)),QtGui.QStandardItem(sign_code_declare)])
                        break
        f_r_d.close()
        # self.tableView_3.setModel(tableModel_3)
        dict_result_3[app_name] = tableModel_3

        print("Recommend %d dangerous permissons in %s/%s_recDangerPerms.txt!" % (cnt_recommend_dangerous,path_results_recommended_perms,app_name))

        if flag_print_dangerous:
            print("共%d个"%cnt_recommend_dangerous)
            

        '''推荐的危险权限//声明权限->需要控制的API'''
        #查询
        print("\nextract declared permissions of %s "%app_name,end='')
        list_decperm_dangerous = []#APK声明的危险权限

        db = sqlite3.connect('../../data/db_LDA.db')
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
            str_apk_perms,str_perms_delete,str_perms_dangerous = ui.get_apk_declare_perms(a) 

        list_decperm_dangerous = str_perms_dangerous.split(';')
        if "" in list_decperm_dangerous:
            list_decperm_dangerous.remove("")

        #越权危险权限->API
        list_recAPI = []
        with open('../map_perm2API.json','r',encoding='utf-8') as f_json:
            dict_perm2api = json.load(f_json)
        with open('../map_dangerPerm2desc.json','r',encoding='utf-8') as f_json:
            dict_dangerPerm2desc = json.load(f_json)

        dict_api2perm = {}
        dict_api2permdsec = {}
        for perm in list_decperm_dangerous:
            if perm not in temp_all_dangerous:#声明的危险权限，不在推荐列表
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
        tableModel_1 = QtGui.QStandardItemModel()#推荐所有权限
        tableModel_1.setHorizontalHeaderLabels(['recControlAPI','perms','permsDesc'])

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
            tableModel_1.appendRow([QtGui.QStandardItem(api),QtGui.QStandardItem(str_api2perms.replace(';','\n')),QtGui.QStandardItem(str_api2permdescs.replace(';','\n'))])

            if flag_print_recAPI:
                print("%s\t%s\t%s"%(api,str_api2perms,str_api2permdescs))
        f_recAPIs.close()   
        dict_result_1[app_name] = tableModel_1
        # self.tableView.setModel(tableModel_1)
        print("Recommend controlling %d APIs in %s/%s!"%(len(list_recAPI),path_results_recommended_APIs,app_name))             

    
    ui.button_end.setText('END')  # 主页面按钮点击后更新按钮文本
    ui.button_end.setEnabled(True)  # 将按钮设置为不可点击
    # self._signal.emit(dict_result_1,dict_result_2,dict_result_3) #LDA完成后发射信号
        

    index_now_1 = 0
    index_now_2 = 0
    index_now_3 = 0
    ui.tableView.setModel(dict_result_1[list_app_name[index_now_1]])#默认显示第一个APP结果
    ui.tableView_2.setModel(dict_result_2[list_app_name[index_now_2]])
    ui.tableView_3.setModel(dict_result_3[list_app_name[index_now_3]])


    ui.label_output_app_name_1.setText(list_app_name[index_now_1])
    ui.label_output_app_name_2.setText(list_app_name[index_now_2])
    ui.label_output_app_name_3.setText(list_app_name[index_now_3])

    #水平方向标签拓展剩下的窗口部分，填满表格
    ui.tableView.horizontalHeader().setStretchLastSection(True)
    ui.tableView_2.horizontalHeader().setStretchLastSection(True)
    ui.tableView_3.horizontalHeader().setStretchLastSection(True)

    # 水平方向，表格大小拓展到适当的尺寸   
    # self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    ui.tableView_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    ui.tableView_3.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    # 据内容自适应宽度
    ui.tableView.resizeColumnsToContents()
    ui.tableView.resizeRowsToContents()
    # self.tableView_2.resizeColumnsToContents()
    # self.tableView_3.resizeColumnsToContents()


'''为app描述(descrip)分词'''
def cut_words(descrip):
    LTP_DATA_DIR = r'..\..\huawei_appstore\ltp_data'  # ltp模型目录的路径
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



      




if __name__=='__main__':
    '''打开APP'''
    app = QtWidgets.QApplication(sys.argv)

    Mainwindow = QtWidgets.QMainWindow() #窗口实例
    ui = Ui_MainWindow_(Mainwindow)
    # ui.setupUi(Mainwindow)
    
    Mainwindow.show() 
    print("open tool UI...")



    
    # self.tableView.resizeRowsToContents()


    sys.exit(app.exec_()) 
