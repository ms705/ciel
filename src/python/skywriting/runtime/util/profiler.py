'''
Created on 5 May 2011

@author: ms705
'''

import ciel
import logging
import subprocess

class SarProfiler:

    def __init__(self, blockstore):
        
        self.proc = None
        self.test = False
        
        if not self.test:
            self.test = test_profiler(["test", "-f", "/usr/lib/sysstat/sadc"], "sar")
            if not self.test:
                ciel.log("Profiler test failed, is sar installed?", "PROFILER", logging.WARNING)
            
        
    def start(self, outputfile):
        ciel.log("Profiler logging to %s" % outputfile, "PROFILER", logging.INFO)
        dn = open("/dev/null", "w")
        args = ["/usr/lib/sysstat/sadc", "-S", "DISK", "1", outputfile]
        self.proc = subprocess.Popen(args, stdout=dn)
    
    def stop(self):
        ciel.log("Profiler stopping", "PROFILER", logging.INFO)
        self.proc.terminate()
        self.proc.wait()
    
def test_profiler(args, friendly_name):
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (outstr, errstr) = proc.communicate()
        if proc.returncode == 0:
            ciel.log.error("Successfully tested %s: executed '%s'" % (friendly_name, multi_to_single_line(outstr)), "PROFILER", logging.INFO)
            return True
        else:
            ciel.log.error("Can't run %s: returned %d, stdout: '%s', stderr: '%s'" % (friendly_name, proc.returncode, outstr, errstr), "PROFILER", logging.WARNING)
            return False
    except Exception as e:
        ciel.log.error("Can't run %s: exception '%s'" % (friendly_name, e), "PROFILER", logging.WARNING)
        return False

def multi_to_single_line(s):
    lines = s.split("\n")
    lines = filter(lambda x: len(x) > 0, lines)
    s = " // ".join(lines)
    if len(s) > 100:
        s = s[:99] + "..."
    return s
