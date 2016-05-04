# -*- coding: utf-8 -*-
"""
Created on Tue May  3 14:01:39 2016

@author: arlittr
"""

import re
import networkx as nx
import pydotplus
#import graphviz

def plotPgvGraph(G,filename=None,printRelationships='relationship',promoteNodeLabels='rtype',prettyPrint=False,printOldNodeLabels=False):
    G2 = G.copy()
    
    #print relationships on edges
    if printRelationships:
        for n,nbrs in G2.adjacency_iter():
            for nbr in nbrs.keys():
                for edgeKey,edgeProperties in G2[n][nbr].items():
                    if prettyPrint == True:
                        edgeProperty = edgeProperties[printRelationships]
                        pattern = r'\'([A-Za-z0-9_\./\\-]*)\''
                        label = re.search(pattern,str(edgeProperty)).group()[1:-1]
                        G2[n][nbr][edgeKey]['label'] = label
                    elif prettyPrint == False:
                        G2[n][nbr][edgeKey]['label'] = edgeProperties[printRelationships]
                    
    #promote the attribute in promoteNodeLabels to node label
    if promoteNodeLabels:
        for n in G2.nodes_iter():
            try:
                if prettyPrint==False:
                    G2.node[n]['label'] = G2.node[n][promoteNodeLabels]
                elif prettyPrint==True:
                    labelList = G2.node[n][promoteNodeLabels]
                    pattern = r'\'([A-Za-z0-9_\./\\-]*)\''
                    if type(labelList) is not list:
                        labelList = [labelList]
                    labels = [re.search(pattern,str(label)).group()[1:-1] for label in labelList]
                    label = ','.join(labels)
                    if printOldNodeLabels==True:
                        label = label + '\n(' + str(G2.node[n]['oldNodeName']) + ')'
                    G2.node[n]['label'] = label
            except:
                G2.node[n]['label'] = None
    
    thisG = nx.drawing.nx_pydot.to_pydot(G2)
    filename = 'plots/'+ 'junk' + '.svg'
    thisG.write(filename,format='svg')
    