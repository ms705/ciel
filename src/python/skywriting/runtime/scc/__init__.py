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
from skywriting.runtime.scc.messages import *


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
    
    me = 1
    coordinator = 0
    
    numcores = 48
    corelist = []
    for i in range(numcores):
        corelist.append(str(i))
    corelist.append(me)
    
    argc = c_int(numcores + 4)
    targv = c_char_p * (numcores + 4)
    argv = targv("libciel-scc", str(numcores), "0.533", *corelist)
    lib.tr_init(argc, argv)
    
    tr_read = lib.tr_read
    tr_read.restype = MESSAGE
    
    # Send an IDLE message to start off
    idlemsg = IdleMessage(me, coordinator).toStruct()
    lib.tr_send(idlemsg)
    
    while True:
        msg = tr_read()
        print "message from coordinator (%d): %s (length %d)" % (msg.source, string_at(msg.msg_body), msg.length) 
        # task stuff
        #lib.tr_send()
        
    
    
def scc_coordinator_main(options, args):

    ciel.log("Starting up SCC coordinator, loading libciel-scc", "SCC", logging.INFO)
    #cdll.LoadLibrary("librcceworker.so")
    libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
    lib = CDLL(libpath + "/libciel-scc.so")
    if lib is None:
        ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
    
    lib.coord_hello()
    #redirect_stdout()
    
    numcores = 48
    corelist = []
    for i in range(numcores):
        corelist.append(str(i))
    argc = c_int(numcores + 3)
    targv = c_char_p * (numcores + 3)
    argv = targv("libciel-scc", str(numcores), "0.533", *corelist)
    lib.coord_init(argc, argv)
    
    coord_read = lib.coord_read
    coord_read.restype = MESSAGE
    coord_send = lib.coord_send
    while True:
        #coord_send(testmsg)
        print "coordinator waiting for messages..."
        # At the coordinator, we keep waiting for messages and return once we have received one
        msg = coord_read()
        print "message from core %d: %s (length %d)" % (msg.source, string_at(msg.msg_body), msg.length)
        if msg.msg_body == "IDLE":
            testmsg = MESSAGE(0, msg.source, 32, "Hello from the coordinator!")
            coord_send(testmsg) 
    
