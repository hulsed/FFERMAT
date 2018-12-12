# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:38:34 2018

@author: Daniel Hulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

class importEE:
    def __init__(self):
        self.EEout={'rate': 1.0, 'effort': 1.0}
        self.elecstate=1.0
        self.faultmodes=['infv','lowv','nov']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.EEout['rate']>2:
            self.faults.add('nov')
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['infv'])):
            self.elecstate=np.inf
        elif self.faults.intersection(set(['nov'])):
            self.elecstate=0.0
        elif self.faults.intersection(set(['lowv'])):
            self.elecstate=0.5
    def behavior(self):
        self.EEout['effort']=self.elecstate
    def updatefxn(self,faults=['nom'],inputs={}, outputs={'EE': {'rate': 1.0, 'effort': 1.0}}):
        self.EEout['rate']=outputs
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'EE': self.EEout}
        return {'outputs':outputs, 'inputs':inputs}
    
class importAir:
    def __init__(self):
        self.Airout={'velocity': 1.0, 'turbulence': 1.0}
        self.velstate=1.0
        self.turbstate=1.0
        self.faultmodes=['novel','lowvel','hivel','gusts','flowsep','turb']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['novel'])):
            self.velstate=0
        elif self.faults.intersection(set(['lowvel'])):
            self.velstate=0.5
        elif self.faults.intersection(set(['hivel'])):
            self.velstate=2.0
        
        if self.faults.intersection(set(['gusts', 'flowsep'])):
            self.turbstate=0.5

    def behavior(self):
        self.Airout['velocity']=self.velstate
        self.Airout['turbulence']=self.turbstate
        
    def updatefxn(self,faults=['nom'],inputs={}, outputs={'Air': {'velocity': 1.0, 'turbulence': 1.0}}):
        self.Airout=outputs['Air']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Air': self.Airout}
        return {'outputs':outputs, 'inputs':inputs}
    

class importSignal:
    def __init__(self):
        self.Sigout={'velocity': 1.0, 'turbulence': 1.0}
        self.velstate=1.0
        self.turbstate=1.0
        self.faultmodes=['novel','lowvel','hivel','gusts','flowsep','turb']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['novel'])):
            self.velstate=0
        elif self.faults.intersection(set(['lowvel'])):
            self.velstate=0.5
        elif self.faults.intersection(set(['hivel'])):
            self.velstate=2.0
        
        if self.faults.intersection(set(['gusts', 'flowsep'])):
            self.turbstate=0.5

    def behavior(self):
        self.Airout['velocity']=self.velstate
        self.Airout['turbulence']=self.turbstate
        
    def updatefxn(self,faults=['nom'],inputs={}, outputs={'Air': {'velocity': 1.0, 'turbulence': 1.0}}):
        self.Airout=outputs['Air']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Air': self.Airout}
        return {'outputs':outputs, 'inputs':inputs}
    
    
class affectDOF:
    def __init__(self):
        self.Airout={'velocity': 1.0, 'turbulence': 1.0}
        self.Forceout={'force': 1.0}
        self.Momentout={'amplitude': 1.0, 'intent':1.0 }
        
        self.mechstate=1.0
        self.surfstate=1.0
        self.EEstate=1.0
        self.ctlstate=0.0
        
        self.faultmodes=['surfbreak', 'surfwarp', 'jam','friction','short', 'opencircuit','ctlbreak','ctldrift']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['jam'])):
            self.mechstate=0.0
        elif self.faults.intersection(set(['friction'])):
            self.mechstate=0.5 
            
        if self.faults.intersection(set(['surfbreak'])):
            self.surfstate=0.0
        elif self.faults.intersection(set(['surfwarp'])):
            self.surfstate=0.5
            
        if self.faults.intersection(set(['short','opencircuit'])):
            self.EEstate=0.0
        
        if self.faults.intersection(set(['ctlbreak'])):
            self.ctlstate=0.0
        elif self.faults.intersection(set(['ctldrift'])):
            self.ctlstate=0.5

    def behavior(self):
        self.Airout['turbulence']=self.Airin['turbulence']*self.surfstate
        
        self.Forceout['force']=self.Airin['velocity']*self.mechstate*self.surfstate*self.EEstate
        
        self.Momentout['amplitude']=self.Airin['velocity']*self.mechstate*self.surfstate*self.EEstate
        
        self.Momentout['intent']=self.Sigin['ctl']*self.Airin['velocity']*self.mechstate*self.surfstate*self.EEstate*self.ctlstate
        
    def updatefxn(self,faults=['nom'],inputs={'Signal':{'ctl': 1.0},'EE': {'rate': 1.0, 'effort': 1.0},'Air': {'velocity': 1.0, 'turbulence': 1.0} }, outputs={'Air': {'velocity': 1.0, 'turbulence': 1.0}}):
        self.Airout=outputs['Air']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Air': self.Airout, 'Moment':self.Momentout, 'Force':self.Forceout}
        return {'outputs':outputs, 'inputs':inputs}


#To do: 
#add import signal function
#graph with multiple control surfaces
#functions to combine force, moment, etc
        