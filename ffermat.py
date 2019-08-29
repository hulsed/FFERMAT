# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 09:38:35 2018

@author: Daniel Hulse
"""
import pydot
import pprint
import sys
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

def plotflowhist(flowhist, fault=''):
    for flow in flowhist['faulty']:
        for var in flowhist['faulty'][flow]:
            plt.plot(flowhist['faulty'][flow][var], color='r')
            plt.plot(flowhist['nominal'][flow][var], color='b')
            plt.legend(['faulty', 'nominal'])
            plt.title('Dynamic Response of '+flow+' '+var+' to fault'+' '+fault)
            plt.show()
        

def showgraph(g, nomg=[]):
    labels=dict()
    for edge in g.edges:
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        labels[edge[0],edge[1]]=flows
    
    
    pos=nx.shell_layout(g)
    #Add ability to label modes/values
    
    nx.draw_networkx(g,pos,node_size=2000,node_shape='s', node_color='g', \
                     width=3, font_weight='bold')
    
    if nomg:
        faults=findfaults(g)   
        faultflows,faultedges=findfaultflows(g, nomg)
        nx.draw_networkx_nodes(g, pos, nodelist=faults.keys(),node_color = 'r',\
                               node_shape='s',width=3, font_weight='bold', node_size = 2000)
        nx.draw_networkx_edges(g,pos,edgelist=faultedges.keys(), edge_color='r', width=2)
    
    nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
    
    if nomg:
        nx.draw_networkx_edge_labels(g,pos,edge_labels=faultedges, font_color='r')
    plt.show()
    
def constructnomscen(g):
    fxnnames=list(g.nodes)
    nomscen={}
    for fxnname in fxnnames:
        nomscen[fxnname]='nom'
    return nomscen

def proponefault(fxnname, faultmode, mdl, time=0, track={}):
    graph=mdl.initialize()
    nomscen=constructnomscen(graph)
    scen=nomscen.copy()
    scen[fxnname]=faultmode
    
    endflows, endfaults, endclass,graph,nomgraph, flowhist =runonefault(mdl, scen, time, track)
    
    return endflows,endfaults,endclass,graph,nomgraph, flowhist

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
        
        endflows, endfaults, endclass, graph, nomgraph, flowhist=runonefault(mdl, scen, time)
               
        fullresults[fxnname, mode, time]={'flow effects': endflows, 'faults':endfaults}
    return fullresults

def classifyresults(mdl,graph,nomgraph):
    endflows=findfaultflows(graph,nomgraph)
    endfaults=findfaults(graph)
    endclass=mdl.findclassification(graph)
    return endflows, endfaults, endclass

def runonefault(mdl, scen, time=0, track={}):
    nomgraph=mdl.initialize()
    nomscen=constructnomscen(nomgraph)
    graph=mdl.initialize()
    timerange=mdl.times
    flowhist={}
    if track:
        for runtype in ['nominal','faulty']:
            flowhist[runtype]={}
            for flow in track:
                flowobj=getflow(flow, graph)
                flowhist[runtype][flow]=flowobj.status()
                for var in flowobj.status():
                    flowhist[runtype][flow][var]=[]
    
    for rtime in range(timerange[0], timerange[-1]+1):
        propagate(nomgraph, nomscen, rtime)
        if rtime==time:
            propagate(graph, scen, rtime)
        else:
            propagate(graph,nomscen,rtime)
        if track:
            for flow in track:
                flowobj=getflow(flow, graph)
                nomflowobj=getflow(flow, nomgraph)
                for var in flowobj.status():
                    flowhist['nominal'][flow][var]=flowhist['nominal'][flow][var]+[nomflowobj.status()[var]]
                    flowhist['faulty'][flow][var]=flowhist['faulty'][flow][var]+[flowobj.status()[var]]
            
    endflows, endfaults, endclass = classifyresults(mdl,graph,nomgraph)
    return endflows, endfaults, endclass, graph, nomgraph, flowhist

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
        for fxnname in funclist:
            fxn=forward.nodes(data='obj')[fxnname]
            fxn.updatefxn(time=time)
            test=0
            edges=list(forward.in_edges(fxnname))+list(forward.out_edges(fxnname))
            for big, end in edges:
                flows=forward.edges[big,end]
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
def findfaultflows(g, nomg):
    endflows=dict()
    endedges=dict()
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        nomflows=nomg.get_edge_data(edge[0],edge[1])
        #flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        flowedges=[]
        for flow in flows:
            if flows[flow].status()!=nomflows[flow].status():
                endflows[flow]=flows[flow].status()
                flowedges=flowedges+[flow]
        if flowedges:
            endedges[edge]=flowedges
            
    return endflows, endedges

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
            

