import os
import re
pid = []
for it in os.popen('ps aux|grep auto_launch').read().split('\n')[:-3]:
    pid.append(re.findall('[0-9]+',it)[0])
for it in os.popen('ps aux|grep train_cls').read().split('\n')[:-3]:
    pid.append(re.findall('[0-9]+',it)[0])
    # print(it)
    # print(re.findall('[0-9]+',it)[0])
for i in pid: os.system(f'kill -9 {i}')
