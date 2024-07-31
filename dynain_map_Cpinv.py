
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

input_filename = '9_prestrained_060'
hisv_in = 47
hisv_out = hisv_in

input_file = input_filename + '.inc'
output_file = input_filename+'_M1_alphaPS.inc'

if len(str(hisv_in)) != 2 or len(str(hisv_out)) != 2:
    print("hisv needs to be two digits, else we need to modify the number of blank spaces in the catch_phrase")
    sys.exit()
    
# Solid
catch_phrase = '         1        '+str(hisv_in)+'         1';
width=5
length=16

# Shell
#catch_phrase = '         1         1        '+str(hisv_in);
#width=8
#length=10

counter = 0;
line_buffer = [];
write_buffer = False
buffer_active = False
buffer_process = False

print("Processing the input file and creating the output file ...")

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
          # read deformation gradient
          defoGrad_list = np.genfromtxt(line_buffer[10:], delimiter=[length]*width)
          # store defoGrad values into a proper matrix
          defoGrad_ten2 = np.zeros([3,3])
          defoGrad_ten2[0,0] = defoGrad_list[0,0]
          defoGrad_ten2[1,0] = defoGrad_list[0,1]
          defoGrad_ten2[2,0] = defoGrad_list[0,2]
          defoGrad_ten2[0,1] = defoGrad_list[0,3]
          defoGrad_ten2[1,1] = defoGrad_list[0,4]
          defoGrad_ten2[2,1] = defoGrad_list[1,0]
          defoGrad_ten2[0,2] = defoGrad_list[1,1]
          defoGrad_ten2[1,2] = defoGrad_list[1,2]
          defoGrad_ten2[2,2] = defoGrad_list[1,3]
          
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
          
          be = np.matmul(np.matmul(defoGrad_ten2,Cpinv_ten2), defoGrad_ten2.T)
          
          Cp_star_inv = be
          Cp_star_inv_delta = Cp_star_inv - np.eye(3)
          
          
          # Determine the output format
          length_of_each_word = (len(line_buffer[1])-1)/width
          if length_of_each_word.is_integer():
              length_of_each_word = int(length_of_each_word)    
          else:
              print("problem with extracting the length of each output word")
              sys.exit()
          line_format = str(length_of_each_word)+'.3e'
          
          # write PK2 stress into the location of the Cauchy stress
          # remove hardening
          #line_A = line_buffer[2][0:16] + f'{0:{line_format}}' + line_buffer[2][32:48] + f'{0:{line_format}}' +  f'{Cp_star_inv_delta[0,0]:{line_format}}\n'

          # reduced hardening
          #alpha = float(line_buffer[2][16:32])
          #alpha_scaled = 0.5 * alpha
          #line_A = line_buffer[2][0:16] + f'{alpha_scaled:{line_format}}' + line_buffer[2][32:48] + f'{alpha_scaled:{line_format}}' +  f'{Cp_star_inv_delta[0,0]:{line_format}}\n'

          # full hardening
          line_A = line_buffer[2][0:64] + f'{Cp_star_inv_delta[0,0]:{line_format}}\n'
          line_B = f'{Cp_star_inv_delta[1,1]:{line_format}}{Cp_star_inv_delta[2,2]:{line_format}}{Cp_star_inv_delta[0,1]:{line_format}}{Cp_star_inv_delta[1,2]:{line_format}}{Cp_star_inv_delta[2,0]:{line_format}}\n'
          alpha_PS = float(line_buffer[2][16:32])
          line_C = f'{alpha_PS:{line_format}}' + line_buffer[4][16:]

          line_buffer[2] = line_A
          line_buffer[3] = line_B
          line_buffer[4] = line_C
          
          # We change the number "hisv" to hisv_out to be consistent with the modified length format
          #line_buffer[0] = line_buffer[0][0:28]+str(hisv_out)+line_buffer[0][30:]
          
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

print("... finished.")
