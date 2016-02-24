#!/usr/bin/env bash
# Helper script to launch python with codeintel in a python2 virtualenv
set -e

COMMAND=$1

SHAREDENV="/mnt/shared/lib/python2"
FALLBACKENV="$HOME/.c9/python2"

if [[ -d $SHAREDENV/lib/python2.7/site-packages/codeintel ]]; then
    ENV=$SHAREDENV
    source $ENV/bin/activate
    PYTHON="$ENV/bin/python"
elif which virtualenv &>/dev/null; then
    if [ ! -e /usr/include/python2.7/Python.h ]; then
        echo "!!Code completion fatal error: python-dev not installed (try sudo apt-get install python-dev)"
        exit 1
    fi

    ENV=$FALLBACKENV
    if ! [[ -d $ENV ]]; then
        virtualenv $ENV
    fi

    source $ENV/bin/activate

    if ! python -c 'import codeintel' &>/dev/null; then
        echo "!!Installing code completion dependencies" >&2
        set -x
        rm -rf /tmp/codeintel $ENV/build
        mkdir /tmp/codeintel
        cd /tmp/codeintel
        pip install --download /tmp/codeintel codeintel==0.9.3 2>&1
        tar xf CodeIntel-0.9.3.tar.gz
        mv CodeIntel-0.9.3/SilverCity CodeIntel-0.9.3/silvercity
        tar czf CodeIntel-0.9.3.tar.gz CodeIntel-0.9.3
        pip install -U --no-index --find-links=/tmp/codeintel codeintel
        echo "!!Done installing dependencies" >&2
    fi

    PYTHON=$ENV/bin/python
else
    echo "!!Code completion fatal error: virtualenv not installed, try 'pip install virtualenv' or 'sudo pip install virtualenv'" >&2
    exit 1
fi

COMMAND=${COMMAND/\$PYTHON/$PYTHON}
COMMAND=${COMMAND/\$ENV/$ENV}
eval "$COMMAND"