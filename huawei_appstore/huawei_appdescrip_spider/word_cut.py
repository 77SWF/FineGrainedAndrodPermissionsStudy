# -*- coding: utf-8 -*-
# @Time : 2022年2月26日
# @Author : 苏婉芳
# @Software: vscode
# pthon 3.6.7-64bit

import csv
import os
from pyltp import Segmentor

#去除中文停用词
def rm_stopwords(words):
    root = os.path.dirname(os.path.realpath(__file__))
    stopwords = [line.strip() for line in open(root+"\\stopwords\\new_ch_stopwords.txt",encoding='UTF-8').readlines()]
    out_str = ""
    for word in words:
        if word not in stopwords:
            out_str += word
            out_str += " "
    return out_str


def cut_words():
    LTP_DATA_DIR = r'C:\Users\susu\Desktop\huawei_appstore\ltp_data'  # ltp模型目录的路径
    cws_model_path = os.path.join(LTP_DATA_DIR, 'cws.model')  # 分词模型路径，模型名称为`cws.model`


    segmentor = Segmentor()  # 初始化实例
    segmentor.load(cws_model_path)  # 加载模型

    final_strs = []
    with open("游戏-华为应用市场app分类与功能描述.csv", 'r',encoding='utf8',newline='') as f:
        # final_strs.append("分词与去停用词结果")
        reader = csv.reader(f)

        i = 1

        print("========开始分词========")
        for row in reader: #第6列综合描述
            descrip = row[5]
            words = segmentor.segment(descrip)  # 分词
            # after_cut.append('/'.join(words))
            # print('/'.join(words))

            final_str = rm_stopwords(words)
            final_strs.append(final_str)

            print("app No.",i)
            # print(final_str)
            # print("============================")
            i = i+1
            # if i == 10:
            #     break

    segmentor.release()  # 释放模型
    print("===========处理结束，写入结果============")

    f2 = open("预处理-游戏-华为应用市场app分类与功能描述.csv",'w',encoding='utf-8-sig',newline='')
    save_csv = csv.writer(f2)
    maxnum = len(final_strs)
    # print(final_strs)
    for i in range(maxnum):
        save_csv.writerow([final_strs[i]])
        i = i+1
    f2.close()
    print("========写入完成========")

# if __name__ == '__main__':
#     cut_words()