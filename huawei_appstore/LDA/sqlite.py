import sqlite3
import pandas as pd


if __name__ == '__main__':
    db = sqlite3.connect("test.db")
    print("Opened database successfully")

    c = db.cursor()
    sql_create_table = '''
    create table topic_vector_16
    (
        app_name text not null, 
        description text not null,
        topics text,
        probilities text
    );
    '''
    c.execute(sql_create_table)
    print("Create table successfully")


    file_path = "LDA-应用-主题向量-分16大类-重清洗-3.csv"
    df = pd.read_csv(file_path,encoding="utf-8")    
    list_descriptions = [t for t in df['迭代3-文件后缀'].tolist()]
    list_names = [t for t in df['应用名'].tolist()]

    for (name,descrip) in zip(list_names,list_descriptions):
        sql_insert = '''
        insert into topic_vector_16(app_name,description) \
            values("{0}","{1}");
        '''.format(name,descrip)
        # print(name,descrip)
        c.execute(sql_insert)

    db.commit()
    db.close()
    print("Close database successfully")


    
    