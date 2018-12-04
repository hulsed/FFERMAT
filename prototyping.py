#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 18:16:39 2018

@author: daniel
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


##BASIC OPERATIONS

#x1 takes precedence over x2 in decidint if num is inf or zero
def m2to1(x):
    if np.size(x)>2:
        x=[x[0], m2to1(x[1:])]
    if x[0]==np.inf:
        y=np.inf
    elif x[1]==np.inf:
        if x[0]==0.0:
            y=0.0
        else:
            y=np.inf
    else:
        y=x[0]*x[1]
    return y
#truncates value to 2 (useful if behavior unchanged by increases)
def trunc(x):
    if x>2.0:
        y=2.0
    else:
        y=x
    return y


#a=1
#inflow=inputfxn(a)
#inflow=1
#b=2
#outflow=mainfxn(b,inflow)
#c=3
#outstate=outputfxn(c,outflow)
#maybe nodes have state values which determines in/out to next?

##MODEL

class importEE:
    def __init__(self):
        self.EEout={'state': 1.0}
        self.elecstate=1.0
        self.faultmodes=[['infv','lowv','nov']]
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['infv'])):
            self.elecstate=np.inf
        elif self.faults.intersection(set(['lowv'])):
            self.elecstate=0.5
        elif self.faults.intersection(set(['nom'])):
            self.elecstate=0.0
    def behavior(self):
        self.EEout['state']=self.elecstate
    def updatefxn(self,fault=['nom'],inputs={}):
        self.faults.update(fault)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'EE': self.EEout}
        return outputs
        
class importWat:
    def __init__(self):
        self.wlstate=1.0
        self.wvstate=1.0
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.modes=[['nowat','hiwat'],['highvisc','solids']]
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['nowat'])):
            self.wlstate=0.0
        elif self.faults.intersection(set(['hiwat'])):
            self.wlstate=np.inf
        if self.faults.intersection(set(['highvisc'])):
            self.wvstate=2.0
        elif self.faults.intersection(set(['solids'])):
            self.wvstate=np.inf
    def behavior(self):
        self.Watout['level']=self.wlstate
        self.Watout['visc']=self.wvstate
    def updatefxn(self,fault=['nom'], inputs={}):
        self.faults.update(fault)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Water': self.Watout}
        return outputs
    
