# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:29:45 2019

@author: dhulse
"""

import ffermat
#import pumpmodel
import quad_mdl2 as mdl

graph=mdl.initialize()

import plotly.graph_objects as go




#scenlist=ffermat.listinitfaults(graph, mdl.times)


#Check various scenarios individually
endflows, endfaults, endclass, endgraph, nomgraph=ffermat.proponefault('AffectDOF', 'RFpropbreak', mdl, time=1)
ffermat.showgraph(endgraph,nomgraph)

endflows, endfaults, endclass, endgraph, nomgraph=ffermat.proponefault('StoreEE', 'break', mdl, time=0)
ffermat.showgraph(endgraph,nomgraph)

ffermat.findfaults(endgraph)
ffermat.findfaultflows(endgraph, nomgraph)

#ffermat.proponefault('CtlDOF', 'noctl', mdl)
#ffermat.proponefault('ConvEEtoMElr', 'short', mdl)



fullresults=ffermat.proplist(mdl)

#ffermat.proponefault('CtlDOF', 'nom', mdl, time=0)

#ffermat.showgraph(graph.subgraph(['ConvEErf','ContEErf', 'ConvEEtoMErf', 'CtlDOF']))

#ffermat.showgraph(graph.subgraph(['ConvEElf','ContEElf', 'ConvEEtoMElf', 'CtlDOF']))