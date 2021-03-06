# Copyright (c) 2010 Derek Murray <derek.murray@cl.cam.ac.uk>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
from __future__ import with_statement
from Queue import Queue
from shared.references import SWReferenceJSONEncoder
from skywriting.runtime.pycurl_rpc import post_string_noreturn, get_string,\
    post_string
import re
import httplib2
import urllib
import httplib
import ciel
import datetime
import logging
import random
import simplejson
import threading
import uuid
from urlparse import urlparse

class FeatureQueues:
    def __init__(self):
        self.queues = {}
        self.streaming_queues = {}
        
    def get_queue_for_feature(self, feature):
        try:
            return self.queues[feature]
        except KeyError:
            queue = Queue()
            self.queues[feature] = queue
            return queue

    def get_streaming_queue_for_feature(self, feature):
        try:
            return self.streaming_queues[feature]
        except KeyError:
            queue = Queue()
            self.streaming_queues[feature] = queue
            return queue

class Worker:
    
    DIRECT_HTTP_RPC = 0
    C2DM_PUSH = 1
    cm_names = ["DIRECT_HTTP_RPC", "C2DM_PUSH"]
    
    def __init__(self, worker_id, worker_descriptor, feature_queues, worker_pool):
        self.id = worker_id
        self.netloc = worker_descriptor['netloc']
        self.features = worker_descriptor['features']
        try:
            self.communication_mechanism = worker_descriptor['communication_mechanism']
        except KeyError:
            self.communication_mechanism = self.DIRECT_HTTP_RPC
        self.scheduling_classes = worker_descriptor['scheduling_classes']
        
        if self.communication_mechanism == self.C2DM_PUSH:
            self.last_ping = None
        else:
            self.last_ping = datetime.datetime.now()
        
        self.failed = False
        self.worker_pool = worker_pool

    def idle(self):
        pass

    def get_effective_scheduling_class(self, scheduling_class):
        if scheduling_class in self.scheduling_classes:
            return scheduling_class
        else:
            return '*'

    def get_effective_scheduling_class_capacity(self, scheduling_class):
        try:
            return self.scheduling_classes[scheduling_class]
        except KeyError:
            return self.scheduling_classes['*']

    def __repr__(self):
        return 'Worker(%s)' % self.id

    def as_descriptor(self):
        return {'worker_id': self.id,
                'netloc': self.netloc,
                'features': self.features,
                'last_ping': self.last_ping.ctime() if self.last_ping is not None else None,
                'failed':  self.failed,
                'communication_mechanism': self.communication_mechanism}
        
class WorkerPool:
    
    def __init__(self, bus, deferred_worker, job_pool):
        self.bus = bus
        self.deferred_worker = deferred_worker
        self.job_pool = job_pool
        self.idle_worker_queue = Queue()
        self.workers = {}
        self.netlocs = {}
        self.idle_set = set()
        self._lock = threading.RLock()
        self.feature_queues = FeatureQueues()
        self.event_count = 0
        self.event_condvar = threading.Condition(self._lock)
        self.max_concurrent_waiters = 5
        self.current_waiters = 0
        self.is_stopping = False
        self.scheduling_class_capacities = {}
        self.scheduling_class_total_capacities = {}
        self.exec_features = {}
        self.c2dm_mgr = C2DMTools()

    def subscribe(self):
        self.bus.subscribe('start', self.start, 75)
        self.bus.subscribe('stop', self.server_stopping, 10) 
        
    def unsubscribe(self):
        self.bus.unsubscribe('start', self.start, 75)
        self.bus.unsubscribe('stop', self.server_stopping) 

    def start(self):
        self.deferred_worker.do_deferred_after(30.0, self.reap_dead_workers)
        
    def reset(self):
        self.idle_worker_queue = Queue()
        self.workers = {}
        self.netlocs = {}
        self.idle_set = set()
        self.feature_queues = FeatureQueues()
        
    def allocate_worker_id(self):
        return str(uuid.uuid1())
        
    def create_worker(self, worker_descriptor):
        with self._lock:
            id = self.allocate_worker_id()
            worker = Worker(id, worker_descriptor, self.feature_queues, self)
            self.workers[id] = worker
            try:
                previous_worker_at_netloc = self.netlocs[worker.netloc]
                ciel.log.error('Worker at netloc %s has reappeared' % worker.netloc, 'WORKER_POOL', logging.WARNING)
                self.worker_failed(previous_worker_at_netloc)
            except KeyError:
                pass
            self.netlocs[worker.netloc] = worker
            self.idle_set.add(id)
            self.event_count += 1
            self.event_condvar.notify_all()
            
            if worker.communication_mechanism == worker.C2DM_PUSH:
                # register with Google
                self.c2dm_mgr.authenticate()
            
            for scheduling_class, capacity in worker.scheduling_classes.items():
                try:
                    capacities = self.scheduling_class_capacities[scheduling_class]
                    current_total = self.scheduling_class_total_capacities[scheduling_class]
                except:
                    capacities = []
                    self.scheduling_class_capacities[scheduling_class] = capacities
                    current_total = 0
                capacities.append((worker, capacity))
                self.scheduling_class_total_capacities[scheduling_class] = current_total + capacity
            
            for feature in worker.features:
                try:
                    self.exec_features[feature].append(worker)
                except:
                    self.exec_features[feature] = [worker]
            
            self.job_pool.notify_worker_added(worker)
            return id

    def notify_job_about_current_workers(self, job):
        """Nasty function included to avoid the race between job creation and worker creation."""
        with self._lock:
            for worker in self.workers.values():
                job.notify_worker_added(worker)

