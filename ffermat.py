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
    try:
        for fxnname in fxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            modes=fxn.faultmodes
            for mode in modes:
                prob=modes[mode]['lprob']
                faultlist.append([fxnname,mode, prob])
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return faultlist

def listscens(g):
    scenlist=[]
    opmodes={}
    fxnnames=list(g.nodes)
    try:
        for fxnname in fxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            try: 
                opmodelist=list(fxn.opermodes.keys())
                opmodes={fxnname:opmodelist}
                for opmode in list(opmodelist):
                    scenlist.append([fxnname,opmode,'NA','nom','NA'])
            except:
                foo=1
            
            
        for fxnname in fxnnames:
            fxn=g.nodes(data='funcobj')[fxnname]
            modes=fxn.faultmodes
            for opfxn, opmodelist in opmodes.items():
                for opmode in opmodelist:
                    for mode in modes:
                        prob=modes[mode]['lprob']
                        scenlist.append([opfxn, opmode, fxnname, mode, prob])
        
    except: 
        print('Incomplete Function Definition, function: '+fxnname)
    return scenlist

def runlist(mdl):
    
    [forwardgraph,backgraph,fullgraph]=mdl.initialize()
    scenlist=listscens(fullgraph)
    
    fullresults={}
    summary={}
    totalscore=0.0
    totalprobs_low={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    totalprobs_high={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    totalprobs_ave={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    allowprobs={'catastrophic': 0.0,'hazardous': 0.0,'major': 0.0,'minor': 0.0,'noeffect': 0.0}
    feasibility='feasible'
    
    for [opfxn, opmode, fxnname, mode, prob] in scenlist:
        [forwardgraph,backgraph,fullgraph]=mdl.initialize()
        
        endflows,endfaults,endclass=runonefault(mdl, forwardgraph,backgraph,fullgraph,opfxn, opmode, fxnname, mode)
        
        repairtype, lowrcost, highrcost=calcrepair(mdl,forwardgraph, endfaults, endclass)
        
        lowscore, highscore, avescore, cost,lowprob,highprob=calcscore(mdl, prob,endclass,repairtype)
               
        fullresults[opfxn, opmode, fxnname, mode]={'flow effects': endflows, 'faults':endfaults, \
                   'classification':endclass, 'repair type': repairtype, \
                   'low score': lowscore, 'high score': highscore, \
                   'average score': avescore, 'probability':prob}
        
        totalscore+=avescore
        totalprobs_low[endclass['total']]+=lowprob
        totalprobs_high[endclass['total']]+=highprob
    
    for classification in totalprobs_low:
        totalprobs_ave[classification]=np.mean([totalprobs_low[classification],totalprobs_high[classification]])
        allowprobs[classification]=mdl.endstatekey[classification]['pfh_allow']*mdl.lifehours
        if totalprobs_ave[classification]> allowprobs[classification]:
            feasibility='infeasible'
    
    summary['totalscore']=totalscore
    summary['expectednum']=totalprobs_ave    
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
        for opfxn, opmode, fxnname, mode in sorted(fullresults, key=lambda x: fullresults[x]['average score'], reverse=descending):
            result=fullresults[opfxn, opmode, fxnname, mode]
            print('OPERATIONAL SCENARIO: ', opfxn, ' ', opmode)
            print('FAULT SCENARIO: ', fxnname, ' ', mode, 'during', opmode)
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

def savereport(fullresults,summary, filename='report.txt'):
    
    file = open(filename, 'w')
    orig_stdout=sys.stdout
    sys.stdout=file

    displayresults(fullresults, summary)   
    
    sys.stdout=orig_stdout
    file.close()
    return

def runonefault(mdl, forwardgraph,backgraph,fullgraph,opfxn, opmode, fxnname, mode):
    
    opfxnobj=fullgraph.nodes(data='funcobj')[opfxn]
    opfxncall=opfxnobj.updatefxn(faults=['nom'], opermode=opmode)
    oneprop(forwardgraph,backgraph,fullgraph,opfxncall,opfxn)
    
    if fxnname!='NA':
        fxn=fullgraph.nodes(data='funcobj')[fxnname]
        #inject fault
        fxncall=fxn.updatefxn(faults=[mode])
        oneprop(forwardgraph,backgraph,fullgraph,fxncall,fxnname)
    
    #propfaults(forwardgraph)
    propagate(forwardgraph, backgraph, opfxn, opmode)
    endflows=findfaultflows(forwardgraph)
    endfaults=findfaults(forwardgraph)
    endclass=findclassification(mdl, forwardgraph)
    
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
        print(activefxns)
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
                if fxnname=='Export_FM':
                    foo=1.0
            else:
                activefxns.update([fxnname])
                for key in forward.nodes('inputs')[fxnname]:
                    forward.nodes('inputs')[fxnname][key]=inputdict[key]
                for key in backward.nodes('outputs')[fxnname]:
                    backward.nodes('outputs')[fxnname][key]=outputdict[key]
            
            #try:
                #update outputs
            if fxnname==opfxn:
                fxncall=fxn.updatefxn(inputs=inputdict, outputs=outputdict, opermode=opmode)
            else:
                fxncall=fxn.updatefxn(inputs=inputdict, outputs=outputdict)
            inputs=fxncall['inputs']
            outputs=fxncall['outputs']
            
            print(forward.edges['Combine_Forces','Export_FM'])
            foo=1
            #except:
            #    print('Difficulty updating function: '+fxnname)
            #    print(outputs)
            
            #if outputs==g.nodes('outputs')[fxnname]:
            #    activefxns.discard(fxnname)        
            #iterate over output edges
            for edge in forward.out_edges(fxnname):
                active_edge=False
            #iterate over flows
                if edge==('Combine_Forces','Export_FM'):
                    foo=1
                    
            
                for outflow in outputs:
                    if outflow in forward.edges[edge]:
                        #print(outputs[outflow])
                        #print(forward.edges[edge][outflow])
                        #print(forward.edges[edge][outflow]!=outputs[outflow])
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
                        #print(inputs[inflow])
                        #print(backward.edges[edge][inflow])
                        #print(backward.edges[edge][inflow]!=inputs[inflow])
                        if backward.edges[edge][inflow]!=inputs[inflow]:
                            active_edge=True
                        backward.edges[edge][inflow]=inputs[inflow]
                #if a new value, functions are now active?
                if active_edge:
                    activefxns.update(edge) 
            
            print(forward.edges['Combine_Forces','Export_FM'])
            foo=1
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

def findclassification(mdl, g):
    endclass=dict()
    fxnnames=list(g.nodes)
    totclass=0.0
    endclass['total']='noeffect'
    #extract list of faults present
    for fxnname in fxnnames:
        fxn=g.nodes(data='funcobj')[fxnname]
        if fxn.type=='classifier':
            endclass[fxnname]=fxn.returnvalue()
            if mdl.endstatekey[endclass[fxnname]]['cost']>totclass:
                endclass['total']=endclass[fxnname]
                totclass=mdl.endstatekey[endclass[fxnname]]['cost']
            
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
    
    
    return lowscore,highscore,avescore,rawcost,lowprob,highprob
    