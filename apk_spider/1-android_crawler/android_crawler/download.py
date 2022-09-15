#coding:utf-8
# import urllib2
import requests
import urllib
import os,sys,socket
import os.path
per_format = 0
import hash_md5
def Schedule(a,b,c):
    global per_format
    '''
    a:已经下载的数据块
    b:数据块的大小
    c:远程文件的大小
    '''
    per = 100*a*b/c
    if per >98:
        per =100
    a = '-> '+str(per)+'%'
    if per_format ==0:
        sys.stdout.write('|'*per+' '*(105-per)+a+'\b'*(105+len(a)-per))
    else :
        sys.stdout.write('|'*(per-per_format)+' '*(105-per)+a+"\b"*(105+len(a)-per))
    sys.stdout.flush()
    per_format=per
def down(url):
    local = 'apk_files/%s.apk'%url.replace('/','').replace('.','').replace(':','')
    socket.setdefaulttimeout(2.0)
    try:
        opener = urllib.FancyURLopener({}) 
        opener.verion = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'
        opener.retrieve(url,local,Schedule) #直接将远程数据下载到本地
    except Exception as e:
        pass
    if os.path.exists(local):
        file_md5 = hash_md5.md5_file(local)
    else:
        return 0 #下载失败 md5=0
    if os.path.exists('apk_files/%s.apk'%file_md5):
        os.remove('apk_files/%s.apk'%file_md5)
    if os.path.exists(local):
        os.rename(local,'apk_files/%s.apk'%file_md5)
    else: return 0
    return file_md5
if __name__ == '__main__':
    print ('\n'+down('http://www.wandoujia.com/apps/com.wandoujia.roshan/download'))
    