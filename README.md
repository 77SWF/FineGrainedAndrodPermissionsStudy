> 作者：苏婉芳
>
> email：77SUSU@sjtu.edu.cn
>
> 日期：2022年6月6日

# 任务书：针对移动APP的细粒度授权机制研究 

随着时代的进步与科技的发展，智能手机在全世界广泛被人们所使用，它改变了人们的生活方式与生活习惯，给人们的生活带来了极大的便利。由Google自主开发的Android系统是全球第一款开放源代码的移动平台操作系统。在现今的手机操作系统中，Android系统因为它的高性价比和开源性，被越来越多地使用，成为了使用最多的手机操作系统。随着技术发展，越来越多的移动APP被安装到智能手机上,这些在APP在方便用户使用的同时，其滥用权限而导致个人隐私信息泄露的问题也愈发严重。

为保护手机的安全，Android系统对运行其上的APP提供权限审核机制，但现有的权限机制存在诸如粗粒度的授权机制、粗粒度的权限、权限滥用问题、权限文档不完整、“权限-API”对应关系不明确等问题，容易使得APP获得过多的权限或者滥用权限，为此本课题拟研究依据APP类型的细粒度授权机制，有效提升手机APP的安全性、保障手机用户的合法利益。

本课题的主要任务包括：

（1）分析现有最新版本Android系统的授权机制以及权限控制机制；

（2）研究细粒度的权限划分与授权机制

分析常用移动APP的功能，对APP类型进行细分，并对每种类型APP的功能进行细化，分析Android系统的权限列表，构建功能权限映射表，建立“APP类型－功能 - 权限”的映射关系。

根据移动APP的所属类型，以最小特权为指导，依据所建立的功能权限映射关系，并考虑用户意愿，对APP进行细粒度的授权。

（３）实现模型可视化工具

# 代码说明

**本研究的代码共有以下几个部分，分别对应以下文件夹：**

1. 华为应用市场爬虫与相关数据处理：huawei_appstore
2. 豌豆荚APK下载的URL爬取：apk_spider
3. APK下载和反编译、权限抽取：apk_analyse
4. API-权限映射关系处理与分析：clawer-api-permission_mapping
5. 应用权限推荐（支持度计算处理）/可视化界面：map_topic2perms
6. 部分结果数据：data
7. 数据库：db_LDA.db

# huawei_appstore

read_results2excel.py：解析getMethodMap_new.py的运行结果写入excel

read_excel2db_sourceCodePerm.py：从excel读取结果写入数据库

## huawei_appdescrip_spider

stopwords：中文停用词库源，包括1）4个常用的；2）迭代增加的

huawei_appdescrip_spider.py：华为应用市场爬取

low_freq_words_filter.py：低频错误词处理

word_cut.py：分词处理

## cut_none_sence_topic_words

cut_none_sence_topic_words.py：迭代补充停用词

## LDA

对华为应用市场描述进行多种LDA分类，及分类结果

含有各种LDA方式，包括直接分类（多种参数）、二级分类、原参数分类等

分别对应各个.py文件，查看代码即可知道具体方式

## ltp_data

分词模型所在位置

# apk_spider

apkurl_spider.py：从豌豆荚的各大类的“全部”爬取

apkurl_spider_subcate.py：从豌豆荚的各大类的各个子类爬取

# apk_analyse

add_39_doc_permissions：补充2020年最新研究的manifest权限信息

download_apk.py：下载爬取的豌豆荚APK链接

extract_perm_xml_1/2.py：从APK解析权限数据

该部分需要在交我算运行近一周时间，本地解析速度过慢，容易出现memory error

# clawer-api-permission_mapping

## clawer_API29to32

补充新版Android的权限映射关系

extract_class_urls.py：抽取类文档链接

getMethodMap_new.py：解析文档提取API-权限映射关系

multi_process_classesPage：多线程处理getMethodMap_new.py的工作

add_exception：补充遗漏的类分析，类似getMethodMap_new.py

## multi_process

多线程处理getMethodMap_new.py的工作

## permissionList

所有结果的集合，excel形式

# map_topic2perms

map_topic2perms.py：运行入口，内有处理论文的3.3与3.4节的函数，运行即可实现输入APP描述，得到推荐权限等结果

read_db2json.py：读取数据库内信息到json文件便于查询使用

UI文件夹：可视化工具，入口为main.py

# data

安卓权限.xls：分析得到的官方文档manifest.permissions的所有数据

manifests_source_code：ASOP源码的部分文件

几个txt文件：获取的完整权限列表

apk：测试数据集（部分，一些已经在分析后删除）