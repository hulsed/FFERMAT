# -*- coding: utf-8 -*-
"""
Created on Tue May  3 14:01:39 2016

@author: arlittr
"""

import networkx as nx

def plotPgvGraph(G,filename=None,printRelationships='relationship',promoteNodeLabels='rtype',printOldNodeLabels=False):
    G2 = G.copy()
    
    #print relationships on edges
    if printRelationships:
        for n,nbrs in G2.adjacency_iter():
            for nbr in nbrs.keys():
                for edgeKey,edgeProperties in G2[n][nbr].items():
                    G2[n][nbr][edgeKey]['label'] = edgeProperties[printRelationships]
                    
    #promote the attribute in promoteNodeLabels to node label
    if promoteNodeLabels:
        for n in G2.nodes_iter():
            try:
                G2.node[n]['label'] = G2.node[n][promoteNodeLabels]
            except:
                G2.node[n]['label'] = None
    
    #draw graph
    thisG = nx.drawing.nx_pydot.to_pydot(G2)
    if filename==None:
        filename = 'plots/'+ 'junk' + '.svg'
    thisG.write(filename,format='svg')
    