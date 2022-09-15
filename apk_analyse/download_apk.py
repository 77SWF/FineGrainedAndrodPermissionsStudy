import sqlite3
import os
from urllib.request import urlretrieve

def get_urls():
    path_db = "../data/db_LDA.db"
    db = sqlite3.connect(path_db)
    c = db.cursor()
    sql = '''select * from apk_url\
        where id > 288;'''
    data = c.execute(sql)
    names =[]
    urls = []
    for row in data:
        names.append(row[1])
        urls.append(row[2])
    db.close()
    return zip(names,urls)

def download_url(url,savename,savedir):
    def report_speed(a,b,c):
        """
        显示下载进度
        :param a: 已经下载的数据块
        :param b: 数据块的大小
        :param c: 远程文件大小
        :return: None
        """
        print("\rDownloading:%5.1f%%"% (a*b*100.0/c),end ="")#\r回行首

    savepath = os.path.join(savedir,savename)
    if not os.path.isfile(savepath):
        print("%s" % savename)
        try:
            urlretrieve(url,savepath,reporthook= report_speed)
            filesize = os.path.getsize(savepath)/1024/1024
            print('\tsize = %.2f Mb' % filesize)
            with open('download_sucess.txt','a',encoding='utf-8') as f:
                f.write(savename)
                f.write('\t')
                f.write(url)
                f.write('\n')
            return filesize
        except:
            print("Error:download %s.apk from %s " %(savename,url))
            with open('download_error.txt','a',encoding='utf-8') as f:
                f.write(savename)
                f.write('\t')
                f.write(url)
                f.write('\n')
            return 0
    else:
        print("%s already exists!" % savename,end ="")
        # f2=open('download_exist.txt','a',encoding='utf-8')
        # f2.write(savename)
        # f2.write('\t')
        # f2.write(url)
        # f2.write('\n')
        # f2.close()

        filesize = os.path.getsize(savepath)/1024/1024
        print('\tsize = %.2f Mb' % filesize)
        return filesize

if __name__ == '__main__':
    zip_names_urls = get_urls()
    savedir = 'D:/apk' #D盘保存/改成服务器上的

    num = 0 #限制下载数量
    size_all = 0 #限制下载存储量
    for name,url in zip_names_urls:
        num += 1
        savename = name + ".apk"
        size = download_url(url,savename,savedir)
        size_all += size
        
        if size_all/1024 > 20:
            print("apk文件总大小:%.2f G"% float(size_all/1024))
            break