# XXX: This is currently disabled because we don't have a big central list of references.
#        try:
#            has_blocks = worker_descriptor['has_blocks']
#        except:
#            has_blocks = False
#            
#        if has_blocks:
#            ciel.log.error('%s has blocks, so will fetch' % str(worker), 'WORKER_POOL', logging.INFO)
#            self.bus.publish('fetch_block_list', worker)
            
        self.bus.publish('schedule')
        return id
    
    def shutdown(self):
        for worker in self.workers.values():
            try:
                get_string('http://%s/control/kill/' % worker.netloc)
            except:
                pass
        
    def get_worker_by_id(self, id):
        with self._lock:
            return self.workers[id]
        
    def get_all_workers(self):
        with self._lock:
            return self.workers.values()
    
    def execute_task_on_worker(self, worker, task):
        try:
            message = simplejson.dumps(task.as_descriptor(), cls=SWReferenceJSONEncoder)
            if worker.communication_mechanism == Worker.C2DM_PUSH:
                # magic push notification
                self.c2dm_mgr.send_message(worker, ",".join([task.job.id, task.task_id]))
            else:
                post_string_noreturn("http://%s/control/task/" % (worker.netloc), message, result_callback=self.worker_post_result_callback)
        except:
            self.worker_failed(worker)

    def abort_task_on_worker(self, task, worker):
        try:
            ciel.log("Aborting task %s on worker %s" % (task.task_id, worker), "WORKER_POOL", logging.WARNING)
            post_string_noreturn('http://%s/control/abort/%s/%s' % (worker.netloc, task.job.id, task.task_id), "", result_callback=self.worker_post_result_callback)
        except:
            self.worker_failed(worker)
    
    def worker_failed(self, worker):
        ciel.log.error('Worker failed: %s (%s)' % (worker.id, worker.netloc), 'WORKER_POOL', logging.WARNING, True)
        with self._lock:
            worker.failed = True
            del self.netlocs[worker.netloc]
            del self.workers[worker.id]

            for scheduling_class, capacity in worker.scheduling_classes.items():
                self.scheduling_class_capacities[scheduling_class].remove((worker, capacity))
                self.scheduling_class_total_capacities[scheduling_class] -= capacity
                if self.scheduling_class_total_capacities[scheduling_class] == 0:
                    del self.scheduling_class_capacities[scheduling_class]
                    del self.scheduling_class_total_capacities[scheduling_class]

        if self.job_pool is not None:
            self.job_pool.notify_worker_failed(worker)

    def worker_ping(self, worker):
        if worker.last_ping is not None:
            with self._lock:
                self.event_count += 1
                self.event_condvar.notify_all()
            worker.last_ping = datetime.datetime.now()

    def server_stopping(self):
        with self._lock:
            self.is_stopping = True
            self.event_condvar.notify_all()

    def investigate_worker_failure(self, worker):
        ciel.log.error('Investigating possible failure of worker %s (%s)' % (worker.id, worker.netloc), 'WORKER_POOL', logging.WARNING)
        try:
            content = get_string('http://%s/control' % worker.netloc)
            id = simplejson.loads(content)
            assert id == worker.id
        except:
            self.worker_failed(worker)

    def get_random_worker(self):
        with self._lock:
            return random.choice(self.workers.values())
        
    def get_random_worker_with_capacity_weight(self, scheduling_class):
        
        with self._lock:
            try:
                candidates = self.scheduling_class_capacities[scheduling_class]
                total_capacity = self.scheduling_class_total_capacities[scheduling_class]
            except KeyError:
                scheduling_class = '*'
                candidates = self.scheduling_class_capacities['*']
                total_capacity = self.scheduling_class_total_capacities['*']
        
            selected_slot = random.randrange(total_capacity)
            curr_slot = 0
            i = 0
            
            for worker, capacity in candidates:
                curr_slot += capacity
                if curr_slot > selected_slot:
                    return worker
            
            ciel.log('Ran out of workers in capacity-weighted selection class=%s selected=%d total=%d' % (scheduling_class, selected_slot, total_capacity), 'WORKER_POOL', logging.ERROR)
            
    def get_random_worker_with_exec_feature(self, feature):
        
        ciel.log("Requested worker with exec feature %s" % feature, 'WORKER_POOL', logging.INFO)
        
        with self._lock:
            try:
                candidates = self.exec_features[feature]
            except KeyError:
                ciel.log('No workers supporting "%s" execution feature exist!' % (feature), 'WORKER_POOL', logging.ERROR)
                
            selected_slot = random.randrange(len(candidates))
            
            return candidates[selected_slot]
            

    def get_worker_at_netloc(self, netloc):
        try:
            return self.netlocs[netloc]
        except KeyError:
            return None

    def reap_dead_workers(self):
        if not self.is_stopping:
            for worker in self.workers.values():
                if worker.failed or worker.last_ping is None:
                    continue
                if (worker.last_ping + datetime.timedelta(seconds=10)) < datetime.datetime.now():
                    failed_worker = worker
                    self.deferred_worker.do_deferred(lambda: self.investigate_worker_failure(failed_worker))
                    
            self.deferred_worker.do_deferred_after(10.0, self.reap_dead_workers)

    def worker_post_result_callback(self, success, url):
        # An asynchronous post_string_noreturn has completed against 'url'. Called from the cURL thread.
        if not success:
            parsed = urlparse(url)
            worker = self.get_worker_at_netloc(parsed.netloc)
            if worker is not None:
                ciel.log("Aysnchronous post against %s failed: investigating" % url, "WORKER_POOL", logging.ERROR)
                # Safe to call from here: this bottoms out in a deferred-work call quickly.
                self.worker_failed(worker)
            else:
                ciel.log("Asynchronous post against %s failed, but we have no matching worker. Ignored." % url, "WORKER_POOL", logging.WARNING)

