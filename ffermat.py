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
    fxnnames=list(g.nodes)
    for fxnname in fxnnames:
        fxn=g.nodes(data='funcobj')[fxnname]
        modes=fxn.faultmodes
        for mode in modes:
            prob=modes[mode]['lprob']
            faultlist.append([fxnname,mode, prob])
    return faultlist

def runlist(mdl):
    
    [forwardgraph,backgraph,fullgraph]=mdl.initialize()
    faultlist=listinitfaults(fullgraph)
    
    fullresults={}
    
    for [fxnname, mode, prob] in faultlist:
        [forwardgraph,backgraph,fullgraph]=mdl.initialize()
        endflows,endfaults,endclass=runonefault(forwardgraph,backgraph,fullgraph,fxnname,mode)
        
        repairtype, lowrcost, highrcost=calcrepair(mdl,forwardgraph, endfaults, endclass)
        
        lowscore, highscore, avescore, cost=calcscore(mdl, prob,endclass,repairtype)
               
        fullresults[fxnname, mode]={'flow effects': endflows, 'faults':endfaults, \
                   'classification':endclass, 'repair type': repairtype, \
                   'low score': lowscore, 'high score': highscore, \
                   'average score': avescore, 'probability':prob}
        
    displayresults(fullresults)
    return fullresults

def displayresults(fullresults):
    
    
    for fxnname, mode in sorted(fullresults, key=lambda x: fullresults[x]['average score'], reverse=True):
        result=fullresults[fxnname, mode]
        print('FAULT SCENARIO: ', fxnname, ' ', mode)
        print('PROBABILITY: ', result['probability'])
        print('SCORE:', result['average score'], ' (', result['low score'], '-', result['high score'], ')')
        print('SEVERITY: ', result['classification'])
        print('REPAIR: ', result['repair type'])
        print('FLOW EFFECTS:')
        pprint.pprint(result['flow effects'])
        print('END FAULTS:')
        print(result['faults'])
        print()    
    
    return

def savereport(fullresults, filename='report.txt'):
    
    file = open(filename, 'w')
    orig_stdout=sys.stdout
    sys.stdout=file

    displayresults(fullresults)   
    
    sys.stdout=orig_stdout
    file.close()
    return

def runonefault(forwardgraph,backgraph,fullgraph,fxnname,mode):
    
    #findfxn
    fxn=fullgraph.nodes(data='funcobj')[fxnname]
    #inject fault
    fxncall=fxn.updatefxn(faults=[mode])
    outputs=fxncall['outputs']
    inputs=fxncall['inputs']
    
    #propogate effect to immediate node edges (forward)
    for edge in forwardgraph.edges(fxnname): 
        for outflow in outputs:
            if outflow in forwardgraph.edges[edge]:
                forwardgraph.edges[edge][outflow]=outputs[outflow]
    #propogate effect to immediate node edges (backward)          
    for edge in backgraph.edges(fxnname):
        for inflow in inputs:
            if inflow in fullgraph.edges[edge]:
                backgraph.edges[edge][inflow]=inputs[inflow]
                
    
    #propfaults(forwardgraph)
    propagate(forwardgraph, backgraph)
    endflows=findfaultflows(forwardgraph)
    endfaults=findfaults(forwardgraph)
    endclass=findclassification(forwardgraph)
    
    return endflows,endfaults,endclass

#goal:
#if an edge has changed, adjacent nodes now active
#if a node has changed, it is also now active
#propagates faults forward    
def propfaultsforward(g):

    fxnnames=list(g.nodes())
    activefxns=set(fxnnames)
    '''
    '''
    while activefxns:
        
        for fxnname in list(activefxns):
            fxn=g.nodes(data='funcobj')[fxnname]
            
            #iterate over input edges
            inputdict={}
            for edge in g.in_edges(fxnname):
                edgeinputs=g.edges[edge]
                inputdict.update(edgeinputs)
            #if same inputs, remove from active functions, otherwise update inputs    
            if inputdict==g.nodes('inputs')[fxnname]:
                activefxns.discard(fxnname)
            else:
                for key in g.nodes('inputs')[fxnname]:
                    g.nodes('inputs')[fxnname][key]=inputdict[key]
            
            #update outputs
            fxncall=fxn.updatefxn(inputs=inputdict)
            outputs=fxncall['outputs']
            #if outputs==g.nodes('outputs')[fxnname]:
            #    activefxns.discard(fxnname)        
            #iterate over output edges
            for edge in g.out_edges(fxnname):
                active_edge=False
            #iterate over flows
                for outflow in outputs:
                    if outflow in g.edges[edge]:
                        if g.edges[edge][outflow]!=outputs[outflow]:
                            active_edge=True
                        g.edges[edge][outflow]=outputs[outflow]

            #if a new value, functions are now active?
                if active_edge:
                    activefxns.update(edge)                 
    return

