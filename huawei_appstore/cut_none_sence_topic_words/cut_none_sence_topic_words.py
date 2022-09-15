import csv
import pandas as pd
import xlwt
import xlrd
import xlutils.copy as xc
import re

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

def rm_words(doc_words,low_freq_words):
    out_str = ""

    words_num = len(doc_words)
    print("tatal:",words_num,'\t',end="")        

    cnt = 0
    for word in doc_words:
        if word not in low_freq_words:
            out_str += word
            out_str += " "
        else:
            cnt += 1
    print("rm:",cnt)        
    return out_str

# 
def cut_none_sence_words():
    file_path = '../huawei_appdescrip_spider/5-直接LDA-应用-华为应用市场app分类与功能描述-重清洗4.xls'
    none_sence_words = [line.strip() for line in open("none_sence_words.txt",encoding='UTF-8').readlines()]

    print("==============读取文件==============")

    df_sheets_dict = pd.read_excel(file_path,sheet_name = None,encoding="utf-8")
    sheets_name = list(df_sheets_dict.keys())

    for sheet_name in sheets_name:
        # if sheet_name == "实用工具" or sheet_name == "社交通讯" or sheet_name == "教育":
        #     continue
        final_strs = []
        final_strs.append(["迭代4-文件后缀"])#改！！！！！！！！

        df_sheet = df_sheets_dict[sheet_name] 
        doc_list = df_sheet['迭代2'].tolist()#改！！！！！！！
        
        print("==============开始过滤：表",sheet_name,"==============")

        i = 1
        for doc in doc_list:
            doc_words = str(doc).split(" ")

            #下面的运行一遍即可
            for word in doc_words: #处理每一个词
                if str(word).startswith("http") or str(word).startswith("www")  or str(word).endswith(".com") or str(word).endswith('.cn'):
                    # print("链接：",word)
                    doc_words[doc_words.index(word)] = ""
                    continue
                else:
                    is_match = re.match('[\.\-\d]+',str(word))
                    if is_match:
                        if(is_match.group() == str(word)):
                            doc_words[doc_words.index(word)] = ""
                            continue
                            # print("数字串：",word)
                if word.encode('utf-8').isalpha():
                    doc_words[doc_words.index(word)] = word.lower()
                    # print(word)
                elif word == "中老年" or word =="老年人" :
                    # print(word)
                    doc_words[doc_words.index(word)] = "中老年人"
                    # print("改后",doc_words[doc_words.index(word)])
                elif word == "Dota2" or word =="Dota":
                    doc_words[doc_words.index(word)] = "DOTA"
                elif word == "小学生" or word == "中小学生":
                    doc_words[doc_words.index(word)] = "中小学"
                elif word == "创作人":
                    doc_words[doc_words.index(word)] = "创作者"
                elif word == "公交卡" or word[-2:] == "通卡":
                    doc_words[doc_words.index(word)] = "交通卡"
                elif word == "ecg":
                    doc_words[doc_words.index(word)] = "心电图"
                    
            final_str = rm_words(doc_words,none_sence_words).strip()
            final_strs.append([final_str])
            # print(final_strs)

            print("app No.",i,'\t',end="")
            i += 1

        print("\n==============表",sheet_name,"过滤结束，写入结果==============")
        write_excel_xls_append(file_path,sheets_name.index(sheet_name),final_strs)
        print("==============表",sheets_name.index(sheet_name)+1,sheet_name,"写入成功==============")


if __name__ == '__main__':
    cut_none_sence_words()




