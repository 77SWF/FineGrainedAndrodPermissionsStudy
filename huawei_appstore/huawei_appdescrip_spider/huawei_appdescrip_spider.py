# -*- codeing = utf-8 -*-
# @Time : 2022年2月22日
# @Author : 苏婉芳
# @Software: vscode

import requests
import json
import random
from concurrent.futures import ThreadPoolExecutor
#import pymongo
import csv


class HuaWei_appPrase(object):
    # 返回子分类信息：[uri，分类名，子分类名]
    def get_uri(self):
        paizhao_subtab_id = '0b58fb4b937049739b13b6bb7c38fd53'  # 拍照的tabid，拍摄美化的第一个不是热门

        subtab_info_list = [] #每项是一个list，每个小list是一个子分类的信息

        # all_tab_uri = list()  # 不含热门
        all_hot_subtab_uri = list() #子分类中“热门”的uri

        for i in range(2):
            # if i == 0:  # 应用
            #     url = 'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&uri=b2b4752f0a524fe5ad900870f88c11ed&maxResults=25&zone=&locale=zh_CN'
            # else:  # 游戏
            #     url = 'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&uri=56a37d6c494545f98aace3da717845b7&maxResults=25&zone=&locale=zh_CN'
            url = 'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&uri=56a37d6c494545f98aace3da717845b7&maxResults=25&zone=&locale=zh_CN'
            r = requests.get(url)
            _json_dict = json.loads(r.text)
            # tabInfo:[{tabId:"",statKey:""},{}]
            tabInfo_list = _json_dict.get('tabInfo')

            for tabInfo in tabInfo_list: # 遍历每个分类
                tab_name = tabInfo.get('tabName') # 所有子分类都是这个分类下的
                
                # # 中断后从新闻阅读继续
                # if tab_name == "影音娱乐" or tab_name == "实用工具" or tab_name == "社交通讯" or tab_name == "教育":
                #     continue

                # 中断后从角色扮演继续
                if tab_name == "角色扮演" or tab_name == "休闲益智":
                    continue
                subtabInfo_list = tabInfo.get('tabInfo') #当前分类下的所有子分类

                # 热门子类别
                hot_subtab = subtabInfo_list[0]
                subtab_id = hot_subtab.get('tabId')
                all_hot_subtab_uri.append(subtab_id)

                for subtabInfo in subtabInfo_list: #遍历每个子分类(除：拍摄美化-拍照)
                    subtab_info = [] #子分类信息：[uri，分类名，子分类名]
                    subtab_id = subtabInfo.get('tabId') #uri

                    if subtab_id not in all_hot_subtab_uri:
                        subtab_info.append(subtab_id) #uri
                        subtab_info.append(tab_name) #分类名

                        subtab_name = subtabInfo.get('tabName')
                        subtab_info.append(subtab_name) #子分类名

                        subtab_info_list.append(subtab_info)

            paizhao_subtab_info = [paizhao_subtab_id,"拍摄美化","拍照"]
            subtab_info_list.append(paizhao_subtab_info)
            # print(subtab_info_list)
        # print("---------------------")
        return subtab_info_list

    # 获取每个分类里应用的appid
    def get_appid(self, uri):
        n = 1
        # 死循环，当layoutData为空时，停止获取appid，即一个类别爬取结束
        while True:
            url = f'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum={n}&uri={uri}&maxResults=250&zone=&locale=zh_CN'
            # url=f'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&uri=33ef450cbac34770a477cfa78db4cf8c&maxResults=250&zone=&locale=zh_CN'

            r = requests.get(url)
            _json_dict = json.loads(r.text)
            layoutData_info = _json_dict.get('layoutData')

            if len(layoutData_info) != 0:
                for app in layoutData_info:
                    datalist = app.get('dataList')
                    for app_type_list in datalist:
                        appid = app_type_list.get('appid')
                        # print(appid) # 测试
                        yield appid
                n += 1
            else:
                break

    # 解析主程序，用于解析每个app ["应用名","功能描述","更新描述"]
    def parse(self, appid):
        app_info = [] # ["应用名","功能描述","更新描述"]

        url = f'https://web-drcn.hispace.dbankcloud.cn/uowap/index?method=internal.getTabDetail&serviceType=20&reqPageNum=1&maxResults=25&uri=app%7C{appid}&shareTo=&currentUrl=https%253A%252F%252Fappgallery.huawei.com%252F%2523%252Fapp%252F{appid}&accessId=&appid={appid}&zone=&locale=zh_CN'
        r = requests.get(url)
        r.encoding = 'utf-8'
        _json_dict = json.loads(r.text)

        app_layoutData = _json_dict.get('layoutData')
        
        #APP名字
        aim_appname = app_layoutData[1]
        name_datalist = aim_appname.get('dataList')
        # print(app_datalist)
        for data1 in name_datalist:
            app_name = data1.get('name')
            # print(app_name)
            app_info.append(app_name) #应用名
            # item['app_name'] = data1.get('name')
        # print("=============")

        # 功能描述 在dataList[6]或[7]
        aim_intro = app_layoutData[7]
        intro_datalist = aim_intro.get('dataList')
        for data2 in intro_datalist:
            app_intro = data2.get('appIntro')
            if app_intro:
                app_intro_format = app_intro.replace('\n', '').replace('\r', '').replace('\t', '')
                # item['app_intro'] = app_intro_format
                app_info.append(app_intro_format)
                # print(app_intro_format)
            else:
                aim_intro = app_layoutData[6]
                intro_datalist = aim_intro.get('dataList')
                for data2 in intro_datalist:
                    app_intro2 = data2.get('appIntro')
                    if app_intro2:
                        app_intro_format = app_intro2.replace('\n', '').replace('\r', '').replace('\t', '')
                        # item['app_intro'] = app_intro_format
                        app_info.append(app_intro_format)
                        # print(app_intro_format)

                    else:
                        # item['app_intro'] = ""
                        app_info.append("")
                        print("================no intro===================")

        # 更新内容 在dataList[5]或[6]
        aim_update = app_layoutData[5]
        update_datalist = aim_update.get('dataList')
        for data in update_datalist:
            app_update = data.get('body')
            if app_update:
                app_update_format = app_update.replace('\n', '').replace('\r', '').replace('\t', '')
                app_info.append(app_update_format)
            else:
                aim_update = app_layoutData[6]
                update_datalist = aim_update.get('dataList')
                # print(update_datalist)
                for data in update_datalist:
                    app_update = data.get('body')
                    # print(app_update) # 有
                    if app_update:
                        app_update_format = app_update.replace('\n', '').replace('\r', '').replace('\t', '')
                        app_info.append(app_update_format)
                        # print(app_update_format)
                    else:
                        app_info.append("")
                        print("================no update===================")

        return app_info

    def saveData(datalist,savepath):
        '''
        保存datalist里的每条数据到指定路径的指定文件savepath
        '''
        print("save to csv...")
        


        for i in range(0,50000):
            # print("存入第%d条" %(i+1))
            data = datalist[i]
            # print(data)
            
        print("save over!")
        

