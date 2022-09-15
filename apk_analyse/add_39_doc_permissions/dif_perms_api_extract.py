import pandas as pd
import lxml
from bs4 import BeautifulSoup
import xlwt
import re,csv

path = 'dif_doc_to_dataset.txt' 
perms_diff = []
with open(path,"r",encoding="utf-8") as f_txt:
    for line in f_txt.readlines():
        perms_diff.append(line[:-1].strip())
print(len(perms_diff))

f_html = open("api_perms_doc.html","r",encoding="utf-8")
html = f_html.read()
# html = askURL('https://developer.android.com/reference/android/Manifest.permission')

bs = BeautifulSoup(html,"html.parser")
items = bs.find_all('div',attrs={"data-version-added":re.compile(r'[0-9]*')})
# items = bs.find_all(lambda element:'data-version-added' in element.attrs)
# print(items)

infos_perm = []
num =0
i=0
for item in items[1:]: #为什么
    info_perm = []
    item_lxml = lxml.etree.HTML(str(item))
    perm = item_lxml.xpath('//h3/@data-text')[0]
    i=i+1
    print("第",i,"个:",perm)

    if perm in perms_diff: #是缺少的权限
        num=num+1
        print(num,': ',perm)

        api_item = item.find('div',class_="api-level")
        api_level = api_item.find('a').text.split(" ")[-1]

        list_text = item_lxml.xpath('//div/p/text()')
        for text in list_text:
            if "Protection level" in text:
                pro_level = text.split(': ')[1].strip()
                break
            else:
                pro_level = ""

        info_perm.append(perm)
        info_perm.append(api_level)
        info_perm.append(pro_level)
        infos_perm.append(info_perm)
        # print(info_perm)

path_new = '../../data/安卓权限-补充.csv'  # CHANGE THIS TO YOUR DATASET PATH
f = open(path_new,"w",encoding="utf-8",newline='')
save_csv = csv.writer(f)

for info in infos_perm:
    save_csv.writerow(info)
f.close()