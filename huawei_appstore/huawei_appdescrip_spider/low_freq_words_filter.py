import csv
from pyltp import Segmentor


def get_low_freq_words():
    word_count = {}

    with open("预处理-应用-华为应用市场app分类与功能描述.csv",'r',encoding="utf-8") as f:
        print("==============读取文件,开始计数==============")
        reader = csv.reader(f)
        i = 1
        for row in reader:
            print("app:",i)
            doc = row[0]
            words = doc.split(" ")
            for word in words:
                word_count[word] = word_count.get(word,0) + 1
            i += 1
    print("==============计数结束==============")

    # # 词频小到大排序            
    # word_items = list(word_count.items())
    # word_items.sort(key=lambda x:x[1], reverse=False)

    print("==============写入低频词：low_freq_words.txt==============")
    words_txt = open('low_freq_words_2.txt','w',encoding="UTF-8")
    for word in word_count.keys():
        cnt = word_count[word]
        if cnt < 2:
            words_txt.writelines(word)
            words_txt.writelines('\n')
    print("==============写入完成==============")


def rm_low_freq(doc_words,low_freq_words):
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


def cut_low_freq_words():
    final_strs = []
    final_strs.append("去低频词")

    print("==============读取文件,开始过滤低频词==============")

    low_freq_words = [line.strip() for line in open("low_freq_words.txt",encoding='UTF-8').readlines()]

    with open("预处理-应用-华为应用市场app分类与功能描述.csv",'r',encoding="utf-8") as f2:
        reader = csv.reader(f2)

        i = 1
        for row in reader:
            descrip = row[0]
            descrip_words = descrip.split(" ")
            final_str = rm_low_freq(descrip_words,low_freq_words).strip()
            final_strs.append(final_str)
            print("app No.",i,'\t',end="")
            i += 1
            # print(descrip,"\n----------------------------------------------------------\n",final_str)


    print("==============过滤结束，写入结果==============")

    after_cut_csv = open("去低频词1-应用-华为应用市场app分类与功能描述.csv",'w',encoding='utf-8-sig',newline='')
    save_csv = csv.writer(after_cut_csv)
    maxnum = len(final_strs)
    # print(final_strs)
    for i in range(maxnum):
        save_csv.writerow([final_strs[i]])
        i = i+1
    after_cut_csv.close()

    print("========写入完成========")


if __name__ == '__main__':
    # get_low_freq_words()
    cut_low_freq_words()




