'''
Created on 12 Mar 2011

@author: ms705
'''

from ctypes import *
from skywriting.runtime.references import SWReferenceJSONEncoder
import simplejson

class MESSAGE(Structure):
    _fields_ = [("source", c_uint),
                ("dest", c_uint), 
                ("length", c_uint), 
                ("msg_body", c_char_p)]


class AbstractMessage:
    
    def toStruct(self):
        #carr = create_string_buffer(self.body)
        #carr_p = pointer(carr)
        ptr = c_char_p(self.body)
        return MESSAGE(self.source, self.dest, len(self.body), ptr)



class IdleMessage(AbstractMessage):
    
    def __init__(self, src, dest):
        self.source = src
        self.dest = dest
        self.body = simplejson.dumps({'type': 'IDLE', 'source': str(src), 'ref': None, 'body': None},  cls=SWReferenceJSONEncoder)
    
    
    
class TaskDispatchMessage(AbstractMessage):
    
    def __init__(self, src, dest, td):
        self.source = src
        self.dest = dest
        self.body = simplejson.dumps({'type': 'SPAWN', 'source': str(src), 'ref': None, 'body': td},  cls=SWReferenceJSONEncoder)
    
    

class TaskCompletedMessage(AbstractMessage):
    
    def __init__(self, src, dest, success, spawned_tasks, published_refs):
        self.source = src
        self.dest = dest
        data = (success, spawned_tasks, published_refs)
        self.body = simplejson.dumps({'type': 'DONE', 'source': str(src), 'ref': None, 'body': data}, cls=SWReferenceJSONEncoder)
    
    
    
class GetReferenceMessage(AbstractMessage):
    
    def __init__(self, src, dest, ref):
        self.source = src
        self.dest = dest
        self.body = simplejson.dumps({'type': 'GET', 'source' : src, 'ref': ref, 'body': None},  cls=SWReferenceJSONEncoder)
    
class PutReferenceMessage(AbstractMessage):
    
    def __init__(self, src, dest, ref, content):
        self.source = src
        self.dest = dest
        self.body = content
    
