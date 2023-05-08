# #!/bin/bash
# if [[ $2 -eq 'pretrain' ]]
# then
#     dvc get https://github.com/Sefaria/Machine-Learning/ "PROJECT_NAME/vectors/all_text_lang_fasttext_model_embedding_size" --out "PROJECT_NAME/vectors/all_text_lang_fasttext_model_embedding_size"
# elif [[ $2 -eq 'train-ner' ]]
# then
#   dvc get https://github.com/Sefaria/Machine-Learning "PROJECT_NAME/models" --out "PROJECT_NAME/models"
#   echo 'train-ref-model'
# fi
# cd util
# python run_project_with_vars.py PROJECT_NAME "ref_lang" $2
#python run_project_with_vars.py project_dir vars_file lang embedding_size
# python job.py en ref 50
import os
import subprocess
import sys
import yaml
import re

from util.run_project_with_vars import run_project_with_vars
project_dir = os.getenv('ML_PROJECT_DIR', default='torah_ner')
tasks = sys.argv[1]  # example: "pretrain" or "pretrain,train-ner"
lang = sys.argv[2]  # example: "en"
vars_file = sys.argv[3]  # example: "ref"
embedding_size = sys.argv[4]  # example: "50"
yml = None

with open(f"{project_dir}/vars/{vars_file}.yml") as f:
    job_vars = yaml.safe_load(f)['vars']

with open(f"{project_dir}/project.yml") as f:
    project_yml = yaml.safe_load(f)
    env_vars = project_yml['env']
    project_vars = project_yml['vars']
    for k in project_vars:
        if k in job_vars:
            project_vars[k] = job_vars[k]
    commands = {x['name']: x.get('deps', []) for x in project_yml['commands']}


for task in tasks.split(","):
    assert task in commands
    for d, dep in enumerate(commands[task]):
        vars_in_dep = re.findall("\$\{(.*?)\}", dep)
        for x in vars_in_dep:
            if x.startswith("vars."):
                dep = dep.replace("${"+x+"}", str(project_vars[x.replace("vars.", "")]))
            elif x.startswith("env."):
                dep = dep.replace("${"+x+"}", str(env_vars[x.replace("env.", "")]))
        actual_path = f"{project_dir}/{dep}"
        if not os.path.exists(actual_path):
            results = os.popen("""dvc get https://github.com/Sefaria/Machine-Learning/ "{}" --out "{}" """.format(actual_path, actual_path))
            print(results.read())

    os.chdir("util")
    run_project_with_vars(project_dir, vars_file, task)
