import sqlite3

db = sqlite3.connect("../../data/db_LDA.db")
c = db.cursor()

sql = '''
select perms_declare from perms_declare_2;
'''

with open("../../data/permList_manifest_208.txt") as f:
    lines = f.readlines()

list_manifest_perms = [perm.strip() for perm in lines]

rows = c.execute(sql)
cnt=0
for row in rows: #每个app
    cnt+=1

    perms = row[0].split(';')
    perms.remove("")

    for perm in perms:
        if perm not in list_manifest_perms:
            print(cnt,perm)
            # temp.append(row[0])


print("over")
