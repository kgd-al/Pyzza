#!/bin/bash

virtual_env_name=venv-pyzza-flet

if [ -z $VIRTUAL_ENV ]
then
  echo "Not inside a virtual environment"
  read -p "Create one named $virtual_env_name (with pyenv)? " answer
  if [[ $answer =~ [Yy]es ]]
  then
    pyenv virtualenv 3.11 $virtual_env_name
    pyenv local $virtual_env_name
    pip install '.[desktop,android,dev]'
    flet doctor
  else
    echo "Refusing to work outside of a virtual environment."
    exit 1
  fi
fi
