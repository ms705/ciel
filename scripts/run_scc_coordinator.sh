#!/bin/sh
BASE=$(dirname $(readlink -f $0))/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python
export PATH=$PATH:/opt/python/local/bin
PYTHON=${PYTHON:-python}

#LIGHTTPD_CONF_ARG="--lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"

REL_BLOCK_LOCATION=${REL_BLOCK_LOCATION:-"store/"}

MASTER=${MASTER_HOST:-http://`hostname -f`:8000}

WORKER_PORT=${WORKER_PORT:-8001}

export CLASSPATH=${BASE}/dist/skywriting.jar
export SW_MONO_LOADER_PATH=${BASE}/src/csharp/bin/loader.exe
export SW_C_LOADER_PATH=${BASE}/src/c/src/loader
export CIEL_SKYPY_BASE=${BASE}/src/python/skywriting/runtime/worker/skypy
export CIEL_SW_STDLIB=${BASE}/src/sw/stdlib
export LIBCIEL_PATH=${BASE}/src/c/src
${PYTHON} ${BASE}/src/python/skywriting/__init__.py --role scc_coordinator --master ${MASTER} --port $WORKER_PORT --staticbase $BASE/src/js/skyweb_worker/ ${LIGHTTPD_CONF_ARG} -b $BASE/$REL_BLOCK_LOCATION -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b $*
