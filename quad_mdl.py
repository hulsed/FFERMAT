# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:30:03 2019



@author: dhulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

scope='full'

rotorlist={'RR','LR','RF', 'LF'}
##Define flows for model
class EE:
    def __init__(self,name):
        self.flowtype='EE'
        self.name=name
        self.rate=1.0
        self.effort=1.0
        self.nominal={'rate':1.0, 'effort':1.0}
    def status(self):
        status={'rate':self.rate, 'effort':self.effort}
        return status.copy() 

nomEE=EE('nominal')

class storeEE:
    def __init__(self, name,EEout):
        self.type='function'
        self.EEout=EEout
        self.effstate=1.0
        self.ratestate=1.0
        self.soc=100
        self.faultmodes={'short':{'rate':'moderate', 'rcost':'major'}, \
                         'degr':{'rate':'moderate', 'rcost':'minor'}, \
                         'break':{'rate':'common', 'rcost':'moderate'}, \
                         'nocharge':{'rate':'moderate','rcost':'minor'}, \
                         'lowcharge':{'rate':'moderate','rcost':'minor'}}
        self.faults=set(['nom'])
    def condfaults(self):
        if self.EEout.rate>2:
            self.faults.add('break')
        if self.soc<10:
            self.faults.add('lowcharge')
        if self.soc<1:
            self.faults.remove('lowcharge')
            self.faults.add('nocharge')
        return 0
    def behavior(self, time):
        if self.faults.intersection(set(['short'])):
            self.effstate=0.0
        elif self.faults.intersection(set(['break'])):
            self.effstate=0.0
        elif self.faults.intersection(set(['degr'])):
            self.effstate=0.5
        
        if self.faults.intersection(set(['nocharge'])):
            self.soc=0.0
            self.effstate=0.0
            
        self.EEout.effort=self.effstate
        self.soc=self.soc-self.EEout.rate*time
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior(time)
        return 

class distEE:
    def __init__(self,EEin,EErr,EElr,EErf,EElf,EEctl):
        self.useprop=1.0
        self.type='function'
        self.EEin=EEin
        self.EErr=EErr
        self.EElr=EElr
        self.EErf=EErf
        self.EElf=EElf
        self.EEctl=EEctl
        self.effstate=1.0
        self.ratestate=1.0
        self.faultmodes={'short':{'rate':'moderate', 'rcost':'major'}, \
                         'degr':{'rate':'moderate', 'rcost':'minor'}, \
                         'break':{'rate':'common', 'rcost':'moderate'}}
        self.faults=set(['nom'])
    def condfaults(self):
        
        if max(self.EErr.rate,self.EElr.rate,self.EErf.rate,self.EElf.rate,self.EEctl.rate)>2:
            self.faults.add('nov') 
    def behavior(self, time):
        if self.faults.intersection(set(['short'])):
            self.ratestate=np.inf
        elif self.faults.intersection(set(['break'])):
            self.effstate=0.0
        elif self.faults.intersection(set(['degr'])):
            self.effstate=0.5
        self.EEin.rate=self.ratestate*self.EEin.effort
        self.EErr.effort=self.effstate*self.EEin.effort
        self.EElr.effort=self.effstate*self.EEin.effort
        self.EErf.effort=self.effstate*self.EEin.effort
        self.EElf.effort=self.effstate*self.EEin.effort
        self.EEctl.effort=self.effstate*self.EEin.effort
        
        self.EEin.rate=max(self.EErr.rate,self.EElr.rate,self.EErf.rate,self.EElf.rate,self.EEctl.rate)
        
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior(time)
        return 
    
class convEE:
    def __init__(self, name, EEin, EEout):
        self.type='function'
        self.EEin=EEin
        self.EEout=EEout
        self.elecstate=1.0
        self.faultmodes={'short':{'rate':'moderate', 'rcost':'major'}, \
                         'degr':{'rate':'moderate', 'rcost':'minor'}, \
                         'break':{'rate':'common', 'rcost':'moderate'}}
        self.faults=set(['nom'])
    def condfaults(self):
        if self.EEout.rate>2:
            self.faults.add('nov')
    def behavior(self):
        if self.faults.intersection(set(['short'])):
            self.EEin.rate=np.inf
            self.EEout.effort=0.0
        elif self.faults.intersection(set(['break'])):
            self.EEin.rate=0.0
            self.EEout.effort=0.0
        elif self.faults.intersection(set(['degr'])):
            self.EEout.effort=0.5
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior()
        return 
    
##future: try to automate this part so you don't have to do it in a wierd order
def initialize():
    
    #initialize graph
    g=nx.DiGraph()
    
    EE_1=EE('EE_1')
    StoreEE=storeEE('StoreEE',EE_1)
    g.add_node('StoreEE', obj=StoreEE)
    
    EErr_1=EE('EErr_1')
    EElr_1=EE('EElr_1')
    EErf_1=EE('EErf_1')
    EElf_1=EE('EElf_1')
    EEclt_1=EE('EEclt_1')
    
    DistEE=distEE(EE_1,EErr_1,EElr_1,EErf_1,EElf_1,EEclt_1)
    g.add_node('DistEE', obj=DistEE)
    
    EErr_2=EE('EErr_2')
    EElr_2=EE('EElr_2')
    EErf_2=EE('EErf_2')
    EElf_2=EE('EElf_2')
    
    ConvEErr=convEE('Convert_EE_RR',EErr_1,EErr_2)
    g.add_node('ConvEErr', obj=ConvEErr)
    ConvEElr=convEE('Convert_EE_LR',EElr_1,EElr_2)
    g.add_node('ConvEElr', obj=ConvEElr)
    ConvEErf=convEE('Convert_EE_RF',EErf_1,EErf_2)
    g.add_node('ConvEErf', obj=ConvEErf)
    ConvEElf=convEE('Convert_EE_LF',EElf_1,EElf_2)
    g.add_node('ConvEElf', obj=ConvEElf)
    
    g.add_edge('StoreEE','DistEE',EE_1=EE_1)
    g.add_edge('DistEE','ConvEErr',EErr_1=EErr_1)
    g.add_edge('DistEE','ConvEElr',EElr_1=EElr_1)
    g.add_edge('DistEE','ConvEErf',EErf_1=EErf_1)
    g.add_edge('DistEE','ConvEElf',EElf_1=EElf_1)
    
    return g

def findclassification(forwardgraph):
    endclass=1.0
    return endclass