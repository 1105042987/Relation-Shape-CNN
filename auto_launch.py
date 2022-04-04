import pynvml
import os
import time
from multiprocessing import Process
import signal

CUDA_LIST = list(range(4))

pynvml.nvmlInit()
handles = [pynvml.nvmlDeviceGetHandleByIndex(cuda) for cuda in CUDA_LIST]
mp = {}
waittimes = 0
with open('job.txt','r') as f:
    left_jobs = len(f.readlines())

def CallAndTurnFlag(cmd,cuda):
    cmd_for_run = cmd.format(cuda).replace('\n','') # + '> {2:0>2}{3:0>2}_{4:0>2}{5:0>2}_cu{0}.log'.format(cuda,*time.localtime())
    print('\n'+cmd_for_run+f'\tpid: {os.getpid()}')
    try:
        os.system(cmd_for_run)
    except Exception as e:
        with open('job.txt','r') as f:
            cmd_list = f.readlines()
        cmd_list.insert(0,cmd)
        with open('job.txt','w') as f:
            for line in cmd_list: f.write(line)
        print("Error happended when calling:",cmd)
        print("Error Detials:",str(e))

def lauch_one(cuda):
    global waittimes
    with open('job.txt','r') as f:
        cmd_list = f.readlines()
    if len(cmd_list)==0: return 0
    idx = 0
    while idx<len(cmd_list) and cmd_list[idx][0]=='#': idx+=1
    if idx==len(cmd_list): return 0
    cmd = cmd_list.pop(idx)
    with open('job.txt','w') as f:
        for line in cmd_list: f.write(line)

    waittimes = 0
    mp[cuda] = Process(target=CallAndTurnFlag,args=(cmd,cuda))
    mp[cuda].start()
    time.sleep(10)
    return len(cmd_list)

def child_exited(sig, frame):
    pid, exitcode = os.wait()
    print("Child process {pid} exited with code {exitcode}".format(
        pid=pid, exitcode=exitcode
    ))

signal.signal(signal.SIGCHLD, child_exited)
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