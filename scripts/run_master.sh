<<<<<<< HEAD:scripts/run_master.sh
#!/bin/sh
BASE=$(dirname $(readlink -f $0))/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python
export PATH=$PATH:/opt/python/local/bin
PYTHON=python
=======
#!/bin/bash
PYTHON=${PYTHON:-python}
BASE=$(${PYTHON} -c "import os,sys;print os.path.dirname(os.path.realpath('$0'))")/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python
>>>>>>> e92787982e42a6775e51f5b92fb6ff8b8a86b553:scripts/run_master.sh

#LIGHTTPD_CONF_ARG="--lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"

# Sensible defaults:
MASTER_PORT=${MASTER_PORT:-8000}

REL_BLOCK_LOCATION=${REL_BLOCK_LOCATION:-"store/"}

<<<<<<< HEAD:scripts/run_master.sh
${PYTHON} $BASE/src/python/skywriting/__init__.py --role master --port $MASTER_PORT --staticbase $BASE/src/js/skyweb/ ${LIGHTTPD_CONF_ARG} -j $BASE/journal/ -b $BASE/$REL_BLOCK_LOCATION -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b $*
=======
ABS_BLOCK_LOCATION="$BASE/$REL_BLOCK_LOCATION"

if [ ! -d "$ABS_BLOCK_LOCATION" ]; then
  mkdir -p "$ABS_BLOCK_LOCATION"
fi

LIGHTTPD_BIN=`which lighttpd`
if [ "$LIGHTTPD_BIN" != "" ]; then
  EXTRA_CONF="${EXTRA_CONF} --lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"
fi

${PYTHON} "$BASE/src/python/skywriting/__init__.py" --role master --port $MASTER_PORT --staticbase "$BASE/src/js/skyweb/" -j $BASE/journal/ -b "$ABS_BLOCK_LOCATION" -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b ${EXTRA_CONF} $*
>>>>>>> e92787982e42a6775e51f5b92fb6ff8b8a86b553:scripts/run_master.sh
