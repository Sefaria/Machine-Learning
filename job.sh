#!/bin/bash
if [[ $2 == 'pretrain' ]]
then
    dvc get https://github.com/Sefaria/Machine-Learning/ "$1/vectors/all_text_$4_fasttext_model_$5" --out "$1/vectors/all_text_$4_fasttext_model_$5"
elif [[ $2 == 'train-ner' ]]
then
    dvc get https://github.com/Sefaria/Machine-Learning "$1/corpus/$3_$4_train.spacy" --out "$1/corpus/$3_$4_train.spacy"
    dvc get https://github.com/Sefaria/Machine-Learning "$1/models/pretrain_$3_$4_$5" --out "$1/models/pretrain_$3_$4_$5"
    dvc get https://github.com/Sefaria/Machine-Learning "$1/corpus/$3_$4_test.spacy" --out "$1/corpus/$3_$4_test.spacy"
fi
cd util 
python run_project_with_vars.py $1 "$3_$4" $2

# bash torah_ner/job.sh torah_ner pretrain ref en 50