from bs4 import BeautifulSoup
import requests
import time
import json
import openpyxl
import urllib.request


all_app = [] #单个app[应用名，apk链接]
num=0

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
    'Cookie':'bdshare_firstime=1502503781235; KEY_WEB_USER_REALNAME_CLICK_COUNT=1; KEY_WEB_USER_REALNAME_INFO=%7B%22name%22%3A%22%E5%BE%90%E6%B2%90%E9%9B%A8%22%2C%22identity%22%3A%22152728199308030610%22%2C%22phone%22%3A%2213701057426%22%7D; ctoken=Bcd4ZK6hUqsDlR9TcC0Twdj-web; _gat=1; _ga=GA1.2.2141433936.1502503778; _gid=GA1.2.482913689.1508223401; Hm_lvt_c680f6745efe87a8fabe78e376c4b5f9=1508223408; Hm_lpvt_c680f6745efe87a8fabe78e376c4b5f9=1508228589',
    'X-Requested-With':'XMLHttpRequest'
}
# ajax_url = ['http://www.wandoujia.com/api/top/more?resourceType=0&page={}&ctoken=Bcd4ZK6hUqsDlR9TcC0Twdj-web'.format(str(i)) for i in range(2, 11)] #排行榜的url

def get_typepage_urls():
    parent_cates_index_url = 'http://www.wandoujia.com/category/app'
    parent_cate_urls = []
    urllib.request.urlretrieve(parent_cates_index_url, 'parent_cates_index_url.html')

    with open ('parent_cates_index_url.html', "r",encoding="utf-8") as myfile:
        targetData=myfile.read()

    # f_urls = open("parent_cate_urls.txt",'w',encoding="utf-8")
    if targetData:
        parsed_html = BeautifulSoup(targetData, "html.parser")
        for child_cate in parsed_html.find_all("li",{ "class":"parent-cate"}):
            for each in child_cate.find_all('a',class_ = "cate-link"):
                url_child_cate = str(each.get("href"))
                # name_child_cate = str(each.get_text())    #已写入txt
                # f_urls.writelines(url_child_cate)
                # f_urls.writelines('\t')
                # f_urls.writelines(name_child_cate)
                # f_urls.write("\n")
                parent_cate_urls.append(url_child_cate)
        # f_urls.close()    
        # print("大类url写入完成！")
        return parent_cate_urls

def get_child_cate_urls():
    cate_index_url = 'http://www.wandoujia.com/category/app'
    child_cate_urls = []

    web_data = requests.get(cate_index_url)
    soup = BeautifulSoup(web_data.text,'lxml')
    # print(soup)
    all_info = soup.select('div.child-cate > a')
    print(all_info)
    
    f_urls = open("child_cate_urls.txt",'w',encoding="utf-8")

    for single_info in all_info:
        print(single_info)
        name_child_cate = single_info.text
        url_child_cate = single_info.get('href')
        f_urls.writelines(url_child_cate)
        f_urls.writelines('\t')
        f_urls.writelines(name_child_cate)
        f_urls.write("\n")
    f_urls.close()    
    print("子类url写入完成！")


def get_first_page(url):
    global num
    # time.sleep(2)
    wb_data = requests.get(url)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    all_info = soup.select('div.app-desc > h2 > a')
    all_id = soup.select('')

    for single_info in all_info:
        single_app = []
        appName = single_info.text
        appID = single_info.get('href').split('/')[-1]
        apkURL = 'https://www.wandoujia.com/apps/'+str(appID)+'/download/dot?ch=detail_normal_dl'
        single_app.append(appName)
        single_app.append(apkURL)
        all_app.append(single_app)
        num = num+1
        print("app No.",num,'\t',appName)


def get_ajax_info(ajax_url):
    global num
    time.sleep(0.2)
    wb_data = requests.get(ajax_url, headers=headers).text
    json_data = json.loads(wb_data)
    json_data = json_data['data']['content']

    if json_data:
        soup = BeautifulSoup(json_data, 'lxml')
        all_info = soup.select('div.app-desc > h2 > a')


        for single_info in all_info:
            single_app = []
            appName = single_info.text
            appID = single_info.get('href').split('/')[-1]
            apkURL = 'https://www.wandoujia.com/apps/'+str(appID)+'/download/dot?ch=detail_normal_dl'
            single_app.append(appName)
            single_app.append(apkURL)
            all_app.append(single_app)
            num += 1
            print("app No.",num,'\t',appName)
        return True
    else:
        return False



def writeExcel(apk):
    wb = openpyxl.Workbook()
    wb.remove_sheet(wb.get_sheet_by_name('Sheet'))
    wb.create_sheet(index=0, title='apk_url')
    sheet = wb.get_sheet_by_name('apk_url')

    sheet.append(['应用名','apk_url'])
    for row in apk:
        sheet.append(row)

    # wb.save('apkURL_豌豆荚.xlsx') #全部
    wb.save('apkURL_豌豆荚_按子类-2.xlsx') #按子类



if __name__ == '__main__':
    # get_child_cate_urls()
    # parent_cate_urls = get_typepage_urls()
    
    parent_cate_urls_names_ids = []

    #全部
    # with open("parent_cate_urls.txt",'r',encoding="utf-8") as f_urls:
    #按各个子类
    with open("child_cate_urls.txt",'r',encoding="utf-8") as f_urls:
        for line in f_urls.readlines():
            id_temp = line.split('/')[-1].split('\t')[0]
            parent_cate_urls_names_ids.append([line.split('\t')[0],line.split('\t')[1],id_temp])

    #逐个连接爬取所以app的名字和appid，appid加到普通下载链接里
    try:
        for url,name,id in parent_cate_urls_names_ids:
            print("=============开始爬取",name[:-1],"================\n")
            get_first_page(url)

            #全部
            # ajax_url_pre = 'https://www.wandoujia.com/wdjweb/api/category/more?catId=' + id
            #按各个分类
            id_parent_cate = id.split('_')[0]
            ajax_url_pre = 'https://www.wandoujia.com/wdjweb/api/category/more?catId=' + id_parent_cate


            #全部
            # ajax_url = [ajax_url_pre+'&subCatId=0&page={}&ctoken=CWoZEsbsWfrNUB71rcoI8-rD'.format(str(i)) for i in range(2, 100)] #可能没到100
            #按各个子类
            id_sub_cate = id.split('_')[1]
            ajax_url_pre = ajax_url_pre + '&subCatId=' + id_sub_cate
            ajax_url = [ajax_url_pre+'&page={}&ctoken=CWoZEsbsWfrNUB71rcoI8-rD'.format(str(i)) for i in range(2, 100)] #可能没到100


            for single_url in ajax_url:
                print(single_url)
                is_page = get_ajax_info(single_url)
                if not is_page:
                    print('=============共',ajax_url.index(single_url)+1,'页================\n')

                    break
                print('=============第',ajax_url.index(single_url)+2,'页完成================\n')
            time.sleep(2)
            
    finally:  
        print("=============开始写入================\n")
        writeExcel(all_app)
        print("=============写入成功!================\n")

        



