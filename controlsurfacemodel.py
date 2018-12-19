# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:38:34 2018

@author: Daniel Hulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

#costs of various end-states to be used
endstatekey={'noeffect': {'pfh_allow': 0, 'cost': 0, 'repair':'NA' },\
             'minor': {'pfh_allow': 1e-3, 'cost': 0.118e7, 'repair':'minor'},\
             'major': {'pfh_allow': 1e-5, 'cost': 2.98e7, 'repair':'moderate' } , \
             'hazardous': {'pfh_allow': 1e-6, 'cost': 16.8e7, 'repair':'major' } , \
             'catastrophic': {'pfh_allow': 1e-7, 'cost': 38.4e7, 'repair':'totaled' } }

#subjective lifecycle probabilities for various faults
lifecycleprob={'veryhigh':{'lb': 0.2, 'ub': 1.0 }, \
               'high':{'lb': 0.05, 'ub': 0.19}, \
               'moderate': {'lb': 0.049, 'ub':0.0005}, \
               'low': {'lb':1.5/1e5, 'ub':0.00049}, \
               'remote': {'lb':0, 'ub':1.49/1e5}}
# see scenario-based FMEA paper http://www.medicalhealthcarefmea.com/papers/kmenta.pdf

# repair costs for 
repaircosts={'totaled':{'lb': 100000, 'ub': 200000}, \
             'major':{'lb':40000, 'ub': 100000}, \
             'moderate':{'lb':5000, 'ub': 40000}, \
             'minor':{'lb':1000 ,'ub': 5000}, \
             'replacement':{'lb':100, 'ub': 1000}, \
             'NA':{'lb':0, 'ub': 0} }

class importEE:
    def __init__(self):
        self.type='function'
        self.EEout={'rate': 1.0, 'effort': 1.0}
        self.elecstate=1.0
        self.faultmodes={'infv':{'lprob':'moderate', 'rcost':'major'}, \
                         'lowv':{'lprob':'moderate', 'rcost':'minor'}, \
                         'nov':{'lprob':'high', 'rcost':'moderate'}}
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
        self.EEout['rate']=outputs['EE']['rate']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        outputs={'EE': self.EEout}
        return {'outputs':outputs, 'inputs':inputs}
    
class importAir:
    def __init__(self):
        self.type='function'
        self.Airout={'velocity': 1.0, 'turbulence': 1.0}
        self.velstate=1.0
        self.turbstate=1.0
        self.faultmodes={'novel': {'lprob':'low', 'rcost':'NA'},
                         'lowvel': {'lprob':'moderate', 'rcost':'NA'},\
                         'hivel': {'lprob':'moderate', 'rcost':'NA'},\
                         'gusts': {'lprob':'veryhigh', 'rcost':'NA'},\
                         'flowsep': {'lprob':'moderate', 'rcost':'NA'},\
                         'turb': {'lprob':'high', 'rcost':'NA'}}
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
        self.type='function'
        self.Sigout={'ctl': 1.0},
        self.sigstate=1.0
        self.faultmodes={'nosig':{'lprob':'low' , 'rcost':'NA'},\
                         'degsig':{'lprob':'low', 'rcost':'NA'}}
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
        outputs=self.Sigout
        return {'outputs':outputs, 'inputs':inputs}
    
    
