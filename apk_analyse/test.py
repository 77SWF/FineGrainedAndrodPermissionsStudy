import os,sqlite3
'''获取数据表中已有perms的app_name列表'''
def get_appname_exist_perms():
    '''获取数据表中已有perms的app_name列表'''
    db = sqlite3.connect("../data/db_LDA.db")
    # print("Opened database successfully.")
    c = db.cursor()

    names = c.execute('''select app_name from perms_declare_2;''')
    list_names = [row[0] for row in names]
    db.close()
    return list_names



def get_dir_filepaths(dirpath):
    '''获取目录dirpath下所有文件的路径list'''
    list_file_path = [] #
    filename_list=os.listdir(dirpath)
    filename_list.sort()

    #数据表中已有perms的app_name列表
    list_appname_exist_perms = get_appname_exist_perms()

    cnt = 0
    for filename in filename_list:
        app_name = filename.split('.')[0]
        #文件夹下列出的是文件，且该apk还没有在数据库里存入perms
        file_path = os.path.join(dirpath, filename)
        if os.path.isfile(file_path) and (app_name not in list_appname_exist_perms) :
            list_file_path.append(file_path)

        # #删除已经分析过的apk文件
        # if os.path.isfile(file_path) and (app_name in list_appname_exist_perms) :
        #     cnt+=1
        #     os.remove(file_path)
        #     print("remove file No.%d %s"%(cnt,app_name))
    return list_file_path

apk_dir = r"D:/apk"
num=212
list_file_path = get_dir_filepaths(apk_dir)
for apk_path in list_file_path:
    num+=1
    app_name = apk_path.split('\\')[-1].split('.')[0]
    print(app_name)
