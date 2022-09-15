from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
'''区别
extrct_class_urls.py: 从diff page爬取的，可能不全
extrct_class_urls_2.py: 从https://developer.android.google.cn/reference/classes爬取，应该是所有的
'''

url = 'https://developer.android.google.cn/reference/classes'
url_pre = 'https://developer.android.google.cn'

# html = urlopen(url).read().decode('utf-8')
with open('page_classes.html','r',encoding='utf-8') as f:
    html = f.read()
soup = BeautifulSoup(html,'html5lib')
print("Get html from page_classes.html successfully...")
# with open('page_classes.html','w',encoding='utf-8') as f:
#     f.write(str(html))
#     f.write('\n')
#     print("Get page to page_classes.html successfully...")

# list_div = soup.find_all('div',class_='devsite-table-wrapper') #错误：检查里和get到的不一样，要看page_classes.html

list_div = soup.find_all('table') #26个字母项
num_classes = 0
list_url_class=[]

for tag_div in list_div:
    # #测试
    # with open('temp.html','w',encoding='utf-8') as f:
    #     f.write(str(tag_div))
    #     f.write('\n')
    #     print("写入一个表(按字母)")
    # list_tr = tag_div.find_all('tr',attrs={'data-version-added':re.compile(r'(0-9)*')})
    # list_tr = tag_div.find_all('tr') #5332个

    # for tr in list_tr_:
    #     if tr not in list_tr:
    #         print(str(tr))
    #         print("###################################################")
    
    list_td = tag_div.find_all('td',class_="jd-linkcol")
    num_classes = num_classes + len(list_td)
    
    for tag_td in list_td:
        str_td = str(tag_td)
        # print(str_td)
        url_back = re.findall((re.compile(r'<a href="(.*?)">')),str_td)[0]
        url_class = url_pre+url_back
        list_url_class.append(url_class)

with open('urlList_from_classesPage.txt','w',encoding='utf-8') as f:
    for url in list_url_class:
        f.write(url+".html")
        f.write('\n')
print("共 %d 个class.\n成功写入urlList_from_classesPage.txt!"%num_classes) #5332个

