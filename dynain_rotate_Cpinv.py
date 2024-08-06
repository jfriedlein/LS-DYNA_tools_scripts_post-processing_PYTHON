
# Clean the workspace and the console for a fresh start as in Matlab "clear,clc"
try:
    from IPython import get_ipython
    get_ipython().magic('clear')
    get_ipython().magic('reset -f')
except:
    pass

import numpy as np
from scipy.linalg import sqrtm
import sys
from io import StringIO
from math import atan, degrees, sin, cos
import time

input_filename = '9_results_CV2D_K5_mP-uD_M1_cut_3D'
hisv_in = 47
hisv_out = hisv_in

input_file = input_filename + '.inc'
output_file = input_filename+'_rot.inc'

if len(str(hisv_in)) != 2 or len(str(hisv_out)) != 2:
    print("hisv needs to be two digits, else we need to modify the number of blank spaces in the catch_phrase")
    sys.exit()
    
# Solid
catch_phrase = '         1        '+str(hisv_in)+'         1';

counter = 0;
line_buffer = [];
write_buffer = False
buffer_active = False
buffer_process = False

print("Processing the input file and creating the output file ...")

print("Reading elements and nodes ...")
t = time.time()
element_node_list = []
node_coord_list = []
start_reading_elements = False
start_reading_nodes = False

# Read the list of elements with all their nodes
with open(input_file, 'r') as input_f: # read only
    # Loop over each line of the input file
    for line_content in input_f:
        if ( "*ELEMENT_SOLID" in line_content ):
            start_reading_elements = True
            continue
        
        if ( start_reading_elements and line_content[0]=="*" ): # Found next keyword
            start_reading_elements = False
            
        if ( start_reading_elements ):
            [element_ID, PID, N1,N2,N3,N4,N5,N6,N7,N8] = np.genfromtxt(StringIO(line_content), delimiter=[8]*10, dtype=int)
            element_node_list.append([element_ID, N1,N2,N3,N4,N5,N6,N7,N8])
            
            
        if ( "*NODE" in line_content ):
            start_reading_nodes = True
            continue
        
        if ( start_reading_nodes and line_content[0]=="*" ): # Found next keyword
            start_reading_nodes = False
            break # end reading
        
        if ( start_reading_nodes ):     
            [node_ID, X, Y, Z] = np.genfromtxt(StringIO(line_content), delimiter=[8, 16, 16, 16], dtype=float)
            node_coord_list.append([int(node_ID), X, Y, Z])             

print(".. finished reading elements and nodes: ",time.time()-t)

print("Determining element centres ...")
t=time.time()
element_centre = []

node_coord_np = np.array(node_coord_list)
node_id_np = np.array(node_coord_np[:,0], dtype=int)

# Compute element centre coordinates for each element
for i in range(len(element_node_list)):
    [element_ID, N1,N2,N3,N4,N5,N6,N7,N8] = element_node_list[i]
    x0 = 0
    z0 = 0
    Nlist = [N1,N2,N3,N4,N5,N6,N7,N8]
    # Loop over each node to find the x- and z-coordinates
    # @todo Optimise
    for N in Nlist:
        index_N = np.where(node_id_np==N)[0][0]
        x0 = x0 + node_coord_list[index_N][1]/8.
        z0 = z0 + node_coord_list[index_N][3]/8.
    # State: Computed x0 and z0 for current element i
    # Compute angle around y-axis (counterclockwise is positive)
    angle_degree = degrees(atan(-z0/x0))
    if ( angle_degree < 0 ):
        # This ensures that we get a positive angle, even when we switch from positive to negative x-values (whilst z is always negative)
        angle_degree = angle_degree + 180
    element_centre.append([element_ID,angle_degree])

print("... finished determining element centres: ",time.time()-t)


print("Processing history ...")
element_centre_np = np.array(element_centre)
element_id_np = np.array(element_centre_np[:,0], dtype=int)

t=time.time()