class moveWat:
    def __init__(self):
        self.EEin={'state': 1.0}
        self.Sigout={'state': 1.0}
        self.Watin={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.modes={'e':{'f': set(['shortc','openc'])}, 
                       'm':{'d':set(['jam','misalign']), 'f':set(['break'])}, 
                       's':{'f': set(['nosensing']), 'd': set(['poorsensing'])}}
        self.faults=set(['nom'])
        self.opermodes=['on','off']
        self.mechstate=1.0
        self.sensestate=1.0
        self.elecstate=1.0
    def resolvefaults(self):
        if any(self.faults.intersection(['shortc'])) and any(self.faults.intersection(['openc'])):
            self.faults.difference_update(['shortc'])
        if any(self.faults.intersection(['nosensing'])) and any(self.faults.intersection(['poorsensing'])):
            self.faults.difference_update(['poorsensing'])       
        if any(self.faults.intersection(['break'])) and any(self.faults.intersection(['jam','misalign'])):
            self.faults.difference_update(['jam','misalign'])
    def condfaults(self):
        if self.EEin['state']==np.inf:
            self.faults.update(['openc','nosensing'])
        if self.Watin['visc']==np.inf and self.EEin>0:
            self.faults.update(['break','openc'])
        elif self.Watin['visc']>1 and self.EEin>0:
            self.faults.update(['misalign'])
        if self.Watin['level']==np.inf:
            if self.EEin>0.0:
                self.faults.update(['shortc','nosensing'])
            else:
                self.faults.update(['shortc','poorsensing'])
    #determines the effect of fault modes on behavior function
    def detbehav(self):
        if self.faults.intersection(set(['shortc','openc'])):
            self.elecstate=0.0
        if self.faults.intersection(set(['break'])):
            self.mechstate=0.0
        elif self.faults.intersection(set(['jam', 'misalign'])):
            self.mechstate=0.5
        if self.faults.intersection(set(['nosensing'])):
            self.sensestate=0
        elif self.faults.intersection(set(['poorsensing'])):
            self.sensestate=0.5
    #calculates behavior
    def behavior(self):
        self.Watout['level']=self.Watin['level']
        self.Watout['visc']=self.Watin['visc']
        self.Watout['flow']=m2to1([ trunc(self.Watout['level']), trunc(1/self.Watin['visc']), self.mechstate, self.elecstate, trunc(self.EEin['state'])])
        self.Sigout['state']=m2to1([self.sensestate, self.elecstate, self.EEin['state']])
        
    def updatefxn(self,faults=['nom'], inputs={'EE':{'state': 1.0}, 'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}):
        self.faults.update(faults)
        self.EEin=inputs['EE']
        self.Watin=inputs['Water']
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Water':self.Watout,'Signal':self.Sigout}
        return outputs

class exportWat():
    def __init__(self):
        self.Watin={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.Wat={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.modes={}
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        return 0
    def behavior(self):
        self.Wat=self.Watin
        return 0
    def updatefxn(self, faults=['nom'],inputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}):
        self.Watin=inputs['Water']
        self.behavior()
        return

class exportSig():
    def __init__(self):
        self.Sigin={'state': 1.0}
        self.Sig=1.0
        self.modes={}
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        return 0
    def behavior(self):
        self.Sig=self.Sigin
        return 0
    def updatefxn(self, faults=['nom'],inputs={'Signal':{'state': 1.0}}):
        self.Sigin=inputs['Signal']
        self.behavior()
        return    

##MODEL GRAPH AND INITIALIZATION    
g=nx.DiGraph()

Import_EE=importEE()
g.add_node('Import_EE', funcdef=importEE, funcobj=Import_EE, inputs={}, outputs={'EE': {'state': 1.0}})
Import_Water=importWat()
g.add_node('Import_Water', funcdef=importWat, funcobj=Import_Water, inputs={},outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}})
Move_Water=moveWat()
g.add_node('Move_Water', funcdef=moveWat, funcobj=Move_Water,inputs={'EE': {'state': 1.0}, 'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}, outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}, 'Signal': {'state': 1.0}})
Export_Water=exportWat()
g.add_node('Export_Water', funcdef=exportWat, funcobj=Export_Water,inputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}},outputs={})
Export_Signal=exportSig()
g.add_node('Export_Signal', funcdef=exportSig, funcobj=Export_Signal, inputs={'Signal': {'state': 1.0}}, outputs={})

EE={'state': 1.0}
g.add_edge('Import_EE', 'Move_Water', EE=EE)
Water_1={'level':1.0, 'visc':1.0, 'flow':1.0}
g.add_edge('Import_Water','Move_Water', Water=Water_1)
Water_2={'level':1.0, 'visc':1.0, 'flow':1.0}
g.add_edge('Move_Water','Export_Water', Water=Water_2)
Signal={'state': 1.0}
g.add_edge('Move_Water','Export_Signal', Signal=Signal)


def showgraph(g):
    labels=dict()
    for edge in g.edges:
        flows=list(g.get_edge_data(edge[0],edge[1]).keys())
        labels[edge[0],edge[1]]=flows
    
    pos=nx.spring_layout(g)
    nx.draw_networkx(g,pos)
    nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
    plt.show()



def runonefault(g):
    #inject fault
    outputs=Import_EE.updatefxn(fault=['nov'])
    for outflow in outputs:
        g.edges['Import_EE','Move_Water'][outflow]=outputs[outflow]

    propagatefaults(g)
    endflows=findfaultflows(g)
    endfaults=findfaults(g)
    
    return endflows,endfaults

#goal:
#if an edge has changed, adjacent nodes now active
#if a node has changed, it is also now active
    
def propagatefaults(g):

    fxnnames=list(g.nodes())
    activefxns=set(fxnnames)
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
            outputs=fxn.updatefxn(inputs=inputdict)
            
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
        
        
#extract end-state of interest
endstate=g.edges['Move_Water','Export_Water']


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
    #extract list of faults present
    for fxnname in fxnnames:
        fxn=g.nodes(data='funcobj')[fxnname]
        fxn.faults.remove('nom')
        if len(fxn.faults) > 0:
            endfaults[fxnname]=fxn.faults
    return endfaults
    


#classify results



#EE1=Import_EE.updatefxn(fault=['infv'])
#Wat1=Import_Water.updatefxn()
#Wat2,Sig1=Move_Water.updatefxn(inputs={'EE': EE1,'Water_1': Wat1})
#Export_Water.updatefxn(inputs={'Water_2':Wat2})
#Export_Signal.updatefxn(inputs={'Signal':Sig1})
    