class C2DMTools:
    
    GOOGLE_ID = "cam.ciel@gmail.com"
    GOOGLE_PWD = "clisawesome"
    PACKAGE_NAME = "uk.ac.cam.cl.ciel"
    
    def __init__(self):
        self.auth_token = None
    
    def authenticate(self):
        if self.auth_token is None:
            data = self._post_https_formenc("www.google.com", "/accounts/ClientLogin", {'Email': self.GOOGLE_ID, 
                                                                                  'Passwd': self.GOOGLE_PWD, 
                                                                                  'accountType': "HOSTED_OR_GOOGLE", 
                                                                                  'source': self.PACKAGE_NAME, 
                                                                                  'service': "ac2dm"})
            for line in data.splitlines():
                m = re.match(r"Auth=(.+)", line)
                if m is not None:
                    self.auth_token = m.group(1)
        else:
            return self.auth_token
        
    def get_token(self):
        return self.auth_token
    
    def send_message(self, worker, message):
        if self.auth_token is not None:
            t = datetime.datetime.now()
            ciel.log("%d:%d:%d.%d POST push message" % (t.hour, t.minute, t.second, t.microsecond), "TIMING", logging.INFO)
            resp = self._post_https_formenc("android.apis.google.com", "/c2dm/send", {'registration_id': worker.netloc,
                                                                                      'data.message': message,
                                                                                      'collapse_key': "new"},
                                                                                      {'Authorization': "GoogleLogin auth=" + self.auth_token})
            print resp
            m = re.match(r"id=(.+)", resp)
            if m is not None:
                return m.group(1)
            else:
                m = re.match(r"Error=(.+)", resp)
                if m is not None:
                    ciel.log("ERROR sending push message: %s" % m.group(1), "C2DM", logging.ERROR)
                else:
                    ciel.log("Unknown error sending push message", "C2DM", logging.ERROR)
        else:
            pass
        
    def _post_https_formenc(self, host, path, data, add_headers=None):
        params = urllib.urlencode(data)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        if add_headers is not None:
            headers = dict(headers.items() + add_headers.items())
        conn = httplib.HTTPSConnection(host)
        conn.request("POST", path, params, headers)
        try:
            response = conn.getresponse()
            if response.status == 200:
                data = response.read()
                return data
            else:
                ciel.log("ERROR POSTing to Google: response was %s %s " % (str(response.status), response.reason))
        finally:
            conn.close()
