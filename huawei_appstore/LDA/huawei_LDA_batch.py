#coding=utf-8

from collections import defaultdict
from datetime import datetime
import math
from operator import itemgetter
import os
import random
import re

import numpy as np
import pandas as pd

import little_mallet_wrapper as lmw
import openpyxl

import copy
import csv

import xlwt
import xlrd
import xlutils.copy as xc

import os


path_to_mallet = 'C:/mallet/bin/mallet'  # CHANGE THIS TO YOUR MALLET PATH

dataset_path = '../huawei_appdescrip_spider/5-直接LDA-应用-华为应用市场app分类与功能描述-重清洗3-.csv'  # CHANGE THIS TO YOUR DATASET PATH
dataset_df = pd.read_csv(dataset_path,encoding="utf-8")

training_data = [t for t in dataset_df['迭代3-文件后缀'].tolist()]
training_data = [str(d).strip() for d in training_data if str(d)]


def write_excel_xls_append(path, id_sheet,value):
    index = len(value)  # 获取需要写入数据的行数

    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[id_sheet])  # 获取工作簿中所有表格中的的第一个表格

    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    cols_old = worksheet.ncols  # 获取表格中已存在的数据的行数

    new_workbook = xc.copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(id_sheet)  # 获取转化后工作簿中的第一个表格

    for i in range(0, index):
        for j in range(0, len(value[i])):
            new_worksheet.write(i, j+cols_old, str(value[i][j]))  # 追加写入数据，注意是从i+rows_old行开始写入
    new_workbook.save(path)  # 保存工作簿
    print("写入完成！")


'''
    训练模型
'''
def train_model(num_topics,
                path_to_training_data,
                path_to_formatted_training_data,
                path_to_model,
                path_to_topic_keys,
                path_to_topic_distributions,
                path_to_word_weights,
                path_to_diagnostics):

    lmw.import_data(path_to_mallet,
                    path_to_training_data,
                    path_to_formatted_training_data,
                    training_data)

    lmw.train_topic_model(path_to_mallet,
                        path_to_formatted_training_data,
                        path_to_model,
                        path_to_topic_keys,
                        path_to_topic_distributions,
                        path_to_word_weights,
                        path_to_diagnostics,
                        num_topics)

'''
    训练模型 L2
'''
def train_model_l2(num_topics,
                path_to_training_data,
                path_to_formatted_training_data,
                path_to_model,
                path_to_topic_keys,
                path_to_topic_distributions,
                path_to_word_weights,
                path_to_diagnostics,
                training_data):

    lmw.import_data(path_to_mallet,
                    path_to_training_data,
                    path_to_formatted_training_data,
                    training_data)

    lmw.train_topic_model(path_to_mallet,
                        path_to_formatted_training_data,
                        path_to_model,
                        path_to_topic_keys,
                        path_to_topic_distributions,
                        path_to_word_weights,
                        path_to_diagnostics,
                        num_topics)

    # print('Training topic model...')
    # flag = os.system(path_to_mallet + ' train-topics --input ' + path_to_formatted_training_data\
    #                                       + ' --num-topics ' + str(num_topics) \
    #                                       + ' --inferencer-filename ' + path_to_model \
    #                                       + ' --output-topic-keys ' + path_to_topic_keys \
    #                                       + ' --output-doc-topics ' + path_to_topic_distributions\
    #                                       + ' --topic-word-weights-file ' + path_to_word_weights\
    #                                       + ' --diagnostics-file ' + path_to_diagnostics\
    #                                       + ' --optimize-interval 10')

    # print('Complete',flag)



