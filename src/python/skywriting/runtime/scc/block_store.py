'''
Created on 15 Mar 2011

@author: ms705
'''
from skywriting.runtime.exceptions import MissingInputException
from shared.references import *
from skywriting.runtime.scc.messages import GetReferenceMessage
import simplejson

import ciel
import logging, sys
import struct
from ctypes import *


from skywriting.runtime.block_store import BlockStore, json_decode_object_hook

class FakeBlockStore(BlockStore):
    
    def __init__(self, bus, hostname, port, base_dir, lib, coreid, ignore_blocks=False):
        BlockStore.__init__(self, bus, hostname, port, base_dir, ignore_blocks)
        self.lib = lib
        self.coreid = coreid
        
    
    def fetch_ref(self, ref):
        
        me = self.coreid
        coordinator = 0
        
        print "actually doing a reference fetch from coordinator for ref %s" % ref
        
        # ask for the reference
        refmsg = pointer(GetReferenceMessage(me, coordinator, ref).toStruct())
        self.lib.tr_send(refmsg)
        
        # wait to hear back
        msg = self.lib.tr_read()
        #print "received data for reference %s (length %d): %s" % (ref, dv.length, string_at(dv.msg_body, dv.length)) 
        # Load TD from JSON
        #bodyObj = simplejson.loads(string_at(dv.msg_body, dv.length), object_hook=json_decode_object_hook)
        
        #return bodyObj['body']
        data = msg.contents.msg_body
        reflen = struct.unpack("I", data[1:5])[0]
        
        datalen = struct.unpack("I", data[(reflen+5):(reflen+9)])[0]
        
        print msg.contents.length
        print reflen
        print datalen
        
        return data[(reflen+9):(reflen+9+datalen)]
    
    
    def retrieve_filenames_for_refs(self, refs):
        
        for ref in refs:
            ciel.log("Reference fetch ref %s" % ref, "FAKEBLOCKSTORE", logging.INFO)
            
            if not self.is_ref_local(ref):
                object = self.fetch_ref(ref)
                self.is_ref_local(self.ref_from_string(object, ref.id))
            
        return [self.filename_for_ref(ref) for ref in refs]
        
        



class FBSReferenceCache:
    
    def __init__(self, block_store):
        self.block_store = block_store
        self.cached_refs = {}
    
    def get(self, ref):
        pass
    