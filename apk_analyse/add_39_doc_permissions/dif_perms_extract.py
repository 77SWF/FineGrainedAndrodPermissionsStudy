import pandas as pd
import lxml
from bs4 import BeautifulSoup

path = '../../data/安卓权限.xls'  # CHANGE THIS TO YOUR DATASET PATH
df_sheets_dict = pd.read_excel(path,sheet_name = "permissions",encoding="utf-8")
list_perms = [t for t in df_sheets_dict['Permission name'].tolist()]

f_html = open("all_perms_api1-32.html","r",encoding="utf-8")
html = f_html.read()

# bs = BeautifulSoup(html,"html.parser")
# items = str(items)
items = lxml.etree.HTML(html)
perms = items.xpath('//tr/td[2]/code/a/text()')

# dif =[]
# for perm in perms:
#     if perm not in list_perms:
#         dif.append(perm)

# for perm in dif:
#     print(perm)
# print("共",len(dif),"个不同")

dif =[]
for perm in list_perms:
    if perm not in perms:
        dif.append(perm)

for perm in dif:
    print(perm)
print("共",len(dif),"个不同")