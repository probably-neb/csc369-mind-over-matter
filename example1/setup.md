Instructions to get this to work :)

# Prelminaries
Make sure you install and get neo4j running as is described in my video on Canvas.

Once you get neo4j running, please create a new project with a new local DBMS. Make sure you also install the APOC plugin.

# Python setup

```
sudo apt-get install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa

sudo apt-get update

sudo apt-get install python3.9

sudo apt-get install python3.9-distutils

sudo apt-get install python3.9-dev

wget https://bootstrap.pypa.io/get-pip.py

sudo python3.9 ./get-pip.py

sudo python3.9 -m pip install virtualenv
```

```
virtualenv --py \`which python3.9\` spacey_pipeline

source spacey_pipeline/bin/activate

pip install --upgrade pip

pip install jupyter notebook==6.* numpy

pip install crosslingual-coreference==0.2.3 spacy-transformers==1.1.5 wikipedia neo4j

pip install transformers==4.18.0

python -m spacy download en_core_web_sm

python -m ipykernel install --user --name spacey_pipeline
```

Now you can start jupyter lab and run the kernel called spacey_pipeline.
