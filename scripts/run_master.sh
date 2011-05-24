#!/bin/sh
PYTHON=${PYTHON:-python}
BASE=$(${PYTHON} -c "import os,sys;print os.path.dirname(os.path.realpath('$0'))")/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python

REL_BLOCK_LOCATION=${REL_BLOCK_LOCATION:-"store/"}
ABS_BLOCK_LOCATION="$BASE/$REL_BLOCK_LOCATION"

if [ ! -d "$ABS_BLOCK_LOCATION" ]; then
  mkdir -p "$ABS_BLOCK_LOCATION"
fi

MASTER_PORT=${MASTER_PORT:-"8000"}

LIGHTTPD_BIN=`which lighttpd`
if [ "$LIGHTTPD_BIN" != "" ]; then
  EXTRA_CONF="${EXTRA_CONF} --lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"
fi

${PYTHON} "$BASE/src/python/skywriting/__init__.py" --role master --port $MASTER_PORT --staticbase "$BASE/src/js/skyweb/" -j $BASE/journal/ -b "$ABS_BLOCK_LOCATION" -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b ${EXTRA_CONF} $*
