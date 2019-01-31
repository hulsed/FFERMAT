# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:38:34 2018

@author: Daniel Hulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

lifehours=20000

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
    
class distributeEE:
    def __init__(self):
        self.type='function'
        self.EEin={'rate': 1.0, 'effort': 1.0}
        self.EELiftR={'rate': 1.0, 'effort': 1.0}
        self.EELiftL={'rate': 1.0, 'effort': 1.0}
        self.EEDragR={'rate': 1.0, 'effort': 1.0}
        self.EEDragL={'rate': 1.0, 'effort': 1.0}
        self.EEYaw={'rate': 1.0, 'effort': 1.0}
        self.EERollR={'rate': 1.0, 'effort': 1.0}
        self.EERollL={'rate': 1.0, 'effort': 1.0}
        self.EEPitchR={'rate': 1.0, 'effort': 1.0}
        self.EEPitchL={'rate': 1.0, 'effort': 1.0}
        
        self.elecstate=1.0
        self.liftrstate=1.0
        self.liftlstate=1.0
        self.dragrstate=1.0
        self.draglstate=1.0
        self.yawstate=1.0
        self.rollrstate=1.0
        self.rolllstate=1.0
        self.pitchrstate=1.0
        self.pitchlstate=1.0
        self.faultmodes={'infv':{'lprob':'moderate', 'rcost':'major'}, \
                         'lowv':{'lprob':'moderate', 'rcost':'minor'}, \
                         'nov':{'lprob':'high', 'rcost':'moderate'}, \
                         'opencLiftR':{'lprob':'low', 'rcost':'minor'}, \
                         'opencLiftL':{'lprob':'low', 'rcost':'minor'}, \
                         'opencDragR':{'lprob':'low', 'rcost':'minor'}, \
                         'opencDragL':{'lprob':'low', 'rcost':'minor'}, \
                         'opencYaw':{'lprob':'low', 'rcost':'minor'}, \
                         'opencRollR':{'lprob':'low', 'rcost':'minor'}, \
                         'opencRollL':{'lprob':'low', 'rcost':'minor'}, \
                         'opencPitchR':{'lprob':'low', 'rcost':'minor'}, \
                         'opencPitchL':{'lprob':'low', 'rcost':'minor'}, \
                         }
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.EELiftR['rate']>2:
            self.faults.add('opencLiftR')
        if self.EELiftL['rate']>2:
            self.faults.add('opencLiftL')
        if self.EEDragR['rate']>2:
            self.faults.add('opencDragR')
        if self.EEDragL['rate']>2:
            self.faults.add('opencDragL')
        if self.EEYaw['rate']>2:
            self.faults.add('opencYaw')
        if self.EERollR['rate']>2:
            self.faults.add('opencRollR')
        if self.EERollL['rate']>2:
            self.faults.add('opencRollL')
        if self.EEPitchR['rate']>2:
            self.faults.add('opencPitchR')
        if self.EEPitchL['rate']>2:
            self.faults.add('opencPitchL')
            
    def detbehav(self):
        if self.faults.intersection(set(['infv'])):
            self.elecstate=np.inf
        elif self.faults.intersection(set(['nov'])):
            self.elecstate=0.0
        elif self.faults.intersection(set(['lowv'])):
            self.elecstate=0.5
        
        if self.faults.intersection(set(['opencLiftR'])):
            self.liftrstate=0.0
        if self.faults.intersection(set(['opencLiftL'])):
            self.liftlstate=0.0
        if self.faults.intersection(set(['opencDragR'])):
            self.dragrstate=0.0
        if self.faults.intersection(set(['opencDragL'])):
            self.draglstate=0.0
        if self.faults.intersection(set(['opencYaw'])):
            self.yawstate=0.0
        if self.faults.intersection(set(['opencRollR'])):
            self.rollrstate=0.0
        if self.faults.intersection(set(['opencRollL'])):
            self.rolllstate=0.0
        if self.faults.intersection(set(['opencPitchR'])):
            self.pitchrstate=0.0
        if self.faults.intersection(set(['opencPitchL'])):
            self.pitchlstate=0.0
    def behavior(self):
        
        self.EELiftR['effort']=aux.m2to1([self.liftrstate,self.elecstate,self.EEin['effort']])
        self.EELiftL['effort']=aux.m2to1([self.liftlstate,self.elecstate,self.EEin['effort']])
        self.EEDragR['effort']=aux.m2to1([self.dragrstate,self.elecstate,self.EEin['effort']])
        self.EEDragL['effort']=aux.m2to1([self.draglstate,self.elecstate,self.EEin['effort']])
        self.EEYaw['effort']=aux.m2to1([self.yawstate,self.elecstate,self.EEin['effort']])
        self.EERollR['effort']=aux.m2to1([self.rollrstate,self.elecstate,self.EEin['effort']])
        self.EERollL['effort']=aux.m2to1([self.rolllstate,self.elecstate,self.EEin['effort']])
        self.EEPitchR['effort']=aux.m2to1([self.pitchrstate,self.elecstate,self.EEin['effort']])
        self.EEPitchL['effort']=aux.m2to1([self.pitchlstate,self.elecstate,self.EEin['effort']])
        
        self.EEin['rate']=self.elecstate
        
    def updatefxn(self,faults=['nom'],inputs={'EE':{'rate': 1.0, 'effort': 1.0}}, outputs={ \
                  'EELiftR':{'rate': 1.0, 'effort': 1.0}, \
                  'EELiftL':{'rate': 1.0, 'effort': 1.0}, 'EEDragR':{'rate': 1.0, 'effort': 1.0}, \
                  'EEDragL':{'rate': 1.0, 'effort': 1.0}, 'EEYaw':{'rate': 1.0, 'effort': 1.0}, \
                  'EERollR':{'rate': 1.0, 'effort': 1.0}, 'EERollL':{'rate': 1.0, 'effort': 1.0}, \
                  'EEPitchR':{'rate': 1.0, 'effort': 1.0}, 'EEPitchL':{'rate': 1.0, 'effort': 1.0}}):
        self.EEin['effort']=inputs['EE']['effort']
        
        self.EELiftR['rate']=outputs['EELiftR']['rate']
        self.EELiftL['rate']=outputs['EELiftL']['rate']
        self.EEDragR['rate']=outputs['EEDragR']['rate']
        self.EEDragL['rate']=outputs['EEDragL']['rate']
        self.EEYaw['rate']=outputs['EEYaw']['rate']
        self.EERollR['rate']=outputs['EERollR']['rate']
        self.EERollL['rate']=outputs['EERollL']['rate']
        self.EEPitchR['rate']=outputs['EEPitchR']['rate']
        self.EEPitchL['rate']=outputs['EEPitchL']['rate']
        
        
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'EE':self.EEin}
        outputs={'EELiftR':self.EELiftR, \
                  'EELiftL':self.EELiftL, 'EEDragR':self.EEDragR, \
                  'EEDragL':self.EEDragL, 'EEYaw':self.EEYaw, \
                  'EERollR':self.EERollR, 'EERollL':self.EERollL, \
                  'EEPitchR':self.EEPitchR, 'EEPitchL':self.EEPitchL}
        return {'outputs':outputs, 'inputs':inputs}
   
