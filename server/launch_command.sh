#!/usr/bin/env bash
# Helper script to launch python with codeintel in a python2 virtualenv
set -e

COMMAND=$1

SHAREDENV="/mnt/shared/lib/$PYTHON"
FALLBACKENV="$HOME/.c9/$PYTHON"

if [[ -d $SHAREDENV ]]; then
    ENV=$SHAREDENV
    source $ENV/bin/activate
    PYTHON="$ENV/bin/$PYTHON"
elif which virtualenv &>/dev/null; then
    ENV=$FALLBACKENV
    if ! [[ -d $ENV ]]; then
        virtualenv $ENV
    fi

    source $ENV/bin/activate

    if ! python -c 'import jedi' &>/dev/null; then
        echo "Installing python support dependencies"
        pip install --upgrade jedi pylint pylint-flask pylint-django >&2
    fi

    PYTHON=$ENV/bin/$PYTHON
else
    echo "!!Code completion fatal error: virtualenv not installed, try 'pip install virtualenv' or 'sudo pip install virtualenv'" >&2
    exit 1
fi

COMMAND=${COMMAND/\$PYTHON/$PYTHON}
COMMAND=${COMMAND/\$ENV/$ENV}
eval "$COMMAND"