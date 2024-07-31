#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 11:00:49 2022

@author: jfriedlein

We couple the x- and y-displacements of the nodes at the top and bottom of a flat 3D-model with a single element in the z-direction.

Optionally ("constrain_zDisp") we can also constrain the z-displacements to zero, which however could also
be done easier by a *CONSTRAINED_GLOBAL keyword on the z=0 and z=1 plane or by symmetry constraints, ...

Basis: see LS-Dyna user's manual "*CONSTRAINED_MULTIPLE_GLOBAL"

@note It appears that we cannot create these constraints for nodes that are already
prescribed by a boundary condition or load. Thus we need to exclude these nodes.
Is there a nice way?

@todo
- Maybe try using some tools for keyword files like,
[https://www.dynalook.com/conferences/15th-international-ls-dyna-conference/computing-technology/qd-2013-build-your-own-ls-dyna-r-tools-quickly-in-python]
"""

## useful commands to clear the workspace and clear the console (MATLAB: clear,clc) from https://stackoverflow.com/questions/54943710/code-to-clear-console-and-variables-in-spyder
#try:
#    from IPython import get_ipython
#    get_ipython().magic('clear')
#    get_ipython().magic('reset -f')
#except:
#    pass

import os
from datetime import datetime
import operator

## Define some colours for nicer output (e.g. error in red)
# From [https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal]
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

## USER-INPUT
#meshKeyword_file = "/calculate/iwtm41_lokal/LS-Dyna/Numerical_examples_in_LS-Dyna/ShearBand_Kuna/ShearBand_Kuna_m4.k"
meshKeyword_file = "mesh_test.k"
constrain_zDisp = False
affix_for_constrained_multiple_global_keywordFile = "_CMG"
Node_keyword = "*NODE"

# Merge the filename for the constrained_multiple_global keyword file
[filename, file_extension] = os.path.splitext(meshKeyword_file)
constrainedKeyword_filename = filename+affix_for_constrained_multiple_global_keywordFile+file_extension

# Output a time stamp
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
print(bcolors.OKBLUE + "\nCurrent Time = " + current_time + "\n" + bcolors.ENDC)

# Read the node ids and the coordinates
print("Reading the nodes from"+meshKeyword_file+"...")
start_reading_node_list = False
comment_line_skipped = False

node_array = []
with open(meshKeyword_file, 'r') as meshfile: # read only 
    for line_keywordFile in meshfile:
        # We finish after reading the data once we detect a line with "*"
        if ( start_reading_node_list and comment_line_skipped and line_keywordFile.startswith("*") ):
            break
        # Third, we can start reading the first node
        if ( start_reading_node_list and comment_line_skipped ):
            row = line_keywordFile.split()
            node_id = int(row[0])
            x_coord = float(row[1])
            y_coord = float(row[2])
            z_coord = float(row[3])
            # Ensure that the node does not belong to the boundary
            # @todo This is very ugly, we need make this more general
            if ( y_coord > 1e-2 and y_coord < 15-1e-2 ):
                node_array.append([node_id,x_coord,y_coord,z_coord])
        # Second, we need to skip the comment line following the catch phrase
        if (start_reading_node_list and comment_line_skipped==False ):
            comment_line_skipped = True
        # First, we look for the catch phrase to init reading the nodes
        if ( Node_keyword in line_keywordFile ):
            start_reading_node_list = True

print("... finished reading the nodes.")                
      
      
# Sort the list of nodes to get the pairs with same (x,y) coordinates so (x,y,bottom) and (x,y, top)
# [https://stackoverflow.com/questions/5212870/sorting-a-python-list-by-two-fields]
node_array_sorted = sorted(node_array, key=operator.itemgetter(1, 2))


# Extract the node pairs (x,y,bottom) and (x,y, top) and store their IDs in "node_pairs"
print("Extracting the node pairs ...")
node_pair_first = 0
node_pair_second = 0
entry = 1

node_pairs = []
for node_set in node_array_sorted:
    if (entry==1):
        node_pair_first = node_set[0]
        entry=entry+1
    elif (entry==2):
        node_pair_second = node_set[0]
        entry=1
        node_pairs.append([node_pair_first, node_pair_second])
  
print("... finished extracting the node pairs.")
    
    
# Create the *CONSTRAINED_MULTIPLE_GLOBAL cards
print("Creating and saving the CONSTRAINED_MULTIPLE_GLOBAL keywords ...")
# set initial ID for CONSTRAINED_MULTIPLE_GLOBAL keyword to "1"
keyword_ID = 1

with open(constrainedKeyword_filename, 'w') as constrainedKeyword_file: # create or overwrite the file
    constrainedKeyword_file.write("*KEYWORD\n")
    for node_pair in node_pairs:
        constrainedKeyword_file.write("*CONSTRAINED_MULTIPLE_GLOBAL\n")
        constrainedKeyword_file.write(str(keyword_ID)+"\n")
        constrainedKeyword_file.write("2\n")
        constrainedKeyword_file.write(str(node_pair[0])+", 1, 1.0\n")
        constrainedKeyword_file.write(str(node_pair[1])+", 1, -1.0\n")
        keyword_ID=keyword_ID+1
        
        constrainedKeyword_file.write("*CONSTRAINED_MULTIPLE_GLOBAL\n")
        constrainedKeyword_file.write(str(keyword_ID)+"\n")        
        constrainedKeyword_file.write("2\n")
        constrainedKeyword_file.write(str(node_pair[0])+", 2, 1.0\n")
        constrainedKeyword_file.write(str(node_pair[1])+", 2, -1.0\n")
        keyword_ID=keyword_ID+1
        
        if ( constrain_zDisp ):
            constrainedKeyword_file.write("*CONSTRAINED_MULTIPLE_GLOBAL\n")
            constrainedKeyword_file.write(str(keyword_ID)+"\n")               
            constrainedKeyword_file.write("1\n")
            constrainedKeyword_file.write(str(node_pair[0])+", 3, 1.0\n")
            constrainedKeyword_file.write("1\n")
            constrainedKeyword_file.write(str(node_pair[1])+", 3, 1.0\n")
            keyword_ID=keyword_ID+1
            
    constrainedKeyword_file.write("*END\n")

print("... finished creating and saving the CONSTRAINED_MULTIPLE_GLOBAL keywords.")
 
print(bcolors.OKBLUE + "\nFinished execution." + bcolors.ENDC)    
    
