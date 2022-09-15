#-*-coding:utf-8-*-
#python3.6.7(pyltp)
#！！！！import过程千万不可终止，否则模型损坏

import os
import sqlite3
from pyltp import Segmentor
import little_mallet_wrapper as lmw
import sys
sys.path.append('../')
from huawei_appdescrip_spider import word_cut #报错没事
import copy


path_to_mallet = 'C:/mallet/bin/mallet'  # CHANGE THIS TO YOUR MALLET PATH
threshold = 0.005 #0.05


def cut_words(descrip):
    '''为app描述(descrip)分词'''
    LTP_DATA_DIR = r'..\ltp_data'  # ltp模型目录的路径
    cws_model_path = os.path.join(LTP_DATA_DIR, 'cws.model')  # 分词模型路径，模型名称为`cws.model`

    segmentor = Segmentor()  # 初始化实例
    segmentor.load(cws_model_path)  # 加载模型
    words = segmentor.segment(descrip)  # 分词
    segmentor.release()  # 释放模型

    return words


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



if __name__ == '__main__':
    select = 2 #重清洗-2/3选择

    
    '''补充LDA数据到数据库'''
    db = sqlite3.connect("../../data/db_LDA.db")
    c=db.cursor()

    #输入原始数据
    # end_flag = input("Input your end flag: ")#end_flag自定义
    end_flag = "end"
    next_app_flag = 'next'
    while True:
        # '''输入数据'''
        flag_test = False #是否测试(非测试时无限读取直至ctrl+C)
        print("Note: 1.end flag = 'end';2.next app flag = 'next'") #end_flag默认

        origin_data = []
        testing_data = []
        list_app_name = []

        app_name = input("Input No.1 app name: ")
        app_name = app_name.strip()
        data = input("Input No.1 app description:\n ")

        list_app_name.append(app_name)


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
            # print(type(words))
            origin_data.append(descrip)
            testing_data.append(words)#加入一个app的描述
            print("--------------------------------------------------------------------")
            if data.strip() != end_flag: #输入next
                data = input("Input No.%d app name or input 'end' to start satisfying: "%(cnt+1))

                if data.strip() != 'end':
                    list_app_name.append(data)
                    data = input("Input No.%d app description:\n "%(cnt+1))

        # print(testing_data)
        '''测试数据（不手动输入）'''
        flag_test = False #是否测试(非测试时无限读取直至ctrl+C)
        # testing_data = []
        # list_app_name = []
        # sql_origin = '''
        # select app_name,description from topic_vector_90 where id>37971;
        # '''
        # rows = c.execute(sql_origin)
        # for row in rows:
        #     list_app_name.append(row[0])
        #     temp = row[1].replace('\r\n'," ")
        #     testing_data.append(temp)
        # print(list_app_name)
        # print(testing_data)

        '''分大类'''
        # 二级分类 L1：16大类
        # num_topics_l1 = 16
        # output_directory_path_l1 = 'huawei_LDA-output-分' + str(num_topics_l1) + '大类-重清洗-%d'%select#使用的模型所在文件夹
        
        # 直接分类：100(1-3)/110/120/130/140/150(1-2)
        num_topics_l1 = 90
        output_directory_path_l1 = 'huawei_LDA-output-分' + str(num_topics_l1) + '类-重清洗-4-3'#使用的模型所在文件夹
        back = output_directory_path_l1.split('重清洗-4-')[-1]
        temp = str(num_topics_l1) + ("" if back.startswith("huawei") else "_"+back)


        list_l1_topic_p = satisfy_app(testing_data,output_directory_path_l1,num_topics_l1)
        '''分类结果写入txt文件'''
        temp_path = "test" if flag_test else "run"
        with open( 'results_%s/result_%sLDA_%s.txt'%(temp_path,temp_path,temp),'a' if not flag_test else 'w',encoding='utf-8') as f:
            for name,doc,data,description_ in zip(list_app_name,testing_data,list_l1_topic_p,origin_data):
                f.write("app name: %s\n"%name)
                f.write("description:%s\n"%description_)
                # f.write("description: %s\n"%doc)
                f.write("topic vector: %s\n\n"%str(data))

        for name,doc,data in zip(list_app_name,testing_data,list_l1_topic_p):
            # print("\t\t\tname_ = \'%s\'"%name,end="\n") #测试所需输入
            # print("\t\t\tvector_ = %s" % str(data))
            print("app name: %s"%name,end="\t")
            # print("\ndoc:\n %s" % doc.strip())
            print("topic vector：%s" % str(data))

            aa=""
            bb=""
            for a,b in data:
                aa+=str(a)+","
                bb+=str(b)+","
            # print(aa,'\n',bb.strip())

            sql_add = '''
            insert into topic_vector_90_3_0005(app_name,description,topics,probilities)\
                values('{0}','{1}','{2}','{3}')
            '''.format(name,doc.strip(),aa,bb.strip())
            c.execute(sql_add)
            # print('insert over')
        db.commit()

        # if flag_test: #测试,结束程序
        #     break

        # print("%s分类完成！"%app_name)
        print("========================================================================")

    db.close()

    ''' 二级分类 L2（暂弃）
    #人工选择每大类分别要分为几小类
    list_num_subtypes = [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3] 

    #在每大类下分小类：list_l2_topic_p
    alllist_l2_topic_p = [] #每个元素是一个大类下的小类信息list_l2_topic_p
    for topic,probility in list_l1_topic_p:
        num_topics_l2 = list_num_subtypes[int(topic)]
        output_directory_path_l2 = '结果集合-%d大类下划分小类-重清洗-%d/L1-topic%d/L2-分%d小类' % (num_topics_l1,select,topic,num_topics_l2)
        list_l2_topic_p = satisfy_app(testing_data,output_directory_path_l2,num_topics_l2)
        alllist_l2_topic_p.append(list_l2_topic_p)
        print("小类\n",list_l2_topic_p)s
        with open( 'result_LDA_%s.txt'%app_name,'a',encoding='utf-8') as f:
            f.write("大类%d下小类：\n%s\n"%(topic,str(list_l2_topic_p)))
    '''


    
