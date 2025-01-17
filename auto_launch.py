import pynvml
import os
import time
from multiprocessing import Process,Manager
import signal

waittimes = 0
CUDA_LIST = list(range(2))

pynvml.nvmlInit()
handles = [pynvml.nvmlDeviceGetHandleByIndex(cuda) for cuda in CUDA_LIST]
manager = Manager()
avaliable = manager.dict({cuda:True for cuda in CUDA_LIST})
mp = {cuda:None for cuda in CUDA_LIST}

yellow = lambda x: f'\033[33m {x} \033[0m'
green = lambda x: f'\033[32m {x} \033[0m'
red = lambda x: f'\033[31m {x} \033[0m'

with open('job.txt','r') as f:
    left_jobs = len(f.readlines())

def CallAndTurnFlag(cmd,cuda):
    cmd_for_run = cmd.format(cuda).replace('\n','') # + '> {2:0>2}{3:0>2}_{4:0>2}{5:0>2}_cu{0}.log'.format(cuda,*time.localtime())
    print(yellow(f'\n{cmd_for_run}\tpid: {os.getpid()}'))
    while avaliable[cuda] is not None:
        try:
            code = os.system(cmd_for_run)
            if code == 2:
                print(red(f'\n{cmd_for_run}\tpid: {os.getpid()} Exit!'))
                with open('job.txt','r') as f: cmd_list = f.readlines()
                cmd_list.insert(0,cmd)
                with open('job.txt','w') as f: 
                    for line in cmd_list: f.write(line)
                break
            elif code == 0: 
                avaliable[cuda]=True
                print(green(f'\n{cmd_for_run}\tpid: {os.getpid()} Finished!'))
                break
            assert code==0, f'Error[{code}] happend!'
        except Exception as e:
            cmd_for_run = cmd_for_run.replace('train_cls.sh','train_cls_resume.sh')
            print(yellow(f'\nretry:{cmd_for_run}\tpid: {os.getpid()}'))
            print(red(f'Because: {e}'))


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
    avaliable[cuda]=False
    if mp[cuda] is not None: mp[cuda].join()
    mp[cuda] = Process(target=CallAndTurnFlag,args=(cmd,cuda))
    mp[cuda].start()
    time.sleep(10)
    return len(cmd_list)

if __name__ == '__main__':
    try:
        while True:
            meminfos = [pynvml.nvmlDeviceGetMemoryInfo(handle) for handle in handles]
            used = [meminfo.used/1024/1024 for meminfo in meminfos]
            print(f' wait {waittimes} min:\t'+',\t'.join([f'{idx}({avaliable[idx]}): {umem} MB' for idx,umem in zip(CUDA_LIST,used)]),end='\r')
            for cuda,umem in zip(CUDA_LIST,used):
                if umem > 1000 or not avaliable[cuda]: continue
                left_jobs = lauch_one(cuda)
            if left_jobs == 0 and all([avaliable[idx] for idx in CUDA_LIST]): break
            time.sleep(60)
            waittimes += 1
    except KeyboardInterrupt:
        print(red('Attention!! Main Process Exit!!'))
        for cuda,th in mp.items():
            avaliable[cuda]=None
            if th is not None:
                th.terminate()