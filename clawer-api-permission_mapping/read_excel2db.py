import os
import pandas as pd
import sqlite3
import string

path = '.\permissionList'
list_filename = os.listdir(path)

list_row_allfile = [] #所有文件中需要权限的API
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
    
    for row in list_row:
        try:
            if row[3] and (row not in list_row_allfile):#需要权限，去重
                list_row_allfile.append(row)
                try:
                    if row[4]:
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
    print("\r写入db_LDA.db: %d/%d"%(i,num_method_perm),end="")
    tag = row[2].replace("'",'"')#单引号换成双引号
    API = row[0].split('--')[0]+'.'+row[1].rstrip(string.digits)
    row[3]=row[3].replace("'",'"')#单引号换成双引号

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
    insert into api2perm_map(API,permTag,allPerm,dangerousPerm)\
        values('{0}','{1}','{2}','{3}');
    '''.format(API,tag,row[3],dangerousPerm) #去除class，method末尾的数字
    c.execute(sql)

db.commit()
db.close()
print("close database.")


