#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 18:16:39 2018

@author: daniel
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

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



class importEE:
    def __init__(self):
        self.EEout=1.0
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
        elif self.faults.intersection(set(['nov'])):
            self.elecstate=0.0
    def behavior(self):
        self.EEout=self.elecstate
    def updatefxn(self,fault=['nom'],inputs={}):
        self.faults=set(fault)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        return self.EEout
        
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
        self.faults=set(fault)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        return self.Watout
    
class moveWat:
    def __init__(self):
        self.EEin=1.0
        self.Sigout=1.0
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
        if self.EEin==np.inf:
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
        self.Watout['flow']=m2to1([ trunc(self.Watout['level']), trunc(1/self.Watin['visc']), self.mechstate, self.elecstate, trunc(self.EEin)])
        self.Sigout=m2to1([self.sensestate, self.elecstate, self.EEin])
        
    def updatefxn(self,faults=['nom'], inputs={'EE':1.0, 'Water_1': {'level':1.0, 'visc':1.0, 'flow':1.0}}):
        self.faults.update(faults)
        self.EEin=inputs['EE']
        self.Watin=inputs['Water_1']
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        return self.Watout, self.Sigout

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
    def updatefxn(self, faults=['nom'],inputs={'Water_2': {'level':1.0, 'visc':1.0, 'flow':1.0}}):
        self.Watin=inputs['Water_2']
        self.behavior()
        return

class exportSig():
    def __init__(self):
        self.Sigin=1.0
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
    def updatefxn(self, faults=['nom'],inputs={'Signal':1.0}):
        self.Sigin=inputs['Signal']
        self.behavior()
        return    
    
g=nx.DiGraph()

Import_EE=importEE()
g.add_node('Import_EE', funcdef=importEE, funcobj=Import_EE)
Import_Water=importWat()
g.add_node('Import_Water', funcdef=importWat, funcobj=Import_Water)
Move_Water=moveWat()
g.add_node('Move_Water', funcdef=moveWat, funcobj=Move_Water)
Export_Water=exportWat()
g.add_node('Export_Water', funcdef=exportWat, funcobj=Export_Water)
Export_Signal=exportSig()
g.add_node('Export_Signal', funcdef=exportSig, funcobj=Export_Signal)

EE=1.0
g.add_edge('Import_EE', 'Move_Water', flow='EE', flowvar=EE)
Water_1={'level':1.0, 'visc':1.0, 'flow':1.0}
g.add_edge('Import_Water','Move_Water', flow='Water_1', flowvar=Water_1)
Water_2={'level':1.0, 'visc':1.0, 'flow':1.0}
g.add_edge('Move_Water','Export_Water', flow='Water_2', flowar=Water_2)
Signal=1.0
g.add_edge('Move_Water','Export_Signal', flow='Signal', flowvar=Signal)


labels=dict()
for (u,v,label) in g.edges.data('flow'):
    labels[(u,v)]=label

edges=g.edges()

pos=nx.spring_layout(g)
nx.draw_networkx(g,pos)
nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
plt.show()

def initedges():
    
    return



fxnnames=list(g.nodes())
for fxnname in fxnnames:
    fxn=g.nodes(data='funcobj')[fxnname]
    outputvals=[x[2] for x in list(g.out_edges(fxnname,data='flowvar'))]
    outputnames=[x[2] for x in list(g.out_edges(fxnname,data='flow'))]
    inputvals=[x[2] for x in list(g.in_edges(fxnname,data='flowvar'))]
    inputnames=[x[2] for x in list(g.in_edges(fxnname,data='flow'))]
    inputdict=dict(zip(inputnames,inputvals))
    fxn.updatefxn(inputs=inputdict)
        




EE1=impE.updatefxn(fault=['infv'])
Wat1=impW.updatefxn()
Wat2,Sig1=moveW.updatefxn(EEin=EE1,Watin=Wat1)
expW.updatefxn(Watin=Wat2)
expS.updatefxn(Sigin=Sig1)
    