# 主函数
def main():
    #创建csv文件
    savepath = "华为应用市场app分类与功能描述.csv"
    f = open(savepath,'a',encoding='utf-8-sig',newline='')
    save_csv = csv.writer(f)
    print("打开华为应用市场app分类与功能描述.csv............")

    # col = ["分类","子分类","应用名","功能描述","更新描述"]
    # save_csv.writerow(col) #表头

    huaweiapp_prase = HuaWei_appPrase()
    
    for subtab_info_list in huaweiapp_prase.get_uri(): #遍历每个子分类
        num = 1
        app_info_list = [] #一个子分类的所有应用信息
        uri = subtab_info_list[0] 
        # tab_name = subtab_info_list[1]
        # subtab_name = subtab_info_list[2]
        app_info1 = subtab_info_list[1:] #[类别，子类别]

        for appid in huaweiapp_prase.get_appid(uri): #遍历当前子分类下每个应用
            app_info2 = huaweiapp_prase.parse(appid) # [应用名，应用介绍，应用更新]
            
            app_info = app_info1 + app_info2
            app_info_list.append(app_info)

            print(num,appid,app_info2[0])
            num = num + 1
    
        #写入一个子分类应用数据
        maxnum = len(app_info_list)
        for i in range(maxnum):
            one_app = app_info_list[i]
            save_csv.writerow(one_app)
            i = i+1
        print("成功写入子类别",app_info1[1],"所有app数据...")
        
    f.close()


    print("********************程序结束********************")


if __name__ == '__main__':
    main()