class distributeSig:
    def __init__(self):
        self.type='function'
        self.Sigin={'ctl': 1.0}
        self.SigLiftR={'ctl': 1.0}
        self.SigLiftL={'ctl': 1.0}
        self.SigDragR={'ctl': 1.0}
        self.SigDragL={'ctl': 1.0}
        self.SigYaw={'ctl': 1.0}
        self.SigRollR={'ctl': 1.0}
        self.SigRollL={'ctl': 1.0}
        self.SigPitchR={'ctl': 1.0}
        self.SigPitchL={'ctl': 1.0}
        
        self.sigstate=1.0
        self.liftrstate=1.0
        self.liftlstate=1.0
        self.dragrstate=1.0
        self.draglstate=1.0
        self.yawstate=1.0
        self.rollrstate=1.0
        self.rolllstate=1.0
        self.pitchrstate=1.0
        self.pitchlstate=1.0
        self.faultmodes={'degsig':{'lprob':'moderate', 'rcost':'minor'}, \
                         'nosig':{'lprob':'high', 'rcost':'moderate'}, \
                         'nosigLiftR':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigLiftL':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigDragR':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigDragL':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigYaw':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigRollR':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigRollL':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigPitchR':{'lprob':'low', 'rcost':'minor'}, \
                         'nosigPitchL':{'lprob':'low', 'rcost':'minor'}, \
                         }
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.SigLiftR['ctl']>2:
            self.faults.add('nosigLiftR')
        if self.SigLiftL['ctl']>2:
            self.faults.add('nosigLiftL')
        if self.SigDragR['ctl']>2:
            self.faults.add('nosigDragR')
        if self.SigDragL['ctl']>2:
            self.faults.add('nosigDragL')
        if self.SigYaw['ctl']>2:
            self.faults.add('nosigYaw')
        if self.SigRollR['ctl']>2:
            self.faults.add('nosigRollR')
        if self.SigRollL['ctl']>2:
            self.faults.add('nosigRollL')
        if self.SigPitchR['ctl']>2:
            self.faults.add('nosigPitchR')
        if self.SigPitchL['ctl']>2:
            self.faults.add('nosigPitchL')
            
    def detbehav(self):
        if self.faults.intersection(set(['nosig'])):
            self.sigstate=0.0
        elif self.faults.intersection(set(['degsig'])):
            self.sigstate=0.5
        
        if self.faults.intersection(set(['nosigLiftR'])):
            self.liftrstate=0.0
        if self.faults.intersection(set(['nosigLiftL'])):
            self.liftlstate=0.0
        if self.faults.intersection(set(['nosigDragR'])):
            self.dragrstate=0.0
        if self.faults.intersection(set(['nosigDragL'])):
            self.draglstate=0.0
        if self.faults.intersection(set(['nosigYaw'])):
            self.yawstate=0.0
        if self.faults.intersection(set(['nosigRollR'])):
            self.rollrstate=0.0
        if self.faults.intersection(set(['nosigRollL'])):
            self.rolllstate=0.0
        if self.faults.intersection(set(['nosigPitchR'])):
            self.pitchrstate=0.0
        if self.faults.intersection(set(['nosigPitchL'])):
            self.pitchlstate=0.0
    def behavior(self):
        
        self.SigLiftR['ctl']=aux.m2to1([self.liftrstate,self.sigstate,self.Sigin['ctl']])
        self.SigLiftL['ctl']=aux.m2to1([self.liftlstate,self.sigstate,self.Sigin['ctl']])
        self.SigDragR['ctl']=aux.m2to1([self.dragrstate,self.sigstate,self.Sigin['ctl']])
        self.SigDragL['ctl']=aux.m2to1([self.draglstate,self.sigstate,self.Sigin['ctl']])
        self.SigYaw['ctl']=aux.m2to1([self.yawstate,self.sigstate,self.Sigin['ctl']])
        self.SigRollR['ctl']=aux.m2to1([self.rollrstate,self.sigstate,self.Sigin['ctl']])
        self.SigRollL['ctl']=aux.m2to1([self.rolllstate,self.sigstate,self.Sigin['ctl']])
        self.SigPitchR['ctl']=aux.m2to1([self.pitchrstate,self.sigstate,self.Sigin['ctl']])
        self.SigPitchL['ctl']=aux.m2to1([self.pitchlstate,self.sigstate,self.Sigin['ctl']])
        
        self.Sigin['rate']=self.sigstate
        
    def updatefxn(self,faults=['nom'],inputs={'Signal':{'ctl': 1.0}}, outputs={ \
                  'SigLiftR':{'ctl': 1.0}, \
                  'SigLiftL':{'ctl': 1.0}, 'SigDragR':{'ctl': 1.0}, \
                  'SigDragL':{'ctl': 1.0}, 'SigYaw':{'ctl': 1.0}, \
                  'SigRollR':{'ctl': 1.0}, 'SigRollL':{'ctl': 1.0}, \
                  'SigPitchR':{'ctl': 1.0}, 'SigPitchL':{'ctl': 1.0}}):
        self.Sigin['ctl']=inputs['Signal']['ctl']
        
        self.SigLiftR['ctl']=outputs['SigLiftR']['ctl']
        self.SigLiftL['ctl']=outputs['SigLiftL']['ctl']
        self.SigDragR['ctl']=outputs['SigDragR']['ctl']
        self.SigDragL['ctl']=outputs['SigDragL']['ctl']
        self.SigYaw['ctl']=outputs['SigYaw']['ctl']
        self.SigRollR['ctl']=outputs['SigRollR']['ctl']
        self.SigRollL['ctl']=outputs['SigRollL']['ctl']
        self.SigPitchR['ctl']=outputs['SigPitchR']['ctl']
        self.SigPitchL['ctl']=outputs['SigPitchL']['ctl']
        
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Sig':self.Sigin}
        outputs={'SigLiftR':self.SigLiftR, \
                  'SigLiftL':self.SigLiftL, 'SigDragR':self.SigDragR, \
                  'SigDragL':self.SigDragL, 'SigYaw':self.SigYaw, \
                  'SigRollR':self.SigRollR, 'SigRollL':self.SigRollL, \
                  'SigPitchR':self.SigPitchR, 'SigPitchL':self.SigPitchL}
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
            self.eename='EE'+dof.capitalize()
            self.signame='Sig'+dof.capitalize()
        else:
            self.forcename='Force'+dof+side
            self.momentname='Moment'+dof+side
            self.eename='EE'+dof.capitalize()+side
            self.signame='Sig'+dof.capitalize()+side
        
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
        
        
    def updatefxn(self,faults=['nom'],inputs={}, outputs={}):
        
        if len(inputs)==0:
            inputs={self.signame:{'ctl': 1.0},self.eename:{'rate': 1.0, 'effort': 1.0},'Air': {'velocity': 1.0, 'turbulence': 1.0}}
        
        if len(outputs)==0:
            if self.side=='c' or self.side=='C':
                outputs={ self.momentname:{'amplitude': 1.0, 'intent':1.0 }, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}
            else:
                outputs={self.forcename:{'force':1.0}, self.momentname:{'amplitude': 1.0, 'intent':1.0 }, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}
                self.Forceout=outputs[self.forcename]
        self.Airin=inputs['Air']
        self.EEin=inputs[self.eename]
        self.Sigin=inputs[self.signame]
        self.Airout=outputs['Air']
        self.Momentout=outputs[self.momentname]
        

        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={self.signame: self.Sigin, self.eename: self.EEin, 'Air':self.Airin}
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
        self.Momentout['intent']=.5*(self.MomentLin['intent']+self.MomentRin['intent'])
        
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
        
class exportLD:
    def __init__(self):
        self.Drag={'amplitude': 1.0, 'intent':1.0 }
        self.Lift={'amplitude': 1.0, 'intent':1.0 }
        self.type='classifier'
        
        self.Severity={'noeffect'}
        self.faultmodes={}
        self.faults=set(['nom'])
    def classify(self):
        if self.Drag['intent']!=1 or self.Drag['amplitude']!=1 or self.Lift['intent']!=1 or self.Lift['amplitude']!=1:
            self.Severity='major'
        else:
            self.Severity='noeffect'
    def returnvalue(self):
        return self.Severity
    
    def updatefxn(self,faults=['nom'],inputs={'lift':{'amplitude': 1.0, 'intent':1.0 }, 'drag':{'amplitude': 1.0, 'intent':1.0 }, 'yaw':{'amplitude': 1.0, 'intent':1.0 } }, outputs={}):
        self.Lift=inputs['lift']
        self.Drag=inputs['drag']
        
        self.classify()
        
        inputs={'Lift': self.Lift, 'Drag': self.Drag}
        outputs={}
        return {'outputs':outputs, 'inputs':inputs} 
    
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

def initialize():
    
    #initialize graph
    g=nx.DiGraph()
    
    ##INITIALIZE NODES
    #INIT Import_EE
    EE={'EE':{'rate': 1.0, 'effort': 1.0}}   
    Import_EE=importEE()
    g.add_node('Import_EE', funcobj=Import_EE, inputs={}, outputs={**EE})
    
    #Init Distribute EE
    EELiftR={'EELiftR':{'rate': 1.0, 'effort': 1.0}}
    EELiftL={'EELiftL':{'rate': 1.0, 'effort': 1.0}}
    EEDragR={'EEDragR':{'rate': 1.0, 'effort': 1.0}}
    EEDragL={'EEDragL':{'rate': 1.0, 'effort': 1.0}}
    EEYaw={'EEYaw':{'rate': 1.0, 'effort': 1.0}}
    EERollR={'EERollR':{'rate': 1.0, 'effort': 1.0}}
    EERollL={'EERollL':{'rate': 1.0, 'effort': 1.0}}
    EEPitchR={'EEPitchR':{'rate': 1.0, 'effort': 1.0}}
    EEPitchL={'EEPitchL':{'rate': 1.0, 'effort': 1.0}}
    Distribute_EE=distributeEE()
    g.add_node('Distribute_EE', funcobj=Distribute_EE, inputs={**EE}, outputs={**EELiftR,\
               **EEDragR,**EEDragL, **EELiftL, **EEYaw,**EERollR,**EERollL,**EEPitchR,**EEPitchL,**EEPitchL})
    
    #INIT Import_Air
    Import_Air=importAir()
    Air={'Air':{'velocity': 1.0, 'turbulence': 1.0}}
    g.add_node('Import_Air', funcobj=Import_Air, inputs={}, outputs={**Air})
    
    #Init Import Signal
    Import_Signal=importSignal()
    Sig={'Signal':{'ctl': 1.0}}
    g.add_node('Import_Signal', funcobj=Import_Signal, inputs={}, outputs={**Sig})
    
    #Init Distribute Signal
    Distribute_Signal=distributeSig()
    SigLiftR={'SigLiftR':{'ctl': 1.0}}
    SigLiftL={'SigLiftL':{'ctl': 1.0}}
    SigDragR={'SigDragR':{'ctl': 1.0}}
    SigDragL={'SigDragL':{'ctl': 1.0}}
    SigYaw={'SigYaw':{'ctl': 1.0}}
    SigRollR={'SigRollR':{'ctl': 1.0}}
    SigRollL={'SigRollL':{'ctl': 1.0}}
    SigPitchR={'SigPitchR':{'ctl': 1.0}}
    SigPitchL={'SigPitchL':{'ctl': 1.0}}
    g.add_node('Distribute_Signal', funcobj=Distribute_Signal, inputs={**Sig}, outputs={**SigLiftR,**SigLiftL,**SigDragR,**SigDragL, \
               **SigYaw,**SigRollR,**SigRollL,**SigPitchR,**SigPitchL})
    
    #Init Affect Roll Right
    Affect_Roll_r=affectDOF('roll','R')
    MomentrollR={'MomentrollR':{'amplitude': 1.0, 'intent':1.0 }}
    ForcerollR={'ForcerollR':{'force':1.0}}
    g.add_node('Affect_Roll_Right', funcobj=Affect_Roll_r, inputs={**EERollR,**Air,**SigRollR}, outputs={**Air, **MomentrollR, **ForcerollR})
    
    #Init Affect Roll Left
    Affect_Roll_l=affectDOF('roll','L')
    MomentrollL={'MomentrollL':{'amplitude': 1.0, 'intent':1.0 }}
    ForcerollL={'ForcerollL':{'force':1.0}}
    g.add_node('Affect_Roll_Left', funcobj=Affect_Roll_l, inputs={**EERollL,**Air,**SigRollL}, outputs={**Air, **MomentrollL, **ForcerollL})
    
    #Init Combine Roll 
    Combine_Roll=combineforceandmoment('roll')
    roll={'roll':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Roll', funcobj=Combine_Roll, inputs={**MomentrollL,**ForcerollL,**MomentrollR,**ForcerollR}, outputs={**roll})
    
    #Init Affect Pitch Right
    Affect_Pitch_r=affectDOF('pitch','R')
    MomentpitchR={'MomentpitchR':{'amplitude': 1.0, 'intent':1.0 }}
    ForcepitchR={'ForcepitchR':{'force':1.0}}
    g.add_node('Affect_Pitch_Right', funcobj=Affect_Pitch_r, inputs={**EEPitchR,**Air,**SigPitchR}, outputs={**Air, **MomentpitchR, **ForcepitchR})
    
    #Init Affect Pitch Left
    Affect_Pitch_l=affectDOF('pitch','L')
    MomentpitchL={'MomentpitchL':{'amplitude': 1.0, 'intent':1.0 }}
    ForcepitchL={'ForcepitchL':{'force':1.0}}
    g.add_node('Affect_Pitch_Left',  funcobj=Affect_Pitch_l, inputs={**EEPitchL,**Air,**SigPitchL}, outputs={**Air,**MomentpitchL , **ForcepitchL})
    
    #Init Combine Pitch 
    Combine_Pitch=combineforceandmoment('pitch')
    pitch={'pitch':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Pitch', funcobj=Combine_Pitch, inputs={**MomentpitchL, **ForcepitchL,**MomentpitchR, **ForcepitchR}, outputs={**pitch})
    
    #Init Affect Yaw
    Affect_Yaw=affectDOF('yaw','C')  
    yaw={'yaw':{'amplitude': 1.0, 'intent':1.0 }}
    #ForceyawC={'ForceyawC':{'force':1.0}}
    g.add_node('Affect_Yaw', funcobj=Affect_Yaw, inputs={**EEYaw,**Air,**SigYaw}, outputs={**Air, **yaw})
    
    #Init Affect Drag Right
    Affect_Drag_r=affectDOF('drag','R')
    MomentdragR={'MomentdragR':{'amplitude': 1.0, 'intent':1.0 }}
    ForcedragR={'ForcedragR':{'force':1.0}}
    g.add_node('Affect_Drag_Right', funcobj=Affect_Drag_r, inputs={**EEDragR,**Air,**SigDragR}, outputs={**Air, **MomentdragR, **ForcedragR})
    
    #Init Affect Drag Left
    Affect_Drag_l=affectDOF('drag','L')
    MomentdragL={'MomentdragL':{'amplitude': 1.0, 'intent':1.0 }}
    ForcedragL={'ForcedragL':{'force':1.0}}
    g.add_node('Affect_Drag_Left', funcobj=Affect_Drag_l, inputs={**EEDragL,**Air,**SigDragL}, outputs={**Air, **MomentdragL, **ForcedragL})
    
    #Init Combine Drag
    Combine_Drag=combineforceandmoment('drag')
    drag={'drag':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Drag', funcobj=Combine_Drag, inputs={**MomentdragL, **ForcedragL,**MomentdragR, **ForcedragR}, outputs={**drag})
    
    #Init Affect Lift Right
    Affect_Lift_r=affectDOF('lift','R')
    MomentliftR={'MomentliftR':{'amplitude': 1.0, 'intent':1.0 }}
    ForceliftR={'ForceliftR':{'force':1.0}}
    g.add_node('Affect_Lift_Right', funcobj=Affect_Lift_r, inputs={**EELiftR,**Air,**SigLiftR}, outputs={**Air, **MomentliftR, **ForceliftR})
    
    #Init Affect Lift Left
    Affect_Lift_l=affectDOF('lift','L')
    MomentliftL={'MomentliftL':{'amplitude': 1.0, 'intent':1.0 }}
    ForceliftL={'ForceliftL':{'force':1.0}}
    g.add_node('Affect_Lift_Left', funcobj=Affect_Lift_l, inputs={**EELiftL,**Air,**SigLiftL}, outputs={**Air, **MomentliftL, **ForceliftL})
    
    #Init Combine Drag
    Combine_Lift=combineforceandmoment('lift')
    lift={'lift':{'amplitude': 1.0, 'intent':1.0 }}
    g.add_node('Combine_Lift', funcobj=Combine_Lift, inputs={**MomentliftL, **ForceliftL,**MomentliftR, **ForceliftR}, outputs={**lift})
        
    #Init Export Air
    Export_Air=exportAir()
    g.add_node('Export_Air', funcobj=Export_Air, inputs={**Air}, outputs={})
    
    #Init Export DOF
    Export_DOF=export6dof()
    g.add_node('Export_DOF', funcobj=Export_DOF, inputs={**roll, **pitch, **yaw}, outputs={})
    
    #Init Explort Lift/Drag
    Export_LD=exportLD()
    g.add_node('Export_LD',funcobj=Export_LD, inputs={**lift,**drag}, outputs={})
    
    
    ##INITIALIZE EDGES
    #Air in flows
    g.add_edge('Import_Air', 'Affect_Roll_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Roll_Left', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Right', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Left', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Yaw', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Lift_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Lift_Left', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Drag_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Drag_Left', Air=Air['Air'])
    #EE flows
    g.add_edge('Import_EE', 'Distribute_EE', EE=EE['EE'])
    
    g.add_edge('Distribute_EE', 'Affect_Roll_Right', EERollR=EERollR['EERollR'])
    g.add_edge('Distribute_EE', 'Affect_Roll_Left', EERollL=EERollL['EERollL'])    
    g.add_edge('Distribute_EE', 'Affect_Pitch_Right', EEPitchR=EEPitchR['EEPitchR'])    
    g.add_edge('Distribute_EE', 'Affect_Pitch_Left',EEPitchL=EEPitchL['EEPitchL'])
    g.add_edge('Distribute_EE', 'Affect_Yaw', EEYaw=EEYaw['EEYaw'])
    g.add_edge('Distribute_EE', 'Affect_Lift_Left', EELiftL=EELiftL['EELiftL'])
    g.add_edge('Distribute_EE', 'Affect_Lift_Right', EELiftR=EELiftR['EELiftR'])
    g.add_edge('Distribute_EE', 'Affect_Drag_Left', EEDragL=EEDragL['EEDragL'])
    g.add_edge('Distribute_EE', 'Affect_Drag_Right', EEDragR=EEDragR['EEDragR'])
    #Signal flows
    g.add_edge('Import_Signal', 'Distribute_Signal', Signal=Sig['Signal'])
    
    
    g.add_edge('Distribute_Signal', 'Affect_Roll_Right', SigRollR=SigRollR['SigRollR'])
    g.add_edge('Distribute_Signal', 'Affect_Roll_Left', SigRollL=SigRollL['SigRollL'])    
    g.add_edge('Distribute_Signal', 'Affect_Pitch_Right', SigPitchR=SigPitchR['SigPitchR'])    
    g.add_edge('Distribute_Signal', 'Affect_Pitch_Left', SigPitchL=SigPitchL['SigPitchL'])
    g.add_edge('Distribute_Signal', 'Affect_Yaw', SigYaw=SigYaw['SigYaw'])
    g.add_edge('Distribute_Signal', 'Affect_Lift_Right', SigLiftR=SigLiftR['SigLiftR'])
    g.add_edge('Distribute_Signal', 'Affect_Lift_Left', SigLiftL=SigLiftL['SigLiftL'])
    g.add_edge('Distribute_Signal', 'Affect_Drag_Right', SigDragR=SigDragR['SigDragR'])
    g.add_edge('Distribute_Signal', 'Affect_Drag_Left', SigDragL=SigDragL['SigDragL'])
    #Roll flows
    g.add_edge('Affect_Roll_Right','Combine_Roll',ForcerollR=ForcerollR['ForcerollR'], MomentrollR=MomentrollR['MomentrollR'])     
    g.add_edge('Affect_Roll_Left','Combine_Roll',ForcerollL=ForcerollL['ForcerollL'], MomentrollL=MomentrollL['MomentrollL'])
    #Pitch flows
    g.add_edge('Affect_Pitch_Right','Combine_Pitch',ForcepitchR=ForcepitchR['ForcepitchR'], MomentpitchR=MomentpitchR['MomentpitchR'])  
    g.add_edge('Affect_Pitch_Left','Combine_Pitch',ForcepitchL=ForcepitchL['ForcepitchL'], MomentpitchL=MomentpitchL['MomentpitchL'])
    #Drag flows
    g.add_edge('Affect_Drag_Right','Combine_Drag',ForcedragR=ForcedragR['ForcedragR'], MomentdragR=MomentdragR['MomentdragR'])  
    g.add_edge('Affect_Drag_Left','Combine_Drag',ForcedragL=ForcedragL['ForcedragL'], MomentdragL=MomentdragL['MomentdragL'])
    #Lift flows
    g.add_edge('Affect_Lift_Right','Combine_Lift',ForceliftR=ForceliftR['ForceliftR'], MomentliftR=MomentliftR['MomentliftR'])  
    g.add_edge('Affect_Lift_Left','Combine_Lift',ForceliftL=ForceliftL['ForceliftL'], MomentliftL=MomentliftL['MomentliftL'])
    #roll, pitch, yaw flows
    g.add_edge('Combine_Pitch', 'Export_DOF',pitch=pitch['pitch'])
    g.add_edge('Combine_Roll', 'Export_DOF',roll=roll['roll'])
    g.add_edge('Affect_Yaw', 'Export_DOF', yaw=yaw['yaw'])
    #lift,drag flows
    g.add_edge('Combine_Lift', 'Export_LD', lift=lift['lift'])
    g.add_edge('Combine_Drag', 'Export_LD', drag=drag['drag'])
    #Air flows 
    g.add_edge('Affect_Roll_Right', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Roll_Left', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Right', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Left', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Yaw', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Lift_Right', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Lift_Left', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Drag_Right', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Drag_Left', 'Export_Air', Air=Air['Air']) 
    
    ##INITALIZE PROPOGATION GRAPHS
    backgraph=g.reverse(copy=True)
    forwardgraph=g
    fullgraph=nx.compose(backgraph, forwardgraph)
    
    return [forwardgraph,backgraph,fullgraph]
        