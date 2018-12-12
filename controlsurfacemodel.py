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
        self.Sigout={'ctl': 1.0},
        self.sigstate=1.0
        self.faultmodes=['nosig','degsig']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        
        if self.Sigout['ctl']>2.0:
            self.faults.update(['nosig'])
        
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['nosig'])):
            self.sigstate=0
        elif self.faults.intersection(set(['degsig'])):
            self.sigstate=0.5
        
    def behavior(self):
        self.Sigout['ctl']=self.sigstate
        
    def updatefxn(self,faults=['nom'],inputs={}, outputs={'Signal': {'ctl': 1.0}}):
        self.Sigout=outputs['Signal']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'Signal': {'ctl': 1.0}}
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
            
        if self.faults.intersection(set(['short'])):
            self.EEstate=0.0
            self.Sigin['ctl']=0.0
        elif self.faults.intersection(set(['opencircuit'])):
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
        
    def updatefxn(self,faults=['nom'],inputs={'Signal':{'ctl': 1.0},'EE': {'rate': 1.0, 'effort': 1.0},'Air': {'velocity': 1.0, 'turbulence': 1.0} }, outputs={'Force':{'force':1.0}, 'Moment':{'amplitude': 1.0, 'intent':1.0 }, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}):
        self.Airin=inputs['Air']
        self.EEin=inputs['EE']
        self.Sigin=inputs['Signal']
        self.Airout=outputs['Air']
        self.Momentout=outputs['Moment']
        self.Forceout=outputs['Force']

        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Signal': self.Sigin, 'EE': self.EEin, 'Air':self.Airin}
        outputs={'Air': self.Airout, 'Moment':self.Momentout, 'Force':self.Forceout}
        return {'outputs':outputs, 'inputs':inputs}
    
class combineforceandmoment:
    def __init__(self):
        self.ForceLin={'force': 1.0}
        self.ForceRin={'force': 1.0}
        self.MomentLin={'amplitude': 1.0, 'intent':1.0 }
        self.MomentRin={'amplitude': 1.0, 'intent':1.0 }
        
        self.structstateL=1.0
        self.structstateR=1.0
        
        self.faultmodes=['breakL','breakR','damageL','damageR']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.ForceLin['force']>2.0 or self.MomentLin['amplitude']>2.0 :
            self.faults.update(['breakL'])
        elif self.ForceLin['force']>1.5 or self.MomentLin['amplitude']>1.5:
            self.faults.update(['damageL'])    
        
        if self.ForceRin['force']>2.0:
            self.faults.update(['breakR'] or self.MomentRin['amplitude']>2.0)
        elif self.ForceRin['force']>1.5:
            self.faults.update(['damageR']  or self.MomentRin['amplitude']>2.0) 
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['breakL'])):
            self.structstateL=0.0
        if self.faults.intersection(set(['breakR'])):
            self.structstateR=0.0
    def behavior(self):
        self.Forceout['force']=.5*(self.structstateL*self.ForceLin['force']+self.structstateR*self.ForceRin['force'])
        
        self.Momentout['amplitude']=.5*(self.structstateL*self.MomentLin['amplitude']+self.structstateR*self.MomentRin['amplitude'])
        
        
        self.ForceLin['force']=self.structstateL*self.ForceLin['force']
        self.ForceRin['force']=self.structstateR*self.ForceRin['force']
        self.MomentLin['amplitude']=self.structstateL*self.MomentLin['amplitude']
        self.MomentRin['amplitude']=self.structstateR*self.MomentRin['amplitude']        
    def updatefxn(self,faults=['nom'],inputs={'Force_L':{'force': 1.0},'Force_R':{'force': 1.0}, 'Moment_R':{'amplitude': 1.0, 'intent':1.0 }, 'Moment_L':{'amplitude': 1.0, 'intent':1.0 } }, outputs={'Force': {'force': 1.0}, 'Moment':{'amplitude': 1.0, 'intent':1.0 }}):
        self.ForceRin=inputs['Force_R']
        self.ForceLin=inputs['Force_L']
        self.Forceout=outputs['Force']
        self.MomentRin=inputs['Moment_R']
        self.MomentLin=inputs['Moment_L']
        self.Momentout=outputs['Moment']
        
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Force_L': self.ForceLin, 'Force_R': self.ForceRin}
        outputs={'Force':self.Forceout}
        return {'outputs':outputs, 'inputs':inputs} 

    
class combinemoment:
    def __init__(self):
        self.MomentLin={'amplitude': 1.0, 'intent':1.0 }
        self.MomentRin={'amplitude': 1.0, 'intent':1.0 }
        
        self.structstateL=1.0
        self.structstateR=1.0
        
        self.faultmodes=['breakL','breakR','damageL','damageR']
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.MomentLin['force']>2.0 or self.MomentRin['force']>2.0:
            self.faults.update(['break'])
        elif self.MomentLin['force']>1.5 or self.MomentRin['force']>1.5:
            self.faults.update(['damage'])    
        
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['break'])):
            self.structstate=0.0

    def behavior(self):
        self.Forceout['force']=self.structstate*0.5*(self.Momentin['force']+self.Momentin['force'])
        
    def updatefxn(self,faults=['nom'],inputs={'MomentL':{'amplitude': 1.0, 'intent':1.0 },'MomentR':{'amplitude': 1.0, 'intent':1.0 }}, outputs={'Moment':{'amplitude': 1.0, 'intent':1.0 }}):
        self.ForceLin=inputs['Force_L']
        self.ForceRin=inputs['Force_R']
        self.Forceout=outputs['Force']

        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Force_L': self.ForceLin, 'Force_R': self.ForceRin}
        outputs={'Force':self.Forceout}
        return {'outputs':outputs, 'inputs':inputs} 

#To do: 
#add import signal function
#graph with multiple control surfaces
#functions to combine force, moment, etc
        