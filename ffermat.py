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
    
def constructnomscen(g):
    fxnnames=list(g.nodes)
    nomscen={}
    for fxnname in fxnnames:
        nomscen[fxnname]='nom'
    return nomscen

def proponefault(fxnname, faultmode, mdl, time=0):
    graph=mdl.initialize()
    nomscen=constructnomscen(graph)
    scen=nomscen.copy()
    scen[fxnname]=faultmode
    
    endflows,endfaults,endclass=runonefault(mdl, graph,scen, time)
    
    return endflows,endfaults,endclass

def listinitfaults(g, times=[0]):
    faultlist=[]
    fxnnames=list(g.nodes)
    nomscen=constructnomscen(g)
        
    try:
        for time in times:
            for fxnname in fxnnames:
                fxn=g.nodes(data='obj')[fxnname]
                modes=fxn.faultmodes
                
                for mode in modes:
                    newscen=nomscen.copy()
                    newscen[fxnname]=mode
                    faultlist.append([fxnname,mode, newscen, time])
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return faultlist

#propogates 
def proplist(mdl):
    
    graph=mdl.initialize()
    times=mdl.times
    scenlist=listinitfaults(graph, times)
    fullresults={}
    
    for [fxnname, mode, scen, time] in scenlist:
        graph=mdl.initialize()
        
        endflows,endfaults,endclass=runonefault(mdl, graph,scen, time)
               
        fullresults[fxnname, mode, time]={'flow effects': endflows, 'faults':endfaults}
    return fullresults

def runonefault(mdl, graph,scen, time=0):

    #propfaults(forwardgraph)
    propagate(graph, scen, time)
    endflows=findfaultflows(graph)
    endfaults=findfaults(graph)
    endclass=mdl.findclassification(graph)
    
    return endflows,endfaults,endclass

def propagate(forward, scen, time):

    fxnnames=list(forward.nodes())
    activefxns=set(fxnnames)

    #set up history of flows to see if any has changed
    tests={}
    flowhist={}
    for fxnname in fxnnames:
        tests[fxnname]=0
        edges=list(forward.in_edges(fxnname))+list(forward.out_edges(fxnname))
        for big, end in edges:
            flows=forward.edges[big,end]
            for flow in flows:
                flowhist[big, end,flow]=forward.edges[big, end][flow].status()
                tests[fxnname]+=1
     #initialize fault           
    for fxnname in scen:
        if scen[fxnname]!='nom':
            fxnobj=forward.nodes(data='obj')[fxnname]
            fxnobj.updatefxn(faults=[scen[fxnname]], time=time)
    n=0
    while activefxns:
        
        funclist=list(activefxns).copy()
        print(funclist)
        for fxnname in funclist:
            fxn=forward.nodes(data='obj')[fxnname]
            fxn.updatefxn(time=time)
            test=0
            edges=list(forward.in_edges(fxnname))+list(forward.out_edges(fxnname))
            for big, end in edges:
                flows=forward.edges[big,end]
                print(flows)
                for flow in flows:
                    if forward.edges[big, end][flow].status()!=flowhist[big, end, flow]:
                        activefxns.add(big)
                        activefxns.add(end)
                    else:
                        test+=1
                    flowhist[big, end, flow]=forward.edges[big, end][flow].status()
                if test>=tests[fxnname]:
                    activefxns.discard(fxnname)
        n+=1
        if n>1000:
            print("Undesired looping in function")
            print(scen)
            print(fxnname)
            break
    return

#extract non-nominal flow paths
def findfaultflows(g):
    endflows=dict()
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        #flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            print(flows[flow].name)
            print(flows[flow].status())
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

def getflow(flowname, g):
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        #flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            if flows[flow].name==flowname:
                flowobj=flows[flow]
    return flowobj
            

