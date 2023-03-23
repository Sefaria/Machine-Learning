from setuptools import setup

setup(
    name='prodigy_utils',
    py_modules=["main"],
    entry_points={
        'prodigy_recipes': [
            'ner-recipe = main:ref_tagging_recipe'
        ],
        'prodigy_db': [
            'mongodb = main:db_manager'
        ]
    },
    install_requires=[
        'pymongo',
        'spacy>=3.0.5',
        'srsly==2.4.3'
    ]
)
