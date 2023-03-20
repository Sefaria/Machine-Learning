FROM python:3.9

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY prodigy prodigy 
RUN python prodigy/prodigy_utils/setup.py develop

COPY util util
ENTRYPOINT bash 

dvc get all files mentioned in 
cd util
python ./run_project_with_vars.py $1 $2 $3



	
	  pretrain/train-ref-model:
	  - "configs/ref-v3.2.cfg"
	  pretrain only:
      - vectors/all_text_${vars.lang}_fasttext_model_${vars.embedding_size}
      train-ref-model only:
	    - "models/pretrain_ref_${vars.lang}_${vars.embedding_size}"

if [[ $1 -eq 'pretrain']]
then
	git add "vectors/all_text_"+$2+"_fasttext_model_"+$3
elif [[ $1 -eq 'train-ref-model']]
then
	git add "models/pretrain_ref_"+$2+"_"+$3
fi