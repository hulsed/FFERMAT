# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:30:03 2019

@author: dhulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

#Declare time range to run model over
times=[0,3, 5, 10]

##Define flows for model
class EE:
    def __init__(self,name):
        self.flowtype='EE'
        self.name=name
        self.rate=1.0
        self.effort=1.0
    def status(self):
        status={'rate':self.rate, 'effort':self.effort}
        return status.copy() 

class ME:
    def __init__(self,name):
        self.flowtype='ME'
        self.name=name
        self.rate=1.0
        self.effort=1.0
        self.nominal={'rate':1.0, 'effort':1.0}
    def status(self):
        status={'rate':self.rate, 'effort':self.effort}
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
        self.stab=1.0
        self.vertvel=1.0
        self.planvel=1.0
        self.vertacc=0.0
        self.nominal={'stab':1.0, 'vertvel':1.0, 'planvel':1.0}
    def status(self):
        status={'stab':self.stab, 'vertvel':self.vertvel, 'planvel':self.planvel}
        return status.copy() 
class Land:
    def __init__(self,name):
        self.flowtype='Land'
        self.name=name
        self.status='landed'
        self.area='start'
        self.nominal={'status':'landed', 'area':'start'}
    def status(self):
        status={'status':self.status, 'area':self.area}
        return status.copy() 

class Env:
    def __init__(self,name):
        self.flowtype='Env'
        self.name=name
        self.elev=0.0
        self.x=0.0
        self.y=0.0
        self.start=[0.0,0.0]
        self.start_xw=5
        self.start_yw=5
        self.start_area=aux.square(self.start,self.start_xw, self.start_yw)
        self.flyelev=30
        self.poi_center=[0,150]
        self.poi_xw=50
        self.poi_yw=50
        self.poi_area=aux.square(self.poi_center, self.poi_xw, self.poi_yw)
        self.dang_center=[0,150]
        self.dang_xw=150
        self.dang_yw=150
        self.dang_area=aux.square(self.dang_center, self.dang_xw, self.dang_yw)
        self.safe1_center=[-25,100]
        self.safe1_xw=10
        self.safe1_yw=10
        self.safe1_area=aux.square(self.safe1_center, self.safe1_xw, self.safe1_yw)
        self.safe2_center=[25,50]
        self.safe2_xw=10
        self.safe2_yw=10
        self.safe2_area=aux.square(self.safe2_center, self.safe2_xw, self.safe2_yw)
        self.nominal={'elev':1.0, 'x':1.0, 'y':1.0}
    def status(self):
        status={'elev':self.elev, 'x':self.x, 'y':self.y}
        return status.copy()

class Direc:
    def __init__(self,name):
        self.flowtype='Dir'
        self.name=name
        self.traj=[0,0,0]
        self.power=1
        self.nominal={'x': self.traj[0], 'y': self.traj[1], 'z': self.traj[2], 'power': 1}
    def status(self):
        status={'x': self.traj[0], 'y': self.traj[1], 'z': self.traj[2], 'power': self.power}
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
    def __init__(self,EEin,EEmot,EEctl):
        self.useprop=1.0
        self.type='function'
        self.EEin=EEin
        self.EEmot=EEmot
        self.EEctl=EEctl
        self.effstate=1.0
        self.ratestate=1.0
        self.faultmodes={'short':{'rate':'moderate', 'rcost':'major'}, \
                         'degr':{'rate':'moderate', 'rcost':'minor'}, \
                         'break':{'rate':'common', 'rcost':'moderate'}}
        self.faults=set(['nom'])
    def condfaults(self):
        
        if max(self.EEmot.rate,self.EEctl.rate)>2:
            self.faults.add('nov') 
    def behavior(self, time):
        if self.faults.intersection(set(['short'])):
            self.ratestate=np.inf
            self.effstate=0.0
        elif self.faults.intersection(set(['break'])):
            self.effstate=0.0
        elif self.faults.intersection(set(['degr'])):
            self.effstate=0.5
        self.EEin.rate=self.ratestate*self.EEin.effort
        self.EEmot.effort=self.effstate*self.EEin.effort
        self.EEctl.effort=self.effstate*self.EEin.effort
        
        self.EEin.rate=aux.m2to1([ self.EEin.effort, self.ratestate, max(self.EEmot.rate,self.EEctl.rate)])
        
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.condfaults()
        self.behavior(time)
        return 
    
