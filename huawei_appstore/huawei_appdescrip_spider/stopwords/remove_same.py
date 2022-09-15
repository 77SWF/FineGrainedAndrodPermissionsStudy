# -*-coding:utf-8-*-

import os
"""
    合并文本文件
"""
merge_file_dir = os.getcwd()+"\\temp" #4个停用词文件
filenames = os.listdir(merge_file_dir)
file = open('ch_stopwords_merge-2.txt', 'w',encoding="UTF-8")

for filename in filenames:
    filepath = merge_file_dir + '\\' + filename
    for line in open(filepath,encoding="UTF-8"):
        file.writelines(line)
    file.write('\n')

"""
    去重
"""
lines = open('ch_stopwords_merge-2.txt', 'r',encoding="UTF-8")
newfile = open('ch_stopwords-2.txt', 'w',encoding="UTF-8")
new = []
for line in lines.readlines():
    if line not in new:
        new.append(line)
        newfile.writelines(line)

file.close()
newfile.close()
