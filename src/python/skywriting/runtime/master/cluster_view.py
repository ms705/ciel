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
from skywriting.runtime.master.job_pool import JOB_STATE_NAMES
from cherrypy._cperror import HTTPError
from skywriting.runtime.task import TASK_STATES, TASK_STATE_NAMES,\
    TASK_COMMITTED
from skywriting.runtime.master.profile_view import make_graph
import cherrypy
import time
from shared.references import SWDataValue, decode_datavalue
from cherrypy.lib.static import serve_file

def table_row(key, *args):
    return '<tr><td><b>%s</b></td>' % key + ''.join(['<td>%s</td>' % str(x) for x in args]) + '</tr>'
        
def span_row(heading, cols=2):
    return '<tr><td colspan="%d" bgcolor="#cccccc" align="center">%s</td></tr>' % (cols, heading)
        
def job_link(job):
    return '<a href="/control/browse/job/%s">%s</a>' % (job.id, job.id)

def ref_link(job, ref):
    return '<a href="/control/browse/ref/%s/%s">%s</a>' % (job.id, ref.id, ref.id)

def ref_id_link(job, ref_id):
    return '<a href="/control/browse/ref/%s/%s">%s</a>' % (job.id, ref_id, ref_id)

def task_link(job, task):
    return '<a href="/control/browse/task/%s/%s">%s</a>' % (job.id, task.task_id, task.task_id)

def pgraph_link(job, task):
    return '<a href="/control/browse/task/%s/%s/pgraph">Graph</a>' % (job.id, task.task_id, task.task_id)

def swbs_link(netloc, ref_id):
    return '<a href="http://%s/data/%s">Link</a>' % (netloc, ref_id)

def header(title=None, jobid=None):
    html = '<html>'
    html += '<head>'
    if title is not None:
        html += '<title>Job Browser</title>'
    html += '<style>html { margin: 0px; } body { margin: 0px; font-family: Helvetica, sans-serif; font-size: 1.0em; } .pageheader {' \
    'height: 80px; width: 100%; background: #0d259e url(\'/data/skyweb/ciel-logo.png\') no-repeat bottom left;' \
    'font-family: Helvetica; font-weight: bold; font-size: 20pt; color: #ffffff; overflow: hidden; text-align: right; margin-bottom: 5px;' \
    '} .pageheader a { color: white; font-size: 12pt; } </style>'
    html += '</head>'
    html += '<body><div class=\"pageheader\">%s<br /><a href=\"/control/browse/job/">All jobs</a> ' % title
    if jobid is not None:
        html += '<a href=\"/control/browse/job/%s\">Job home</a>' % jobid
    html += '</div>'
    
    return html


class WebBrowserRoot:
    
    def __init__(self, job_pool):
        self.job = JobBrowserRoot(job_pool)
        self.task = TaskBrowserRoot(job_pool)
        self.ref = RefBrowserRoot(job_pool)
        
class JobBrowserRoot:

    def __init__(self, job_pool):
        self.job_pool = job_pool
        
    @cherrypy.expose
    def index(self):
        jobs = self.job_pool.get_all_job_ids()
        job_string = header('Job Browser')
        job_string += '<table>'
        for job_id in jobs:
            job = self.job_pool.get_job_by_id(job_id)
            job_string += table_row('Job', job_link(job), JOB_STATE_NAMES[job.state])
        job_string += '</table></body></html>'
        return job_string
        
    @cherrypy.expose
    def default(self, job_id):
        try:
            job = self.job_pool.get_job_by_id(job_id)
        except KeyError:
            raise HTTPError(404)

        job_string = header('Job Browser', job_id)
        job_string += '<table>'
        job_string += table_row('ID', job.id)
        job_string += table_row('Root task', task_link(job, job.root_task))
        job_string += table_row('State', JOB_STATE_NAMES[job.state])
        job_string += table_row('Output ref', ref_id_link(job, job.root_task.expected_outputs[0]))
        job_string += span_row('Task states')
        for name, state in TASK_STATES.items():
            try:
                job_string += table_row('Tasks ' + name, job.task_state_counts[state])
            except KeyError:
                job_string += table_row('Tasks ' + name, 0)
        job_string += span_row('Task type/duration', 5)
        job_string += table_row('*', str(job.all_tasks.get()), str(job.all_tasks.min), str(job.all_tasks.max), str(job.all_tasks.count))
        for type, avg in job.all_tasks_by_type.items():
            job_string += table_row(type, str(avg.get()), str(avg.min), str(avg.max), str(avg.count))
        job_string += '</table></body></html>'
        return job_string

class TaskBrowserRoot:
    
    def __init__(self, job_pool):
        self.job_pool = job_pool
        
    @cherrypy.expose
    def default(self, job_id, task_id, attr=None):
        
        #attr = None
        
        try:
            job = self.job_pool.get_job_by_id(job_id)
        except KeyError:
            raise HTTPError(404)
        
        try:
            task = job.task_graph.get_task(task_id)
        except KeyError:
            raise HTTPError(404)
        
        if attr is None:
            
            task_string = header('Task Browser', job_id)
            task_string += '<table>'
            task_string += table_row('ID', task.task_id)
            task_string += table_row('State', TASK_STATE_NAMES[task.state])
            for worker in [task.get_worker()]:
                task_string += table_row('Worker', worker.netloc if worker is not None else None)
            #if task.state is TASK_COMMITTED:
            #    task_string += table_row('Profiling Output', pgraph_link(job,task) )
            task_string += span_row('Dependencies')
            for local_id, ref in task.dependencies.items():
                task_string += table_row(local_id, ref_link(job, ref))
            task_string += span_row('Outputs')
            for i, output_id in enumerate(task.expected_outputs):
                task_string += table_row(i, ref_id_link(job, output_id))
            task_string += span_row('History')
            for t, name in task.history:
                task_string += table_row(time.mktime(t.timetuple()) + t.microsecond / 1e6, name)
            if len(task.children) > 0:
                task_string += span_row('Children')
                for i, child in enumerate(task.children):
                    task_string += table_row(i, '%s</td><td>%s</td><td>%s' % (task_link(job, child), child.handler, TASK_STATE_NAMES[child.state]))
            task_string += '</table></body></html>'
            return task_string
        
        elif attr == "pgraph":
            
            filename = make_graph(task)
            return serve_file(filename)

class RefBrowserRoot:
    
    def __init__(self, job_pool):
        self.job_pool = job_pool

    @cherrypy.expose         
    def default(self, job_id, ref_id):
        
        try:
            job = self.job_pool.get_job_by_id(job_id)
        except KeyError:
            raise HTTPError(404)
        
        try:
            ref = job.task_graph.get_reference_info(ref_id).ref
        except KeyError:
            raise HTTPError(404)

        ref_string = header('Task Browser', job_id)
        ref_string += '<table>'
        ref_string += table_row('ID', ref_id)
        ref_string += table_row('Ref type', ref.__class__.__name__)
        if isinstance(ref, SWDataValue):
            ref_string += table_row('Value', decode_datavalue(ref))
        elif hasattr(ref, 'location_hints'):
            ref_string += span_row('Locations')
            for netloc in ref.location_hints:
                ref_string += table_row(netloc, swbs_link(netloc, ref.id))
        ref_string += '</table></body></html>'
        return ref_string