def propagate(forward, backward):

    fxnnames=list(forward.nodes())
    activefxns=set(fxnnames)
    '''
    '''
    while activefxns:
        
        for fxnname in list(activefxns):
            fxn=forward.nodes(data='funcobj')[fxnname]
            
            #iterate over input edges
            inputdict={}
            outputdict={}
            for edge in forward.in_edges(fxnname):
                edgeinputs=forward.edges[edge]
                inputdict.update(edgeinputs)
            for edge in backward.in_edges(fxnname):
                edgeoutputs=backward.edges[edge]
                outputdict.update(edgeoutputs)
            #if same inputs and outputs, remove from active functions, otherwise update inputs    
            if inputdict==forward.nodes('inputs')[fxnname] and outputdict==backward.nodes('outputs')[fxnname]:
                activefxns.discard(fxnname)
            else:
                for key in forward.nodes('inputs')[fxnname]:
                    forward.nodes('inputs')[fxnname][key]=inputdict[key]
                for key in backward.nodes('outputs')[fxnname]:
                    backward.nodes('outputs')[fxnname][key]=outputdict[key]
            
            #update outputs
            fxncall=fxn.updatefxn(inputs=inputdict, outputs=outputdict)
            inputs=fxncall['inputs']
            outputs=fxncall['outputs']
            
            #if outputs==g.nodes('outputs')[fxnname]:
            #    activefxns.discard(fxnname)        
            #iterate over output edges
            for edge in forward.out_edges(fxnname):
                active_edge=False
            #iterate over flows
                for outflow in outputs:
                    if outflow in forward.edges[edge]:
                        if forward.edges[edge][outflow]!=outputs[outflow]:
                            active_edge=True
                        forward.edges[edge][outflow]=outputs[outflow]

            #if a new value, functions are now active?
                if active_edge:
                    activefxns.update(edge) 
            
            for edge in backward.out_edges(fxnname):
                active_edge=False
            #iterate over flows
                for inflow in inputs:
                    if inflow in backward.edges[edge]:
                        if backward.edges[edge][inflow]!=inputs[inflow]:
                            active_edge=True
                        backward.edges[edge][inflow]=inputs[inflow]
                #if a new value, functions are now active?
                if active_edge:
                    activefxns.update(edge) 
    return 
        
#extract end-state of interest
#endstate=g.edges['Move_Water','Export_Water']


#extract non-nominal flow paths
def findfaultflows(g):
    endflows=dict()
    for edge in g.edges:
        g.get_edge_data(edge[0],edge[1])
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            states=list(g.get_edge_data(edge[0],edge[1])[flow])
            for state in states:
                value=g.get_edge_data(edge[0],edge[1])[flow][state]
                if value!=1.0:
                    endflows[edge[0],edge[1],flow,state]=value
    return endflows

#generates lists of faults present
def findfaults(g):
    endfaults=dict()
    fxnnames=list(g.nodes)
    #extract list of faults present
    for fxnname in fxnnames:
        fxn=g.nodes(data='funcobj')[fxnname]
        if fxn.faults.issuperset({'nom'}):
            fxn.faults.remove('nom')
        if len(fxn.faults) > 0:
            endfaults[fxnname]=fxn.faults
    return endfaults

def findclassification(g):
    endclass=dict()
    fxnnames=list(g.nodes)
    #extract list of faults present
    for fxnname in fxnnames:
        fxn=g.nodes(data='funcobj')[fxnname]
        if fxn.type=='classifier':
            endclass[fxnname]=fxn.returnvalue()

    return endclass

def calcrepair(mdl,g, endfaults, endclass):
    
    totalcost=0.0
    totalrepair='NA'
    lowcost=0.0
    highcost=0.0
    
 #costs from flow-based damage to functions   
    for fxnname in endfaults:
        fxn=g.nodes(data='funcobj')[fxnname]
        modes=endfaults[fxnname]   
        for mode in modes:
            repair=fxn.faultmodes[mode]['rcost']
            totalcost+=np.mean([mdl.repaircosts[repair]['lb'], mdl.repaircosts[repair]['ub']])
 
#costs from end-state classification           
    for classfxn in endclass:
        repairtype= mdl.repaircosts[mdl.endstatekey[endclass[classfxn]]['repair']]
        classcost=np.mean([repairtype['lb'], repairtype['ub']])
        if classcost > totalcost:
            totalcost=classcost
    
    if totalcost > mdl.repaircosts['totaled']['ub']:
        totalcost=mdl.repaircosts['totaled']['ub']
    
    for repairtype in mdl.repaircosts:
        if totalcost >=mdl.repaircosts[repairtype]['lb'] and totalcost < mdl.repaircosts[repairtype]['ub']:
            totalrepair=repairtype
            lowcost=mdl.repaircosts[repairtype]['lb']
            highcost=mdl.repaircosts[repairtype]['ub']
    
    return totalrepair, lowcost, highcost

def calcscore(mdl, lprob, endclass, repair):
    lowprob=mdl.lifecycleprob[lprob]['lb']
    highprob=mdl.lifecycleprob[lprob]['ub']
    rawcost=0.0
    for classfxn in endclass:
        cost=mdl.endstatekey[endclass[classfxn]]['cost']
        rawcost+=cost
    
    lowscore=lowprob*(rawcost+mdl.repaircosts[repair]['lb'])
    highscore=highprob*(rawcost+mdl.repaircosts[repair]['ub'])
    avescore=np.mean([highscore, lowscore])
    
    return lowscore,highscore,avescore,rawcost
    