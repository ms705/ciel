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
import struct

from ctypes import *
from skywriting.runtime.scc.messages import *


class SCCCoordinator:
    
    COORDINATOR_CORE_ID = 0
    
    def __init__(self, name, queue_manager, num_cores):
        self.name = name
        self.num_cores = num_cores
        self.qm = queue_manager
        self.current_tasks = []
        self.threads = []
        for i in range(num_cores):
            self.current_tasks.append(None)
            self.threads.append(None)
            
        self.block_store = self.qm.job_manager.worker.block_store
    
    
    def convert_refs(self, refs):
        
        ciel.log("Started reference conversion for %d refs" % len(refs), "SCC", logging.INFO)
        
        refs_as_strings = self.block_store.retrieve_strings_for_refs(refs)
        
        refs_as_datavalues = [SWDataValue(ref.id, self.block_store.encode_datavalue(val)) for ref, val in zip(refs, refs_as_strings)]
        
        ciel.log("Finished reference conversion for %d refs" % len(refs), "SCC", logging.INFO)
        
        return refs_as_datavalues
    
    
    def handle_task(self, task, coreid):
        
        next_td = task.as_descriptor()
        
        # Converts inputs, dependencies and task_private to SWDataValues
        #next_td["inputs"] = self.convert_refs(next_td["inputs"])
        #next_td["dependencies"] = self.convert_refs(next_td["dependencies"])
        #next_td["task_private"] = self.convert_refs([next_td["task_private"]])[0]
        
        task_record = task.taskset.build_task_record(next_td)
        task_record.task_set.job.task_started()
        task_record.start_time = datetime.datetime.now()
        
        # Manufacture the dispatch message and send it to the task runner
        coord_send = self.lib.coord_send
        dispatchmsg = pointer(TaskDispatchMessage(self.COORDINATOR_CORE_ID, coreid, next_td).toStruct())
        coord_send(dispatchmsg)
        
        # Keep a record of the fact that this core is now working on a task
        self.current_tasks[coreid] = (task, task_record)


    def thread_main(self):
        
        ciel.log("Starting up SCC coordinator, loading libciel-scc", "SCC", logging.INFO)
        libpath = os.getenv("LIBCIEL_PATH", "../src/c/src")
        self.lib = CDLL(libpath + "/libciel-scc.so")
        if self.lib is None:
            ciel.log.error("Failed to load libciel-scc", "SCC", logging.ERROR, True)
        
        self.lib.coord_hello()
        #redirect_stdout()
        
        # Manufacture a list of cores that we can pass as arguments to the coord_init function
        # in libciel. 
        corelist = []
        for i in range(self.num_cores):
            corelist.append(str(i))
        argc = c_int(self.num_cores + 3)
        targv = c_char_p * (self.num_cores + 3)
        
        # Args taken (according to RCCE convention): 
        # (1) executable name, 
        # (2) number of cores used, 
        # (3) clock frequency in GHz (for timing ONLY, doesn't set clock freq)
        # (4...50) core IDs for UE 0...47  
        argv = targv("libciel-scc", str(self.num_cores), "0.533", *corelist)
        self.lib.coord_init(argc, argv)
        
        # Set up the return type for the coordinator receive method (ptr to message struct)
        coord_read = self.lib.coord_read
        coord_read.restype = POINTER(MESSAGE)
        
        # Main message loop
        while True:
            # At the coordinator, we keep waiting for messages and return once we have received one
            ciel.log("Coordinator waiting for messages...", "SCC", logging.INFO)
            msg = coord_read()
            ciel.log("Got message, parsing...", "SCC", logging.INFO)
            #print "message from core %d: %s (length %d)" % (msg.contents.source, string_at(msg.contents.msg_body[5:]), msg.contents.length)
            
            # Get the message body out
            body = msg.contents.msg_body
            
            # We no longer decode all messages as JSON immediately
            #bodyjson = simplejson.loads(body, object_hook=json_decode_object_hook)
            
            # Find out what sort of message this is -- stored in first byte of message string
            msg_type = int(body[0])
            
            ciel.log("Message from core %d of (length %d, type %s)" % (msg.contents.source, msg.contents.length, AbstractMessage.type_to_string(msg_type)), "SCC", logging.INFO)
            
            # Switch on message type
            if msg_type == AbstractMessage.IDLE_MESSAGE:
                # IDLE message: sent by cores when they initially report to the coordinator
                ciel.log("Got idle message from core %d" % msg.contents.source, "SCC")
                self.send_next_task_to_core(msg.contents.source)
            
            elif msg_type == AbstractMessage.GET_MESSAGE:
                # GET message: task runner is asking for a reference's data to be sent over, 
                # so we respond with that in a PUT message 
                ciel.log("Got reference fetch message from core %d for reference %s" % (msg.contents.source, body[1:]))
                
                ref = simplejson.loads(body[1:], object_hook=json_decode_object_hook)
                if not self.block_store.is_ref_local(ref):
                    ciel.log.error("Task runner %d asked for ref %s, which is not available locally", "SCC", logging.ERROR, False)
                else:
                    fname = self.block_store.filename_for_ref(ref)
                    
                    buf = ""
                    buf += open(fname, 'rb').read()
                    
                    refmsg = pointer(PutReferenceMessage(0, msg.contents.source, ref, buf))
                    ciel.log("Sending message to core %d:" % (msg.contents.source, refmsg))
                    self.lib.coord_send(refmsg)
                
            elif msg_type == AbstractMessage.PUT_MESSAGE:
                reflen = struct.unpack("I", body[1:5])[0]
                clen = struct.unpack("I", body[(5+reflen):(5+reflen+4)])[0]
                #print len(body)
                #print " ".join([str(ord(x)) for x in body[0:6]])
                ciel.log("Got reference put message from core %d for reference (length %d, ref %d, contents %d)" % (msg.contents.source, msg.contents.length, reflen, clen))
                
                refid = body[5:(5+reflen)]
                contents = body[(5+reflen+4):(5+reflen+4+clen)]
                
                # Write the reference out to the block store
                self.block_store.ref_from_string(contents, refid)
                
                
            elif msg_type == AbstractMessage.DONE_MESSAGE:
                # We are receiving the results of a task execution
                ciel.log("Got task completion message from core %d (length %d)" % (msg.contents.source, msg.contents.length), "SCC", logging.INFO)
                
                reslen = struct.unpack("I", body[1:5])[0]
                (success, spawned_tasks, published_refs) = simplejson.loads(body[5:(reslen+5)], object_hook=json_decode_object_hook)
                
                #success = bodyjson["body"][0]
                #spawned_tasks = bodyjson["body"][1] 
                #published_refs = bodyjson["body"][2]
                
                record = self.current_tasks[msg.contents.source][1]
                task = self.current_tasks[msg.contents.source][0]

                ciel.log("Start handling task completion (task from core %d)" % msg.contents.source, "SCC", logging.INFO)
                
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
                        self.block_store.is_ref_local(ref)
                    
                    if not task:
                        ciel.log.error('Tried to handle completed task from core %d, but found no record of it in current_tasks' % (msg.contents.source), 'SCC', logging.ERROR, True)
                    task.taskset.task_graph.spawn_and_publish(spawned_tasks, published_refs, task.as_descriptor())
                    task.taskset.dec_runnable_count()
                    
                    ciel.log("Done handling task completion (task from core %d), thread joining" % msg.contents.source, "SCC", logging.INFO)
 
                    print "got to the end of task, thread joining"
                    self.threads[msg.contents.source].join()
                    
                    ciel.log("Joined, spinning up new thread", "SCC", logging.INFO)
 
                    self.send_next_task_to_core(msg.contents.source)
 
                    ciel.log("Spawn handler thread up and running", "SCC", logging.INFO)
 
                else:
                    # report an error
                    ciel.log.error('Task %s on core %d did not complete successfully' % (task['task_id'], msg.contents.source), 'SCC', logging.ERROR, True)
                    pass
                
                
            else:
                ciel.log.error('Received unrecognized message type %s from core %d' % (body[0], msg.contents.source), 'SCC', logging.ERROR, True)
            
            print "got to the end of the coordinator receive loop"
        
        
    def send_next_task_to_core(self, coreid):
        
        # We launch a new thread to handle the dispatch and running of a task in a non-blocking fashion.
        # Note that this creates a maximum of (num_cores - 1) threads on the coordinator
        self.threads[coreid] = threading.Thread(target=self.task_handler_thread_main, args=[coreid])
        self.threads[coreid].start()
        
        
    def task_handler_thread_main(self, coreid):
        
        # Get the next task from the queue manager
        task = self.qm.get_next_task(self.name)
        
        if task is None:
            return
        else:
            try:
                self.handle_task(task, coreid)
            except Exception:
                ciel.log.error('Uncaught error handling task in pool: %s' % (self.name), 'SCC', logging.ERROR, True)
            
            # Notify the queue manager that the task is now completed 
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
        tr_read.restype = POINTER(MESSAGE)
        
        # Send an IDLE message to start off
        idlemsg = pointer(IdleMessage(me, coordinator).toStruct())
        lib.tr_send(idlemsg)
        
        while True:
            msg = tr_read()
            #print "message from coordinator (%d) of length %d: %s" % (msg.contents.source, msg.contents.length, string_at(msg.contents.msg_body, msg.contents.length)) 
            # Load TD from JSON
            #bodyObj = simplejson.loads(string_at(msg.contents.msg_body, msg.contents.length), object_hook=json_decode_object_hook)
            body = string_at(msg.contents.msg_body)
            msg_type = int(body[0])
            print "message from coordinator (%d) of length %d, type %s" % (msg.contents.source, msg.contents.length, AbstractMessage.type_to_string(msg_type)) 
            
            if not msg_type == AbstractMessage.SPAWN_MESSAGE:
                ciel.log.error('Message received is not of type SPAWN!', 'SCC', logging.ERROR, True)
                continue
            
            #td = bodyObj["body"]
            td = simplejson.loads(string_at(body[1:]), object_hook=json_decode_object_hook)
            
            _=[self.block_store.is_ref_local(x) for x in td["inputs"]]
            
            # Make a TaskSetExecutionRecord and a TaskExecutionRecord with most of the parameters stubbed out
            taskset = TaskSetExecutionRecord(td, self.block_store, None, execution_features, self.worker)
            record = TaskExecutionRecord(td, taskset, execution_features, self.block_store, None, self.worker)
            
            # Run the actual task (this will block)
            try:
                record.run()
            except:
                ciel.log.error('Error during executor task execution', 'SCC', logging.ERROR, True)
            
            ciel.log("Task on task runner completed", "SCC", logging.INFO)
            
            _=[self.block_store.is_ref_local(x) for x in record.published_refs]
            
            # We're now done and can send our outputs back
            #record.task_set.job.task_finished()
            if record.success:
                record.published_refs = self.convert_refs(record.published_refs)
                #pass
                #task.taskset.task_graph.spawn_and_publish(task_record.spawned_tasks, task_record.published_refs, next_td)
                
            # send the data for the task's published references
            for ref in record.published_refs:
                if not self.block_store.is_ref_local(ref):
                    ciel.log.error("Tried to publish a non-local reference (%s)" % ref, "SCC", False)
                else:
                    fname = self.block_store.filename_for_ref(ref)
                    
                    buf = ""
                    buf += open(fname, 'rb').read()
                    
                    refmsg = pointer(PutReferenceMessage(me, coordinator, ref, buf).toStruct())
                    self.lib.coord_send(refmsg)
            
            msg = pointer(TaskCompletedMessage(me, coordinator, record.success, record.spawned_tasks, record.published_refs).toStruct())
            lib.tr_send(msg)
            print "sent task completion message, end of loop"
            
        
        

def scc_taskrunner_main(options, args):
    tr = SCCTaskRunner()
    tr.run(options, args)
    