with open(output_file, 'w') as output_f: # create new file or overwrite old
  with open(input_file, 'r') as input_f: # read only
    # Loop over each line of the input file
    for line_content in input_f:
      # Currently reading the buffer
      if ( buffer_active==True ):
          # looking for the end of the buffer,
          # '*' either indicates the next keyword or the end of the file via '*END'
          if ( (catch_phrase in line_content) or ('*' in line_content) ):
              buffer_active = False
              buffer_process = True
          # not found the end yet, so continue reading into the buffer
          else:
              line_buffer.append( line_content ) 
          
      # Finished reading the buffer,
      # now process the data and output the block
      if ( buffer_process ):       
          # read element_id
          line0 = np.fromstring(line_buffer[0], dtype=float, sep=' ')
          EID = int(line0[0])
          
          # read angle_rad for current element 
          index_e = np.where(element_id_np==EID)[0][0]
          angle_degree = element_centre_np[index_e,1]
          angle_rad = np.radians(angle_degree)
          
          # Counterclockwise rotation around y-axis (signs such that stress tensor is rotated counterclockwise around y-axis)
          rotation_matrix = np.array([[cos(angle_rad),0,sin(angle_rad)],[0,1,0],[-sin(angle_rad),0,cos(angle_rad)]])
          
          # read Cpinv
          Cpinv_R0to3 = np.fromstring(line_buffer[2], dtype=float, sep=' ')
          Cpinv_4to8 = np.fromstring(line_buffer[3], dtype=float, sep=' ')
          Cpinv_ten2 = np.zeros([3,3])
          Cpinv_ten2[0,0] = 1+Cpinv_R0to3[4]
          Cpinv_ten2[1,1] = 1+Cpinv_4to8[0]
          Cpinv_ten2[2,2] = 1+Cpinv_4to8[1]
          Cpinv_ten2[0,1] = Cpinv_4to8[2]
          Cpinv_ten2[1,2] = Cpinv_4to8[3]
          Cpinv_ten2[2,0] = Cpinv_4to8[4]
          Cpinv_ten2[1,0] = Cpinv_ten2[0,1]
          Cpinv_ten2[2,1] = Cpinv_ten2[1,2]
          Cpinv_ten2[0,2] = Cpinv_ten2[2,0]
          
          Cp = np.linalg.inv(Cpinv_ten2)
          
          Cp_rot = np.matmul(np.matmul(rotation_matrix,Cp), rotation_matrix.T)

          Cp_rot_inv = np.linalg.inv(Cp_rot)
          Cp_rot_inv_delta = Cp_rot_inv - np.eye(3)
          
          # Determine the output format
          length_of_each_word = (len(line_buffer[1])-1)/5
          if length_of_each_word.is_integer():
              length_of_each_word = int(length_of_each_word)    
          else:
              print("problem with extracting the length of each output word")
              sys.exit()
          line_format = str(length_of_each_word)+'.6e'
          
          # write PK2 stress into the location of the Cauchy stress
          line_A = line_buffer[2][0:64] + f'{Cp_rot_inv_delta[0,0]:{line_format}}\n'
          line_B = f'{Cp_rot_inv_delta[1,1]:{line_format}}{Cp_rot_inv_delta[2,2]:{line_format}}{Cp_rot_inv_delta[0,1]:{line_format}}{Cp_rot_inv_delta[1,2]:{line_format}}{Cp_rot_inv_delta[2,0]:{line_format}}\n'

          line_buffer[2] = line_A
          line_buffer[3] = line_B
          
          # We change the number "hisv" to hisv_out to be consistent with the modified length format
          line_buffer[0] = line_buffer[0][0:28]+str(hisv_out)+line_buffer[0][30:]
          
          # write the relevant part of modified buffer into output file
          # relevant are first 5 lines (excluding the "es" and "defoGrad"), 
          for out_line in line_buffer:
              output_f.write( out_line )
          # Processed the buffer
          buffer_process = False
          
      # If you find the catch_phrase, start reading the new block
      # @note This uses an overlap, above we detect the catch_phrase in the same 
      # line to find the end of the block and here we still process the same line, 
      # but now using its content
      if ( buffer_active==False ):
          if (catch_phrase in line_content):
              # Empty the line_buffer to start a new block
              line_buffer = []
              line_buffer.append( line_content )
              buffer_active = True
          else:
              # just output the input lines unchanged into the output file
              # This is the standard case for all line contents that do not belong to the history
              # @todo Restructure this, so this default case is more obvious
              output_f.write( line_content )

print("... finished processing history: ",time.time()-t)

print("... finished.")
