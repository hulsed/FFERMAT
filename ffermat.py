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

def plotflowhist(flowhist, fault='', time=0):
    for flow in flowhist['faulty']:
        fig = plt.figure()
        plots=len(flowhist['faulty'][flow])
        fig.add_subplot(np.ceil((plots+1)/2),2,plots)
        plt.tight_layout(pad=2.5, w_pad=2.5, h_pad=2.5, rect=[0, 0.03, 1, 0.95])
        n=1
        for var in flowhist['faulty'][flow]:
            plt.subplot(np.ceil((plots+1)/2),2,n)
            n+=1
            a, =plt.plot(flowhist['faulty'][flow][var], color='r')
            b, =plt.plot(flowhist['nominal'][flow][var], color='b')
            c =plt.axvline(x=time, color='k')
            plt.title(var)
        plt.subplot(np.ceil((plots+1)/2),2,n)
        plt.legend([a,b],['faulty', 'nominal'])
        fig.suptitle('Dynamic Response of '+flow+' to fault'+' '+fault)
        plt.show()

def plotghist(ghist,faultscen=[]):
    for time in ghist:
        graph=ghist[time]
        showgraph(graph, faultscen, time)

def showgraph(g, faultscen=[], time=[]):
    labels=dict()
    for edge in g.edges:
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        labels[edge[0],edge[1]]=flows
    
    pos=nx.shell_layout(g)
    #Add ability to label modes/values
    
    nx.draw_networkx(g,pos,node_size=2000,node_shape='s', node_color='g', \
                     width=3, font_weight='bold')
    
    faults=findfaults(g)   
    faultflows,faultedges=findfaultflows(g)
    nx.draw_networkx_nodes(g, pos, nodelist=faults.keys(),node_color = 'r',\
                          node_shape='s',width=3, font_weight='bold', node_size = 2000)
    nx.draw_networkx_edges(g,pos,edgelist=faultedges.keys(), edge_color='r', width=2)
    
    nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
    
    nx.draw_networkx_edge_labels(g,pos,edge_labels=faultedges, font_color='r')
    
    if faultscen:
        plt.title('Propagation of faults to '+faultscen+' at t='+str(time))
    
    plt.show()
    
def constructnomscen(g):
    fxnnames=list(g.nodes)
    nomscen={}
    for fxnname in fxnnames:
        nomscen[fxnname]='nom'
    return nomscen

def proponefault(fxnname, faultmode, mdl, time=0, track={}, gtrack={}):
    graph=mdl.initialize()
    nomscen=constructnomscen(graph)
    scen=nomscen.copy()
    scen[fxnname]=faultmode
    
    endresults, resgraph, flowhist, graphhist =runonefault(mdl, scen, time, track, gtrack)
    
    return endresults,resgraph, flowhist, graphhist

def listinitfaults(g, times=[0]):
    faultlist=[]
    fxnnames=list(g.nodes)
    nomscen=constructnomscen(g)
        
    try:
        for time in times:
            for fxnname in fxnnames:
                fxn=getfxn(fxnname,g)
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
        
        endresults, resgraph, flowhist=runonefault(mdl, scen, time)
               
        fullresults[fxnname, mode, time]=endresults
    return fullresults

def classifyresults(mdl,resgraph):
    endflows,endedges=findfaultflows(resgraph)
    endfaults=findfaults(resgraph)
    endclass=mdl.findclassification(resgraph, endfaults, endflows)
    return endflows, endfaults, endclass

def runonefault(mdl, scen, time=0, track={}, gtrack={}):
    nomgraph=mdl.initialize()
    nomscen=constructnomscen(nomgraph)
    graph=mdl.initialize()
    timerange=mdl.times
    flowhist={}
    graphhist={}
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
        if rtime in gtrack:
            rgraph=makeresultsgraph(graph,nomgraph)
            graphhist[rtime]=rgraph
            
    resgraph=makeresultsgraph(graph, nomgraph)        
    endflows, endfaults, endclass = classifyresults(mdl,resgraph)
    endresults={'flows': endflows, 'faults': endfaults, 'classification':endclass}
    return endresults, resgraph, flowhist, graphhist

