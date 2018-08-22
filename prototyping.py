#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 18:16:39 2018

@author: daniel
"""

import networkx as nx
import matplotlib.pyplot as plt

g=nx.DiGraph()
g.add_node('inputfxn', funcdef='fxn1')
g.add_node('mainfxn', funcdef='fxn2')
g.add_node('outputfxn', funcdef='fxn3')

g.add_edge('inputfxn', 'mainfxn', flow='inflow')
g.add_edge('mainfxn','outputfxn', flow='outflow')

labels=dict()
for (u,v,label) in g.edges.data('flow'):
    labels[(u,v)]=label

edges=g.edges()


pos=nx.spring_layout(g)
nx.draw_networkx(g,pos)
nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
plt.show()

a=1
inflow=inputfxn(a)
b=2
outflow=mainfxn(b,inflow)
c=3
outstate=outputfxn(c,outflow)
#maybe nodes have state values which determines in/out to next?
def inputfxn(a):
    inflow=a
    return inflow

def mainfxn(b,inflow):
    outflow=b*inflow
    return outflow

def outputfxn(c,outflow):
    outstate=c*outflow
    return outstate


    