class affectDOF:
    def __init__(self, dof, side):
        self.type='function'
        self.Airout={'velocity': 1.0, 'turbulence': 1.0}
        self.Forceout={'force': 1.0}
        self.Momentout={'amplitude': 1.0, 'intent':1.0 }
        
        self.mechstate=1.0
        self.surfstate=1.0
        self.EEstate=1.0
        self.ctlstate=1.0
        
        self.faultmodes={'surfbreak':{'lprob':'remote', 'rcost':'replacement'}, \
                         'surfwarp':{'lprob':'low', 'rcost':'replacement'}, \
                         'jamcl':{'lprob':'low', 'rcost':'minor'}, \
                         'jamopen':{'lprob':'low', 'rcost':'minor'}, \
                         'friction':{'lprob':'moderate', 'rcost':'replacement'},\
                         'short':{'lprob':'low', 'rcost':'minor'}, \
                         'opencircuit':{'lprob':'low', 'rcost':'replacement'}, \
                         'ctlbreak':{'lprob':'remote', 'rcost':'replacement'}, \
                         'ctldrift':{'lprob':'low', 'rcost':'replacement'}}
        self.faults=set(['nom'])
        
        self.dof=dof
        self.side=side
        
        if side=='C':
            self.forcename='Force'+dof+side
            self.momentname=dof      
        else:
            self.forcename='Force'+dof+side
            self.momentname='Moment'+dof+side
        
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.EEin['effort']>2.0:
            self.faults.add('opencircuit')
        return 0
    def detbehav(self):
        if  self.faults.intersection(set(['jamopen'])):
            self.mechstate=2.0
        elif self.faults.intersection(set(['jamcl'])):
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
            self.EEin['rate']=np.inf
        elif self.faults.intersection(set(['opencircuit'])):
            self.EEstate=0.0
            self.EEin['rate']=0
        else:
            self.EEin['rate']=self.EEin['effort']*self.EEstate
        
        if self.faults.intersection(set(['ctlbreak'])):
            self.ctlstate=0.0
        elif self.faults.intersection(set(['ctldrift'])):
            self.ctlstate=0.5

    def behavior(self):
        self.Airout['turbulence']=self.Airin['turbulence']*self.surfstate
        
        self.Forceout['force']=self.Airin['velocity']*self.mechstate*self.surfstate*self.EEstate
        
        self.Momentout['amplitude']=self.Airin['velocity']*self.EEin['effort']*self.mechstate*self.surfstate*self.EEstate
        
        self.Momentout['intent']=self.Sigin['ctl']*self.Airin['velocity']*self.EEin['effort']*aux.dev(self.mechstate)*self.surfstate*self.EEstate*self.ctlstate
        
        
    def updatefxn(self,faults=['nom'],inputs={'Signal':{'ctl': 1.0},'EE': {'rate': 1.0, 'effort': 1.0},'Air': {'velocity': 1.0, 'turbulence': 1.0} }, outputs={}):
        
        if len(outputs)==0:
            if self.side=='c' or self.side=='C':
                outputs={ self.momentname:{'amplitude': 1.0, 'intent':1.0 }, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}
            else:
                outputs={self.forcename:{'force':1.0}, self.momentname:{'amplitude': 1.0, 'intent':1.0 }, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}
                self.Forceout=outputs[self.forcename]
        self.Airin=inputs['Air']
        self.EEin=inputs['EE']
        self.Sigin=inputs['Signal']
        self.Airout=outputs['Air']
        self.Momentout=outputs[self.momentname]
        

        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Signal': self.Sigin, 'EE': self.EEin, 'Air':self.Airin}
        if self.side=='c' or self.side=='C':
            outputs={'Air': self.Airout, self.momentname:self.Momentout}
        else:
            outputs={'Air': self.Airout, self.momentname:self.Momentout, self.forcename:self.Forceout}
        return {'outputs':outputs, 'inputs':inputs}
    
