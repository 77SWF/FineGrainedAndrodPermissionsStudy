'''
读取api2perm_map_2到
1、map_dangerousPerm2API.json

'''

import sqlite3


dangerousPermissionList = ["ACCEPT_HANDOVER","ACCESS_COARSE_LOCATION","ACCESS_FINE_LOCATION","ADD_VOICEMAIL","ANSWER_PHONE_CALLS","BODY_SENSORS","CALL_PHONE","CAMERA","GET_ACCOUNTS","PROCESS_OUTGOING_CALLS","READ_CALENDAR","READ_CALL_LOG","READ_CONTACTS","READ_EXTERNAL_STORAGE","READ_PHONE_NUMBERS","READ_PHONE_STATE","READ_SMS","RECEIVE_MMS","RECEIVE_WAP_PUSH","RECORD_AUDIO","SEND_SMS","USE_SIP","WRITE_CALENDAR","WRITE_CALL_LOG","WRITE_CONTACTS","WRITE_EXTERNAL_STORAGE","ACCEPT_HANDOVER","ACTIVITY_RECOGNITION","ACCESS_BACKGROUND_LOCATION","ACCESS_MEDIA_LOCATION","UWB_RANGING","BLUETOOTH_ADVERTISE","BLUETOOTH_CONNECT","BLUETOOTH_SCAN","BODY_SENSORS_BACKGROUND","NEARBY_WIFI_DEVICES","POST_NOTIFICATIONS","READ_MEDIA_AUDIO","READ_MEDIA_IMAGE","READ_MEDIA_VIDEO","READ_CELL_BROADCASTS"]
dict_perm2api = {}
for perm in dangerousPermissionList:
    dict_perm2api[perm] = []
print("initiate dict_perm2api...")


'''连接数据库'''
db = sqlite3.connect("../data/db_LDA.db")
print("\nOpened database successfully...")
c = db.cursor()

path_json = "map_perm2API.json"
f = open(path_json,'w',encoding='utf-8')
f.write('{\n')


sql = '''select API,dangerousPerm from api2perm_map_2;''' # 列API dangerousPerm
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
for row in data: #写入dict_perm2api
    if not row[1]:#不需危险权限
        continue
    list_perm = row[1].split(';')
    try:
        list_perm.remove("")
    except:
        pass

    api = row[0]
    for perm in list_perm:
        if api not in dict_perm2api[perm]:
            dict_perm2api[perm].append(api)

for perm,list_api in dict_perm2api.items():
    f.write("    \"%s\":[\n" % perm)

    num_apis = len(list_api)
    cnt_api = 0
    for api in list_api:
        cnt_api+=1
        f.write("        \"%s\"" % api)
        if cnt_api<num_apis:#不是最后一个api
            f.write(",\n")
        else:
            f.write("\n")
    f.write("    ],\n")
f.write('}')


'''关闭数据库'''
db.commit()
db.close()
print("Close database successfully.")

print("over.")