class affectDOF:
    def __init__(self, name, EEin, Ctlin, DOFout, archtype):
        self.type='function'
        self.EEin=EEin
        self.Ctlin=Ctlin
        self.DOF=DOFout
        self.archtype=archtype
        self.faultmodes={}
        if archtype=='quad':
            LineRF=line('RF')
            LineLF=line('LF')
            LineLR=line('LR')
            LineRR=line('RR')
            self.lines=[LineRF,LineLF,LineLR, LineRR]
        
        for lin in self.lines:
            self.faultmodes.update(lin.faultmodes)  
        self.faults={'nom'}
    def behavior(self, time):
        Air={}
        EEin={}
        #injects faults into lines
        for lin in self.lines:
            for fault in self.faults:
                if fault in lin.faultmodes:
                    lin.faults.update([fault])
            lin.behavior(self.EEin.effort, self.Ctlin.int)
            Air[lin.name]=lin.Airout
            EEin[lin.name]=lin.EE_in
        
        if any(value==np.inf for value in EEin.values()):
            self.EEin.rate=np.inf
        elif any(value!=0.0 for value in EEin.values()):
            self.EEin.rate=np.max(list(EEin.values()))
        else:
            self.EEin.rate=0.0
        
        if all(value==1.0 for value in Air.values()):
            self.DOF.stab=1.0
            self.DOF.vertacc=0.0
        elif all(value==0.0 for value in Air.values()):
            self.DOF.stab=1.0
            self.DOF.vertacc=-1.0
        elif all(value==2.0 for value in Air.values()):
            self.DOF.stab=1.0
            self.DOF.vertacc=1.0
        elif any(value==0.0 for value in Air.values()):
            self.DOF.stab=0.0
            self.DOF.vertacc=-0.5
        elif any(value==2.0 for value in Air.values()):
            self.DOF.stab=0.0
            self.DOF.vertacc=0.5
        #need to expand on this, add directional velocity, etc
        return
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.behavior(time)
        return 

class line:
    def __init__(self, name):
        self.type='component'
        self.name=name 
        self.elecstate=1.0
        self.elecstate_in=1.0
        self.ctlstate=1.0
        self.mechstate=1.0
        self.propstate=1.0
        self.Airout=1.0
        self.faultmodes={name+'short':{'rate':'moderate', 'rcost':'major'}, \
                         name+'openc':{'rate':'moderate', 'rcost':'major'}, \
                         name+'ctlup':{'rate':'moderate', 'rcost':'minor'}, \
                         name+'ctldn':{'rate':'moderate', 'rcost':'minor'}, \
                         name+'ctlbreak':{'rate':'common', 'rcost':'moderate'}, \
                         name+'mechbreak':{'rate':'common', 'rcost':'moderate'}, \
                         name+'mechfriction':{'rate':'common', 'rcost':'moderate'}, \
                         name+'propwarp':{'rate':'veryrare', 'rcost':'replacement'}, \
                         name+'propstuck':{'rate':'veryrare', 'rcost':'replacement'}, \
                         name+'propbreak':{'rate':'veryrare', 'rcost':'replacement'}
                         }
        self.faults=set(['nominal'])
    def behavior(self, EEin, Ctlin):
        if self.faults.intersection(set([self.name+'short'])):
            self.elecstate=0.0
            self.elecstate_in=np.inf
        elif self.faults.intersection(set([self.name+'openc'])):
            self.elecstate=0.0
            self.elecstate_in=0.0
        if self.faults.intersection(set([self.name+'ctlbreak'])):
            self.ctlstate=0.0
        elif self.faults.intersection(set([self.name+'ctldn'])):
            self.ctlstate=0.5
        elif self.faults.intersection(set([self.name+'ctlup'])):
            self.ctlstate=2.0
        if self.faults.intersection(set([self.name+'mechbreak'])):
            self.mechstate=0.0
        elif self.faults.intersection(set([self.name+'mechfriction'])):
            self.mechstate=0.5
            self.elecstate_in=2.0
        if self.faults.intersection(set([self.name+'propstuck'])):
            self.propstate=0.0
            self.mechstate=0.0
            self.elecstate_in=4.0
        elif self.faults.intersection(set([self.name+'propbreak'])):
            self.propstate=0.0
        elif self.faults.intersection(set([self.name+'propwarp'])):
            self.propstate=0.5
        
        self.Airout=aux.m2to1([EEin,self.elecstate,Ctlin,self.ctlstate,self.mechstate,self.propstate])
        self.EE_in=aux.m2to1([EEin,self.elecstate_in])     
    