class combineforceandmoment:
    def __init__(self,dof):
        self.type='function'
        self.ForceLin={'force': 1.0}
        self.ForceRin={'force': 1.0}
        self.MomentLin={'amplitude': 1.0, 'intent':1.0 }
        self.MomentRin={'amplitude': 1.0, 'intent':1.0 }

        self.Forceout={'force': 1.0}
        self.Momentout={'amplitude': 1.0, 'intent':1.0 }
        
        self.structstateL=1.0
        self.structstateR=1.0
        
        self.dof=dof
        
        self.faultmodes={'breakL':{'lprob':'remote', 'rcost':'moderate'}, \
                         'breakR':{'lprob':'remote', 'rcost':'moderate'}, \
                         'damageL':{'lprob':'low', 'rcost':'moderate'},\
                         'damageR':{'lprob':'low', 'rcost':'moderate'}}
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
        self.Momentout['intent']=.5*(self.MomentLin['amplitude']+self.MomentRin['amplitude'])
        
        #self.ForceLin['force']=self.structstateL*self.ForceLin['force']
        #self.ForceRin['force']=self.structstateR*self.ForceRin['force']
        #self.MomentLin['amplitude']=self.structstateL*self.MomentLin['amplitude']
        #self.MomentRin['amplitude']=self.structstateR*self.MomentRin['amplitude']        
    def updatefxn(self,faults=['nom'], inputs={}, outputs={}):
        
        if len(inputs)==0:
            inputs={'Force'+self.dof+'L':{'force': 1.0},'Force'+self.dof+'R':{'force': 1.0}, 'Moment'+self.dof+'R':{'amplitude': 1.0, 'intent':1.0 }, 'Moment'+self.dof+'L':{'amplitude': 1.0, 'intent':1.0 } }
        if len(outputs)==0:
            outputs={ self.dof:{'amplitude': 1.0, 'intent':1.0 }}
            
        
        self.ForceRin=inputs['Force'+self.dof+'R']
        self.ForceLin=inputs['Force'+self.dof+'L']
        #self.Forceout=outputs['Force']
        self.MomentRin=inputs['Moment'+self.dof+'R']
        self.MomentLin=inputs['Moment'+self.dof+'L']
        self.Momentout=outputs[self.dof]
        
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Force'+self.dof+'L': self.ForceLin, 'Force'+self.dof+'R': self.ForceRin, 'Moment'+self.dof+'R': self.MomentRin, 'Moment'+self.dof+'L':self.MomentLin}
        outputs={self.dof:self.Momentout}
        return {'outputs':outputs, 'inputs':inputs} 

    
#class combinemoment:
#    def __init__(self):
#        self.MomentLin={'amplitude': 1.0, 'intent':1.0 }
#        self.MomentRin={'amplitude': 1.0, 'intent':1.0 }
#        
#        self.structstateL=1.0
#        self.structstateR=1.0
#        
#        self.faultmodes=['breakL','breakR','damageL','damageR']
#        self.faults=set(['nom'])
#    def resolvefaults(self):
#        return 0
#    def condfaults(self):
#        if self.MomentLin['force']>2.0 or self.MomentRin['force']>2.0:
#            self.faults.update(['break'])
#        elif self.MomentLin['force']>1.5 or self.MomentRin['force']>1.5:
#            self.faults.update(['damage'])    
#        
#        return 0
#    def detbehav(self):
#        if self.faults.intersection(set(['break'])):
#            self.structstate=0.0
#
#    def behavior(self):
#        self.Forceout['force']=self.structstate*0.5*(self.Momentin['force']+self.Momentin['force'])
#        
#    def updatefxn(self,faults=['nom'],inputs={'MomentL':{'amplitude': 1.0, 'intent':1.0 },'MomentR':{'amplitude': 1.0, 'intent':1.0 }}, outputs={'Moment':{'amplitude': 1.0, 'intent':1.0 }}):
#        self.ForceLin=inputs['Force_L']
#        self.ForceRin=inputs['Force_R']
#        self.Forceout=outputs['Force']
#
#        self.faults.update(faults)
#        self.condfaults()
#        self.resolvefaults()
#        self.detbehav()
#        self.behavior()
#        inputs={'Force_L': self.ForceLin, 'Force_R': self.ForceRin}
#        outputs={'Force':self.Forceout}
#        return {'outputs':outputs, 'inputs':inputs} 
    
class export6dof:
    def __init__(self):
        self.Roll={'amplitude': 1.0, 'intent':1.0 }
        self.Pitch={'amplitude': 1.0, 'intent':1.0 }
        self.Yaw={'amplitude': 1.0, 'intent':1.0 }
        self.type='classifier'
        
        self.Severity={'noeffect'}
        self.faultmodes={}
        self.faults=set(['nom'])
    def classify(self):
        if self.Roll['intent']==0 or self.Pitch['intent']==0 or self.Yaw['intent']==0 or self.Roll['amplitude']==0:
            self.Severity='catastrophic'
        elif self.Roll['intent']!=1 or self.Pitch['intent']!=1 or self.Yaw['intent']!=1:
            self.Severity='hazardous'
        elif self.Roll['amplitude']!=1 or self.Pitch['amplitude']!=1 or self.Yaw['amplitude']!=1:
            self.Severity='major'
        else:
            self.Severity='noeffect'
        
    def returnvalue(self):
        return self.Severity
    
    def updatefxn(self,faults=['nom'],inputs={'roll':{'amplitude': 1.0, 'intent':1.0 }, 'pitch':{'amplitude': 1.0, 'intent':1.0 }, 'yaw':{'amplitude': 1.0, 'intent':1.0 } }, outputs={}):
        self.Roll=inputs['roll']
        self.Pitch=inputs['pitch']
        self.Yaw=inputs['yaw']
        
        self.classify()
        
        inputs={'Roll': self.Roll, 'Pitch': self.Pitch, 'Yaw': self.Yaw}
        outputs={}
        return {'outputs':outputs, 'inputs':inputs} 

