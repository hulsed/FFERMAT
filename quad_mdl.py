# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:30:03 2019

@author: dhulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

##Define flows for model
class EE:
    def __init__(self,name):
        self.flowtype='EE'
        self.name=name
        self.rate=1.0
        self.effort=1.0
        self.int=1.0
        self.act=1.0
        self.nominal={'rate':1.0, 'effort':1.0,'int':1.0, 'act':1.0}
    def status(self):
        status={'rate':self.rate, 'effort':self.effort, 'int':1.0, 'act': 1.0}
        return status.copy() 

class ME:
    def __init__(self,name):
        self.flowtype='ME'
        self.name=name
        self.rate=1.0
        self.effort=1.0
        self.int=1.0
        self.act=1.0
        self.nominal={'rate':1.0, 'effort':1.0,'int':1.0, 'act':1.0}
    def status(self):
        status={'rate':self.rate, 'effort':self.effort, 'int':1.0, 'act': 1.0}
        return status.copy() 
class Air:
    def __init__(self,name):
        self.flowtype='ME'
        self.name=name
        self.rate=1.0
        self.effort=1.0
        self.int=1.0
        self.act=1.0
        self.nominal={'rate':1.0, 'effort':1.0,'int':1.0, 'act':1.0}
    def status(self):
        status={'rate':self.rate, 'effort':self.effort, 'int':1.0, 'act': 1.0}
        return status.copy() 

class Sig:
    def __init__(self,name):
        self.flowtype='Sig'
        self.name=name
        self.int=1.0
        self.act=1.0
        self.nominal={'int':1.0, 'act':1.0}
    def status(self):
        status={'int':self.int, 'act':self.act}
        return status.copy() 

class DOF:
    def __init__(self,name):
        self.flowtype='DOF'
        self.name=name
        self.elev=1.0
        self.stab=1.0
        self.vertvel=1.0
        self.planvel=1.0
        self.nominal={'elev':1.0, 'stab':1.0, 'vertvel':1.0, 'planvel':1.0}
    def status(self):
        status={'elev':self.elev, 'stab':self.stab, 'vertvel':self.vertvel, 'planvel':self.planvel}
        return status.copy() 

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
    
class contEE:
    def __init__(self, name, EEin, EEout,Sigin):
        self.type='function'
        self.EEin=EEin
        self.EEout=EEout
        self.Sigin=Sigin
        self.elecstate=1.0
        self.faultmodes={'short':{'rate':'moderate', 'rcost':'major'}, \
                         'degup':{'rate':'moderate', 'rcost':'minor'}, \
                         'degdn':{'rate':'moderate', 'rcost':'minor'}, \
                         'break':{'rate':'common', 'rcost':'moderate'}, \
                         'failup':{'rate':'moderate', 'rcost':'minor'}, \
                         'faildn':{'rate':'moderate', 'rcost':'minor'}
                         }
        self.faults=set(['nom'])
    def condfaults(self):
        if self.EEout.rate>2:
            self.faults.add('break')
            self.faults.add('faildn')
    def behavior(self):
        if self.faults.intersection(set(['short'])):
            self.EEin.rate=np.inf
            self.EEout.effort=0.0
            self.EEout.act=0.0
        elif self.faults.intersection(set(['break'])):
            self.EEin.rate=0.0
            self.EEout.effort=0.0
            self.EEout.act=0.0
        elif self.faults.intersection(set(['degr'])):
            self.EEout.effort=0.5
            self.EEout.act=0.5
        elif self.faults.intersection(set(['failup'])):
            self.EEout.act=np.inf
        elif self.faults.intersection(set(['faildn'])):
            self.EEout.act=0.0
        elif self.faults.intersection(set(['degup'])):
            self.EEout.act=2.0
        elif self.faults.intersection(set(['degdn'])):
            self.EEout.act=0.5
        else:
            self.EEin.rate=self.EEout.rate
            self.EEout.act=self.Sigin.act
        self.EEout.int=self.Sigin.int
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior()
        return 

