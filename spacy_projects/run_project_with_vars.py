import typer
import subprocess
import yaml


def run_project_with_vars(project: str, vars_name: str, task: str):
    with open(f"{project}/vars/{vars_name}.yml", 'r') as fin:
        yin = yaml.safe_load(fin)
        cmd = f"python -m spacy project run {task} . --force".split()
        print_out_cmd = cmd
        for var_name, var_value in yin['vars'].items():
            cmd += [f'--vars.{var_name}', f"{var_value}"]
            if "password" not in var_name:
                print_out_cmd += [f'--vars.{var_name}', f"{var_value}"]
        print("Running command:", print_out_cmd)
        process = subprocess.Popen(cmd, cwd=project)
        stdout, stderr = process.communicate()


if __name__ == '__main__':
    typer.run(run_project_with_vars)
