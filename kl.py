import os
import re
import sys

pid = []
for it in os.popen('ps aux|grep auto_launch').read().split('\n')[:-3]:
    print(it)
    pid.append(re.findall('[0-9]+',it)[0])
for it in os.popen('ps aux|grep train_cls').read().split('\n')[:-3]:
    pid.append(re.findall('[0-9]+',it)[0])
    print(it)
    # print(it)
    # print(re.findall('[0-9]+',it)[0])
if len(sys.argv)>1 and sys.argv[1]=='k':
    for i in pid: os.system(f'kill -9 {i}')
