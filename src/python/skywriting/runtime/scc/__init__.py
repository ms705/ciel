'''
Created on 9 Mar 2011

@author: ms705
'''
from skywriting.runtime.exceptions import ReferenceUnavailableException,\
    AbortedException
from skywriting.runtime.block_store import json_decode_object_hook,\
    SWReferenceJSONEncoder, BlockStore
from skywriting.runtime.local_task_graph import LocalTaskGraph, LocalJobOutput
from skywriting.runtime.task_executor import TaskExecutionRecord,\
    TaskSetExecutionRecord
from skywriting.runtime.executors import ExecutionFeatures
from shared.references import SWDataValue
import datetime
import ciel
import logging
import os, sys
import threading
import simplejson

from ctypes import *
from skywriting.runtime.scc.messages import *


class SCCCoordinator:
    
    def __init__(self, name, queue_manager, num_cores):
        self.name = name
        self.num_cores = num_cores
        self.qm = queue_manager
        self.current_tasks = []
        for i in range(num_cores):
            self.current_tasks.append(None)
    
    def get_next_task(self, name):
        pass
    
    def convert_refs(self, refs):
        
        refs_as_strings = self.qm.job_manager.worker.block_store.retrieve_strings_for_refs(refs)
        
        refs_as_datavalues = [SWDataValue(ref.id, self.qm.job_manager.worker.block_store.encode_datavalue(val)) for ref, val in zip(refs, refs_as_strings)]
        
        return refs_as_datavalues
    
    def handle_task(self, task, coreid):
        
        next_td = task.as_descriptor()
        
        next_td["inputs"] = self.convert_refs(next_td["inputs"])
        next_td["dependencies"] = self.convert_refs(next_td["dependencies"])
        next_td["task_private"] = self.convert_refs([next_td["task_private"]])[0]
        
        task_record = task.taskset.build_task_record(next_td)
        task_record.task_set.job.task_started()
        task_record.start_time = datetime.datetime.now()
        
        td_string = simplejson.dumps(next_td, cls=SWReferenceJSONEncoder)
        
        coord_send = self.lib.coord_send
        testmsg = MESSAGE(0, coreid, len(td_string), td_string)
        coord_send(testmsg)
        
        self.current_tasks[coreid] = (task, task_record)


    def thread_main(self):
        
        ciel.log("Starting up SCC coordinator, loading libciel-scc", "SCC", logging.INFO)
        #cdll.LoadLibrary("librcceworker.so")
        libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
        self.lib = CDLL(libpath + "/libciel-scc.so")
        if self.lib is None:
            ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
        
        self.lib.coord_hello()
        #redirect_stdout()
        
        corelist = []
        for i in range(self.num_cores):
            corelist.append(str(i))
        argc = c_int(self.num_cores + 3)
        targv = c_char_p * (self.num_cores + 3)
        argv = targv("libciel-scc", str(self.num_cores), "0.533", *corelist)
        self.lib.coord_init(argc, argv)
        
        coord_read = self.lib.coord_read
        coord_read.restype = MESSAGE
        
        
        while True:
            #coord_send(testmsg)
            print "coordinator waiting for messages..."
            # At the coordinator, we keep waiting for messages and return once we have received one
            msg = coord_read()
            print "message from core %d: %s (length %d)" % (msg.source, string_at(msg.msg_body), msg.length)
            if msg.msg_body == "IDLE":
                self.send_next_task_to_core(msg.source)
            else:
                # We are receiving the results of a task execution
                (success, spawned_tasks, published_refs) = simplejson.loads(msg.msg_body, object_hook=json_decode_object_hook)
                if success:
                    record = self.current_tasks[msg.source][1]
                    task = self.current_tasks[msg.source][0]
                    
                    record.success = True
                    record.finish_time = datetime.datetime.now()
                    execution_time = record.finish_time - record.start_time
                    execution_secs = execution_time.seconds + execution_time.microseconds / 1000000.0
                    record.task_set.job.task_finished(task, execution_secs)
                    
                    record.spawned_tasks = spawned_tasks
                    
                    record.published_refs = published_refs
                    
                    if not task:
                        ciel.log.error('Tried to handle completed task from core %d, but found no record of it in current_tasks' % (msg.source), 'SCC', logging.ERROR, True)
                    task.taskset.task_graph.spawn_and_publish(spawned_tasks, published_refs, task.as_descriptor())
                    task.taskset.dec_runnable_count()
                    self.send_next_task_to_core(msg.source)
                else:
                    # report an error
                    ciel.log.error('Task %s on core %d did not complete successfully' % (task['task_id'], msg.source), 'SCC', logging.ERROR, True)
                    pass
                
                
    def send_next_task_to_core(self, coreid):
        task = self.qm.get_next_task(self.name)
        if task is None:
            return
        else:
            try:
                self.handle_task(task, coreid)
            except Exception:
                ciel.log.error('Uncaught error handling task in pool: %s' % (self.name), 'SCC', logging.ERROR, True)
            self.qm.notify(self.name)

class FakeWorker:
    
    def __init__(self, blockstore):
        self.block_store = blockstore
        


def redirect_stdout():
    print "Redirecting stdout"
    sys.stdout.flush() # <--- important when redirecting to files
    newstdout = os.dup(1)
    devnull = os.open('/dev/null', os.O_WRONLY)
    os.dup2(devnull, 1)
    os.close(devnull)
    sys.stdout = os.fdopen(newstdout, 'w')


class SCCTaskRunner:
    
    def __init__(self):
        self.block_store = BlockStore(ciel.engine, None, None, "/tmp")
        self.worker = FakeWorker(self.block_store) 
        
    
    
    def convert_refs(self, refs):
        
        refs_as_strings = self.block_store.retrieve_strings_for_refs(refs)
        
        refs_as_datavalues = [SWDataValue(ref.id, self.block_store.encode_datavalue(val)) for ref, val in zip(refs, refs_as_strings)]
        
        return refs_as_datavalues
    
    
    def run(self, options, args):
    
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
        
        execution_features = ExecutionFeatures()
        #execution_features.check_executors()
        
        
        
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
            # Load TD from JSON
            td = simplejson.loads(msg.msg_body, object_hook=json_decode_object_hook)
            
            # Make a TaskSetExecutionRecord and a TaskExecutionRecord with most of the parameters stubbed out
            taskset = TaskSetExecutionRecord(td, self.block_store, None, execution_features, self.worker)
            record = TaskExecutionRecord(td, taskset, execution_features, self.block_store, None, self.worker)
            
            # Run the actual task (this will block)
            try:
                record.run()
            except:
                ciel.log.error('Error during executor task execution', 'MWPOOL', logging.ERROR, True)
            
            # We're now done and can send our outputs back
            #record.task_set.job.task_finished()
            if record.success:
                record.published_refs = self.convert_refs(record.published_refs)
                #task.taskset.task_graph.spawn_and_publish(task_record.spawned_tasks, task_record.published_refs, next_td)

            msg = TaskCompletedMessage(me, coordinator, record.success, record.spawned_tasks, record.published_refs).toStruct()
            lib.tr_send(msg)
            
        
        

def scc_taskrunner_main(options, args):
    tr = SCCTaskRunner()
    tr.run(options, args)
    
