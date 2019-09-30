# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 14:19:26 2019

@author: Daniel Hulse
"""

#Using the model that was set up, we can now perform a few different operations

#First, import the fault propogation library as well as the model
import ffermat
import ex_pump as mdl


#Before seeing how faults propogate, it's useful to see how the model performs
#in the nominal state to check to see that the model has been defined correctly.
# Some things worth checking:
#   -are all functions on the graph?
#   -are the functions connected with the correct flows?
#   -do any faults occur in the nominal state?
#   -do all the flow states proceed as desired over time?

endresults, resgraph, flowhist, ghist=ffermat.runnominal(mdl, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'})
ffermat.showgraph(resgraph)
ffermat.plotflowhist(flowhist, 'Nominal')

#We might further query the faults to see what happens to the various states
endresults, resgraph, flowhist, ghist=ffermat.proponefault('Move Water', 'short', mdl, time=10, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'})
ffermat.showgraph(resgraph)
ffermat.plotflowhist(flowhist, 'short', time=10)
#in addition to these visualizations, we can also look at the final results 
#to see which specific faults were caused, as well as the flow states
print(endresults)

#we can also look at other faults
endresults, resgraph, flowhist, ghist=ffermat.proponefault('Export Water', 'block', mdl, time=10, track={'Wat_1','Wat_2', 'EE_1', 'Sig_1'})
ffermat.showgraph(resgraph)
ffermat.plotflowhist(flowhist, 'blockage', time=10)
print(endresults)

#finally, to get the results of all of the scenarios, we can go through the list
#note that this will propogate faults based on the times vector put in the model,
# e.g. times=[0,3,15,55] will propogate the faults at the begining, end, and at
# t=15 and t=15
fullresults=ffermat.proplist(mdl)
print(fullresults)