'''
    主题词
'''
def topic_words(num_topics,output_directory_path,num_training_data_l2):
    # # 只有词，没有概率 暂时没用
    # topic_keys_path = output_directory_path + '/mallet.topic_keys.' + str(num_topics)
    # topic_keys = [line.split('\t')[2].split() for line in open(topic_keys_path, 'r',encoding="utf-8")] 

    # 有词和概率
    word_weight_path = output_directory_path + '/mallet.word_weights.' + str(num_topics)

    topic_word_weight_dict = defaultdict(lambda: defaultdict(float))
    topic_sum_dict = defaultdict(float)
    with open(word_weight_path,'r',encoding="utf-8") as f:       
        for _line in f:        
            _topic, _word, _weight = _line.split('\t')
            topic_word_weight_dict[_topic][_word] = float(_weight)
            topic_sum_dict[_topic] += float(_weight)

    topic_word_probability_dict = defaultdict(lambda: defaultdict(float))
    for _topic, _word_weight_dict in topic_word_weight_dict.items():
        for _word, _weight in _word_weight_dict.items():
            topic_word_probability_dict[int(_topic)][_word] = _weight / topic_sum_dict[_topic]


    num_p = 20  #显示前几个主题词？

    newfile = open(output_directory_path+'/keywords_and_p_all_topics.txt', 'w',encoding="UTF-8")
    newfile.writelines("training data num: %d\n" % num_training_data_l2)

    for _topic, _word_probability_dict in topic_word_probability_dict.items():
        # print('Topic', _topic)
        newfile.writelines('Topic')
        newfile.writelines('\t')
        newfile.writelines(str(_topic))
        newfile.writelines('\n')
        newfile.writelines('\n')

        for _word, _probability in sorted(_word_probability_dict.items(), key=lambda x: x[1], reverse=True)[:num_p]:
            # print(round(_probability, 4), '\t', _word)
            p = round(_probability, 4)
            newfile.writelines(str(p))
            newfile.writelines('\t')
            newfile.writelines(str(_word))
            newfile.writelines('\n')
        newfile.writelines('-----------------------')
        newfile.writelines('\n')

    newfile.close()
    print("以概率排序的主题词写入完成！")
    return topic_word_probability_dict


'''
    doc主题分布
'''
def doc_distribute(num_topics,output_directory_path):
    topic_distributions = lmw.load_topic_distributions(output_directory_path + '/mallet.topic_distributions.' + str(num_topics))


    num_max_p_topics =  num_topics #取每个doc最可能的topic个数

    indexs_max_p_all = [] #存所有doc的主题向量，主题向量=[(主题,概率),()]

    for i in range(len(training_data)): #遍历所有doc
        p_topics = copy.deepcopy(topic_distributions[i]) #每个doc的概率list
        indexs_max_p = [] #存1个doc最可能的topic下标

        for j in range(num_max_p_topics): #找最大值
            max_p = max(p_topics)
            index_max_p = p_topics.index(max_p)

            # indexs_max_p.append((index_max_p,max_p)) #(主题下标，概率) 
            indexs_max_p.append((index_max_p,round(max_p,4))) #(主题下标，概率)
            # indexs_max_p.append((index_max_p,round(max_p,4)*100)) #(主题下标，概率) 概率单位%
            p_topics[index_max_p] = -1 #最大值改0

        indexs_max_p_all.append(indexs_max_p)#按doc原顺序的topic下标，概率大到小排



    # 只写入概率>0.05的topic
    print("写入主题向量...")

    data = []
    data.append(["主题","概率"])

    maxnum = len(indexs_max_p_all)

    for i in range(maxnum): 
        topic_vector = copy.deepcopy(indexs_max_p_all[i]) #遍历每个app的主题向量=[(主题,概率),()]
        temp = []

        for j in range(num_topics): #遍历主题向量内每个元组，共num_topics个
            if topic_vector[j][1] <= 0.05: 
                topic_vector = topic_vector[:j]
                break
            else:
                temp.append(topic_vector[j][0])
                temp.append(topic_vector[j][1])

        data.append(temp)
        
    write_excel_xls_append("LDA-应用-主题向量-分"+str(num_topics)+"大类-重清洗-3.xls",0,data) #改


