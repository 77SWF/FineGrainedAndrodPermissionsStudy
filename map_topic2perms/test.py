import json


f = open('topic2supportRate_code_json_0005/app_topic_73.json','r')
d = json.load(f)

k=[]
v=[]
cnt=0
for key,value in d.items():
    cnt+=1
    k.append(key)
    v.append(value)

print(k)
print(v)