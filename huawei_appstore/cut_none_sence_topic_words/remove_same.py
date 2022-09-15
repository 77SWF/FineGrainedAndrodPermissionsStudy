# -*-coding:utf-8-*-

import os
"""
    合并文本文件
"""
###合并建模路径的
# path_d = '../LDA/huawei_LDA_output_原分类测试'
# derectory_names = os.listdir(path_d)

# keywords_file_paths = []
# for derectory_name in derectory_names:#进每一个大类的文件夹
#     if derectory_name == "keywords_and_p_all_topics.txt":
#         continue
#     files_path = path_d + '/' + derectory_name
#     file_names = os.listdir(files_path)
#     for file_name in file_names:
#         if file_name.split(".")[1] == 'topic_keys':
#             keywords_file_path = files_path + '/' +file_name
#             keywords_file_paths.append(keywords_file_path)

#### 文件夹里的
keywords_file_paths = []
path = os.getcwd() + '\\topic_words_1'
file_names = os.listdir(path)
for name in file_names:
    file_path = path + '\\' + name
    keywords_file_paths.append(file_path)
#####到这

merge_file = open("merge.txt",'w',encoding="utf-8")
for filepath in keywords_file_paths:
    for line in open(filepath,encoding="UTF-8"):
        merge_file.write(line)
    merge_file.write('\n')


"""
    去重
"""
merge_file = open('merge.txt', 'r',encoding="UTF-8")
newfile = open('rm_same_topic_words.txt', 'w',encoding="UTF-8")
new = []
words_list = []

for line in merge_file.readlines():
    # new_line = line.split("\t")[2:]
    # if len(new_line)>0:
    #     words = new_line[0].split(" ")
    #     for word in words:
    #         if word not in new:
    #             new.append(word)
    #             newfile.writelines(word)
    #             newfile.writelines('\n')

    ###读文件夹的
    if line not in new:
        new.append(line)
        newfile.writelines(line)


merge_file.close()
newfile.close()
