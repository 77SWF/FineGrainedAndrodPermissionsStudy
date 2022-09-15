import pandas as pd
import sqlite3

#url列去重过、加'应用名-华为'列后的文件
# path='../apk_spider/apkURL_豌豆荚_按各子类.xlsx'
path='../apk_spider/apkURL_豌豆荚_按子类-2.xlsx'
df_sheet = pd.read_excel(path,sheet_name = 'apk_url',encoding="utf-8",keep_default_na=False)
names_apk =[t for t in df_sheet['应用名'].tolist() if t]
print(len(names_apk))
urls_apk =[t for t in df_sheet['apk_url'].tolist() if t]
names_huawei =[t for t in df_sheet['应用名-华为'].tolist() if t]

#连接数据库
db = sqlite3.connect('../data/db_LDA.db')
print("open database...")
c = db.cursor()

# 当前数据库里的
urls = []
names = []
records = c.execute('select * from apk_url;')
for record in records:
    urls.append(record[2])
    names.append(record[1].split('-')[0])

# 在华为里有该应用名的
# data = []
new_names_apk = [] #url不重复的项
new_urls_apk = []
num = 0
sum = len(names_apk)
for name,url in zip(names_apk,urls_apk):
    num+=1
    print('进度: %d/%d'%(num,sum))

    if (url not in urls) and (name in names_huawei): 
        new_names_apk.append(name)
        new_urls_apk.append(url)
        # data.append([name,url])

#豌豆荚：文件1-7757个;文件2-1278个
print("有效apk url:",len(new_names_apk),"个") 


#本次数据中，相同app_name的项的处理
for name,url in sorted(zip(new_names_apk,new_urls_apk)):
    count_excel = new_names_apk.count(name)
    if name in names:  #数据库里有
        count_db = names.count(name)
    else:
        count_db = 0
    count = count_db + count_excel

    if count > 1 and count_excel>0: #有重复:本次数据内 or 数据库内
        #修改全部重复的值，下一次轮到这些应用，不会重复了
        # 同名应用加编号:-i
        # 华为里只是可能有这个名字的应用，有可能华为1个，下载的apk有多个，手动判断！！
        # 是为了防止download_apk.py下载app重名但不同apk时不下载
        print('重名app:%s\t%d'%(name,count))
        with open("save2db_tb_apkurl_same_name_times",'r') as f:
            lines = f.readlines()
        with open("save2db_tb_apkurl_same_name_times",'w') as f:
            is_exist = False
            for line in lines:
                if name not in line: #其他行照旧写入
                    f.write(line)
                else: #同名行重新写入数字
                    is_exist=True
                    f.write(name)
                    f.write('\t')
                    f.write(count)
                    f.write('\n')


        for i in range(count_excel): #0~count-1
            index = new_names_apk.index(name)
            new_names_apk[index] = name + '-%d'%(count+i)
        #记录重复值，不在数据库的说明是这批数据才重复；若在数据仅有1个，也说明是这批才出现重复
        if name not in names or count_db == 1:
            f = open("save2db_tb_apkurl_same_name.txt",'a',encoding='utf-8')
            f.write(name)
            f.write('\n')
            f.close() 


# 处理完才能写入数据库（不能合并到上面的for里）
for name,url in zip(new_names_apk,new_urls_apk):
        sql = '''
        insert into apk_url(app_name,apk_url)\
            values("{0}","{1}");
        '''.format(name,url)
        c.execute(sql)

db.commit()
db.close()
print("close database.")


