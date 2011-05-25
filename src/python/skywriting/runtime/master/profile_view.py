from matplotlib import rc, use
from skywriting.runtime.executor_helpers import sync_retrieve_refs
import subprocess
use('Agg')
import math
import sys
import matplotlib.pylab as plt
import time
import tempfile


def run_command(cmd):
    
    args = cmd.split()
    
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
        proc = subprocess.Popen(args, stdout=t)
        proc.wait()
    
    return t.name

def process_entry(e):
    try:
        t = time.strptime(e, "%H:%M:%S")
        ts = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
        return ts
    except ValueError:
        pass
    try:
        val = float(e)
        return val
    except ValueError:
        pass
    try:
        val = int(e)
        return val
    except ValueError:
        pass


def make_graph(task):
    
    pdict = task.get_profiling()
    
    pref = pdict["profiler_data"]
    
    ctx, = sync_retrieve_refs([pref], None)
    
    pfilename = ctx.filename
    
    cpufile_name = run_command("sar -u -f %s" % pfilename)
    tmpfile = run_command("sar -n DEV -f %s" % pfilename)
    netfile_name = run_command("grep eth0 %s" % tmpfile)
    blockfile_name = run_command("sar -b -f %s" % pfilename)
    
    
    rc('font',**{'family':'sans-serif','sans-serif':['Helvetica'],'serif':['Helvetica'], 'size':10})
    #rc('text', usetex=True)
    rc('figure', figsize=(12,8))
    rc('figure.subplot', left=0.1, top=0.9, bottom=0.1)
    rc('axes', linewidth=1)
    rc('lines', linewidth=1)
    
    xs = []
    ys = []
    durations = []
    
    
    
    with open(cpufile_name) as cpufile:
        cpuseries = [[process_entry(y.strip()) for y in x.split()] for x in cpufile.readlines()]
    
    with open(netfile_name) as netfile:
        netseries = [[process_entry(y.strip()) for y in x.split()] for x in netfile.readlines()]
    
    with open(blockfile_name) as blockfile:
        blockseries = [[process_entry(y.strip()) for y in x.split()] for x in blockfile.readlines()]
    
    
    xseriesstart = [0,0,0]
    xseries = [[],[],[]]
    yseries = [[],[],[],[]]
    
    for r in cpuseries:
        if len (r) < 1 or r[0] is None:
            continue
        else:
            if len(xseries[0]) == 0:
                xseriesstart[0] = r[0]
            xseries[0].append(r[0]-xseriesstart[0])
            if r[7] is None:
                yseries[0].append(0)
            else:
                yseries[0].append(100.0-r[7])  # CPU idle %
    
    for r in netseries:
        if len (r) < 1 or r[0] is None:
            continue
        else:
            if len(xseries[1]) == 0:
                xseriesstart[1] = r[0]
            xseries[1].append(r[0]-xseriesstart[1])
            yseries[1].append(r[4])   # recv kB/s
            yseries[3].append(r[5])   # sent kB/s
    
    for r in blockseries:
        if len (r) < 1 or r[0] is None:
            continue
        else:
            if len(xseries[2]) == 0:
                xseriesstart[2] = r[0]
            xseries[2].append(r[0]-xseriesstart[2])
            yseries[2].append(r[5])
    
    
    #fig = plt.figure()
    
    #plt.subplots_adjust(wspace=0.2)
    
    plt.figure()
    plt.ylabel('Time')
    
    
    i = 0
    for col in ['red', 'red','red']:
        ax = plt.subplot(3, 1, i+1, frame_on=True)
        if i == 1:
            plt.plot(xseries[i], yseries[1], label='recv', color='red')
            plt.plot(xseries[i], yseries[3], label='sent', color='green')
            plt.ylabel(r'kB/s', rotation='vertical')
            plt.legend(loc=0)
        else:
            plt.plot(xseries[i], yseries[i], color=col)
        if i < 2:
            plt.xticks([])
    #    plt.yticks([])
    #    plt.axvline(0, 0, 20, color='k')
    #    plt.axhline(0, 0, color='k')
        #lbl = plt.ylabel(sys.argv[i][-6:-4])
        #lbl.set_rotation(90)
        if i == 0:
            plt.ylim(0, 100)
            plt.ylabel(r'CPU load %', rotation='vertical')
    #    elif i == 1:
    #        plt.ylim(0, 125000000)
        elif i == 2:
            plt.ylabel(r'blocks/s', rotation='vertical')
            #plt.ylim(0, 128000)
        i += 1
    
    #print ax.axis()
    #plt.xticks([0, min(durations), max(durations)], ['0', str(int(math.ceil(min(durations)))), str(int(math.ceil(max(durations))))])
    plt.xlabel('Time [sec]')
    
    
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as t:
        print t
        print t.name
        filename = t.name
    
    plt.savefig(filename, format='svg')
    
    return filename
