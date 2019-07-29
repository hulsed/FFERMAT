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

def makefullgraph(g):
    backgraph=g.reverse(copy=True)
    forwardgraph=g
    fullgraph=nx.compose(backgraph, forwardgraph)
    return backgraph, forwardgraph, fullgraph

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
    try:
        for fxnname in fxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            modes=fxn.faultmodes
            
            for mode in modes:
                prob=modes[mode]['lprob']
                faultlist.append([fxnname,mode])
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return faultlist

def listscens(mdl,g):
    scenlist=[]
    opmodes={}
    
    operfxnnames=list(g.nodes)
    
    if mdl.scope=='full':
        faultfxnnames=list(g.nodes)
    else:
        faultfxnnames=mdl.scope['functions']

    try:
        for fxnname in operfxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            try: 
                opmodelist=list(fxn.opermodes.keys())
                opmodes={fxnname:opmodelist}
                for opmode in list(opmodelist):
                    scenlist.append([fxnname,opmode,'NA','nom', 'NA','nom'])
            except:
                foo=1
            
            
        for fxnname in faultfxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            modes=fxn.faultmodes
            opermodes=fxn.operscens
            pffxnname=fxn.pffxn
            pffxn=g.nodes(data='funcobj')[pffxnname]
            
            for opfxn, opmodelist in opmodes.items():
                for opmode in opermodes:
                    for mode in modes:
                        condmodes=pffxn.condmodes
                        indmodes=pffxn.indmodes
                        
                        scenlist.append([opfxn, opmode, fxnname, mode, 'NA', 'nom'])
                        
                        for pfmode in condmodes:
                            scenlist.append([opfxn, opmode, fxnname, mode, pffxnname, pfmode])
            for pfmode in indmodes:
                scenlist.append([opfxn, opmode, pffxnname, pfmode, 'NA', 'nom'])
        
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return scenlist

#propogates 
def proplist(mdl):
    
    [forwardgraph,backgraph,fullgraph]=mdl.initialize()
    scenlist=listscens(mdl,fullgraph)
    fullresults={}
    
    for [opfxn, opmode, fxnname, mode, pffxnname, pfmode] in scenlist:
        [forwardgraph,backgraph,fullgraph]=mdl.initialize()
        
        endflows,endfaults,endclass=runonefault(mdl, forwardgraph,backgraph,fullgraph,opfxn, opmode, fxnname, mode, pffxnname, pfmode)
               
        fullresults[opfxn, opmode, fxnname, mode]={'flow effects': endflows, 'faults':endfaults}
    return fullresults


