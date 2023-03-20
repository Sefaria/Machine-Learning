#!/bin/bash

dvc get "configs/ref-v3.2.cfg"
if [[ $1 -eq 'pretrain' ]]
  then
    dvc get "vectors/all_text_$2_fasttext_model_$3"
elif [[ $1 -eq 'train-ref-model' ]]
  then
    dvc get "models/pretrain_ref_$2_$3"
fi