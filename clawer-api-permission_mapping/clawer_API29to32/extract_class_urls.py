from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

list_url = []
for i in range(29,33):
    url = 'https://developer.android.google.cn/sdk/api_diff/%s/changes/classes_index_additions'%str(i)
    list_url.append(url)

url_pre = 'https://developer.android.google.cn'

list_url_diff_ = []
list_url_diff = [] #去重

for url in list_url: #遍历4个API级别 29~32
    html = urlopen(url).read().decode('utf-8')
    soup = BeautifulSoup(html,'html5lib')
    list_div = soup.find_all('div',attrs={"style":'line-height:1.5em;color:black'})
    # print(len(list_div))

    for tag_div in list_div:
        list_a = tag_div.find_all('a',class_='hiddenlink')
        for tag_a in list_a:
            url_back = tag_a['href'].split('#')[0]
            url_diff = url_pre+url_back #API之间变化的页面，如https://developer.android.google.cn/sdk/api_diff/29/changes/pkg_android.icu.text#Bidi
            list_url_diff_.append(url_diff)

# f_url_diff = open('urls_diff_29to32.txt','w',encoding='utf-8') #保存到文件
for url in list_url_diff_: #去重
    if url not in list_url_diff:
        list_url_diff.append(url)
        # f_url_diff.write(url)
        # f_url_diff.write('\n')
# f_url_diff.close()


list_url_class_=[]
list_url_class=[] #去重

num_diff_page = 0
for url_diff in list_url_diff:
    num_diff_page+=1
    print("\rdiff_page: %d/%d"%(num_diff_page,len(list_url_diff)),end="")

    html = urlopen(url_diff).read().decode('utf-8')
    soup = BeautifulSoup(html,'html5lib')
    
    tag_added_classes = soup.find('table',attrs={'summary':'Added Classes'})
    if not tag_added_classes:#可能是interface！！改爬虫代码，判断是exception/interface还是classes
        tag_added_classes = soup.find('table',attrs={'summary':'Added Classes and Interfaces'}) 
    if not tag_added_classes:
        continue

    list_tr = tag_added_classes.find_all('tr',class_='TableRowColor')
    for tag_tr in list_tr:
        tag_a = tag_tr.find('a',attrs={'href':re.compile('.*')})
        url_back = tag_a['href'].split('..')[-1]
        url_class = url_pre+url_back
        list_url_class_.append(url_class)

f_url_classes = open('urlList_29to32.txt','w',encoding='utf-8') #保存到文件
for url in list_url_class_:
    if url not in list_url_class:
        list_url_class.append(url)
        f_url_classes.write(url)
        f_url_classes.write('\n')
f_url_classes.close()


