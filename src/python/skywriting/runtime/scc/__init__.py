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
from skywriting.runtime.scc.block_store import FakeBlockStore
import tempfile
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
        self.threads = []
        for i in range(num_cores):
            self.current_tasks.append(None)
            self.threads.append(None)
    
    #def get_next_task(self, name):
    #    pass
    
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
        
        coord_send = self.lib.coord_send
        dispatchmsg = TaskDispatchMessage(0, coreid, next_td).toStruct()
        coord_send(dispatchmsg)
        
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
            #print "message from core %d: %s (length %d)" % (msg.source, string_at(msg.msg_body, msg.length), msg.length)
            
            # decode the message JSON
            body = string_at(msg.msg_body, msg.length)
            bodyjson = simplejson.loads(body, object_hook=json_decode_object_hook)
            
            print "message from core %d of (length %d, type %s)" % (msg.source, msg.length, bodyjson["type"])
            
            if bodyjson["type"] == "IDLE":
                #self.send_next_task_to_core(msg.source)
                print "got idle message from core %d" % msg.source
                self.threads[msg.source] = threading.Thread(target=self.send_next_task_to_core, args=[msg.source])
                self.threads[msg.source].start()
            elif bodyjson["type"] == "GET":
                print "got reference fetch message from core %d for reference %s" % (msg.source, bodyjson["ref"])
                pass
            elif bodyjson["type"] == "DONE":
                # We are receiving the results of a task execution
                print "got task completion message from core %d" % msg.source
                #(success, spawned_tasks, published_refs) = simplejson.loads(string_at(msg.msg_body, msg.length), object_hook=json_decode_object_hook)
                success = bodyjson["body"][0]
                spawned_tasks = bodyjson["body"][1] 
                published_refs = bodyjson["body"][2]
                
                record = self.current_tasks[msg.source][1]
                task = self.current_tasks[msg.source][0]

                
                if success:
                    record.success = True
                    record.finish_time = datetime.datetime.now()
                    execution_time = record.finish_time - record.start_time
                    execution_secs = execution_time.seconds + execution_time.microseconds / 1000000.0
                    record.task_set.job.task_finished(task, execution_secs)
                    
                    record.spawned_tasks = spawned_tasks
                    
                    record.published_refs = published_refs
                    
                    # We need to iterate over the published references here and check if they are local
                    # This will force the local block store to actually write the received SWDataValues out
                    # so that they can be sent to future tasks 
                    for ref in published_refs:
                        self.qm.job_manager.worker.block_store.is_ref_local(ref)
                    
                    if not task:
                        ciel.log.error('Tried to handle completed task from core %d, but found no record of it in current_tasks' % (msg.source), 'SCC', logging.ERROR, True)
                    task.taskset.task_graph.spawn_and_publish(spawned_tasks, published_refs, task.as_descriptor())
                    task.taskset.dec_runnable_count()
                    
                    print "got to the end of task, thread joining"
                    self.threads[msg.source].join()
                    
                    self.threads[msg.source] = threading.Thread(target=self.send_next_task_to_core, args=[msg.source])
                    self.threads[msg.source].start()

                else:
                    # report an error
                    ciel.log.error('Task %s on core %d did not complete successfully' % (task['task_id'], msg.source), 'SCC', logging.ERROR, True)
                    pass
                
                
            else:
                ciel.log.error('Received unrecognized message type %s from core %d' % (bodyjson["type"], bodyjson["src"]), 'SCC', logging.ERROR, True)
            
            print "got to the end of the coordinator receive loop"
            
            
    def send_next_task_to_core(self, coreid):
        task = self.qm.get_next_task(self.name)
        #self.lib.coord_notify();
        
        if task is None:
            return
        else:
            try:
                self.handle_task(task, coreid)
            except Exception:
                ciel.log.error('Uncaught error handling task in pool: %s' % (self.name), 'SCC', logging.ERROR, True)
            self.qm.notify(self.name)
            #self.threads[coreid].join()

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
        
        bsdir = tempfile.mkdtemp(prefix="scc-tr-tmp")
        ciel.log("Task runner creating fake block store backing directory at %s" % bsdir, "SCC", logging.INFO)
        
        libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
        self.lib = CDLL(libpath + "/libciel-scc.so")
        
        self.block_store = FakeBlockStore(ciel.engine, None, None, bsdir, self.lib)
        self.worker = FakeWorker(self.block_store) 
        
    
    
    def convert_refs(self, refs):
        
        refs_as_strings = self.block_store.retrieve_strings_for_refs(refs)
        
        refs_as_datavalues = [SWDataValue(ref.id, self.block_store.encode_datavalue(val)) for ref, val in zip(refs, refs_as_strings)]
        
        return refs_as_datavalues
    
    
    def run(self, options, args):
    
        ciel.log("Starting up SCC task runner, loading libciel-scc", "SCC", logging.INFO)
        #cdll.LoadLibrary("librcceworker.so")
        lib = self.lib
        if lib is None:
            ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
        
        lib.tr_hello()
        #redirect_stdout()
        
        if len(args) > 0:
            me = int(args[0])
        else:
            me = 1
        coordinator = 0
        
        execution_features = ExecutionFeatures()
        #execution_features.check_executors()
        
        
        numcores = 48
        corelist = []
        for i in range(numcores):
            corelist.append(str(i))
        corelist.append(str(me))
        
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
            #print "message from coordinator (%d) of length %d: %s" % (msg.source, msg.length, string_at(msg.msg_body, msg.length)) 
            # Load TD from JSON
            bodyObj = simplejson.loads(string_at(msg.msg_body, msg.length), object_hook=json_decode_object_hook)
            print "message from coordinator (%d) of length %d, type %s" % (msg.source, msg.length, bodyObj['type']) 
            
            if not bodyObj['type'] == 'SPAWN':
                ciel.log.error('Message received is not of type SPAWN!', 'SCC', logging.ERROR, True)
                continue
            
            td = bodyObj["body"]
            
            _=[self.block_store.is_ref_local(x) for x in td["inputs"]]
            
            # Make a TaskSetExecutionRecord and a TaskExecutionRecord with most of the parameters stubbed out
            taskset = TaskSetExecutionRecord(td, self.block_store, None, execution_features, self.worker)
            record = TaskExecutionRecord(td, taskset, execution_features, self.block_store, None, self.worker)
            
            # Run the actual task (this will block)
            try:
                record.run()
            except:
                ciel.log.error('Error during executor task execution', 'SCC', logging.ERROR, True)
            
            print "task completed"
            
            _=[self.block_store.is_ref_local(x) for x in record.published_refs]
            
            # We're now done and can send our outputs back
            #record.task_set.job.task_finished()
            if record.success:
                record.published_refs = self.convert_refs(record.published_refs)
                #pass
                #task.taskset.task_graph.spawn_and_publish(task_record.spawned_tasks, task_record.published_refs, next_td)

            msg = TaskCompletedMessage(me, coordinator, record.success, record.spawned_tasks, record.published_refs).toStruct()
            lib.tr_send(msg)
            print "sent task completion message, end of loop"
            
        
        

def scc_taskrunner_main(options, args):
    tr = SCCTaskRunner()
    tr.run(options, args)
    