class exportAir:
    def __init__(self):
        self.type='function'
        self.Airin={'velocity': 1.0, 'turbulence': 1.0}
        self.velstate=1.0
        self.turbstate=1.0
        self.faultmodes={}
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        return 0
    def behavior(self):
        return 0
        
    def updatefxn(self,faults=['nom'],inputs={'Air':{'velocity': 1.0, 'turbulence': 1.0}}, outputs={}):
        self.Airin=inputs['Air']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Air': self.Airin}
        return {'outputs':outputs, 'inputs':inputs}
    

#To do: 
#add import signal function
#graph with multiple control surfaces
#functions to combine force, moment, etc
        
##MODEL GRAPH AND INITIALIZATION   

def initfxns():
    Import_EE=importEE()
    Import_Air=importAir()
    Import_Signal=importSignal()
    
    Affect_Roll_r=affectDOF('roll','R')
    Affect_Roll_l=affectDOF('roll','L')
    Combine_Roll=combineforceandmoment('roll')
    
    Affect_Pitch_r=affectDOF('pitch','R')
    Affect_Pitch_l=affectDOF('pitch','L')
    Combine_Pitch=combineforceandmoment('pitch')
    
    Affect_Yaw=affectDOF('yaw','C')  
    
    Export_Air=exportAir()
    
    Export_DOF=export6dof()
    return Import_EE, Import_Air, Import_Signal, Affect_Roll_r, Affect_Roll_l, Combine_Roll, Affect_Pitch_r, Affect_Pitch_l, Combine_Pitch, Affect_Yaw, Export_Air, Export_DOF

