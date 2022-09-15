import os
import pandas as pd
import little_mallet_wrapper as lmw
import huawei_LDA_batch

'''本py：16大类的每个大类，LDA划分成3~7小类
输出到文件夹：结果集合-16大类下划分小类/'''

def get_top_docs_(training_data, topic_distributions, topic_index):
    '''得到指定topic( topic_index 0~num_topics-1 )下、P>0.05的所有：
        (P,doc)、doc在training_data里的顺序(=下标+1)'''
    # 迭代zip(每个doc的主题向量 列表，所有doc 列表)
    # 遍历每个doc及其主题向量，取主题向量里指定index的主题的P，组成(P,doc)
    # 按P大到小排序，返回前n个(P,doc)
    sorted_data = sorted([(_distribution[topic_index], _document) 
                          for _distribution, _document 
                          in zip(topic_distributions, training_data)], reverse=True)
    for data in sorted_data:
        if data[0] > 0.05:
            continue
        else:
            index = sorted_data.index(data)
            break
    
    list_index = []#doc在training_data里的下标
    list_p_doc = sorted_data[:index]#(P,doc) P>0.05
    for data in list_p_doc:
        index = training_data.index(data[1]) #doc在training_data里的下标
        list_index.append(index+1) #+1表从1开始计数

    return list_index,list_p_doc




'''载入4w条training_data'''
path_to_mallet = 'C:/mallet/bin/mallet'  # CHANGE THIS TO YOUR MALLET PATH
dataset_path = '../huawei_appdescrip_spider/5-直接LDA-应用-华为应用市场app分类与功能描述-重清洗3-.csv'  # CHANGE THIS TO YOUR DATASET PATH
dataset_df = pd.read_csv(dataset_path,encoding="utf-8")

training_data = [t for t in dataset_df['迭代2'].tolist()] #所有描述数据list 按顺序
training_data = [str(d).strip() for d in training_data if str(d)]
print("training_data载入完成...")



'''模型训练路径设置'''
num_topics = 16  # CHANGE THIS TO YOUR PREFERRED NUMBER OF TOPICS

output_directory_path = 'huawei_LDA-output-分' + str(num_topics) + '大类-重清洗-2' # CHANGE THIS TO YOUR OUTPUT DIRECTORY
if not os.path.isdir(output_directory_path): #还没有输出文件夹时
    os.makedirs(output_directory_path) #创建输出文件夹

path_to_training_data           = output_directory_path + '/training.txt'
path_to_formatted_training_data = output_directory_path + '/mallet.training'
path_to_model                   = output_directory_path + '/mallet.model.' + str(num_topics)
path_to_topic_keys              = output_directory_path + '/mallet.topic_keys.' + str(num_topics)
path_to_topic_distributions     = output_directory_path + '/mallet.topic_distributions.' + str(num_topics)
path_to_word_weights            = output_directory_path + '/mallet.word_weights.' + str(num_topics)
path_to_diagnostics             = output_directory_path + '/mallet.diagnostics.' + str(num_topics) + '.xml'
print("路径设置完成...")



'''加载结果'''
# 只有词，没有概率 暂时没用
topic_keys_path = output_directory_path + '/mallet.topic_keys.' + str(num_topics)
topic_keys = [line.split('\t')[2].split() for line in open(topic_keys_path, 'r',encoding="utf-8")] 
topic_distributions = lmw.load_topic_distributions(output_directory_path + '/mallet.topic_distributions.' + str(num_topics))
print("原始LDA结果载入完成...")



'''使用get_top_docs_获得0~15共16个topic下对应的数据：原下标，(P,doc)，训练每个大类下小类'''
for i in range(16):
# for i in range(1):
    print("大类%d下划分小类..."%i)

    list_index,list_p_doc = get_top_docs_(training_data,topic_distributions,i)
    training_data_l2 = [t[1] for t in list_p_doc] #每大类的doc训练数据
    num_training_data_l2 = len(training_data_l2)
    
    '''每大类，分别3-7小类建模'''
    for j in range(3,8):
    # for j in range(3,4):
        print("============划分成",j,"小类============")
        num_topics_l2 = j

        output_directory_path_l2 = '结果集合-%d大类下划分小类-重清洗-2/L1-topic%d/L2-分%d小类' % (num_topics,i,j)
        if not os.path.isdir(output_directory_path_l2):
            os.makedirs(output_directory_path_l2)

        path_to_training_data_l2           = output_directory_path_l2 + '/training.txt'
        path_to_formatted_training_data_l2 = output_directory_path_l2 + '/mallet.training'
        path_to_model_l2                   = output_directory_path_l2 + '/mallet.model.' + str(num_topics_l2)
        path_to_topic_keys_l2              = output_directory_path_l2 + '/mallet.topic_keys.' + str(num_topics_l2)
        path_to_topic_distributions_l2     = output_directory_path_l2 + '/mallet.topic_distributions.' + str(num_topics_l2)
        path_to_word_weights_l2            = output_directory_path_l2 + '/mallet.word_weights.' + str(num_topics_l2)
        path_to_diagnostics_l2             = output_directory_path_l2 + '/mallet.diagnostics.' + str(num_topics_l2) + '.xml'

        #训练模型
        huawei_LDA_batch.train_model_l2(num_topics_l2,
                path_to_training_data_l2,
                path_to_formatted_training_data_l2,
                path_to_model_l2,
                path_to_topic_keys_l2,
                path_to_topic_distributions_l2,
                path_to_word_weights_l2,
                path_to_diagnostics_l2,
                training_data_l2)
        
        #写入主题词及其概率分布：keywords_and_p_all_topics.txt
        topic_word_probability_dict_l2 = huawei_LDA_batch.topic_words(num_topics_l2,output_directory_path_l2,num_training_data_l2)
        
        #写入散度
        huawei_LDA_batch.divergence(num_topics_l2,output_directory_path_l2,topic_word_probability_dict_l2)
        
        #导入主题向量，按training_data熟悉怒写入到excel
        #改！！！！按list_index顺序存到数据库
        # huawei_LDA_batch.doc_distribute(num_topics_l2,output_directory_path_l2)


