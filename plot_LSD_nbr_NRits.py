#!/usr/bin/env python3

try:
    from IPython import get_ipython
    get_ipython().magic('clear')
    get_ipython().magic('reset -f')
except:
    pass

import matplotlib.pyplot as plt
from math import log,exp

# Some specs of the messag file
trigger_phrase = 'Iteration:    1'
first_it_counter = 1
continue_phrase = 'Iteration:'
finished_phrase = 'T i m i n g   i n f o r m a t i o n'
abort_counting_phrase = 'convergence failure, repeat step'
search_aborted_phrase = 'equilibrium search aborted'
pos_of_residuum = 33
length_of_residuum_word = 13
step_size_phrase = 'current step size ='
dt_pos = 25-4
dt_length = 20
compTime_catch_phrase = 'Elapsed time'
compTime = 0
n_cycles = 0

max_y = 1 # maximum for displacement norm residuum

# init
plt.clf()   # clear the plot, needed in a new session
plt.ion()   # somehow improves the handling
plt.grid()  # add grid lines to plot
plt.figure(1) # create figure 1 of 2

# Read the entire messag file line by line
list_of_plots_data = []
with open('messag') as f:
    for line in f:
        inner_list = [elt.strip() for elt in line.split(';')]
        list_of_plots_data.append(inner_list)
        
valid_line = False
step_counter = 0
sum_NR_its = 0
current_NR_counter = 0
skip_plot = False
dt_list = []

# Process each line of the messag file as aved in list list_of_plots_data
for i_line in range(0,len(list_of_plots_data)):
    current_line = list_of_plots_data[i_line][0]
    valid_line = False
    # Process the current block that either ends by finding the next block (trigger_phrase) or by the simulation ending
    if ( (trigger_phrase in current_line) or (finished_phrase in current_line) ):
        # If the block failed, we skip plotting the data as bar
        if ( skip_plot == True ):
          print('Time step ',step_counter+1,'failed')
          skip_plot = False
        # A successfully ended block is finished by plotting the data as bar
        else:
          plt.bar(step_counter,current_NR_counter,color='blue')
        
        if (trigger_phrase in current_line): # do not add for finished_phrase
          valid_line = True
        sum_NR_its = sum_NR_its + current_NR_counter
        max_y = max(current_NR_counter,max_y)
        current_NR_counter = 0
        step_counter = step_counter + 1   
    elif ( continue_phrase in current_line):
        valid_line = True
    elif ( (abort_counting_phrase in current_line) or (search_aborted_phrase in current_line)):
        skip_plot = True
        step_counter = step_counter - 1  
    elif (step_size_phrase in current_line):
        dt_current = float(current_line[dt_pos:(dt_pos+dt_length)])
        dt_list.append(dt_current)
    
    if ( valid_line ):
        current_NR_counter = current_NR_counter + 1

    if ( compTime_catch_phrase in current_line ):
        compTime = current_line[12:20]
        n_cycles = current_line[32:40]
             
plt.xlabel('time step')
plt.ylabel('nbr NR-its')

plt.axis([0, step_counter, 0, max_y])

plt.show()
step_counter=step_counter-1
print('number steps:',step_counter)
print('sum NR iterations:',sum_NR_its)
print('avg NR iterations:',sum_NR_its/step_counter)
print('computation time in sec:',float(compTime) )
print('number of cycles:',int(n_cycles) )

plt.figure(2)
plt.plot(dt_list)
plt.xlabel('time step')
plt.ylabel('time step size')

sec = input('Press a key to end the program\n')
