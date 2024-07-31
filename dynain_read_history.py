
# Clean the workspace and the console for a fresh start as in Matlab "clear,clc"
try:
    from IPython import get_ipython
    get_ipython().magic('clear')
    get_ipython().magic('reset -f')
except:
    pass

import numpy as np
import sys

## USER-INPUT
# Name of the dynain results file, here input without file extensions ".inc"
input_filename = 'forming_simulation_P-uGD_tet1_PK2/9_results_P-uGD_tet1'
# Number of history variables given as "hisv" under *INITIAL_STRESS_SOLID
hisv_in = 43

## 
input_file = input_filename + '.inc'

if ( len(str(hisv_in)) != 2 ):
    print("hisv needs to be two digits, else we need to modify the number of blank spaces in the catch_phrase")
    sys.exit()

# The algorithm looks for this catch_phrase to identify the element-wise data sets
catch_phrase = '         1        '+str(hisv_in)+'         1';

counter = 0;
line_buffer = [];
write_buffer = False
buffer_active = False
buffer_process = False

print("Started reading the input file ...")

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
      # now process the data
      if ( buffer_process ):
          # read Cauchy stress from line 1 (Cauchy component 0 to 4) and line 2 (Cauchy component 5)
          Cauchy_stress_0to4 = np.fromstring(line_buffer[1], dtype=float, sep=' ')
          Cauchy_stress_5andR = np.fromstring(line_buffer[2], dtype=float, sep=' ')
          # store Cauchy stress values into a proper matrix
          Cauchy_stress_ten2 = np.zeros([3,3])
          Cauchy_stress_ten2[0,0] = Cauchy_stress_0to4[0]
          Cauchy_stress_ten2[1,1] = Cauchy_stress_0to4[1]
          Cauchy_stress_ten2[2,2] = Cauchy_stress_0to4[2]
          Cauchy_stress_ten2[0,1] = Cauchy_stress_0to4[3]
          Cauchy_stress_ten2[1,2] = Cauchy_stress_0to4[4]
          Cauchy_stress_ten2[2,0] = Cauchy_stress_5andR[0]
          Cauchy_stress_ten2[1,0] = Cauchy_stress_ten2[0,1]
          Cauchy_stress_ten2[2,1] = Cauchy_stress_ten2[1,2]
          Cauchy_stress_ten2[0,2] = Cauchy_stress_ten2[2,0]
          
          # read accumulated plastic strain (line index 2, entry index 1)
          accumulated_plastic_strain = np.fromstring(line_buffer[2], dtype=float, sep=' ')[1]
          
          # read inverse right Cauchy-Green plastic strain tensor
          ipRCG_Rand0 = np.fromstring(line_buffer[2], dtype=float, sep=' ')
          ipRCG_1to5 = np.fromstring(line_buffer[3], dtype=float, sep=' ')
          # store inverse right Cauchy-Green plastic strain tensor values into a proper matrix
          ipRCG_ten2 = np.zeros([3,3])
          ipRCG_ten2[0,0] = ipRCG_Rand0[4]
          ipRCG_ten2[1,1] = ipRCG_1to5[0]
          ipRCG_ten2[2,2] = ipRCG_1to5[1]
          ipRCG_ten2[0,1] = ipRCG_1to5[2]
          ipRCG_ten2[1,2] = ipRCG_1to5[3]
          ipRCG_ten2[2,0] = ipRCG_1to5[4]
          ipRCG_ten2[1,0] = ipRCG_ten2[0,1]
          ipRCG_ten2[2,1] = ipRCG_ten2[1,2]
          ipRCG_ten2[0,2] = ipRCG_ten2[2,0]

          # read scalar damage variable
          damage = np.fromstring(line_buffer[4], dtype=float, sep=' ')[0]

          # read deformation gradient
          defoGrad_R0to3 = np.fromstring(line_buffer[9], dtype=float, sep=' ')
          defoGrad_4to8 = np.fromstring(line_buffer[10], dtype=float, sep=' ')
          # store defoGrad values into a proper matrix
          defoGrad_ten2 = np.zeros([3,3])
          defoGrad_ten2[0,0] = defoGrad_R0to3[1]
          defoGrad_ten2[1,0] = defoGrad_R0to3[2]
          defoGrad_ten2[2,0] = defoGrad_R0to3[3]
          defoGrad_ten2[0,1] = defoGrad_R0to3[4]
          defoGrad_ten2[1,1] = defoGrad_4to8[0]
          defoGrad_ten2[2,1] = defoGrad_4to8[1]
          defoGrad_ten2[0,2] = defoGrad_4to8[2]
          defoGrad_ten2[1,2] = defoGrad_4to8[3]
          defoGrad_ten2[2,2] = defoGrad_4to8[4]
          
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

print("... finished.")
