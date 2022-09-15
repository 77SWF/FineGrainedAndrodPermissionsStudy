import os
import pandas as pd
import sqlite3
import string
from bs4 import BeautifulSoup
import re

find_permission = re.compile(r'android:name="(.*?)"') #permission

def get_all_perms():
    '''从源码12版本清单文件提取所有权限：689个'''
    allpermList = []
    source_code_path = "../data/manifests_source_code/AndroidManifest-Android12.xml"
    with open(source_code_path,'r',encoding="utf-8") as f:
        xml = f.read()
        soup = BeautifulSoup(xml,"xml")
        items_perm = soup.find_all('permission')
        for item in items_perm:
            item = str(item)
            perm = re.findall(find_permission,item)[0]

            perm = perm.split('.')[-1]
            allpermList.append(perm)

            #发现没必要分什么开头了
            # if perm.startswith("com.android."):
            #     allpermList.append(perm)
            # else:
            #     perm = perm.split('.')[-1]
            #     allpermList.append(perm)

    print('源码里权限个数：',len(allpermList)) #689个
    return allpermList




path = '.\permissionList'
list_filename = os.listdir(path)

# allpermList = get_all_perms()
'''get_all_perms()的结果从txt读取'''
allpermList = []
path_txt_allpermList_sourceCode = r'..\data\allpermList_sourceCode.txt'
with open(path_txt_allpermList_sourceCode,'r',encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        allpermList.append(line.strip()) #默认空格或换行符
print('源码里权限个数：',len(allpermList)) #689个



list_row_allfile = [] #所有文件中需要权限的API [row[0],row[1],tag,新的perms,row[4]]
num_row = 0
num_file = 0
num_dangerous = 0

for filename in list_filename:
    num_file +=1
    print("handle %s"%filename)
    path_file = os.path.join(path,filename)

    df_sheet = pd.read_excel(path_file,header=None,encoding="utf-8",keep_default_na=False)
    list_row = df_sheet.values.tolist()

    num = len(list_row)
    num_row = num_row + num
    
    for row in list_row: #excel的每一行
        data = []
        perms = ""
        try:
            if row[2]: #有含"permission"的tag,重新读[row[0],row[1],row[2],新的perms,row[4]]
                tag = row[2]
                for perm in allpermList: #重新获取perms
                    if perm in tag: #tag里有这个权限
                        perms = perms + perm + ";"
                        
                data.append(row[0])
                data.append(row[1])
                data.append(row[2])
                data.append(perms) #有permission tag的行先写入data
                data.append(row[4])
            if perms and (data not in list_row_allfile):#需要权限，且去重
                list_row_allfile.append(data)
                try:
                    if row[4]: #有危险权限
                        num_dangerous+=1
                except:
                    pass
        except:
            continue

num_method_perm = len(list_row_allfile) #需要权限的API总数
with open("read_excel2db_log.txt",'w',encoding='utf-8') as f:
    f.write("共%d个文件，%d个method，其中%d个需要权限,%d个包括dangerous权限"%(num_file,num_row,num_method_perm,num_dangerous))
    print("共%d个文件，%d个method，其中%d个需要权限,%d个包括dangerous权限"%(num_file,num_row,num_method_perm,num_dangerous))

path_db = 'C:/Users/susu/Desktop/Graduation_Design/FineGrainedAndrodPermissionsStudy/data/db_LDA.db'
db = sqlite3.connect(path_db)
c = db.cursor()
print("open database...")


#排序：先按类,类内按method
list_row_allfile.sort(key=lambda x:(x[0],x[1]))
i = 0 
for row in list_row_allfile:
    i+=1
    print("\r写入db_LDA.db: %d/%d %s"%(i,num_method_perm,row[1].rstrip(string.digits)),end="")
    # tag = re.sub("'","\'",row[2])
    tag = row[2].replace("'",'"') #单引号换成双引号
    # tag = tag.replace("'",'"') #单引号换成双引号
    API = row[0].split('--')[0]+'.'+row[1].rstrip(string.digits)
    row[3]=row[3].replace("'",'"')#单引号换成双引号

    dangerousPerm = ""
    try:
        if row[4]:
            dangerousPerm = row[4]
    except:
            dangerousPerm = ""

    # try:
    #     if row[3]:
    #         allPerm = row[3]
    # except:
    #         allPerm = ""        

    sql = '''
    insert into api2perm_map_2(API,permTag,allPerm,dangerousPerm)\
        values('{0}','{1}','{2}','{3}');
    '''.format(API,tag,row[3],dangerousPerm) #去除class，method末尾的数字
    c.execute(sql)

    # try:
    #     sql = '''
    #     insert into api2perm_map_2(API,permTag,allPerm,dangerousPerm)\
    #         values('{0}','{1}','{2}','{3}');
    #     '''.format(API,tag,row[3],dangerousPerm) #去除class，method末尾的数字
    #     c.execute(sql)
    # except:
    #     with open("test.txt",'a') as f:
    #         f.write(API)
    #         f.write('\n\n')
    #         f.write(tag)
    #         f.write('\n\n')
    #         f.write(row[3])
    #         f.write('\n\n')
    #         f.write(dangerousPerm)
    #         f.write('\n\n')
    #     print("\n写入txt\n")
        
db.commit()
db.close()
print("close database.")


