# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 09:38:35 2018

@author: Daniel Hulse
"""
import pprint
import sys
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

def showgraph(g):
    labels=dict()
    for edge in g.edges:
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        labels[edge[0],edge[1]]=flows
    
    pos=nx.spring_layout(g)
    nx.draw_networkx(g,pos)
    nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
    plt.show()

def listinitfaults(g):
    faultlist=[]
    nomscen={}
    fxnnames=list(g.nodes)
    for fxnname in fxnnames:
        nomscen[fxnname]='nom'
        
    try:
        for fxnname in fxnnames:
            fxn=g.nodes(data='obj')[fxnname]
            modes=fxn.faultmodes
            
            for mode in modes:
                newscen=nomscen.copy()
                newscen[fxnname]=mode
                faultlist.append([fxnname,mode, newscen])
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return faultlist

#propogates 
def proplist(mdl):
    
    graph=mdl.initialize()
    scenlist=listinitfaults(graph)
    fullresults={}
    
    for [fxnname, mode, scen] in scenlist:
        graph=mdl.initialize()
        
        endflows,endfaults,endclass=runonefault(mdl, graph,scen)
               
        fullresults[fxnname, mode]={'flow effects': endflows, 'faults':endfaults}
    return fullresults

def runonefault(mdl, graph,scen):

    #propfaults(forwardgraph)
    propagate(graph, scen)
    endflows=findfaultflows(graph)
    endfaults=findfaults(graph)
    endclass=mdl.findclassification(graph)
    
    return endflows,endfaults,endclass

def propagate(forward, scen):

    fxnnames=list(forward.nodes())
    activefxns=set(fxnnames)
    
    #set up history of flows to see if any has changed
    tests={}
    flowhist={}
    for fxnname in fxnnames:
        tests[fxnname]=0.0
        for big, end in forward.edges(fxnname):
            flows=forward.edges[big,end]
            for flow in flows:
                flowhist[big, end,flow]=forward.edges[big, end][flow].status()
                tests[fxnname]+=1
     #initialize fault           
    for fxnname in scen:
        if scen[fxnname]!='nom':
            fxnobj=forward.nodes(data='obj')[fxnname]
            fxnobj.updatefxn(faults=[scen[fxnname]])
    
    while activefxns:
        n=0
        for fxnname in list(activefxns):
            fxn=forward.nodes(data='obj')[fxnname]
                       
            fxn.updatefxn()
            test=0
            for big, end in forward.edges(fxnname):
                flows=forward.edges[big,end]
                for flow in flows:
                    if forward.edges[big, end][flow].status()!=flowhist[big, end, flow]:
                        activefxns.add(big)
                        activefxns.add(end)
                    else:
                        activefxns.discard(end)
                        test+=1
                    flowhist[big, end, flow]=forward.edges[big, end][flow].status()
                if test>=tests[fxnname]:
                    activefxns.discard(fxnname)
            n+=1
            if n>1000:
                print("Undesired looping in function")
                print(scen)
                break
    return

#extract non-nominal flow paths
def findfaultflows(g):
    endflows=dict()
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        #flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            if flows[flow].status()!=flows[flow].nominal:
                endflows[flow]=flows[flow].status()
    return endflows

#generates lists of faults present
def findfaults(g):
    endfaults=dict()
    fxnnames=list(g.nodes)
    #extract list of faults present
    for fxnname in fxnnames:
        fxn=g.nodes(data='obj')[fxnname]
        if fxn.faults.issuperset({'nom'}):
            fxn.faults.remove('nom')
        if len(fxn.faults) > 0:
            endfaults[fxnname]=fxn.faults
    return endfaults

def getfxn(fxnname, graph):
    fxn=graph.nodes(data='obj')[fxnname]
    return fxn