class convEEtoME:
    def __init__(self, name, EEin, MEout,Sigout):
        self.type='function'
        self.EEin=EEin
        self.MEout=MEout
        self.Sigout=Sigout
        self.elecstate=1.0
        self.mechstate=1.0
        self.ctlstate=1.0
        self.faultmodes={
                         'friction':{'rate':'moderate', 'rcost':'replacement'},\
                         'short':{'rate':'rare', 'rcost':'minor'}, \
                         'openc':{'rate':'veryrare', 'rcost':'replacement'}, \
                         'break':{'rate':'rare', 'rcost':'replacement'}, \
                         'drift':{'rate':'veryrare', 'rcost':'replacement'}}
        self.faults=set(['nom'])
    def condfaults(self):
        if self.EEin.rate>2:
            self.faults.add('break')
            self.faults.add('faildn')
    def behavior(self):
        if self.faults.intersection(set(['short'])):
            self.elecstate=np.inf
            self.mechstate=0.0
            self.ctlstate=0.0
        elif self.faults.intersection(set(['break'])):
            self.mechstate=0.0
            self.ctlstate=0.0
        elif self.faults.intersection(set(['openc'])):
            self.elecstate=0.0
            self.ctlstate=0.0
        elif self.faults.intersection(set(['friction'])):
            self.mechstate=0.5
            self.ctlstate=0.5
        elif self.faults.intersection(set(['drift'])):
            self.ctlstate=0.5

        self.MEout.effort=aux.m2to1([self.EEin.effort,self.mechstate,self.ctlstate])
        self.MEout.act=aux.m2to1([self.EEin.act,self.elecstate,self.mechstate,self.ctlstate])
        self.MEout.int=self.EEin.int
        self.EEin.rate=aux.m2to1([self.elecstate, self.MEout.rate])
        self.Sigout.act=aux.m2to1([self.elecstate, self.MEout.act, self.ctlstate])
        self.Sigout.int=self.EEin.int
        
            
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior()
        return 
    
class convMEtoAir:
    def __init__(self, name, MEin, Airout):
        self.type='function'
        self.MEin=MEin
        self.Airout=Airout
        self.mechstate=1.0
        self.faultmodes={'break':{'rate':'rare', 'rcost':'replacement'}, \
                         'warp':{'rate':'veryrare', 'rcost':'replacement'}}
        self.faults=set(['nom'])
    def behavior(self):
        if self.faults.intersection(set(['break'])):
            self.mechstate=0.5
        elif self.faults.intersection(set(['warp'])):
            self.mechstate=1.5
        
        self.MEin.rate=self.MEin.effort/self.mechstate
        self.Airout.effort=self.MEin.rate*self.MEin.effort
        self.Airout.rate=self.MEin.rate
        self.Airout.int=self.MEin.int
        self.Airout.act=self.Airout.effort*self.MEin.act

    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.behavior()
        return 

