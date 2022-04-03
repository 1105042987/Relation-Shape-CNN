import pynvml
import os
import time
from multiprocessing import Process

CUDA_LIST = list(range(4))

pynvml.nvmlInit()
handles = [pynvml.nvmlDeviceGetHandleByIndex(cuda) for cuda in CUDA_LIST]
flags = [{'idle':True,'th':None} for i in range(len(CUDA_LIST))]
waittimes = 0
with open('job.txt','r') as f:
    left_jobs = len(f.readlines())

def CallAndTurnFlag(cmd,cuda):
    print('\n'+cmd+f'\tpid: {os.getpid()}')
    try:
        os.system(cmd)
    except Exception as e:
        print("Error happended when calling:",cmd.split('>')[0])
        print("Error Detials:",str(e))
    flags[cuda]['idle'] = True

def lauch_one(cuda):
    global waittimes
    with open('job.txt','r') as f:
        cmd_list = f.readlines()
    if not flags[cuda]['idle']: return len(cmd_list)
    if len(cmd_list)==0: return 0
    idx = 0
    while idx<len(cmd_list) and cmd_list[idx][0]=='#': idx+=1
    if idx==len(cmd_list): return 0
    cmd = cmd_list.pop(idx)
    cmd = cmd.format(cuda).replace('\n','') # + '> {2:0>2}{3:0>2}_{4:0>2}{5:0>2}_cu{0}.log'.format(cuda,*time.localtime())
    with open('job.txt','w') as f:
        for line in cmd_list: f.write(line)

    if flags[cuda]['th'] is not None: flags[cuda]['th'].join()
    flags[cuda]['idle'] = False
    waittimes = 0
    flags[cuda]['th'] = Process(target=CallAndTurnFlag,args=(cmd,cuda))
    flags[cuda]['th'].start()
    time.sleep(10)
    return len(cmd_list)

while True:
    meminfos = [pynvml.nvmlDeviceGetMemoryInfo(handle) for handle in handles]
    used = [meminfo.used/1024/1024 for meminfo in meminfos]
    print(f'wait {waittimes} min:\t'+',\t'.join([f'{idx}: {it} MB' for idx,it in zip(CUDA_LIST,used)]),end='\r')
    for cuda,it in enumerate(used):
        if it > 1000: continue
        left_jobs = lauch_one(cuda)
    if left_jobs == 0: break
    time.sleep(60)
    waittimes += 1