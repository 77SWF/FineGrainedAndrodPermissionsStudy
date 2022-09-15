'''
读取api2perm_map_2到
1、permissions_32.json
2、permissions_32_dangerous.json
path:C:\Download\Lib\site-packages\androguard\core\api_specific_resources\api_permission_mappings

Note: 同名函数用descriptor，获得()里的东西后，用 ;和空格 分开后的len()，就是函数名-后面的数字
['android.net.wifi.aware.WifiAwareManager.attach-2/3',/
'android.telephony.TelephonyManager.getImei-0/1']

问题：手动删去最后一个k-v对后面的逗号
'''

import sqlite3


'''连接数据库'''
db = sqlite3.connect("../data/db_LDA.db")
print("\nOpened database successfully...")
c = db.cursor()

#另一个文件permissions_32_dangerous.json，列dangerousPerm
# path_json = "C:\\Download\\Lib\\site-packages\\androguard\\core\\api_specific_resources\\api_permission_mappings\\permissions_32_dangerous.json"
path_json = "C:\\Download\\Lib\\site-packages\\androguard\\core\\api_specific_resources\\api_permission_mappings\\permissions_32.json"
f = open(path_json,'w',encoding='utf-8')
f.write('{\n')


# sql = '''select API,dangerousPerm from api2perm_map_2;''' #列API dangerousPerm
sql = '''select API,allPerm from api2perm_map_2;''' # 列API allPerm
data = c.execute(sql)



''' json格式例子
{
    "android.net.wifi.WifiManager.WifiLock.acquire":[
        "WAKE_LOCK"
    ],
    "android.webkit.WebSettings.setGeolocationEnabled":[
        "ACCESS_FINE_LOCATION",
        "ACCESS_COARSE_LOCATION"
    ]
}
'''
last_row=[]
for row in data:
    if row==last_row: #同名同权限的只取1个
        continue
    if not row[1]:
        continue
    f.write("    \"%s\":[\n" % row[0])
    str_perms = row[1]
    list_perms = str_perms.split(";")
    try:
        list_perms.remove('')
    except:
        pass
    # print(list_perms)
    num_perms = len(list_perms)
    cnt_perms = 0
    for perm in list_perms:
        cnt_perms += 1
        f.write("        \"%s\"" % perm)
        if cnt_perms<num_perms:#不是最后一个权限
            f.write(",\n")
        else:#最后一个权限
            f.write("\n")
    f.write("    ],\n")

    last_row=row
f.write('}')


'''关闭数据库'''
db.commit()
db.close()
print("Close database successfully.")

print("over.")