'''
Created on 12 Mar 2011

@author: ms705
'''

from ctypes import *
from struct import *

from skywriting.runtime.references import SWReferenceJSONEncoder
import simplejson

class MESSAGE(Structure):
    _fields_ = [("source", c_uint),
                ("dest", c_uint), 
                ("length", c_uint), 
                ("msg_body", POINTER(c_char))]


class AbstractMessage:
    
    IDLE_MESSAGE = 0
    SPAWN_MESSAGE = 1
    DONE_MESSAGE = 2
    GET_MESSAGE = 3
    PUT_MESSAGE = 4
    
    def toStruct(self):
        #carr = create_string_buffer(self.body)
        #carr_p = pointer(carr)
        ptr = cast(self.body, POINTER(c_char))
        return MESSAGE(self.source, self.dest, sizeof(self.body), ptr)
    
    
    @staticmethod
    def type_to_string(msgtype):
        
        if msgtype == AbstractMessage.IDLE_MESSAGE:
            return 'IDLE_MESSAGE'
        elif msgtype == AbstractMessage.SPAWN_MESSAGE:
            return 'SPAWN_MESSAGE'
        elif msgtype == AbstractMessage.DONE_MESSAGE:
            return 'DONE_MESSAGE'
        elif msgtype == AbstractMessage.GET_MESSAGE:
            return 'GET_MESSAGE'
        elif msgtype == AbstractMessage.PUT_MESSAGE:
            return 'PUT_MESSAGE'
        



class IdleMessage(AbstractMessage):
    
    def __init__(self, src, dest):
        self.source = src
        self.dest = dest
        #self.body = simplejson.dumps({'type': 'IDLE', 'source': str(src), 'ref': None, 'body': None},  cls=SWReferenceJSONEncoder)
        self.body = create_string_buffer(str(self.IDLE_MESSAGE))
    
    def str(self):
        return 'IDLE_MESSAGE <from: ' + self.source + ', to: ' + self.dest + '>' 
    
    
class TaskDispatchMessage(AbstractMessage):
    
    def __init__(self, src, dest, td):
        self.source = src
        self.dest = dest
        #self.body = simplejson.dumps({'type': 'SPAWN', 'source': str(src), 'ref': None, 'body': td},  cls=SWReferenceJSONEncoder)
        self.body = create_string_buffer(str(self.SPAWN_MESSAGE) + simplejson.dumps(td,  cls=SWReferenceJSONEncoder))
    
    def str(self):
        return 'SPAWN_MESSAGE <from: ' + self.source + ', to: ' + self.dest + ', body_len: ' + len(self.body) + '>' 
    
    
class TaskCompletedMessage(AbstractMessage):
    
    def __init__(self, src, dest, success, spawned_tasks, published_refs):
        self.source = src
        self.dest = dest
        data = simplejson.dumps((success, spawned_tasks, published_refs), cls=SWReferenceJSONEncoder)
        #self.body = simplejson.dumps({'type': 'DONE', 'source': str(src), 'ref': None, 'body': data}, cls=SWReferenceJSONEncoder)
        
        self.body = create_string_buffer(1 + 4 + len(str(data)))
        self.body[0] = str(self.DONE_MESSAGE)
        self.body[1:5] = pack("I", len(data))
        self.body[5:] = data
    
    def str(self):
        return 'DONE_MESSAGE <from: ' + self.source + ', to: ' + self.dest + ', body_len: ' + len(self.body) + '>' 
    
    
class GetReferenceMessage(AbstractMessage):
    
    def __init__(self, src, dest, ref):
        self.source = src
        self.dest = dest
        #self.body = simplejson.dumps({'type': 'GET', 'source' : src, 'ref': ref, 'body': None},  cls=SWReferenceJSONEncoder)
        data = simplejson.dumps(ref,  cls=SWReferenceJSONEncoder)
        self.body = create_string_buffer(1 + 4 + len(data))
        self.body[0] = str(self.GET_MESSAGE)
        self.body[1:5] = pack("I", len(data)) 
        self.body[5:] = data
    
    def str(self):
        return 'GET_MESSAGE <from: ' + self.source + ', to: ' + self.dest + ', body_len: ' + len(self.body) + '>' 
    
    
class PutReferenceMessage(AbstractMessage):
    
    def __init__(self, src, dest, ref, content):
        self.source = src
        self.dest = dest
        refid = ref.id
        reflen = len(refid)
        clen = len(str(content))
        
        self.body = create_string_buffer(1 + 4 + reflen + 4 + clen)
        self.body[0] = str(self.PUT_MESSAGE)
        self.body[1:5] = pack("I", reflen)
        boundary1 = 5+reflen
        self.body[5:boundary1] = refid
        boundary2 = boundary1+4
        self.body[boundary1:boundary2] = pack("I", clen)
        print len(str(content))
        print len(self.body[boundary2:]) 
        self.body[boundary2:] = str(content)
    
    def str(self):
        return 'PUT_MESSAGE <from: ' + self.source + ', to: ' + self.dest + ', body_len: ' + len(self.body) + '>' 
    
