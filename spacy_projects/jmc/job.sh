#!/bin/bash
if [[ $2 -eq 'pretrain' ]]
then
    dvc get https://github.com/Sefaria/Machine-Learning/ "$1/vectors/all_text_$3_fasttext_model_$4" --out "$1/vectors/all_text_$3_fasttext_model_$4"
elif [[ $2 -eq 'train-ref-model' ]]
then
  dvc get https://github.com/Sefaria/Machine-Learning "$1/models" --out "$1/models"
  echo 'train-ref-model'
fi
cd util 
python run_project_with_vars.py $1 "ref_$3" $2