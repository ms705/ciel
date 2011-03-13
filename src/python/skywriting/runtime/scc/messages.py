'''
Created on 12 Mar 2011

@author: ms705
'''

from ctypes import *

class MESSAGE(Structure):
    _fields_ = [("source", c_uint),
                ("dest", c_uint), 
                ("length", c_uint), 
                ("msg_body", c_char_p)]


class AbstractMessage:
    
    def toStruct(self):
        return MESSAGE(self.source, self.dest, len(self.body)+1, self.body)



class IdleMessage(AbstractMessage):
    
    def __init__(self, src, dest):
        self.source = src
        self.dest = dest
        self.body = "IDLE"
    
    
    
class TaskDispatchMessage(AbstractMessage):
    
    def __init__(self, src, dest, td):
        self.source = src
        self.dest = dest
        self.body = td  # XXX: need some magic parsing here
    

class TaskCompletedMessage(AbstractMessage):
    
    def __init__(self, src, dest, tid):
        self.source = src
        self.dest = dest
        self.body = "DONE with task: " + tid  # XXX: need some magic parsing here
    
