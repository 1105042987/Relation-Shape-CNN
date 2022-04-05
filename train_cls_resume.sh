#!/usr/bin/env sh
base=../logs/rscnn/$1
export CUDA_VISIBLE_DEVICES=$2 
python -u train_cls.py --config cfgs/$1.yaml --resume >> $base/log.txt
