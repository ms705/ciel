#!/bin/sh
BASE=$(dirname $(readlink -f $0))/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python
export PATH=$PATH:/opt/python/local/bin
PYTHON=python

#LIGHTTPD_CONF_ARG="--lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"

# Sensible defaults:
MASTER_PORT=${MASTER_PORT:-8000}

REL_BLOCK_LOCATION=${REL_BLOCK_LOCATION:-"store/"}

${PYTHON} $BASE/src/python/skywriting/__init__.py --role master --port $MASTER_PORT --staticbase $BASE/src/js/skyweb/ ${LIGHTTPD_CONF_ARG} -j $BASE/journal/ -b $BASE/$REL_BLOCK_LOCATION -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b $*
