<<<<<<< HEAD:scripts/run_worker.sh
#!/bin/sh
BASE=$(dirname $(readlink -f $0))/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python
export PATH=$PATH:/opt/python/local/bin
=======
#!/bin/bash
>>>>>>> e92787982e42a6775e51f5b92fb6ff8b8a86b553:scripts/run_worker.sh
PYTHON=${PYTHON:-python}
BASE=$(${PYTHON} -c "import os,sys;print os.path.dirname(os.path.realpath('$0'))")/..
export PYTHONPATH=$PYTHONPATH:$BASE/src/python

<<<<<<< HEAD:scripts/run_worker.sh
#LIGHTTPD_CONF_ARG="--lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"

REL_BLOCK_LOCATION=${REL_BLOCK_LOCATION:-"store/"}
=======
if [[ $REL_BLOCK_LOCATION == "" ]]; then
    REL_BLOCK_LOCATION="store/"
fi
ABS_BLOCK_LOCATION="$BASE/$REL_BLOCK_LOCATION"
>>>>>>> e92787982e42a6775e51f5b92fb6ff8b8a86b553:scripts/run_worker.sh

MASTER=${MASTER_HOST:-http://127.0.0.1:8000}

WORKER_PORT=${WORKER_PORT:-8001}

if [[ $SCALA_HOME != "" ]]; then
    SCALA_CLASSPATH=$SCALA_HOME/lib/scala-library.jar
    if [ ! -e "${SCALA_CLASSPATH}" ]; then
      echo Not found: ${SCALA_CLASSPATH}
      exit 1
    fi
fi

LIGHTTPD_BIN=`which lighttpd`
if [ "$LIGHTTPD_BIN" != "" ]; then
  EXTRA_CONF="${EXTRA_CONF} --lighttpd-conf $BASE/src/python/skywriting/runtime/lighttpd.conf"
fi

GSON_VERSION=1.7.1
export CLASSPATH=${BASE}/dist/skywriting.jar:${BASE}/ext/google-gson-${GSON_VERSION}/gson-${GSON_VERSION}.jar:${SCALA_CLASSPATH}
export SW_MONO_LOADER_PATH=${BASE}/src/csharp/bin/loader.exe
export SW_C_LOADER_PATH=${BASE}/src/c/src/loader
export CIEL_SKYPY_BASE=${BASE}/src/python/skywriting/runtime/worker/skypy
export CIEL_SW_BASE=${BASE}/src/python/skywriting/lang
export CIEL_SW_STDLIB=${BASE}/src/sw/stdlib
<<<<<<< HEAD:scripts/run_worker.sh
${PYTHON} ${BASE}/src/python/skywriting/__init__.py --role worker --master ${MASTER} --port $WORKER_PORT --staticbase $BASE/src/js/skyweb_worker/ ${LIGHTTPD_CONF_ARG} -b $BASE/$REL_BLOCK_LOCATION -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b $*
=======
${PYTHON} ${BASE}/src/python/skywriting/__init__.py --role worker --master ${MASTER} --port $WORKER_PORT --staticbase $BASE/src/js/skyweb_worker/ ${HTTPD} -b $BASE/$REL_BLOCK_LOCATION -T ciel-process-aaca0f5eb4d2d98a6ce6dffa99f8254b ${EXTRA_CONF} $*
>>>>>>> e92787982e42a6775e51f5b92fb6ff8b8a86b553:scripts/run_worker.sh
