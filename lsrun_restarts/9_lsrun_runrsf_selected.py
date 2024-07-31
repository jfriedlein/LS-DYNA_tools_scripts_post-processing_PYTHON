#!/usr/bin/env python3

# @todo Check escape of ctrl+c to be able to enter "conv", "sw1", ... [https://stackoverflow.com/questions/18114560/python-catch-ctrl-c-command-prompt-really-want-to-quit-y-n-resume-executi]

# Clear workspace for a fresh start
try:
    from IPython import get_ipython
    get_ipython().magic('clear')
    get_ipython().magic('reset -f')
except:
    pass

import os
import sys
import subprocess
from glob import glob
from datetime import datetime

# Maximum number of retries for one folder
n_restarts = 7

# Number of CPUs to use in case of restarting
# @todo extract this number from the 0_run.asc file (NCPU for restart needs to be identical to NCPU of initial run)
NCPU=7

# Choose "False" to let the script directly start with an existing runrsf-file if present
force_to_start_with_fresh_run = True # True False

retry_ERROR_termination_once = False # True False

delete_rsf_lsd_at_NORMAL = True # True False

# Name of source file where to look for the termination type
# @todo Some information is only written to the terminal, but not into e.g. 'messag'.
#       Maybe store and search through terminal screen output
messag_filename = 'messag'

# Catch phrases to detect the termination type
normal_phrase = ' N o r m a l    t e r m i n a t i o n  '
error_phrase = ' E r r o r   t e r m i n a t i o n '
memoryLeak_phrase = '     Please report this message to LST'

# Collect the folder(s) with the simulation(s) to be run
folder_list = []
#folder_list.append(['','lsdyna'])

folder_list.append(['folder containing 0_run.asc to be executed','lsdyna'])

# Clear content of logfile
logFile = open('9_logfile.txt', 'w')
logFile.close()

# Colours and functions for uniformly formatted output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def output_to_logfile(string):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    logFile = open('9_logfile.txt', 'a')
    logFile.write(current_time+"<< "+string+'\n')
    logFile.close()

def print_header(string):
    print( bcolors.HEADER + string + bcolors.ENDC)
    output_to_logfile(string)

def print_warning(string):
    print( bcolors.WARNING + string + bcolors.ENDC)
    output_to_logfile(string)

def print_fail(string):
    print( bcolors.FAIL + string + bcolors.ENDC)
    output_to_logfile(string)
    
def print_ok(string):
    print( bcolors.OKGREEN + string + bcolors.ENDC)
    output_to_logfile(string)
    
def output_screen_file(proc, folder, i_restarts):
    outputFile = open(folder+os.sep+'9_run_stdOutput.txt', 'w')
    for line in proc.stdout:
        # [https://stackoverflow.com/questions/21689365/python-3-typeerror-must-be-str-not-bytes-with-sys-stdout-write]
        sys.stdout.buffer.write(line)
        outputFile.buffer.write(line)
    proc.wait()
    summary_messag = "9_lsrun_restarts<< i_restarts="+str(i_restarts)
    outputFile.write( summary_messag )
    outputFile.close()
    output_to_logfile(summary_messag)

# Loop over each folder to execute the simulations one-by-one
for folderPair in folder_list:
    folder = folderPair[0]
    exeName = folderPair[1]
    print_header("Processing folder: "+folder+" ...")
    start_time_for_this_folder = datetime.now()
    # Loop over a number of n_restarts to enable multiple tries for a normal termination
    for i_restarts in range(0,n_restarts):
        # If it is a later try, search for runrsf-file, if runrsf exists restart from "runrsf"
        result = glob(folder+os.sep+'runrsf')
        if ( ( i_restarts>=1 or force_to_start_with_fresh_run==False ) and len(result)>0 ):
            if (os.path.exists(folder+os.sep+exeName)):
                print_header("Restarting with runrsf ...")
                proc=subprocess.Popen(["./"+exeName+" r=runrsf NCPU="+str(NCPU)], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                output_screen_file(proc, folder, i_restarts)
                print_header("... finished with restarting runrsf.")
            else:
                print_fail("Missing executable "+exeName+". Proceed to next folder" )
        # If it is the first try or there is no runrsf-file in the later try, use the standard "run"
        else:
            # Start the 0_run.asc file and wait until the process finished
            print_header("Starting run-file in folder: "+folder+" ...")
            proc = subprocess.Popen(["sh","./0_run.asc"], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            #proc = subprocess.Popen([exeName," i="+"1_main.k ncpu=8 memory=20m"], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output_screen_file(proc, folder, i_restarts)
            print_header( "... finished run-file: "+folder+"." )
                
        # Find the most recent messag-file
        # @todo We should delete everything in the folder including the older messag-file on the first restart to ensure seeing the newest file, but actually sorting by the modification time will give the newest file not the highest number, so if e.g. messag02 is the newest it would ignore the older messag04
        result = glob(folder+os.sep+'*'+messag_filename+'*')
        result = sorted(result, key=os.path.getmtime)
        messag_newest_withPath = result[-1]

        # Check the messag file of the finished process to decide what to do next (either restart or continue)
        if (os.path.exists(folder+os.sep+messag_filename)):
           # Extract last line of file
            # [https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python]
            with open(messag_newest_withPath, 'rb') as f:
                try:  # catch OSError in case of a one line file 
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                except OSError:
                    f.seek(0)
                last_line = f.readline().decode()
            
           # Decide what to do based on last_line from messag-file
            if ( normal_phrase in last_line ):
                print_ok("NORMAL termination -> Proceeding to next folder")
                if ( delete_rsf_lsd_at_NORMAL ):
                    print_ok(" ... deleting runrsf and lsdyna.")
                    os.remove(folder+os.sep+"runrsf")
                    os.remove(folder+os.sep+"lsdyna")
                    for d3dump_file in glob(folder+os.sep+'*'+"d3dump"+'*'):
                        os.remove(d3dump_file)
                break
            elif ( error_phrase in last_line ):
                if ( retry_ERROR_termination_once == True ):
                    if ( i_restarts>=1 ):
                        print_fail("ERROR termination -> restarted once and failed -> Proceeding to next folder")
                        break
                    else:
                        print_header("ERROR termination -> restart once")
                else:
                    print_fail("ERROR termination -> Proceeding to next folder")
                    break
            elif ( memoryLeak_phrase in last_line ):
                print_header("MEMORY LEAK ETC -> restart for "+str(i_restarts+1)+". time")
            else:
                print_fail("Unknown last line found in messag file. Proceeding to next folder")
                break
        else:
            print_fail("Failed to find messag file. Proceeding to next folder")
            break
    
    print_header("... finished processing folder: "+folder+" after time="+str(datetime.now()-start_time_for_this_folder) )

print_header("... finished entire run.")