def propagate(g, scen, time):
    fxnnames=list(g.nodes())
    activefxns=set(fxnnames)
    #set up history of flows to see if any has changed
    tests={}
    flowhist={}
    for fxnname in fxnnames:
        tests[fxnname]=0
        edges=list(g.in_edges(fxnname))+list(g.out_edges(fxnname))
        for big, end in edges:
            flows=g.edges[big,end]
            for flow in flows:
                flowhist[big, end,flow]=g.edges[big, end][flow].status()
                tests[fxnname]+=1
     #initialize fault           
    for fxnname in scen:
        if scen[fxnname]!='nom':
            fxn=getfxn(fxnname, g)
            fxn.updatefxn(faults=[scen[fxnname]], time=time)
    n=0
    while activefxns:
        funclist=list(activefxns).copy()
        for fxnname in funclist:
            fxn=getfxn(fxnname, g)
            fxn.updatefxn(time=time)
            test=0
            edges=list(g.in_edges(fxnname))+list(g.out_edges(fxnname))
            for big, end in edges:
                flows=g.edges[big,end]
                for flow in flows:
                    if g.edges[big, end][flow].status()!=flowhist[big, end, flow]:
                        activefxns.add(big)
                        activefxns.add(end)
                    else:
                        test+=1
                    flowhist[big, end, flow]=g.edges[big, end][flow].status()
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
def findfaultflows(g, nomg=[]):
    endflows=dict()
    endedges=dict()
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        flowedges=[]
        #if comparing a nominal with a non-nominal
        if nomg:
            nomflows=nomg.get_edge_data(edge[0],edge[1])
            for flow in flows:
                if flows[flow].status()!=nomflows[flow].status():
                    endflows[flow]=flows[flow].status()
                    flowedges=flowedges+[flow]
        #if results are already in the graph structure
        else:
            for flow in flows:
                if flows[flow]['status']=='Degraded':
                    endflows[flow]=flows[flow]['values']
                    flowedges=flowedges+[flow]
        if flowedges:
                endedges[edge]=flowedges    
    return endflows, endedges
#generates full list of faults, with properties
def listfaultsprops(endfaults,g, prop='all'):
    faultlist=dict()
    for fxnname in endfaults:
        for faultname in endfaults[fxnname]:
            if prop==all:
                faultlist[fxnname+' '+faultname]=getfaultprops(fxnname,faultname,g)
            else:
                faultlist[fxnname+' '+faultname]=getfaultprops(fxnname,faultname,g, prop)
    return faultlist

#generates lists of faults present
def findfaults(g):
    endfaults=dict()
    fxnnames=list(g.nodes)
    #extract list of faults present
    for fxnname in fxnnames:
        faults=findfault(fxnname, g)
        if len(faults) > 0:
            endfaults[fxnname]=faults
    return endfaults
#find a fault in a given function
def findfault(fxnname, g):
    if 'faults' in g.nodes[fxnname]:
        faults=g.nodes[fxnname]['faults']
    else:
        fxn=getfxn(fxnname, g)
        faults=fxn.faults.copy()
        if faults.issuperset({'nom'}):
            faults.remove('nom')
        if faults.issuperset({'nominal'}):
            faults.remove('nominal')
    return faults

def getfxn(fxnname, graph):
    fxn=graph.nodes(data='obj')[fxnname]
    return fxn

def getflow(flowname, g):
    for edge in g.edges:
        flows=g.get_edge_data(edge[0],edge[1])
        #flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            if flow==flowname:
                if type(flows[flow]) is dict:
                    flowobj=flows[flow]['obj']
                else:
                    flowobj=flows[flow]
    return flowobj
#gets defined properties of a fault
def getfaultprops(fxnname, faultname, g, prop='all'):
    fxn=getfxn(fxnname, g)
    if prop=='all':
        faultprops=fxn.faultmodes[faultname]
    else:
        faultprops=fxn.faultmodes[faultname][prop]
    return faultprops

def makeresultsgraph(g, nomg):
    rg=g.copy() 
    for edge in g.edges:
        for flow in list(g.edges[edge].keys()):
            flowobj=g.edges[edge][flow]
            nomflowobj=nomg.edges[edge][flow]
            
            if flowobj.status()!=nomflowobj.status():
                status='Degraded'
            else:
                status='Nominal'
            rg.edges[edge][flow]={'values':flowobj.status(),'status':status, 'obj':flowobj}
    for node in g.nodes:
        faults=findfault(node, g)
        rg.nodes[node]['faults']=faults
    return rg
            

