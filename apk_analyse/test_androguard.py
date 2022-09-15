# from dis import code_info
import os
import re
import sys
import traceback
from lxml import etree
import sqlite3

# # 引入androguard的路径，根据个人存放的位置而定
# androguard_module_path = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'androguard' )
# if not androguard_module_path in sys.path:
#     sys.path.append(androguard_module_path)
    
from androguard.misc import AnalyzeAPK
from androguard.core.bytecodes import apk
from androguard.core.androconf import load_api_specific_resource_module

'''取apk文件夹所有apk'''
path = r"D:/apk"
# files = []
# path_list=os.listdir(path)
# path_list.sort()
# for name in path_list:
#     if os.path.isfile(os.path.join(path, name)):
#         files.append(name)
# files = files[0:5]
files = ['语玩1.apk']
print("文件夹%s读取完成,共%d个APK!"%(path,len(files)))



def get_dir_api_permissions():
    ''' 从APK提取API对应权限到output_api_premission/apkname__api_perm(最新到API 28)
    返回code_infos=[code_info],每个APK的：[应用名，API的str，权限的str]
    '''
    out_path = ".\\output_api_premission"
    
    code_infos = [] #所有APK的信息
    for apkfile in files: #处理每个APK
        print("解析%s..."% apkfile,flush=True)
        file_name = os.path.splitext(apkfile)[0] #不含后缀

        try:  #APK解析成功(有的很慢)
            out = AnalyzeAPK(path + '/' + apkfile)
        except:#apk解析失败 下一个
            out = ["","",""] 
            with open("fail_AnalyzeAPK.txt",'a') as f:
                f.write("%s\t"%(file_name))
                f.write('\n')
                traceback.print_exc(file=f)#异常traceback写入文件
                # goto.begin
                print("failed.")
            continue

        #每个APK的信息，写入数据表
        code_info = [] #[应用名，API的str，权限的str]
        str_APIs = ""
        str_perms = ""
        list_APIs = []
        list_perms = []

        dx = out[2] 
        # print("successfully.")

        permmap = load_api_specific_resource_module('api_permission_mappings',api=32) 



        # 遍历所有class的每个method，提取需要权限的API
        for meth_analysis in dx.get_methods(): #返回MethodAnalysis对象（一个dex文件一个对象）的列表(迭代器) 而不是直接method的list
            meth = meth_analysis.get_method() #str(meth)如：Landroid/app/Activity;->navigateUpTo(Landroid/content/Intent;)Z
                                              #即 class;->method 描述符
            
            #改成map表的API格式，eg.android.net.wifi.WifiManager.WifiLock.isHeld
            meth_class_name = meth.get_class_name()
            meth_class_name =  meth_class_name[1:-1].replace('/','.').replace('$','.') #去掉L和末尾的; 改成android.net.wifi.WifiManager.WifiLock class形式
            meth_name = meth.get_name()
            name = meth_class_name + '.' + meth_name #android.net.wifi.WifiManager.WifiLock.isHeld形式
            # meth_descriptor = meth.get_descriptor()
            
            if name in ['android.net.wifi.aware.WifiAwareManager.attach','android.telephony.TelephonyManager.getImei']:
                meth_descriptor = meth.get_descriptor()
                temp_desc = re.findall(re.compile(r'(\(.*?\))'),meth_descriptor)[0]
                temp_desc = temp_desc[1:-1].replace(' ',';')
                temp_list = temp_desc.split(';')
                if "" in temp_list:
                    temp_list.remove("")
                name = name + "-" + str(len(temp_list))
                
            # name  = meth.get_class_name() + "-" + meth.get_name() + "-" + str(meth.get_descriptor())  #map文件同形式的完整函数名
            for key,value in permmap.items():  #key函数 value权限的list
                if name  == key:  #函数在map文件
                    if name not in list_APIs:
                        list_APIs.append(name)
                        str_APIs = str_APIs+name+';'
                    for perm in value:
                        if perm not in list_perms:
                            list_perms.append(perm)
                            str_perms = str_perms + perm + ";" #保存该函数信息
                            
                    # #api-perm映射写入txt文件
                    # result = str(meth) + ' : ' + str(value) # 提取的函数:[权限list]
                    # f_api_perm.write(result + '\n')  

        #该APK的信息
        code_info.append(file_name)
        code_info.append(str_APIs)
        code_info.append(str_perms)
        code_infos.append(code_info)

        # #api-perm映射写入txt文件结果
        # f_api_perm.close()
        # print("output:",file_name + "_api_perm.txt 写入完成!")

    
    return code_infos

def get_dir_manifest_xml():
    '''提取APK的Androidmanifest.xml为output_xml/apkname.html'''
    out_path = ".\\output_xml"
    for apkfile in files:
        file_name = os.path.splitext(apkfile)[0] 
        filename = os.path.join(out_path, file_name + ".xml") #html可格式化，更好查看

        if not os.path.isfile(filename):
            print("提取%s..."% apkfile,end="\t")
            a = apk.APK(path + '/' + apkfile) 

            # 保存xml到html文件
            xml = a.get_android_manifest_xml() #返回xml解码字符串class 'bytes'，用于保存文件
            f = open(filename, 'w', encoding='utf-8')
            f.write(str(etree.tostring(xml),'utf-8'))  
            f.close()
            print("over")
        else:
            print("%s.xml already exists!" % file_name)

        '''分析xml里的权限，则可不用写入xml文件再读取，等处理文件夹的代码写好再拷贝过来'''

def get_dir_perm():
    '''提取APK的所有uses-permission权限，和自己提取结果一样'''
    for apkfile in files:
        print("提取%s..."% apkfile,end="\t")
        a = apk.APK(path + '/' + apkfile) 
        list_perm = a.get_permissions() # 所有uses-permission权限





if __name__=='__main__':
    # '''连接数据库'''
    # db = sqlite3.connect("../data/db_LDA.db")
    # print("\nOpened database successfully...")
    # c = db.cursor()

    code_infos = get_dir_api_permissions()
    print(code_infos)
    # for app_name,API,perms in code_infos:
        # sql = '''
        # insert into perms_code(app_name,API,perms_code)\
        #     values("{0}","{1}","{2}");
        # '''.format(app_name,API,perms)
        # c.execute(sql)

    # get_dir_perm()
    # get_dir_manifest_xml()

    # '''关闭数据库'''
    # db.commit()
    # db.close()
    # print("Close database successfully.")