def runsummary(mdl):
    
    [forwardgraph,backgraph,fullgraph]=mdl.initialize()
    scenlist=listscens(mdl,fullgraph)
    
    faultrates={}
    fullresults={}
    summary={}
    totalscore=0.0
    totalprobs={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    allowprobs={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    feasibility='feasible'
    
    for [opfxn, opmode, fxnname, mode, pffxnname, pfmode] in scenlist:
        [forwardgraph,backgraph,fullgraph]=mdl.initialize()
        
        endflows,endfaults,endclass=runonefault(mdl, forwardgraph,backgraph,fullgraph,opfxn, opmode, fxnname, mode, pffxnname, pfmode)
        
        if fxnname !='NA':
        
            fxn=getfxn(fxnname,forwardgraph)
            faultrates=mdl.calcrate(mode,fxn,mdl)
        else:
            faultrates['life_exp']=0.0
            faultrates['mit_prob']=0.0
        
        lexp=faultrates['life_exp']*mdl.opfrac[opmode]
        pfh=faultrates['mit_prob']*mdl.opfrac[opmode]
        
        repairtype, lowrcost, highrcost=mdl.calcrepair(mdl,forwardgraph, endfaults, endclass)
        
        score,eventcost=mdl.calcscore(mdl,lexp, endclass,repairtype)
               
        fullresults[opfxn, opmode, fxnname, mode]={'flow effects': endflows, 'faults':endfaults, \
                   'classification':endclass, 'repair type': repairtype, \
                   'estimated score': score, 'expected amount':lexp}
        
        totalscore+=score
        totalprobs[endclass['total']]+=pfh
    
    for classification in totalprobs:
        allowprobs[classification]=mdl.endstatekey[classification]['pfh_allow']*mdl.lifehours
        if totalprobs[classification]> allowprobs[classification]:
            feasibility='infeasible'
    
    summary['totalscore']=totalscore
    summary['expectednum']=totalprobs  
    summary['expectednum_allow']=allowprobs
    summary['feasibility']=feasibility
    
    displayresults(fullresults, summary, justsummary=True)
    return fullresults, summary


def displayresults(fullresults, summary, descending=True, justsummary=False):
    
    print('SUMMARY')
    print('--------------------------------------------')
    print('TOTAL SCORE:', summary['totalscore'])
    print('FEASIBILITY:', summary['feasibility'])
    print('Failure Type', '\t \t','Expected Number', '\t', 'Allowable')
    for classification in summary['expectednum']:
        print(classification.ljust(11), '\t \t', str(summary['expectednum'][classification]).ljust(15), '\t', str(summary['expectednum_allow'][classification]).ljust(15))
    
    
    
    if not justsummary:
        print()
        print('FULL RESULTS:')
        print('--------------------------------------------')
        for opfxn, opmode, fxnname, mode in sorted(fullresults, key=lambda x: fullresults[x]['estimated score'], reverse=descending):
            result=fullresults[opfxn, opmode, fxnname, mode]
            print('OPERATIONAL SCENARIO: ', opfxn, ' ', opmode)
            print('FAULT SCENARIO: ', fxnname, ' ', mode, 'during', opmode)
            print('EXPECTED NUM: ', result['expected amount'])
            print('SCORE:', result['estimated score'])
            print('SEVERITY: ', result['classification'])
            print('REPAIR: ', result['repair type'])
            print('FLOW EFFECTS:')
            pprint.pprint(result['flow effects'])
            print('END FAULTS:')
            print(result['faults'])
            print()    
    
    return

def savereport(fullresults,summary, filename='report.txt'):
    
    file = open(filename, 'w')
    orig_stdout=sys.stdout
    sys.stdout=file

    displayresults(fullresults, summary)   
    
    sys.stdout=orig_stdout
    file.close()
    return

def runonefault(mdl, forwardgraph,backgraph,fullgraph,opfxn, opmode, fxnname, mode, pffxnname, pfmode):
    
    opfxnobj=fullgraph.nodes(data='funcobj')[opfxn]
    opfxncall=opfxnobj.updatefxn(faults=['nom'], opermode=opmode)
    oneprop(forwardgraph,backgraph,fullgraph,opfxncall,opfxn)
    
    if pffxnname!='NA':
        pffxnobj=fullgraph.nodes(data='funcobj')[pffxnname]
        pffxncall=pffxnobj.updatefxn(faults=[pfmode], opermode=opmode)
        oneprop(forwardgraph, backgraph,fullgraph,pffxncall,pffxnname)
    
    if fxnname!='NA':
        fxn=fullgraph.nodes(data='funcobj')[fxnname]
        #inject fault
        fxncall=fxn.updatefxn(faults=[mode])
        oneprop(forwardgraph,backgraph,fullgraph,fxncall,fxnname)
    
    #propfaults(forwardgraph)
    propagate(forwardgraph, backgraph, opfxn, opmode)
    endflows=findfaultflows(forwardgraph)
    endfaults=findfaults(forwardgraph)
    endclass=mdl.findclassification(mdl, forwardgraph)
    
    return endflows,endfaults,endclass

def oneprop(forwardgraph, backgraph,fullgraph, fxncall,fxnname):
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
        
    return 
def getfxn(g,fxnname):
    fxn=g.nodes(data='funcobj')[fxnname]
    return fxn

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

def propagate(forward, backward, opfxn, opmode):

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
            #find any new inputs from the edges going in and out
            collectfxnedgevals(forward, inputdict, fxnname)
            collectfxnedgevals(backward, outputdict, fxnname)
            #if same inputs and outputs, remove from active functions, otherwise update inputs
            checkandupdatenodes(inputdict, outputdict,fxnname, forward, backward, activefxns)
            
            #update outputs
            if fxnname==opfxn:
                fxncall=fxn.updatefxn(inputs=inputdict, outputs=outputdict, opermode=opmode)
            else:
                fxncall=fxn.updatefxn(inputs=inputdict, outputs=outputdict)
                
            inputs=fxncall['inputs']
            outputs=fxncall['outputs']
            #update edges with new input/output values from the update function and add related functions to list
            checkandupdateedges(forward, outputs,fxnname, activefxns)
            checkandupdateedges(backward, inputs,fxnname, activefxns)
    return

def checkandupdatenodes(inputdict, outputdict,fxnname, forward, backward, activefxns):
    #if same inputs and outputs, remove from active functions, otherwise update inputs    
    if inputdict==forward.nodes('inputs')[fxnname] and outputdict==backward.nodes('outputs')[fxnname]:
        activefxns.discard(fxnname)
    else:
        activefxns.update([fxnname])
        for key in forward.nodes('inputs')[fxnname]:
            forward.nodes('inputs')[fxnname][key]=inputdict[key]
        for key in backward.nodes('outputs')[fxnname]:
            backward.nodes('outputs')[fxnname][key]=outputdict[key]

def collectfxnedgevals(forward, inputdict, fxnname):
    #find any new inputs from the edges going in and out
    for edge in forward.in_edges(fxnname):
        edgeinputs=forward.edges[edge]
        inputdict.update(edgeinputs)

def checkandupdateedges(forward, outputs,fxnname, activefxns):
    #use new input/output values from function to update edges
    for edge in forward.out_edges(fxnname):
            #iterate over flows            
                for outflow in outputs:
                    if outflow in forward.edges[edge]:
                        if forward.edges[edge][outflow]!=outputs[outflow]:
                            forward.edges[edge][outflow]=outputs[outflow]
                            #if a new value, add connected function to list of active functions
                            activefxns.update(edge)


#extract non-nominal flow paths
def findfaultflows(g):
    endflows=dict()
    for edge in g.edges:
        g.get_edge_data(edge[0],edge[1])
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        for flow in flows:
            states=list(g.get_edge_data(edge[0],edge[1])[flow])
            
            if 'dev' in states:
                devval=g.get_edge_data(edge[0],edge[1])[flow]['dev']
                expval=g.get_edge_data(edge[0],edge[1])[flow]['exp']
                deviation=expval-devval
            elif 'ctl' in states:
                ctlval=g.get_edge_data(edge[0],edge[1])[flow]['ctl']
                expval=g.get_edge_data(edge[0],edge[1])[flow]['exp']
                deviation=expval-ctlval
            else:
                for state in states:
                    value=g.get_edge_data(edge[0],edge[1])[flow][state]
                    if type(value) is dict:
                        deviation=value['exp']-value['dev']
                        if deviation!=0.0:
                            endflows[edge[0],edge[1],flow,state]=deviation
                    elif value!=1.0:
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

def getfxn(fxnname, graph):
    fxn=graph.nodes(data='funcobj')[fxnname]
    return fxn