def initialize():
    g=nx.DiGraph()
    
    Import_EE, Import_Air, Import_Signal, Affect_Roll_r, Affect_Roll_l, Combine_Roll, Affect_Pitch_r, Affect_Pitch_l, Combine_Pitch, Affect_Yaw, Export_Air, Export_DOF=initfxns()
    
    
    EE={'EE':{'rate': 1.0, 'effort': 1.0}}   
    
    g.add_node('Import_EE', funcobj=Import_EE, inputs={}, outputs={**EE})
    
    
    Air={'Air':{'velocity': 1.0, 'turbulence': 1.0}}
    g.add_node('Import_Air', funcobj=Import_Air, inputs={}, outputs={**Air})
    Sig={'Signal':{'ctl': 1.0}}
    g.add_node('Import_Signal', funcobj=Import_Signal, inputs={}, outputs={**Sig})
    
    
    MomentrollR={'MomentrollR':{'amplitude': 1.0, 'intent':1.0 }}
    ForcerollR={'ForcerollR':{'force':1.0}}
    g.add_node('Affect_Roll_Right', funcobj=Affect_Roll_r, inputs={**EE,**Air,**Sig}, outputs={**Air, **MomentrollR, **ForcerollR})
    
    MomentrollL={'MomentrollL':{'amplitude': 1.0, 'intent':1.0 }}
    ForcerollL={'ForcerollL':{'force':1.0}}
    g.add_node('Affect_Roll_Left', funcobj=Affect_Roll_l, inputs={**EE,**Air,**Sig}, outputs={**Air, **MomentrollL, **ForcerollL})
    
    roll={'roll':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Roll', funcobj=Combine_Roll, inputs={**MomentrollL,**ForcerollL,**MomentrollR,**ForcerollR}, outputs={**roll})
    
    MomentpitchR={'MomentpitchR':{'amplitude': 1.0, 'intent':1.0 }}
    ForcepitchR={'ForcepitchR':{'force':1.0}}
    g.add_node('Affect_Pitch_Right', funcobj=Affect_Pitch_r, inputs={**EE,**Air,**Sig}, outputs={**Air, **MomentpitchR, **ForcepitchR})
    
    MomentpitchL={'MomentpitchL':{'amplitude': 1.0, 'intent':1.0 }}
    ForcepitchL={'ForcepitchL':{'force':1.0}}
    
    g.add_node('Affect_Pitch_Left',  funcobj=Affect_Pitch_l, inputs={**EE,**Air,**Sig}, outputs={**Air,**MomentpitchL , **ForcepitchL})
    
    pitch={'pitch':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Pitch', funcobj=Combine_Pitch, inputs={**MomentpitchL, **ForcepitchL,**MomentpitchR, **ForcepitchR}, outputs={**pitch})
    
    yaw={'yaw':{'amplitude': 1.0, 'intent':1.0 }}
    #ForceyawC={'ForceyawC':{'force':1.0}}
    g.add_node('Affect_Yaw', funcobj=Affect_Yaw, inputs={**EE,**Air,**Sig}, outputs={**Air, **yaw})
    
    g.add_node('Export_Air', funcobj=Export_Air, inputs={**Air}, outputs={})
    
    g.add_node('Export_DOF', funcobj=Export_DOF, inputs={**roll, **pitch, **yaw}, outputs={})
    
    g.add_edge('Import_Air', 'Affect_Roll_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Roll_Left', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Right', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Left', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Yaw', Air=Air['Air'])
    
    g.add_edge('Import_EE', 'Affect_Roll_Right', EE=EE['EE'])
    g.add_edge('Import_EE', 'Affect_Roll_Left', EE=EE['EE'])    
    g.add_edge('Import_EE', 'Affect_Pitch_Right', EE=EE['EE'])    
    g.add_edge('Import_EE', 'Affect_Pitch_Left',EE=EE['EE'])
    g.add_edge('Import_EE', 'Affect_Yaw', EE=EE['EE'])

    g.add_edge('Import_Signal', 'Affect_Roll_Right', Signal=Sig['Signal'])
    g.add_edge('Import_Signal', 'Affect_Roll_Left', Signal=Sig['Signal'])    
    g.add_edge('Import_Signal', 'Affect_Pitch_Right', Signal=Sig['Signal'])    
    g.add_edge('Import_Signal', 'Affect_Pitch_Left', Signal=Sig['Signal'])
    g.add_edge('Import_Signal', 'Affect_Yaw', Signal=Sig['Signal'])   
    
    g.add_edge('Affect_Roll_Right','Combine_Roll',ForcerollR=ForcerollR['ForcerollR'], MomentrollR=MomentrollR['MomentrollR'])     
    g.add_edge('Affect_Roll_Left','Combine_Roll',ForcerollL=ForcerollL['ForcerollL'], MomentrollL=MomentrollL['MomentrollL'])
    
    g.add_edge('Affect_Pitch_Right','Combine_Pitch',ForcepitchR=ForcepitchR['ForcepitchR'], MomentpitchR=MomentpitchR['MomentpitchR'])  
    g.add_edge('Affect_Pitch_Left','Combine_Pitch',ForcepitchL=ForcepitchL['ForcepitchL'], MomentpitchL=MomentpitchL['MomentpitchL'])
    
    g.add_edge('Combine_Pitch', 'Export_DOF',pitch=pitch['pitch'])
    g.add_edge('Combine_Roll', 'Export_DOF',roll=roll['roll'])
    g.add_edge('Affect_Yaw', 'Export_DOF', yaw=yaw['yaw'])
    
    g.add_edge('Affect_Roll_Right', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Roll_Left', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Right', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Left', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Yaw', 'Export_Air', Air=Air['Air']) 
    

    backgraph=g.reverse(copy=True)
    forwardgraph=g
    fullgraph=nx.compose(backgraph, forwardgraph)
    
    return [forwardgraph,backgraph,fullgraph]
        