class ctlDOF:
    def __init__(self, name,EEin, Dir, Ctl, DOFs):
        self.type='classifier'
        self.EEin=EEin
        self.Ctl=Ctl
        self.Dir=Dir
        self.DOFs=DOFs
        self.ctlstate=1.0
        self.faultmodes={'noctl':{'rate':'rare', 'rcost':'high'}, \
                         'degctl':{'rate':'rare', 'rcost':'high'}}
        self.faults=set(['nom'])
    def behavior(self, time):
        if self.faults.intersection(set(['noctl'])):
            self.ctlstate=0.0
        elif self.faults.intersection(set(['degctl'])):
            self.ctlstate=0.5
        
        upthrottle=1.0
        if self.Dir.traj[2]>=1:
            upthrottle=2.0
        elif self.Dir.traj[2]==0:
            upthrottle=1.0
        elif self.Dir.traj[2]<=1:
            upthrottle=0.5
            
        if self.Dir.traj[0]==0 and self.Dir.traj[1]==0:
            forwardthrottle=1.0
        else:
            forwardthrottle=2.0
        
        pwr=self.Dir.power
        self.Ctl.int=upthrottle*forwardthrottle*pwr
        self.Ctl.act=self.EEin.effort*self.ctlstate*upthrottle*forwardthrottle*pwr

    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.behavior(time)

class planpath:
    def __init__(self, name,EEin, Env, Dir):
        self.type='function'
        self.EEin=EEin
        self.Env=Env
        self.Dir=Dir

        self.faultmodes={'noloc':{'rate':'rare', 'rcost':'high'}, \
                         'degloc':{'rate':'rare', 'rcost':'high'}}
        self.faults=set(['nom'])
    def behavior(self, t):
        
        if t>40:
            self.Dir.power=0
        elif t<1:
            self.Dir.power=0
        else:
            self.Dir.power=1

        if t>=30:
            self.Dir.traj=[0,0,-1]
        elif t>=20:
            self.Dir.traj=[0,-1,0]
        elif t>=10:
            self.Dir.traj=[0,1,0]
        elif t>=0:
            self.Dir.traj=[0,0,1]
            
        if self.faults.intersection(set(['noloc'])):
            self.Dir.traj=[0,0,0]
        elif self.faults.intersection(set(['degloc'])):
            self.Dir.traj=[0,0,-1]
        if self.EEin.effort<0.5:
            self.Dir.power=0.0
            self.Dir.traj=[0,0,0]
        
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        self.faults.update(faults)
        self.behavior(time)