class affectDOF:
    def __init__(self, name, Airrr, Airlr, Airrf, Airlf, DOFs):
        self.type='classifier'
        self.Airrr=Airrr
        self.Airlr=Airlr
        self.Airrf=Airrf
        self.Airlf=Airlf
        self.DOFs=DOFs
        self.faultmodes={'nom':{'rate':'common', 'rcost':'NA'}}
        self.faults=set(['nom'])
    def behavior(self, time):
        self.elev=1.0
        self.stab=1.0
        self.vertvel=1.0
        self.planvel=1.0
        if 0.5 in [self.Airrr.rate,self.Airlr.rate,self.Airrf.rate,self.Airlf.rate]:
            self.DOFs.stab=0.5
            self.vertvel=-2
        elif 0.0 in [self.Airrr.rate,self.Airlr.rate,self.Airrf.rate,self.Airlf.rate]:
            self.DOFs.stab=0.5
            self.vertvel=-10
        elif 2.0:
            self.DOFs.stab=2.0
            self.vertvel=2.0
        
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.behavior(time)
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
    
    Sigrr_1=Sig('Sigrr_1')
    Siglr_1=Sig('Siglr_1')
    Sigrf_1=Sig('Sigrf_1')
    Siglf_1=Sig('Siglf_1')
    
    Sigrr_2=Sig('Sigrr_2')
    Siglr_2=Sig('Siglr_2')
    Sigrf_2=Sig('Sigrf_2')
    Siglf_2=Sig('Siglf_2')
    
    EErr_3=EE('EErr_3')
    EElr_3=EE('EElr_3')
    EErf_3=EE('EErf_3')
    EElf_3=EE('EElf_3')
    
    ContEErr=contEE('ContEErr',EErr_2,EErr_3,Sigrr_1)
    g.add_node('ContEErr', obj=ContEErr)
    ContEElr=contEE('ContEElr',EElr_2,EElr_3,Siglr_1)
    g.add_node('ContEElr', obj=ContEElr)
    ContEErf=contEE('ContEErf',EErf_2,EErf_3,Sigrf_1)
    g.add_node('ContEErf', obj=ContEErf)
    ContEElf=contEE('ContEElf',EElf_2,EElf_3,Siglf_1)
    g.add_node('ContEElf', obj=ContEElf)
    
    g.add_edge('ConvEErr','ContEErr',EErr_2=EErr_2)
    g.add_edge('ConvEElr','ContEElr',EElr_2=EElr_2)
    g.add_edge('ConvEErf','ContEErf',EErf_2=EErf_2)
    g.add_edge('ConvEElf','ContEElf',EElf_2=EElf_2)
    
    MErr=ME('MErr')
    MElr=ME('MElr')
    MErf=ME('MErf')
    MElf=ME('MElf')
    
    ConvEEtoMErr=convEEtoME('ConvEEtoMErr', EErr_3, MErr, Sigrr_2)
    g.add_node('ConvEEtoMErr', obj=ConvEEtoMErr)
    ConvEEtoMElr=convEEtoME('ConvEEtoMElr', EElr_3, MElr, Siglr_2)
    g.add_node('ConvEEtoMElr', obj=ConvEEtoMElr)
    ConvEEtoMErf=convEEtoME('ConvEEtoMErf', EErf_3, MErf, Sigrf_2)
    g.add_node('ConvEEtoMErf', obj=ConvEEtoMErf)
    ConvEEtoMElf=convEEtoME('ConvEEtoMElf', EElf_3, MElf, Siglf_2)
    g.add_node('ConvEEtoMElf', obj=ConvEEtoMElf)
    
    g.add_edge('ContEErr', 'ConvEEtoMErr', EErr_3=EErr_3)
    g.add_edge('ContEElr', 'ConvEEtoMElr', EElr_3=EElr_3)
    g.add_edge('ContEErf', 'ConvEEtoMErf', EErr_3=EErf_3)
    g.add_edge('ContEElf', 'ConvEEtoMElf', EElf_3=EElf_3)
    
    Airrr=Air('Airrr')
    Airlr=Air('Airlr')
    Airrf=Air('Airrf')
    Airlf=Air('Airlf')
    
    ConvMEtoAirrr=convMEtoAir('ConvMEtoAirrr', MErr, Airrr)
    g.add_node('ConvMEtoAirrr', obj=ConvMEtoAirrr)
    ConvMEtoAirlr=convMEtoAir('ConvMEtoAirlr', MElr, Airlr)
    g.add_node('ConvMEtoAirlr', obj=ConvMEtoAirlr)
    ConvMEtoAirrf=convMEtoAir('ConvMEtoAirrf', MErf, Airrf)
    g.add_node('ConvMEtoAirrf', obj=ConvMEtoAirrf)
    ConvMEtoAirlf=convMEtoAir('ConvMEtoAirlf', MElf, Airlf)
    g.add_node('ConvMEtoAirlf', obj=ConvMEtoAirlf)
    
    g.add_edge('ConvEEtoMErr','ConvMEtoAirrr',MErr=MErr)
    g.add_edge('ConvEEtoMElr','ConvMEtoAirlr',MElr=MElr)
    g.add_edge('ConvEEtoMErf','ConvMEtoAirrf',MErf=MErf)
    g.add_edge('ConvEEtoMElf','ConvMEtoAirlf',MElf=MElf)
    
    DOFs=DOF('DOFs')
    AffectDOF=affectDOF('AffectDOF',Airrr,Airlf,Airrf,Airlf,DOFs)
    g.add_node('AffectDOF',obj=AffectDOF)
    
    g.add_edge('ConvMEtoAirrr','AffectDOF', Airrr=Airrr)
    g.add_edge('ConvMEtoAirlr','AffectDOF',Airlr=Airlr)
    g.add_edge('ConvMEtoAirrf', 'AffectDOF', Airrf=Airrf)
    g.add_edge('ConvMEtoAirlf', 'AffectDOF', Airlf=Airlf)
    
    
    return g

def findclassification(forwardgraph):
    endclass=1.0
    return endclass