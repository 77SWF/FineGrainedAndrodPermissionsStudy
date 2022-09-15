'''
1 从爬取的urlList_29to32.txt【2 urlList_from_classesPage.txt】中去除
1 urlList_29to30+old.txt【2 urlList_29to30+old+29to32diff.txt】中的已有项
to 1 urlList-1.txt【2 urlList.txt】
result1:两个都不变 还是441条 所以仍取urlList_29to32.txt——应该是后缀.html没加的原因
'''


from matplotlib.pyplot import close


list_new = [] #爬取的
list_exist = [] #现有的

with open('urlList_29to32.txt','r',encoding='utf-8') as f:
# with open('urlList_from_classesPage.txt','r',encoding='utf-8') as f:
    lines_new = f.readlines()
    list_new = [line for line in lines_new]

with open('urlList_29to30+old.txt','r',encoding='utf-8') as f:
# with open('urlList_29to30+old+29to32diff.txt','r',encoding='utf-8') as f:
    lines_exist = f.readlines()
    list_exist = [line for line in lines_exist]

''' 去重去了11个 原文件"urlList_29to30+old+29to32diff-未去重.txt"
#已存在的这个txt去重
temp=[]
for line in lines_exist:
    if line not in temp:
        temp.append(line)
with open('urlList_29to30+old+29to32diff.txt','w',encoding='utf-8') as f:
    for url in temp:
        f.write(url)
#去重后再读        
with open('urlList_29to30+old+29to32diff.txt','r',encoding='utf-8') as f:
    lines_exist = f.readlines()
    list_exist = [line for line in lines_exist]
'''

list_refresh = []
num = 0

#改名
f_delete = open('urlList-1_inNew_inOld.txt','w',encoding='utf-8')
'''
f_delete2 = open('urlList_notInClassesPage_inOld.txt','w',encoding='utf-8')
'''
for url in list_new:
    num+=1
    print("\r判断classesPage: %d/%d"%(num,len(list_new)),end="")

    if url not in list_exist:
        list_refresh.append(url) #新爬的有 但旧的没有
    else:
        f_delete.write(url) #新爬的有 旧的也有
    
'''
print("")
num2=0
for url in list_exist:
    num2+=1
    print("\r判断old: %d/%d"%(num2,len(list_exist)),end="") 
    if url not in list_new: #旧的有 新的没有
        f_delete2.write(url)
'''

f = open('urlList-1.txt','w',encoding='utf-8')
for url in list_refresh:
    f.write(url)
    # f.write('\n')
f.close()
f_delete.close()
'''
f_delete2.close()
'''