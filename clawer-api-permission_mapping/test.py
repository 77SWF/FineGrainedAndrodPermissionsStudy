from bs4 import BeautifulSoup
import re

find_permission = re.compile(r'android:name="(.*?)"') #permission

def get_all_perms():
    '''从源码12版本清单文件提取所有权限：689个'''
    allpermList = []
    source_code_path = "../data/manifests_source_code/AndroidManifest-Android12.xml"
    with open(source_code_path,'r',encoding="utf-8") as f:
        xml = f.read()
        soup = BeautifulSoup(xml,"xml")
        items_perm = soup.find_all('permission')
        for item in items_perm:
            item = str(item)
            perm = re.findall(find_permission,item)[0]
            # if perm.startswith("com.android."):
            #     allpermList.append(perm)
            # else:
            perm = perm.split('.')[-1]
            allpermList.append(perm)
    print('源码里权限个数：',len(allpermList)) #689个
    return allpermList

perms = get_all_perms()

f = open("allpermList_sourceCode.txt",'w')
for perm in perms:
    f.write(perm)
    f.write('\n')
f.close()