class trajectory:
    def __init__(self, name, Env, DOF, Land, Dir):
        self.type='dynamics'
        self.Env=Env
        self.DOF=DOF
        self.Land=Land
        self.Dir=Dir
        self.lasttime=0
        self.faultmodes={'nom':{'rate':'common', 'rcost':'NA'}}
        self.faults=set(['nom'])
    def condfaults(self):
        if self.Env.elev<=0:
            if  self.DOF.vertvel>5:
                self.Land.status='majorcrash'
            elif self.DOF.planvel>5:
                self.Land.status='majorcrash'
            elif self.DOF.stab<0.5:
                self.Land.status='minorcrash'
            else:
                self.Land.status='landed'
            
            if  aux.inrange(self.Env.start_area, self.Env.x, self.Env.y):
                self.Land.area='nominal'
            elif aux.inrange(self.Env.safe1_area, self.Env.x, self.Env.y) or aux.inrange(self.Env.safe2_area, self.Env.x, self.Env.y):
                self.Land.area='nonnominal_safe'
            elif aux.inrange(self.Env.dang_area, self.Env.x, self.Env.y):
                self.Land.area='nonnominal_dangerous'
            else:
                self.Land.area='nonnominal_unsanctioned'
        else:
            self.Land.status='flying'
            self.Land.area='NA'
    def behavior(self):
        if self.DOF.stab<0.5:
            self.DOF.vertvel=-10
            self.DOF.planvel=3
        
        self.Env.elev=self.Env.elev+self.DOF.vertvel
        self.Env.x=self.Env.x*self.DOF.planvel*self.Dir.traj[0]
        self.Env.y=self.Env.y*self.DOF.planvel*self.Dir.traj[1]
    def updatefxn(self,faults=['nom'],opermode=[], time=0):
        if time>self.lasttime:
            self.behavior()
            self.lasttime=time
        self.condfaults()

##future: try to automate this part so you don't have to do it in a wierd order
def initialize():
    
    #initialize graph
    g=nx.DiGraph()
    
    EE_1=EE('EE_1')
    StoreEE=storeEE('StoreEE',EE_1)
    g.add_node('StoreEE', obj=StoreEE)
    
    EEmot=EE('EEmot')
    EEctl=EE('EEctl')
    
    DistEE=distEE(EE_1,EEmot,EEctl)
    g.add_node('DistEE', obj=DistEE)
    g.add_edge('StoreEE','DistEE', EE_1=EE_1)
    
    Ctl1=Sig('Ctl1')
    DOFs=DOF('DOFs')
    
    AffectDOF=affectDOF('AffectDOF',EEmot,Ctl1,DOFs,'quad')
    g.add_node('AffectDOF', obj=AffectDOF)
    Dir1=Direc('Dir1')
    CtlDOF=ctlDOF('CtlDOF',EEctl, Dir1, Ctl1, DOFs)
    g.add_node('CtlDOF', obj=CtlDOF)
    g.add_edge('DistEE','AffectDOF', EEmot=EEmot)
    g.add_edge('DistEE','CtlDOF', EEctl=EEctl)
    g.add_edge('CtlDOF','AffectDOF', Ctl1=Ctl1,DOFs=DOFs)

    Env1=Env('Env1')
    Planpath=planpath('Planpath',EEctl, Env1,Dir1)
    g.add_node('Planpath', obj=Planpath)
    g.add_edge('DistEE','Planpath', EEctl=EEctl)
    g.add_edge('Planpath','CtlDOF', Dir1=Dir1)
    
    Land1=Land('Land')
    Trajectory=trajectory('Trajectory',Env1,DOFs,Land1,Dir1)
    g.add_node('Trajectory', obj=Trajectory)
    g.add_edge('Trajectory','AffectDOF',DOFs=DOFs)
    g.add_edge('Planpath', 'Trajectory', Dir1=Dir1, Env1=Env1)
    
    return g

#def environment(DOF,t):
#    if DOF.stab
    
def findclassification(g):
    
    #need to add means of giving fault
    #Trajectory.Land.status=1.0
    #Trajectory.Land.status=1.0
    
#    if Trajectory.Land.status=='majorcrash':
#        land=1000
#    elif Trajectory.Land.status=='minorcrash':
#        land= 200
#    elif Trajectory.Land.status=='minorcrash':
#        land=1
#    else:
#        land=np.nan
#    
#    if Trajectory.Land.area=='nominal':
#        area=1
#    elif Trajectory.Land.area=='nonnominal_safe':
#        area=10
#    elif Trajectory.Land.area=='nonnominal_dangerous':
#        area=100
#    elif Trajectory.Land.area=='nonnominal_unsanctioned':
#        area=30
#    else:
#        area=np.nan
        
    land=1
    area=1
    endclass=land*area
    
    
    return endclass