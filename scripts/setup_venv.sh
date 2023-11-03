#!/bin/bash

if [[ $PWD == *"scripts"* ]]
then
    cd ..
fi

if [ -d ./.venv ]; then
    export answer
    echo "Rewrite current venv? [y/n]"
    read answer
    if [ $answer != "y" ]; then
        echo "Aborting"
        exit
    else
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            echo "Deactivate current venv first!"
            exit
        fi
        rm -rf ./.venv
    fi
fi

python -m venv --copies .venv

source ./.venv/bin/activate &&\
pip install wheel &&\
pip install -r ./requirements.txt $1 &&\
deactivate
