'''
Created on 9 Mar 2011

@author: ms705
'''
from skywriting.runtime.exceptions import ReferenceUnavailableException,\
    AbortedException
from skywriting.runtime.local_task_graph import LocalTaskGraph, LocalJobOutput
from skywriting.runtime.task_executor import TaskExecutionRecord
import ciel
import logging
import os, sys

from ctypes import *


class SCCTaskRunner:
    
    def get_next_task(self, name):
        pass
    
    def thread_main(self):
        while True:
            task = self.get_next_task(self.name)
            if task is None:
                return
            else:
                try:
                    self.handle_task(task)
                except Exception:
                    ciel.log.error('Uncaught error handling task in pool: %s' % (self.name), 'MULTIWORKER', logging.ERROR, True)
                self.queue_manager.notify()

    def handle_task(self, task):
        next_td = task.as_descriptor()
        next_td["inputs"] = [task.taskset.retrieve_ref(ref) for ref in next_td["dependencies"]]
        task_record = task.taskset.build_task_record(next_td)
        try:
            task_record.run()
        except:
            ciel.log.error('Error during executor task execution', 'MWPOOL', logging.ERROR, True)
        if task_record.success:
            task.taskset.task_graph.spawn_and_publish(task_record.spawned_tasks, task_record.published_refs, next_td)
        task.taskset.dec_runnable_count()


def redirect_stdout():
    print "Redirecting stdout"
    sys.stdout.flush() # <--- important when redirecting to files
    newstdout = os.dup(1)
    devnull = os.open('/dev/null', os.O_WRONLY)
    os.dup2(devnull, 1)
    os.close(devnull)
    sys.stdout = os.fdopen(newstdout, 'w')


def scc_taskrunner_main(options, args):

    ciel.log("Starting up SCC task runner, loading libciel-scc", "SCC", logging.INFO)
    #cdll.LoadLibrary("librcceworker.so")
    libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
    lib = CDLL(libpath + "/libciel-scc.so")
    if lib is None:
        ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
    
    lib.tr_hello()
    #redirect_stdout()
    argc = c_int(4)
    targv = c_char_p * 4 
    argv = targv("2", "0.533", "00" "01")
    lib.tr_init(argc, argv)
    
    while True:
        lib.tr_send()
        
    
    
def scc_coordinator_main(options, args):

    ciel.log("Starting up SCC coordinator, loading libciel-scc", "SCC", logging.INFO)
    #cdll.LoadLibrary("librcceworker.so")
    libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
    lib = CDLL(libpath + "/libciel-scc.so")
    if lib is None:
        ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
    
    lib.coord_hello()
    #redirect_stdout()
    argc = c_int(4)
    targv = c_char_p * 4 
    argv = targv("2", "0.533", "00" "01")
    lib.coord_init()
    
    while True:
        lib.coord_read()
    
