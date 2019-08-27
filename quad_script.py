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

endflows,endfaults,endclass,endgraph=ffermat.proponefault('CtlDOF', 'short', mdl)

ffermat.findfaults(endgraph)
ffermat.findfaultflows(endgraph)

#ffermat.proponefault('CtlDOF', 'noctl', mdl)
#ffermat.proponefault('ConvEEtoMElr', 'short', mdl)

ffermat.showgraph(graph)

#fullresults=ffermat.proplist(mdl)

#ffermat.proponefault('CtlDOF', 'nom', mdl, time=0)

#ffermat.showgraph(graph.subgraph(['ConvEErf','ContEErf', 'ConvEEtoMErf', 'CtlDOF']))

#ffermat.showgraph(graph.subgraph(['ConvEElf','ContEElf', 'ConvEEtoMElf', 'CtlDOF']))