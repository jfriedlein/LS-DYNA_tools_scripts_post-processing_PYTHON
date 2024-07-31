#!/usr/bin/env python3
# Plot the residual convergence history from LS-Dyna messag files
# @note Make sure that you use NLPRINT=2 (*CONTROL_IMPLICIT_SOLUTION) 
# to output the force residual that is being plotted here.

# Clean start, delete previous workspace
try:
    from IPython import get_ipython
    get_ipython().magic('clear')
    get_ipython().magic('reset -f')
except:
    pass

# Import tools for plotting and matrices
import matplotlib.pyplot as plt
import numpy

# Some specs of the messag file
# Filename where to extract the data from
filename = 'messag'
# Trigger phrase to detect new load step
trigger_phrase = 'Iteration:    1'
# Number of lines after the trigger phrase to find the line with the residual data
n_lines_after_trigger = 3
#
first_it_counter = 1
# Phrase to detect a continuation of the iterations
continue_phrase = 'Iteration:'
# Position in the line where the value of the residual is located
pos_of_residuum = 59
# number of digits used for the residual in the "filename" file
length_of_residuum_word = 9
# phrase indicating the end of file/simulation
end_phrase1 = 'N o r m a l    t e r m i n a t i o n'
end_phrase2 = 'E r r o r    t e r m i n a t i o n'

abort_counting_phrase = 'convergence failure, repeat step'
search_aborted_phrase = 'equilibrium search aborted'
search_aborted_phrase2 = '*** This implicit time step is being terminated'

# maximum for residuum (only start value, will be adapted to the found maximum)
max_y = 1 
# for a log-plot the ylimit cannot be zero (only start value, will be adapted to the found maximum)
min_y = 1 
# maximum number or NR iterations (only start value, will be adapted to the found maximum)
max_x = 3

# init the plot
plt.ion()   # open the plot and continue running
plt.grid()  # show a background grid
plt.yscale('log',basey=10) # use logarithmic scale on y-axis

min_x = first_it_counter

afresh = True

while (True):

    if ( afresh ):
        # init the plot
        plt.clf()
        plt.ion()   # open the plot and continue running
        plt.grid()  # show a background grid
        plt.yscale('log',basey=10) # use logarithmic scale on y-axis

        # Plot qconv in the background
        # This is plotted before the data, so it appears in the background
        max_x_for_background_qconv = 20
        for i in range(-2,int(max_x_for_background_qconv)):
            xConvR = [int(min_x+i)]
            # The lines start at a y-value of 0.5 (needs to be less than 1 here for the qconv plot to work properly)
            yConvR = [0.5]
            counter = 0
            for j in range(int(min_x+i),int(1.1*max_x_for_background_qconv)):
                xConvR.append(j+1)
                yConvR.append(yConvR[counter]**2)
                counter = counter+1
            plt.plot(xConvR, yConvR,'--k')


    # Read the complete file containing the convergence history
    list_of_plots_data = []
    with open(filename) as f:
        for line in f:
            inner_list = [elt.strip() for elt in line.split(';')]
            list_of_plots_data.append(inner_list)
         
    # Init values for the for-loop
    x_block = []
    y_block = []
    valid_trigger_line = False
    valid_line = False
    current_block_failed = False
    n_NR_its_total = 0
    n_load_steps = 0
    counter = 0


    # Extract data from the file
    for i_line in range(0,len(list_of_plots_data)):
        valid_line = False
        current_line = list_of_plots_data[i_line][0]
        if ( trigger_phrase in current_line ):
            if ( len(x_block) > 0 ):
                # Normalise the residual to the value in the first NR-iteration of each time step
                # [https://stackoverflow.com/questions/8244915/how-do-you-divide-each-element-in-a-list-by-an-int]
                y_block[:] = [y / y_block[0] for y in y_block]
                # Do not normalise:
                #y_block[:] = y_block[:]
                # Find the min and max for the plot range
                max_x = max( max_x, max(x_block) )
                max_y = max( max_y, max(y_block) )
                min_y = min( min_y, min(y_block) )
            lineStyle = 'solid'
            # Plotted steps that failed as dotted line
            if (current_block_failed):
                lineStyle = 'dotted'
            plt.plot(x_block,y_block,linestyle=lineStyle)
            x_block = []
            y_block = []
            valid_trigger_line = True
            current_block_failed = False
            n_load_steps = n_load_steps+1
        elif ( continue_phrase in current_line):
            valid_trigger_line = True
        elif ( (abort_counting_phrase in current_line) or (search_aborted_phrase in current_line) or (search_aborted_phrase2 in current_line) ):
            current_block_failed = True
            
        # Wait the number of lines between the trigger phrase and the value
        if ( valid_trigger_line ):
            counter = counter + 1

        if ( counter >= n_lines_after_trigger+1 ):
            valid_line = True

        # Read the residual value from this line
        if ( valid_line ):
            x_block.append(len(x_block)+1)
            y_block.append( float(current_line[pos_of_residuum:(pos_of_residuum+length_of_residuum_word)]) )
            #plt.plot(x_block,y_block,marker="x")
            n_NR_its_total = n_NR_its_total+1
            max_x = max(max_x,len(x_block))
            counter = 0
            valid_trigger_line = False
            
        # Found the end of the file, so we plot the last, yet unfinished load step
        if ( end_phrase1 in current_line or end_phrase2 in current_line or i_line==len(list_of_plots_data)-1 ):
            if ( len(x_block) > 0 ):
                # Normalise the residual to the value in the first NR-iteration of each time step
                # [https://stackoverflow.com/questions/8244915/how-do-you-divide-each-element-in-a-list-by-an-int]
                y_block[:] = [x / y_block[0] for x in y_block]
                # Do not normalise:
                #y_block[:] = y_block[:]
                # Find the min and max for the plot range
                max_x = max( max_x, max(x_block) )
                max_y = max( max_y, max(y_block) )
                min_y = min( min_y, min(y_block) )
            lineStyle = 'solid'
            # Plotted steps that failed as dotted line
            if ( i_line==len(list_of_plots_data)-1 ):
                lineStyle = 'dashed'
            plt.plot(x_block,y_block,linestyle=lineStyle)
           
            
    # Customise the plot
    plt.xticks(numpy.arange(0, max_x+1, 1.0))
    plt.xlabel('NR iterations')
    plt.ylabel('normalised force residuum')
    plt.axis([min_x, 1.1*max_x, 0.9*min_y, 1.1*max_y])

    plt.show()

    # Output some overall statistics for this file
    print("total nbr of NR its: "+str(n_NR_its_total) )
    print("total nbr of load steps: "+str(n_load_steps) )
    print("average nbr of NR its per load step: "+str(n_NR_its_total/n_load_steps) )

    # We use the following to stop the plot from closing directly
    #sec = input('Press a key to end the program\n')

    # Ask how we shall proceed:
    print()
    input_user = input("press 2 to replot the figure afresh;\npress ENTER to add the new plot to the previous plots;\npress 'n' to choose a different data set;\npress 0 to end the program on good terms: ")

    if ( input_user=='' ):  # append to the existing figure
      afresh=False
    elif ( input_user=='2'  ):  # plot the figure afresh
      afresh=True # equals initial value but must be set again in case it was set to true before
    elif ( input_user=='n' or input_user=='new' ):
      newSession=True
      print('#############################################################')
      break
    elif ( input_user=='0'  ):
      break     # to completely end this code
        
    #end of the while loop
#end of newSession while_loop
