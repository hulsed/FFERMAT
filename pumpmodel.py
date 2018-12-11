# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 09:42:23 2018

@author: Daniel Hulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux


##MODEL

class importEE:
    def __init__(self):
        self.EEout={'state': 1.0}
        self.elecstate=1.0
        self.faultmodes=['infv','lowv','nov']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['infv'])):
            self.elecstate=np.inf
        elif self.faults.intersection(set(['nov'])):
            self.elecstate=0.0
        elif self.faults.intersection(set(['lowv'])):
            self.elecstate=0.5
    def behavior(self):
        self.EEout['state']=self.elecstate
    def updatefxn(self,faults=['nom'],inputs={}, outputs={}):
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'EE': self.EEout}
        return {'outputs':outputs, 'inputs':inputs}
        
class importWat:
    def __init__(self):
        self.wlstate=1.0
        self.wvstate=1.0
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.faultmodes=['nowat','hiwat','highvisc','solids']
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
        self.Watout['flow']
    def updatefxn(self,faults=['nom'], inputs={}, outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}):
        self.Watout['flow']=outputs['Water']['flow']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Water': self.Watout}
        return {'outputs':outputs, 'inputs':inputs}
    
class moveWat:
    def __init__(self):
        self.EEin={'state': 1.0}
        self.Sigout={'state': 1.0}
        self.Watin={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        #self.faultmodes={'e':{'f': set(['shortc','openc'])}, 
        #               'm':{'d':set(['jam','misalign']), 'f':set(['break'])}, 
        #               's':{'f': set(['nosensing']), 'd': set(['poorsensing'])}}
        self.faultmodes=['shortc','openc','jam','misalign','break','nosensing','poorsensing']
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
        if self.Watin['visc']==np.inf and self.EEin['state']>0:
            self.faults.update(['break','openc'])
        elif self.Watin['visc']>1 and self.EEin['state']>0:
            self.faults.update(['misalign'])
        if self.Watin['level']==np.inf:
            if self.EEin['state']>0.0:
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
        self.Watout['flow']=aux.m2to1([ aux.trunc(self.Watout['level']), aux.trunc(1/self.Watin['visc']), self.mechstate, self.elecstate, aux.trunc(self.EEin['state'])])
        self.Watin=self.Watout
        self.Sigout['state']=aux.m2to1([self.sensestate, self.elecstate, self.EEin['state']])
        
    def updatefxn(self,faults=['nom'], inputs={'EE':{'state': 1.0}, 'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}, outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0},'Signal':{'state': 1.0}}):
        self.faults.update(faults)
        self.EEin=inputs['EE']
        self.Watin=inputs['Water']
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Water':self.Watout,'Signal':self.Sigout}
        inputs={'EE':self.EEin,'Water':self.Watin}
        return {'outputs':outputs, 'inputs':inputs}

class exportWat():
    def __init__(self):
        self.Watin={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.Wat={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.faultmodes={}
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
    def updatefxn(self, faults=['nom'],inputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}, outputs={}):
        self.Watin=inputs['Water']
        self.behavior()
        outputs={}
        inputs={'Water':self.Watin}
        return {'outputs':outputs, 'inputs':inputs}

class exportSig():
    def __init__(self):
        self.Sigin={'state': 1.0}
        self.Sig=1.0
        self.faultmodes={}
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
    def updatefxn(self, faults=['nom'],inputs={'Signal':{'state': 1.0}}, outputs={}):
        self.Sigin=inputs['Signal']
        self.behavior()
        outputs={}
        inputs={'Signal':self.Sigin}
        return {'outputs':outputs, 'inputs':inputs}

##MODEL GRAPH AND INITIALIZATION   

def initfxns():
    Import_EE=importEE()
    Import_Water=importWat()
    Move_Water=moveWat()
    Export_Water=exportWat()
    Export_Signal=exportSig()
    return Import_EE,Import_Water, Move_Water, Export_Water, Export_Signal

def initialize():
    g=nx.DiGraph()
    
    Import_EE,Import_Water, Move_Water, Export_Water, Export_Signal=initfxns()
    
    g.add_node('Import_EE', funcdef=importEE, funcobj=Import_EE, inputs={}, outputs={'EE': {'state': 1.0}})
    g.add_node('Import_Water', funcdef=importWat, funcobj=Import_Water, inputs={},outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}})
    g.add_node('Move_Water', funcdef=moveWat, funcobj=Move_Water,inputs={'EE': {'state': 1.0}, 'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}}, outputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}, 'Signal': {'state': 1.0}}) 
    g.add_node('Export_Water', funcdef=exportWat, funcobj=Export_Water,inputs={'Water': {'level':1.0, 'visc':1.0, 'flow':1.0}},outputs={})
    g.add_node('Export_Signal', funcdef=exportSig, funcobj=Export_Signal, inputs={'Signal': {'state': 1.0}}, outputs={})
    
    EE={'state': 1.0}
    g.add_edge('Import_EE', 'Move_Water', EE=EE)
    Water_1={'level':1.0, 'visc':1.0, 'flow':1.0}
    g.add_edge('Import_Water','Move_Water', Water=Water_1)
    Water_2={'level':1.0, 'visc':1.0, 'flow':1.0}
    g.add_edge('Move_Water','Export_Water', Water=Water_2)
    Signal={'state': 1.0}
    g.add_edge('Move_Water','Export_Signal', Signal=Signal)
    
    backgraph=g.reverse(copy=True)
    forwardgraph=g
    fullgraph=nx.compose(backgraph, forwardgraph)
    
    return [forwardgraph,backgraph,fullgraph]