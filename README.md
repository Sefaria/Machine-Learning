# Machine-Learning
Scripts for training and testing machine learning models based on Sefaria's data

## Setup

### Install Local DBManager package

There is a local python package included in this repo which contains utility functions and classes for interfacing with Prodigy. These utilities are also used for defining the interface between Mongo and spaCy so they are required to install before running any training tasks.

To install, follow instructions in `prodigy/prodigy_utils/README.txt`.

### Install requirements

Run: `pip install -r requirements.txt`

#### DVC

This repo uses DVC to track changes to large data files or models. DVC is installed using `requirements.txt`. However, you can follow [these instructions](https://dvc.org/doc/install/completion) to install shell completion as well.

DVC is modeled after git. The following is a list of common DVC commands:

```shell
dvc add <filename>  # add filename to DVC tracking
dvc pull            # pull latest data from remote
dvc push            # push latest data to remote
```

See [here](https://dvc.org/doc/start/data-management/data-versioning) for more documentation.

Note, we are currently using Google Storage on the development cluster as the remote for this repo.

## Run

Most scripts in this repo are run using spaCy projects. See [here](https://spacy.io/usage/projects) for general documentation on spaCy projects.

### Run a project using new `vars` override script

The new way to run a spaCy project is to use the `vars` override script located at `utils/run_project_with_vars.py`

This script allows you to use a base project.yml file and inject overrides to variables from a separate file which is
convenient when there are multiple possible variables for one project.

Follow these steps to run with vars overrides:

```shell
cd util
python ./run_project_with_vars.py [project] [vars_name] [task]
```

#### run_project_with_vars parameters

| Param     | Description                                                                                                                         |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------|
| project   | name of a project folder. E.g. `torah_ner`                                                                                          |
| vars_name | name of a vars file. This must be located in the project folder under the `vars` folder. E.g. `ref_he`. Note, leave of file suffix. |
| task      | name of a command or workflow in the project's project.yml file.                                                                    |

## Projects

Below is a list of current projects

### torah_ner

This project is meant to train NER classifiers for multiple tasks. Each task is defined in a `vars` file in `torah_ner/vars`.
You must use `run_project_with_vars.py` to run this project.

#### vars

| Vars file | Description                                                                         |
|-----------|-------------------------------------------------------------------------------------|
| ref_he    | Vars for training Hebrew NER model to recognize citations                           |
| subref_he | Vars for training Hebrew NER model to recognize parts of citation within a citation |
|           |                                                                                     |