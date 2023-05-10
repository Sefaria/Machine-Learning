import os
import sys
import yaml
import re
from run_project_with_vars import run_project_with_vars

def parse_yml(dep):
    # a typical dependency listed in project.yml will be of the form 'vectors/all_text_${vars.lang}_fasttext_model_${vars.embedding_size}'
    # so we need to parse it to yield vectors/all_text_en_fasttext_model_50'
    vars_in_dep = re.findall("\$\{(.*?)\}", dep)
    for x in vars_in_dep:
        if x.startswith("vars."):
            dep = dep.replace("${" + x + "}", str(project_vars[x.replace("vars.", "")]))
        elif x.startswith("env."):
            dep = dep.replace("${" + x + "}", str(env_vars[x.replace("env.", "")]))
    return dep

project_dir = os.getenv('ML_PROJECT_DIR', default='torah_ner')
parent_dir = os.path.dirname(os.getcwd())
tasks = sys.argv[1]  # example: "pretrain" or "pretrain,train-ner"
lang = sys.argv[2]  # example: "en"
vars_file = sys.argv[3]  # example: "ref_en"
embedding_size = sys.argv[4]  # example: "50"
yml = None

os.chdir(f"{project_dir}")
with open(f"vars/{vars_file}.yml") as f:
    job_vars = yaml.safe_load(f)['vars']  # load the variables specific to this job in vars_file.yml

with open(f"project.yml") as f:
    project_yml = yaml.safe_load(f)
    env_vars = project_yml['env']

    # load the global vars from the project.yml and override any keys found in this specific job
    project_vars = project_yml['vars']
    for k in project_vars:
        if k in job_vars:
            project_vars[k] = job_vars[k]

    # 'commands' is a dictionary of tasks to a list of dependency files
    commands = {x['name']: x.get('deps', []) for x in project_yml['commands']}
    outputs = {x['name']: x.get('outputs', []) for x in project_yml['commands']}

for task in tasks.split(","):
    assert task in commands, f"{task} not found"
    for d, dep in enumerate(commands[task]):
        dep = parse_yml(dep)
        # if this dependency doesn't exist, try to get it from dvc and fail if it's not on dvc
        print(f"Looking for {dep}...")
        actual_path = f"{project_dir}/{dep}"
        if not os.path.exists(dep):
            os.system("""dvc get https://github.com/Sefaria/Machine-Learning/ "{}" --out "{}" """.format(actual_path, dep))
            assert os.path.exists(dep), f"{dep} not found in DVC."
            print(f"Successfully download {dep}")
        else:
            print(f"{dep} already exists")

    run_project_with_vars(project_dir, vars_file, task)
    # for output in outputs[task]:
    #     output = parse_yml(output)
    #     actual_path = f"{project_dir}/{output}"
    #     if not os.path.exists(output+".dvc"):
    #         os.system(f"dvc add {output}")