'''
    doc主题分布 写入到数据库
'''
def doc_distribute_2db(num_topics,output_directory_path):
    topic_distributions = lmw.load_topic_distributions(output_directory_path + '/mallet.topic_distributions.' + str(num_topics))


    num_max_p_topics =  num_topics #取每个doc最可能的topic个数

    indexs_max_p_all = [] #存所有doc的主题向量，主题向量=[(主题,概率),()]

    for i in range(len(training_data)): #遍历所有doc
        p_topics = copy.deepcopy(topic_distributions[i]) #每个doc的概率list
        indexs_max_p = [] #存1个doc最可能的topic下标

        for j in range(num_max_p_topics): #找最大值
            max_p = max(p_topics)
            index_max_p = p_topics.index(max_p)

            # indexs_max_p.append((index_max_p,max_p)) #(主题下标，概率) 
            indexs_max_p.append((index_max_p,round(max_p,4))) #(主题下标，概率)
            # indexs_max_p.append((index_max_p,round(max_p,4)*100)) #(主题下标，概率) 概率单位%
            p_topics[index_max_p] = -1 #最大值改0

        indexs_max_p_all.append(indexs_max_p)#按doc原顺序的topic下标，概率大到小排



    # 只写入概率>0.05的topic
    print("写入主题向量...")

    data = []
    data.append(["主题","概率"])

    maxnum = len(indexs_max_p_all)

    for i in range(maxnum): 
        topic_vector = copy.deepcopy(indexs_max_p_all[i]) #遍历每个app的主题向量=[(主题,概率),()]
        temp = []

        for j in range(num_topics): #遍历主题向量内每个元组，共num_topics个
            if topic_vector[j][1] <= 0.05: 
                topic_vector = topic_vector[:j]
                break
            else:
                temp.append(topic_vector[j][0])
                temp.append(topic_vector[j][1])

        data.append(temp)
        
    write_excel_xls_append("LDA-应用-主题向量-分"+str(num_topics)+"大类-重清洗-3.xls",0,data) #改


'''
    散度
'''
def divergence(num_topics,output_directory_path,topic_word_probability_dict):
    divergence_file = open(output_directory_path+'/divergence_topic_words.txt', 'w',encoding="UTF-8")

    for i in range(16):
        k = i+1
        while(k<=num_topics-1):
            divergence = lmw.get_js_divergence_topics(i,k, topic_word_probability_dict)
            divergence_file.writelines(str(i)) 
            divergence_file.writelines('\t')
            divergence_file.writelines(str(k))
            divergence_file.writelines('\t')
            divergence_file.writelines('d = ')
            divergence_file.writelines(str(round(divergence,4)))

            divergence_file.writelines('\n')
            k += 1

    divergence_file.close()
    print("主题散度写入完成！")

if __name__ == '__main__':
    # num_topics = 16  # CHANGE THIS TO YOUR PREFERRED NUMBER OF TOPICS

    for i in range(12,16):    
        print("============正在分",i,"类============")
        num_topics = i

        # if i == 12:
        #     output_directory_path = 'huawei_LDA-output-分' + str(num_topics) + '大类-重清洗-3' # 改

        #     path_to_training_data           = output_directory_path + '/training.txt'
        #     path_to_formatted_training_data = output_directory_path + '/mallet.training'
        #     path_to_model                   = output_directory_path + '/mallet.model.' + str(num_topics)
        #     path_to_topic_keys              = output_directory_path + '/mallet.topic_keys.' + str(num_topics)
        #     path_to_topic_distributions     = output_directory_path + '/mallet.topic_distributions.' + str(num_topics)
        #     path_to_word_weights            = output_directory_path + '/mallet.word_weights.' + str(num_topics)
        #     path_to_diagnostics             = output_directory_path + '/mallet.diagnostics.' + str(num_topics) + '.xml'

        #     topic_word_probability_dict = topic_words(num_topics,output_directory_path)
        #     divergence(num_topics,output_directory_path,topic_word_probability_dict)
        # else:

        output_directory_path = '测试' + str(num_topics) + '大类-重清洗-3' # 改
        os.makedirs(output_directory_path)

        path_to_training_data           = output_directory_path + '/training.txt'
        path_to_formatted_training_data = output_directory_path + '/mallet.training'
        path_to_model                   = output_directory_path + '/mallet.model.' + str(num_topics)
        path_to_topic_keys              = output_directory_path + '/mallet.topic_keys.' + str(num_topics)
        path_to_topic_distributions     = output_directory_path + '/mallet.topic_distributions.' + str(num_topics)
        path_to_word_weights            = output_directory_path + '/mallet.word_weights.' + str(num_topics)
        path_to_diagnostics             = output_directory_path + '/mallet.diagnostics.' + str(num_topics) + '.xml'

        train_model(num_topics,
                path_to_training_data,
                path_to_formatted_training_data,
                path_to_model,
                path_to_topic_keys,
                path_to_topic_distributions,
                path_to_word_weights,
                path_to_diagnostics)
        topic_word_probability_dict = topic_words(num_topics,output_directory_path)
        doc_distribute(num_topics,output_directory_path)
        divergence(num_topics,output_directory_path,topic_word_probability_dict)