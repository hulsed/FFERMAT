# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:38:34 2018

@author: Daniel Hulse
"""

import networkx as nx
import numpy as np

import auxfunctions as aux

lifehours=20000
lifedays=lifehours/4

scope={'functions':['Affect_Roll_Right','Affect_Roll_Left','Affect_Pitch_Right','Affect_Pitch_Left',\
                    'Affect_Yaw','Affect_Liftdn_Right', 'Affect_Liftdn_Left','Affect_Liftpr_Right', 'Affect_Liftpr_Left']}

opfrac={'forward': 0.6, 'roll':0.05, 'pitch':0.15, 'yaw':0.01, 'liftdn':0.15, 'liftup':0.04}

#costs of various end-states to be used
endstatekey={'noeffect': {'pfh_allow': 0, 'cost': 0, 'repair':'NA' },\
             'minor': {'pfh_allow': 1e-3, 'cost': 0.118e7, 'repair':'minor'},\
             'major': {'pfh_allow': 1e-5, 'cost': 2.98e7, 'repair':'moderate' } , \
             'hazardous': {'pfh_allow': 1e-6, 'cost': 16.8e7, 'repair':'major' } , \
             'catastrophic': {'pfh_allow': 1e-7, 'cost': 38.4e7, 'repair':'totaled' }, \
             'NA': {'pfh_allow': 0, 'cost': 0, 'repair':'NA' }}

#subjective lifecycle probabilities for various faults
#lifecycleprob={'veryhigh':{'lb': 0.2, 'ub': 1.0 }, \
#               'high':{'lb': 0.05, 'ub': 0.19}, \
#               'moderate': {'lb': 0.049, 'ub':0.0005}, \
#               'low': {'lb':1.5/1e5, 'ub':0.00049}, \
#               'remote': {'lb':0, 'ub':1.49/1e5},\
#               'NA':{'lb':0, 'ub':0}}
# see scenario-based FMEA paper http://www.medicalhealthcarefmea.com/papers/kmenta.pdf

#rates for various faults:
rates={'veryrare':{'av':.2e-6,'lb':0.05e-6,'ub':1e-6},\
       'rare':{'av':5e-6,'lb':1e-6,'ub':10e-6},\
       'moderate':{'av':50e-6,'lb':10e-6,'ub':100e-6},\
       'common':{'av':200e-6,'lb':100e-6,'ub':500e-6}}


# repair costs for 
repaircosts={'totaled':{'lb': 100000, 'ub': 200000, 'av':150000}, \
             'major':{'lb':40000, 'ub': 100000, 'av':70000}, \
             'moderate':{'lb':5000, 'ub': 40000, 'av':20000}, \
             'minor':{'lb':1000 ,'ub': 5000, 'av':2000}, \
             'replacement':{'lb':100, 'ub': 1000, 'av':500}, \
             'NA':{'lb':0, 'ub': 0, 'av':0.0} }

maintenancecosts={'sensing': {'av':0.5, 'lb':0,'ub':1}, \
                'minorinspection': {'av':50, 'lb':10,'ub':100}, \
                 'majorinspection': {'av': 200, 'lb': 50, 'ub':400}, \
                 'minormaintenance': {'av': 150, 'lb': 50, 'ub':200}, \
                  'majormaintenance': {'av': 400, 'lb': 100, 'ub':700}, \
                  'replacement': {'av':800, 'lb':200, 'ub': 2000}}

maintenancesched={'continuous':{'av':0.1, 'lb':0.01, 'ub':0.5}, \
                  'daily':{'av':1.0, 'lb':0.25, 'ub':10}, \
                  'monthly':{'av':30, 'lb':10,'ub':60}, '90day':{'av':90, 'lb':60,'ub':120},\
                  '6mo':{'av':180,'lb':120,'ub':270}, 'yearly':{'av':365,'lb':270,'ub':2*365},\
                  '5year':{'av':5*365,'lb':2*365,'ub':10*365}}

class importEE:
    def __init__(self):
        self.useprop=1.0
        self.type='function'
        self.EEout={'rate': 1.0, 'effort': 1.0}
        self.elecstate=1.0
        self.faultmodes={'infv':{'rate':'moderate', 'rcost':'major'}, \
                         'lowv':{'rate':'moderate', 'rcost':'minor'}, \
                         'nov':{'rate':'common', 'rcost':'moderate'}}
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'infv':0.3,'lowv':0.9, 'nov':0.9}}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'infv':0.5,'lowv':0.5, 'nov':0.5}}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'infv':0.1,'lowv':0.1, 'nov':0.1}} 
                    }
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
    def updatefxn(self,faults=['nom'],opermode=[],inputs={}, outputs={'EE': {'rate': 1.0, 'effort': 1.0}}):
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
        self.useprop=1.0
        self.type='function'
        self.EEin={'rate': 1.0, 'effort': 1.0}
        self.EELiftdnR={'rate': 1.0, 'effort': 1.0}
        self.EELiftdnL={'rate': 1.0, 'effort': 1.0}
        self.EELiftprR={'rate': 1.0, 'effort': 1.0}
        self.EELiftprL={'rate': 1.0, 'effort': 1.0}
        self.EEYaw={'rate': 1.0, 'effort': 1.0}
        self.EERollR={'rate': 1.0, 'effort': 1.0}
        self.EERollL={'rate': 1.0, 'effort': 1.0}
        self.EEPitchR={'rate': 1.0, 'effort': 1.0}
        self.EEPitchL={'rate': 1.0, 'effort': 1.0}
        
        self.elecstate=1.0
        self.Liftdnrstate=1.0
        self.Liftdnlstate=1.0
        self.Liftprrstate=1.0
        self.Liftprlstate=1.0
        self.yawstate=1.0
        self.rollrstate=1.0
        self.rolllstate=1.0
        self.pitchrstate=1.0
        self.pitchlstate=1.0
        self.faultmodes={'infv':{'rate':'moderate', 'rcost':'major'}, \
                         'lowv':{'rate':'moderate', 'rcost':'minor'}, \
                         'nov':{'rate':'common', 'rcost':'moderate'}, \
                         'opencLiftdnR':{'rate':'rare', 'rcost':'minor'}, \
                         'opencLiftdnL':{'rate':'rare', 'rcost':'minor'}, \
                         'opencLiftprR':{'rate':'rare', 'rcost':'minor'}, \
                         'opencLiftprL':{'rate':'rare', 'rcost':'minor'}, \
                         'opencYaw':{'rate':'rare', 'rcost':'minor'}, \
                         'opencRollR':{'rate':'rare', 'rcost':'minor'}, \
                         'opencRollL':{'rate':'rare', 'rcost':'minor'}, \
                         'opencPitchR':{'rate':'rare', 'rcost':'minor'}, \
                         'opencPitchL':{'rate':'rare', 'rcost':'minor'}, \
                         }
        
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'infv':0.3,'lowv':0.5, 'nov':0.5,'opencLiftdnR':0.5,\
                                                                               'opencLiftdnL':0.5,'opencLiftprR':0.5, 'opencLiftprL':0.5,'opencYaw':0.5, \
                                                                               'opencRollR':0.5,'opencRollL':0.5,'opencPitchR':0.5, 'opencPitchL':0.5  }}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'infv':0.1,'lowv':0.1, 'nov':0.1,'opencLiftdnR':0.1,\
                                                                               'opencLiftdnL':0.2,'opencLiftprR':0.2, 'opencLiftprL':0.2,'opencYaw':0.2, \
                                                                               'opencRollR':0.2,'opencRollL':0.2,'opencPitchR':0.2, 'opencPitchL':0.2  }}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'infv':0.2,'lowv':0.2, 'nov':0.2,'opencLiftdnR':0.2,\
                                                                               'opencLiftdnL':0.2,'opencLiftprR':0.2, 'opencLiftprL':0.2,'opencYaw':0.2, \
                                                                               'opencRollR':0.2,'opencRollL':0.2,'opencPitchR':0.2, 'opencPitchL':0.2  }} 
                    }
        
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.EELiftdnR['rate']>2:
            self.faults.add('opencLiftdnR')
        if self.EELiftdnL['rate']>2:
            self.faults.add('opencLiftdnL')
        if self.EELiftprR['rate']>2:
            self.faults.add('opencLiftprR')
        if self.EELiftprL['rate']>2:
            self.faults.add('opencLiftprL')
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
        
        if self.faults.intersection(set(['opencLiftdnR'])):
            self.Liftdnrstate=0.0
        if self.faults.intersection(set(['opencLiftdnL'])):
            self.Liftdnlstate=0.0
        if self.faults.intersection(set(['opencLiftprR'])):
            self.Liftprrstate=0.0
        if self.faults.intersection(set(['opencLiftprL'])):
            self.Liftprlstate=0.0
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
        
        self.EELiftdnR['effort']=aux.m2to1([self.Liftdnrstate,self.elecstate,self.EEin['effort']])
        self.EELiftdnL['effort']=aux.m2to1([self.Liftdnlstate,self.elecstate,self.EEin['effort']])
        self.EELiftprR['effort']=aux.m2to1([self.Liftprrstate,self.elecstate,self.EEin['effort']])
        self.EELiftprL['effort']=aux.m2to1([self.Liftprlstate,self.elecstate,self.EEin['effort']])
        self.EEYaw['effort']=aux.m2to1([self.yawstate,self.elecstate,self.EEin['effort']])
        self.EERollR['effort']=aux.m2to1([self.rollrstate,self.elecstate,self.EEin['effort']])
        self.EERollL['effort']=aux.m2to1([self.rolllstate,self.elecstate,self.EEin['effort']])
        self.EEPitchR['effort']=aux.m2to1([self.pitchrstate,self.elecstate,self.EEin['effort']])
        self.EEPitchL['effort']=aux.m2to1([self.pitchlstate,self.elecstate,self.EEin['effort']])
        
        self.EEin['rate']=self.elecstate
        
    def updatefxn(self,faults=['nom'],opermode=[],inputs={'EE':{'rate': 1.0, 'effort': 1.0}}, outputs={ \
                  'EELiftdnR':{'rate': 1.0, 'effort': 1.0}, \
                  'EELiftdnL':{'rate': 1.0, 'effort': 1.0}, 'EELiftprR':{'rate': 1.0, 'effort': 1.0}, \
                  'EELiftprL':{'rate': 1.0, 'effort': 1.0}, 'EEYaw':{'rate': 1.0, 'effort': 1.0}, \
                  'EERollR':{'rate': 1.0, 'effort': 1.0}, 'EERollL':{'rate': 1.0, 'effort': 1.0}, \
                  'EEPitchR':{'rate': 1.0, 'effort': 1.0}, 'EEPitchL':{'rate': 1.0, 'effort': 1.0}}):
        self.EEin['effort']=inputs['EE']['effort']
        
        self.EELiftdnR['rate']=outputs['EELiftdnR']['rate']
        self.EELiftdnL['rate']=outputs['EELiftdnL']['rate']
        self.EELiftprR['rate']=outputs['EELiftprR']['rate']
        self.EELiftprL['rate']=outputs['EELiftprL']['rate']
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
        outputs={'EELiftdnR':self.EELiftdnR, \
                  'EELiftdnL':self.EELiftdnL, 'EELiftprR':self.EELiftprR, \
                  'EELiftprL':self.EELiftprL, 'EEYaw':self.EEYaw, \
                  'EERollR':self.EERollR, 'EERollL':self.EERollL, \
                  'EEPitchR':self.EEPitchR, 'EEPitchL':self.EEPitchL}
        return {'outputs':outputs, 'inputs':inputs}
   
class distributeSig:
    def __init__(self):
        self.useprop=1.0
        self.type='function'
        self.Sigin={'rollctl': 1.0, 'pitchctl': 1.0,'yawctl': 1.0,'liftprctl': 1.0,\
                   'liftdnexp': 1.0,'rollexp': 1.0, 'pitchexp': 1.0,'yawexp': 1.0,'liftprexp': 1.0,'liftdnexp': 1.0}
        self.SigLiftdnR={'ctl': 1.0, 'exp': 1.0}
        self.SigLiftdnL={'ctl': 1.0, 'exp': 1.0}
        self.SigLiftprR={'ctl': 1.0, 'exp': 1.0}
        self.SigLiftprL={'ctl': 1.0, 'exp': 1.0}
        self.SigYaw={'ctl': 1.0, 'exp': 1.0}
        self.SigRollR={'ctl': 1.0, 'exp': 1.0}
        self.SigRollL={'ctl': 1.0, 'exp': 1.0}
        self.SigPitchR={'ctl': 1.0, 'exp': 1.0}
        self.SigPitchL={'ctl': 1.0, 'exp': 1.0}
        
        self.sigstate=1.0
        self.liftdnrstate=1.0
        self.liftdnlstate=1.0
        self.liftprrstate=1.0
        self.liftprlstate=1.0
        self.yawstate=1.0
        self.rollrstate=1.0
        self.rolllstate=1.0
        self.pitchrstate=1.0
        self.pitchlstate=1.0
        self.faultmodes={'degsig':{'rate':'moderate', 'rcost':'minor'}, \
                         'nosig':{'rate':'moderate', 'rcost':'moderate'}, \
                         'nosigLiftdnR':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigLiftdnL':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigLiftprR':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigLiftprL':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigYaw':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigRollR':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigRollL':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigPitchR':{'rate':'rare', 'rcost':'minor'}, \
                         'nosigPitchL':{'rate':'rare', 'rcost':'minor'}, \
                         }
        
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'degsig':0.2,'nosig':0.9, 'nosigLiftdnR':0.3, 'nosigLiftdnL':0.3,'nosigLiftprR':0.3, \
                                                                               'nosigLiftprL':0.3,'nosigYaw':0.3,'nosigRollR':0.3,'nosigRollL':0.3,'nosigPitchR':0.3,'nosigPitchL':0.3 }}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'degsig':0.6,'nosig':0.2, 'nosigLiftdnR':0.6, 'nosigLiftdnL':0.6,'nosigLiftprR':0.8, \
                                                                               'nosigLiftprL':0.8,'nosigYaw':0.8,'nosigRollR':0.8,'nosigRollL':0.8,'nosigPitchR':0.8,'nosigPitchL':0.8 }}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'degsig':0.2,'nosig':0.2, 'nosigLiftdnR':0.2, 'nosigLiftdnL':0.2,'nosigLiftprR':0.2, \
                                                                               'nosigLiftprL':0.2,'nosigYaw':0.2,'nosigRollR':0.2,'nosigRollL':0.2,'nosigPitchR':0.2,'nosigPitchL':0.2 }}} 
        
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.SigLiftdnR['ctl']>2:
            self.faults.add('nosigLiftdnR')
        if self.SigLiftdnL['ctl']>2:
            self.faults.add('nosigLiftdnL')
        if self.SigLiftprR['ctl']>2:
            self.faults.add('nosigLiftprR')
        if self.SigLiftprL['ctl']>2:
            self.faults.add('nosigLiftprL')
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
        
        if self.faults.intersection(set(['nosigLiftdnR'])):
            self.liftdnrstate=0.0
        if self.faults.intersection(set(['nosigLiftdnL'])):
            self.liftdnlstate=0.0
        if self.faults.intersection(set(['nosigLiftprR'])):
            self.liftprrstate=0.0
        if self.faults.intersection(set(['nosigLiftprL'])):
            self.liftprlstate=0.0
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
        
        self.SigLiftdnR['ctl']=1.0+aux.m2to1([self.liftdnrstate,self.sigstate])*(self.Sigin['liftdnctl']-1.0)
        self.SigLiftdnL['ctl']=1.0+aux.m2to1([self.liftdnlstate,self.sigstate])*(self.Sigin['liftdnctl']-1.0)
        self.SigLiftprR['ctl']=1.0+aux.m2to1([self.liftprrstate,self.sigstate])*(self.Sigin['liftprctl']-1.0)
        self.SigLiftprL['ctl']=1.0+aux.m2to1([self.liftprlstate,self.sigstate])*(self.Sigin['liftprctl']-1.0)
        self.SigYaw['ctl']=1.0+aux.m2to1([self.yawstate,self.sigstate])*(self.Sigin['yawctl']-1.0)
        self.SigRollR['ctl']=1.0+aux.m2to1([self.rollrstate,self.sigstate])*(self.Sigin['rollctl']-1.0)
        self.SigRollL['ctl']=1.0+aux.m2to1([self.rolllstate,self.sigstate])*(1.0-self.Sigin['rollctl'])
        self.SigPitchR['ctl']=1.0+aux.m2to1([self.pitchrstate,self.sigstate])*(self.Sigin['pitchctl']-1.0)
        self.SigPitchL['ctl']=1.0+aux.m2to1([self.pitchlstate,self.sigstate])*(self.Sigin['pitchctl']-1.0)
        
        self.SigLiftdnR['exp']=self.Sigin['liftdnexp']
        self.SigLiftdnL['exp']=self.Sigin['liftdnexp']
        self.SigLiftprR['exp']=self.Sigin['liftprexp']
        self.SigLiftprL['exp']=self.Sigin['liftprexp']
        self.SigYaw['exp']=self.Sigin['yawexp']
        self.SigRollR['exp']=self.Sigin['rollexp']
        self.SigRollL['exp']=2.0-self.Sigin['rollexp']
        self.SigPitchR['exp']=self.Sigin['pitchexp']
        self.SigPitchL['exp']=self.Sigin['pitchexp']      
        
        
    def updatefxn(self,faults=['nom'],opermode=[],inputs={'Signal':{'rollctl': 1.0, 'pitchctl': 1.0,'yawctl': 1.0,'liftprctl': 1.0,\
                   'liftdnctl': 1.0,'rollexp': 1.0, 'pitchexp': 1.0,'yawexp': 1.0,'liftprexp': 1.0,'liftdnexp': 1.0}}, outputs={ \
                  'SigLiftdnR':{'ctl': 1.0, 'exp': 1.0}, \
                  'SigLiftdnL':{'ctl': 1.0, 'exp': 1.0}, 'SigLiftprR':{'ctl': 1.0, 'exp': 1.0}, \
                  'SigLiftprL':{'ctl': 1.0, 'exp': 1.0}, 'SigYaw':{'ctl': 1.0, 'exp': 1.0}, \
                  'SigRollR':{'ctl': 1.0, 'exp': 1.0}, 'SigRollL':{'ctl': 1.0, 'exp': 1.0}, \
                  'SigPitchR':{'ctl': 1.0, 'exp': 1.0}, 'SigPitchL':{'ctl': 1.0, 'exp': 1.0}}):
            
        self.Sigin['rollctl']=inputs['Signal']['rollctl']
        self.Sigin['pitchctl']=inputs['Signal']['pitchctl']
        self.Sigin['yawctl']=inputs['Signal']['yawctl']
        self.Sigin['liftprctl']=inputs['Signal']['liftprctl']
        self.Sigin['liftdnctl']=inputs['Signal']['liftdnctl']
        self.Sigin['rollexp']=inputs['Signal']['rollexp']
        self.Sigin['pitchexp']=inputs['Signal']['pitchexp']
        self.Sigin['yawexp']=inputs['Signal']['yawexp']
        self.Sigin['liftprexp']=inputs['Signal']['liftprexp']
        self.Sigin['liftdnexp']=inputs['Signal']['liftdnexp']
        
        self.SigLiftdnR['ctl']=outputs['SigLiftdnR']['ctl']
        self.SigLiftdnL['ctl']=outputs['SigLiftdnL']['ctl']
        self.SigLiftprR['ctl']=outputs['SigLiftprR']['ctl']
        self.SigLiftprL['ctl']=outputs['SigLiftprL']['ctl']
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
        inputs={'Signal':self.Sigin}
        outputs={'SigLiftdnR':self.SigLiftdnR, \
                  'SigLiftdnL':self.SigLiftdnL, 'SigLiftprR':self.SigLiftprR, \
                  'SigLiftprL':self.SigLiftprL, 'SigYaw':self.SigYaw, \
                  'SigRollR':self.SigRollR, 'SigRollL':self.SigRollL, \
                  'SigPitchR':self.SigPitchR, 'SigPitchL':self.SigPitchL}
        return {'outputs':outputs, 'inputs':inputs}
    
class importAir:
    def __init__(self):
        self.useprop=1.0
        self.type='function'
        self.Airout={'velocity': 1.0, 'turbulence': 1.0}
        self.velstate=1.0
        self.turbstate=1.0
        self.faultmodes={'novel': {'rate':'rare', 'rcost':'NA'},
                         'lowvel': {'rate':'rare', 'rcost':'NA'},\
                         'hivel': {'rate':'rare', 'rcost':'NA'},\
                         'gusts': {'rate':'rare', 'rcost':'NA'},\
                         'flowsep': {'rate':'rare', 'rcost':'NA'}}
        
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'novel':0.0,'lowvel':0.0,'hivel':0.0,'gusts':0.9, 'flowsep':0.9 }}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'novel':0.0,'lowvel':0.0,'hivel':0.0,'gusts':0.0, 'flowsep':0.9 }}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'novel':0.0,'lowvel':0.0,'hivel':0.0,'gusts':0.0, 'flowsep':1.0 }}}
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
            self.turbstate=0.85

    def behavior(self):
        self.Airout['velocity']=self.velstate
        self.Airout['turbulence']=self.turbstate
        
    def updatefxn(self,faults=['nom'],inputs={},opermode=[], outputs={'Air': {'velocity': 1.0, 'turbulence': 1.0}}):
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
        self.useprop=1.0
        self.type='function'
        self.Sigout={'Signal':{'rollctl': 1.0,'pitchctl': 1.0,'yawctl': 1.0,'liftprctl': 1.0,'liftdnctl': 1.0, \
                     'rollexp': 1.0, 'pitchexp':1.0, 'yawexp':1.0, 'liftprexp':1.0, 'liftdnexp':1.0}},
        self.sigstate=1.0
        self.faultmodes={'nosig':{'rate':'rare' , 'rcost':'NA'},\
                         'degsig':{'rate':'rare', 'rcost':'NA'}}
        
        self.opermodes={'forward': {'roll':1.0, 'pitch':1.0, 'yaw':1.0, 'liftdn':1.0, 'liftpr':1.0},\
                        'roll':{'roll':2.0, 'pitch':1.0, 'yaw':1.0, 'liftdn':1.0, 'liftpr':1.0}, \
                        'pitch':{'roll':1.0, 'pitch':2.0, 'yaw':1.0, 'liftdn':1.0, 'liftpr':1.0}, \
                        'yaw':{'roll':1.0, 'pitch':1.0, 'yaw':2.0, 'liftdn':1.0, 'liftpr':1.0},\
                        'liftdn':{'roll':1.0, 'pitch':1.0, 'yaw':1.0, 'liftdn':2.0, 'liftpr':1.0},\
                        'liftup':{'roll':1.0, 'pitch':1.0, 'yaw':1.0, 'liftdn':1.0, 'liftpr':2.0}}
        
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'degsig':0.2,'nosig':0.9}}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'degsig':0.9,'nosig':0.5}}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'degsig':0.7,'nosig':0.7}}} 
        
        
        self.opermode='forward' 
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        signals=list(self.Sigout['Signal'].values())
        
        if any(signal>2.0 for signal in signals):
            self.faults.update(['nosig'])
        
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['nosig'])):
            self.sigstate=0
        elif self.faults.intersection(set(['degsig'])):
            self.sigstate=1.5
        
    def behavior(self):
        
        self.Sigout['Signal']['rollctl']=1.0+self.sigstate*(self.opermodes[self.opermode]['roll']-1.0)
        self.Sigout['Signal']['pitchctl']=1.0+self.sigstate*(self.opermodes[self.opermode]['pitch']-1.0)
        self.Sigout['Signal']['yawctl']=1.0+self.sigstate*(self.opermodes[self.opermode]['yaw']-1.0)
        self.Sigout['Signal']['liftprctl']=1.0+self.sigstate*(self.opermodes[self.opermode]['liftpr']-1.0)
        self.Sigout['Signal']['liftdnctl']=1.0+self.sigstate*(self.opermodes[self.opermode]['liftdn']-1.0)
        
        self.Sigout['Signal']['rollexp']=self.opermodes[self.opermode]['roll']
        self.Sigout['Signal']['pitchexp']=self.opermodes[self.opermode]['pitch']
        self.Sigout['Signal']['yawexp']=self.opermodes[self.opermode]['yaw']
        self.Sigout['Signal']['liftprexp']=self.opermodes[self.opermode]['liftpr']
        self.Sigout['Signal']['liftdnexp']=self.opermodes[self.opermode]['liftdn']
    def updatefxn(self,faults=['nom'], opermode='forward',inputs={}, outputs={'Signal': {'rollctl': 1.0, \
                  'pitchctl': 1.0,'yawctl': 1.0,'liftprctl': 1.0,'liftdnctl': 1.0, \
                  'rollexp': 1.0, 'pitchexp':1.0, 'yawexp':1.0, 'liftprexp':1.0, 'liftdnexp':1.0}}):
        self.Sigout=outputs
        self.faults.update(faults)
        self.opermode=opermode
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
        self.Healthout={'state':1.0}
        
        
        self.mechstate=1.0
        self.surfstate=1.0
        self.EEstate=1.0
        self.ctlstate=1.0
        
        self.faultmodes={'surfbreak':{'rate':'veryrare', 'rcost':'replacement'}, \
                         'surfwarp':{'rate':'rare', 'rcost':'replacement'}, \
                         'jamup':{'rate':'rare', 'rcost':'minor'}, \
                         'jamoff':{'rate':'rare', 'rcost':'minor'}, \
                         'friction':{'rate':'moderate', 'rcost':'replacement'},\
                         'short':{'rate':'rare', 'rcost':'minor'}, \
                         'opencircuit':{'rate':'veryrare', 'rcost':'replacement'}, \
                         'ctlbreak':{'rate':'rare', 'rcost':'replacement'}, \
                         'ctldrift':{'rate':'veryrare', 'rcost':'replacement'}}
        self.faults=set(['nom'])
        
        self.maint={'check':{'type':'minorinspection', 'sched':'daily', 'eff':{'surfbreak':0.95,'surfwarp':0.95,'jamup':0.95,'jamoff':0.95,'friction':0.95, \
                                                                               'short':0.95,'opencircuit':0.95,'ctlbreak':0.95,'ctldrift':0.95}}, \
                    'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'surfbreak':0.5,'surfwarp':0.5,'jamup':0.5,'jamoff':0.5,'friction':0.8, \
                                                                               'short':0.5,'opencircuit':0.5,'ctlbreak':0.5,'ctldrift':0.5}}, \
                    'endoflife':{'type':'replacement', 'sched':'5year', 'eff':{'surfbreak':0.2,'surfwarp':0.2,'jamup':0.2,'jamoff':0.2,'friction':0.2, \
                                                                               'short':0.2,'opencircuit':0.2,'ctlbreak':0.2,'ctldrift':0.2}}} 
                
        if dof=='liftdn':
            self.useprop=0.2
            self.operscens=['roll','forward']
        if dof=='liftpr':
            self.useprop=0.2
            self.operscens=['liftup','forward']
        if dof=='roll':
            self.useprop=0.05
            self.operscens=['roll','forward']
        if dof=='pitch':
            self.useprop=0.15
            self.operscens=['pitch','forward']
        if dof=='yaw':
            self.useprop=0.06
            self.operscens=['yaw','forward']
        
        if dof!='liftdn':
            self.operscens=['liftdn','forward']
            self.faultmodes['jamdown']={'rate':'rare', 'rcost':'minor'}
            self.maint['check']['eff']['jamdown']=0.5
            self.maint['evaluation']['eff']['jamdown']=0.3
            self.maint['endoflife']['eff']['jamdown']=0.1
        
        self.dof=dof
        self.side=side
        
        if side=='C':
            self.forcename='Force'+dof.capitalize()+side
            self.eename='EE'+dof.capitalize()
            self.signame='Sig'+dof.capitalize()
            self.healthname='Health'+dof.capitalize()
            self.pffxn='Sense_Health_'+dof.capitalize()
        else:
            self.forcename='Force'+dof.capitalize()+side
            self.eename='EE'+dof.capitalize()+side
            self.signame='Sig'+dof.capitalize()+side
            self.healthname='Health'+dof.capitalize()+side
            self.pffxn='Sense_Health_'+dof.capitalize()+'_'+aux.rlc(side)
        
        self.Forceout={'dev':1.0, 'exp':1.0}
    def resolvefaults(self):
        return 0
    def condfaults(self):
        if self.EEin['effort']>2.0:
            self.faults.add('opencircuit')
        return 0
    def detbehav(self):
        if  self.faults.intersection(set(['jamup'])):
            self.mechstate=2.0
        elif self.faults.intersection(set(['jamdown'])):
            self.mechstate=0.0
        elif self.faults.intersection(set(['jamoff'])):
            self.mechstate=1.0
        elif self.faults.intersection(set(['friction'])):
            self.mechstate=1.5 
            
        if self.faults.intersection(set(['surfbreak'])):
            self.surfstate=1.0
        elif self.faults.intersection(set(['surfwarp'])):
            self.surfstate=1.5
            
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
            self.EEstate=0.0
        elif self.faults.intersection(set(['ctldrift'])):
            self.ctlstate=0.5
            
        if len(self.faults.difference(set(['nom'])))>0:
            self.healthstate=0.5
        else:
            self.healthstate=1.0

    def behavior(self):
        self.Airout['turbulence']=self.Airin['turbulence']*self.surfstate
        
        aforce=self.mechstate*self.surfstate*self.Airin['turbulence']
        
        power=1.0+aux.m2to1([self.Airin['velocity'], self.EEstate, self.EEin['effort']])*(self.ctlstate*self.Sigin['ctl']-1.0)
        #self.Forceout[self.forcename]['dev']=power*self.Airin['velocity']*self.mechstate*self.surfstate
        #self.Forceout[self.forcename]['exp']=self.Sigin['exp']
        
        self.Forceout['dev']=aforce*power
        self.Forceout['exp']=self.Sigin['exp']
        
        self.Healthout['state']=self.healthstate
        
    def updatefxn(self,faults=['nom'],opermode=[],inputs={}, outputs={}):
        
        if len(inputs)==0:
            inputs={self.signame:{'ctl': 1.0, 'exp': 1.0},self.eename:{'rate': 1.0, 'effort': 1.0},'Air': {'velocity': 1.0, 'turbulence': 1.0}}
        
        #if len(outputs)==0:
        #    outputs={self.forcename:{'dev':1.0, 'exp':1.0}, 'Air': {'velocity': 1.0, 'turbulence': 1.0}}
        #    self.Forceout=outputs[self.forcename]
                
        self.Airin=inputs['Air']
        self.EEin=inputs[self.eename]
        self.Sigin=inputs[self.signame]
        #self.Airout=outputs['Air']
        

        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={self.signame: self.Sigin, self.eename: self.EEin, 'Air':self.Airin}
        outputs={'Air': self.Airout,self.forcename:self.Forceout, self.healthname:self.Healthout}
        return {'outputs':outputs, 'inputs':inputs}
    
class combineforces:
    def __init__(self):
        self.useprop=1.0
        self.type='function'
        self.ForceLiftdnR={'dev': 1.0, 'exp': 1.0}
        self.ForceLiftdnL={'dev': 1.0, 'exp': 1.0}
        self.ForceLiftprR={'dev': 1.0, 'exp': 1.0}
        self.ForceLiftprL={'dev': 1.0, 'exp': 1.0}
        self.ForceYawC={'dev': 1.0, 'exp': 1.0}
        self.ForceRollR={'dev': 1.0, 'exp': 1.0}
        self.ForceRollL={'dev': 1.0, 'exp': 1.0}
        self.ForcePitchR={'dev': 1.0, 'exp': 1.0}
        self.ForcePitchL={'dev': 1.0, 'exp': 1.0}
        self.roll={'dev': 1.0, 'exp': 1.0}
        self.pitch={'dev': 1.0, 'exp': 1.0}
        self.yaw={'dev': 1.0, 'exp': 1.0}
        self.lift={'dev': 1.0, 'exp': 1.0}
        self.drag={'dev': 1.0, 'exp': 1.0}
        
        self.faultmodes={}
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        return 0
    def behavior(self, calctype):
        
        liftdn=1.0-0.5*self.ForceLiftdnR[calctype]-0.5*self.ForceLiftdnL[calctype]
        liftdnroll=0.5*(self.ForceLiftdnR[calctype]-self.ForceLiftdnL[calctype])
        liftdnyaw=self.ForceLiftdnR[calctype]-self.ForceLiftdnL[calctype]
        liftdndrag=abs(1.0-self.ForceLiftdnR[calctype])+abs(1.0-self.ForceLiftdnL[calctype])
        
        liftpr=0.5*self.ForceLiftprR[calctype]+0.5*self.ForceLiftprL[calctype]
        liftprroll=0.5*(self.ForceLiftprR[calctype]-self.ForceLiftprL[calctype])
        liftpryaw=self.ForceLiftprR[calctype]-self.ForceLiftprL[calctype]
        liftprdrag=abs(1.0-self.ForceLiftprR[calctype])+abs(1.0-self.ForceLiftprL[calctype])
        liftprpitch=-1.0+0.5*self.ForceLiftprR[calctype]+0.5*self.ForceLiftprL[calctype]
        
        primaryroll=0.5*(self.ForceRollR[calctype]-self.ForceRollL[calctype])
        rollyaw=self.ForceRollR[calctype]-self.ForceRollL[calctype]
        rolldrag=abs(1.0-self.ForceRollR[calctype])+abs(1.0-self.ForceRollL[calctype])
        
        primaryyaw=self.ForceYawC[calctype]
        yawdrag=abs(1.0-self.ForceYawC[calctype])
        
        primarypitch=0.5*self.ForcePitchR[calctype]+0.5*self.ForcePitchL[calctype]
        pitchyaw=self.ForcePitchR[calctype]-self.ForcePitchL[calctype]
        pitchroll=0.5*(self.ForcePitchR[calctype]-self.ForcePitchL[calctype])
        pitchdrag=abs(1.0-self.ForcePitchR[calctype])+abs(1.0-self.ForcePitchL[calctype])
        
        self.roll[calctype]=1.0+primaryroll+0.25*liftdnroll+0.5*liftprroll+0.1*pitchroll
        self.yaw[calctype]=primaryyaw+0.1*pitchyaw+0.25*rollyaw+0.1*liftdnyaw+0.25*liftpryaw
        self.pitch[calctype]=primarypitch+0.25*liftprpitch
        
        self.drag[calctype]=1.0+0.5*(0.25*liftdndrag+0.5*liftprdrag+0.25*rolldrag+0.1*yawdrag+0.2*pitchdrag)
        self.lift[calctype]=liftpr+liftdn
        

        
    def updatefxn(self,faults=['nom'],opermode=[],inputs={ \
                  'ForceLiftdnR':{'dev': 1.0, 'exp': 1.0}, \
                  'ForceLiftdnL':{'dev': 1.0, 'exp': 1.0}, 'ForceLiftprR':{'dev': 1.0, 'exp': 1.0}, \
                  'ForceLiftprL':{'dev': 1.0, 'exp': 1.0}, 'ForceYawC':{'dev': 1.0, 'exp': 1.0}, \
                  'ForceRollR':{'dev': 1.0, 'exp': 1.0}, 'ForceRollL':{'dev': 1.0, 'exp': 1.0}, \
                  'ForcePitchR':{'dev': 1.0, 'exp': 1.0}, 'ForcePitchL':{'dev': 1.0, 'exp': 1.0}},\
            outputs={'Moment':{'roll':{'dev': 1.0, 'exp': 1.0}, 'pitch':{'dev': 1.0, 'exp': 1.0},\
                               'yaw':{'dev': 1.0, 'exp': 1.0}},'Force':{'drag':{'dev': 1.0, 'exp': 1.0}, 'lift':{'dev': 1.0, 'exp': 1.0}}}):
        
        self.ForceLiftdnR=inputs['ForceLiftdnR']
        self.ForceLiftdnL=inputs['ForceLiftdnL']
        self.ForceLiftprR=inputs['ForceLiftprR']
        self.ForceLiftprL=inputs['ForceLiftprL']
        self.ForceYawC=inputs['ForceYawC']
        self.ForceRollR=inputs['ForceRollR']
        self.ForceRollL=inputs['ForceRollL']
        self.ForcePitchR=inputs['ForcePitchR']
        self.ForcePitchL=inputs['ForcePitchL']
        
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior('exp')
        self.behavior('dev')
        inputs={'ForceLiftdnR':self.ForceLiftdnR, \
                  'ForceLiftdnL':self.ForceLiftdnL, 'ForceLiftprR':self.ForceLiftprR, \
                  'ForceLiftprL':self.ForceLiftprL, 'ForceYawC':self.ForceYawC, \
                  'ForceRollR':self.ForceRollR, 'ForceRollL':self.ForceRollL, \
                  'ForcePitchR':self.ForcePitchR, 'ForcePitchL':self.ForcePitchL}
        outputs={'Moment':{'roll':self.roll, 'pitch':self.pitch, 'yaw':self.yaw},'Force':{'drag':self.drag,'lift':self.lift}}
        return {'outputs':outputs, 'inputs':inputs}
    
    
class exportForcesandMoments:
    def __init__(self):
        self.useprop=1.0
        self.roll={'dev': 1.0, 'exp': 1.0}
        self.pitch={'dev': 1.0, 'exp': 1.0}
        self.yaw={'dev': 1.0, 'exp': 1.0}
        self.lift={'dev': 1.0, 'exp': 1.0}
        self.drag={'dev': 1.0, 'exp': 1.0}
        
        self.type='classifier'
        
        self.Severity='noeffect'
        self.faultmodes={}
        self.faults=set(['nom'])
    def classify(self):
        rolldiff=self.Moment['roll']['dev']-self.Moment['roll']['exp']
        pitchdiff=self.Moment['pitch']['dev']-self.Moment['pitch']['exp']
        yawdiff=self.Moment['yaw']['dev']-self.Moment['yaw']['exp']
        liftdiff=self.Force['lift']['dev']-self.Force['lift']['exp']
        dragdiff=self.Force['drag']['dev']-self.Force['drag']['exp']
        
        
        if any(1.0<=abs(x) for x in [rolldiff, pitchdiff,yawdiff,liftdiff,dragdiff]):
            self.Severity='catastrophic'
        elif any(0.5<=abs(x) for x in [rolldiff, pitchdiff,yawdiff,liftdiff,dragdiff]):
            self.Severity='hazardous'
        elif any(0.25<=abs(x) for x in [rolldiff, pitchdiff,yawdiff,liftdiff,dragdiff]):
            self.Severity='major'
        elif any(0.0!=x for x in [rolldiff, pitchdiff,yawdiff,liftdiff,dragdiff]):
            self.Severity='minor'
        else:
            self.Severity='noeffect'
    def returnvalue(self):
        return self.Severity
    
    def updatefxn(self,faults=['nom'],opermode=[],inputs={'Moment':{'roll':{'dev': 1.0, 'exp': 1.0}, 'pitch':{'dev': 1.0, 'exp': 1.0},\
                               'yaw':{'dev': 1.0, 'exp': 1.0}},'Force':{'drag':{'dev': 1.0, 'exp': 1.0}, 'lift':{'dev': 1.0, 'exp': 1.0}}}, outputs={}):
        self.Force=inputs['Force']
        self.Moment=inputs['Moment']
        
        self.roll=inputs['Moment']['roll']
        self.pitch=inputs['Moment']['pitch']
        self.yaw=inputs['Moment']['yaw']
        self.lift=inputs['Force']['lift']
        self.drag=inputs['Force']['drag']
        
        self.classify()
        
        inputs={'Moment':{'roll':self.roll, 'pitch':self.pitch,\
                               'yaw':self.yaw},'Force':{'drag':self.drag, 'lift':self.lift}}
        outputs={}
        return {'outputs':outputs, 'inputs':inputs} 

class exportAir:
    def __init__(self):
        self.useprop=1.0
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
        
    def updatefxn(self,faults=['nom'],opermode=[],inputs={'Air':{'velocity': 1.0, 'turbulence': 1.0}}, outputs={}):
        self.Airin=inputs['Air']
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        inputs={'Air': self.Airin}
        return {'outputs':outputs, 'inputs':inputs}
    
class senseHealth:
    def __init__(self, dof, side):
        self.type= 'safetyfeature'
        self.useprop=1.0
        
        a={'falsenegative':{'rate':'rare', 'rcost':'replacement'}}
        self.condmodes=a
        b= {'falsepositive':{'rate':'veryrare', 'rcost':'replacement'}}
        self.indmodes=b
        
        self.maint={'evaluation':{'type':'majorinspection', 'sched':'monthly', 'eff':{'falsenegative':0.5, 'falsepositive':0.5}}}
        
        self.faultmodes={**self.condmodes,**self.indmodes}
        
        self.detectstate=1.0
        
        self.Sigout={'maint':1.0}
        
        if side=='C':
            self.signame='MSig'+dof.capitalize()
            self.healthname='Health'+dof.capitalize()+side
            self.assocfxn='Affect_'+dof.capitalize()
        else:
            self.signame='MSig'+dof.capitalize()+side
            self.healthname='Health'+dof.capitalize()+side
            self.assocfxn='Affect_'+dof.capitalize()+'_'+aux.rlc(side)
        
        self.Healthin={'state': 1.0}
        self.faults=set(['nom'])
    def resolvefaults(self):
        return 0
    def condfaults(self):
        return 0
    def detbehav(self):
        if self.faults.intersection(set(['falsepositive'])):
            self.detectstate=0.5
        elif self.faults.intersection(set(['falsenegative'])):
            self.detectstate=2.0
        return 0
    def behavior(self):
        
        self.Sigout['maint']=self.detectstate*self.Healthin['state']
        
        return 0
    def updatefxn(self,faults=['nom'],opermode=[],inputs={}, outputs={}):
        
        if len(inputs)==0:
            inputs={self.healthname:{'state': 1.0}}
        if len(outputs)==0:
            outputs={self.signame:{'maint':10.}}
        
        
        self.Healthin=inputs[self.healthname]
        self.faults.update(faults)
        self.condfaults()
        self.resolvefaults()
        self.detbehav()
        self.behavior()
        
        outputs={self.signame: self.Sigout}        
        return {'outputs':outputs, 'inputs':inputs}
    
class exportMaint:
    def __init__(self):
        self.type= 'classifier'
        self.Severity='operational'
        self.faultmodes={}
        self.faults=set(['nom'])
    def classify(self):
        
        self.command='operational'
        
        for thisinput in self.inputs:
            if self.inputs[thisinput]['maint']<=0.5:
                self.Severity='detected'

        return 0
    def returnvalue(self):
        return self.Severity
    def updatefxn(self,faults=['nom'],opermode=[], inputs={'MSigYaw':{'maint':1.0},'MSigRollL':{'maint':1.0},\
                  'MSigRollR':{'maint':1.0},'MSigPitchL':{'maint':1.0},'MSigPitchR':{'maint':1.0},\
                  'MSigLiftdnR':{'maint':1.0}, 'MSigLiftdnL':{'maint':1.0}, 'MSigLiftprR':{'maint':1.0},\
                  'MSigLiftprL':{'maint':1.0}}, outputs={}):
        self.inputs=inputs
        
        self.classify()
       
        return {'outputs':outputs, 'inputs':inputs}
    
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
    EELiftdnR={'EELiftdnR':{'rate': 1.0, 'effort': 1.0}}
    EELiftdnL={'EELiftdnL':{'rate': 1.0, 'effort': 1.0}}
    EELiftprR={'EELiftprR':{'rate': 1.0, 'effort': 1.0}}
    EELiftprL={'EELiftprL':{'rate': 1.0, 'effort': 1.0}}
    EEYaw={'EEYaw':{'rate': 1.0, 'effort': 1.0}}
    EERollR={'EERollR':{'rate': 1.0, 'effort': 1.0}}
    EERollL={'EERollL':{'rate': 1.0, 'effort': 1.0}}
    EEPitchR={'EEPitchR':{'rate': 1.0, 'effort': 1.0}}
    EEPitchL={'EEPitchL':{'rate': 1.0, 'effort': 1.0}}
    Distribute_EE=distributeEE()
    g.add_node('Distribute_EE', funcobj=Distribute_EE, inputs={**EE}, outputs={**EELiftdnR,\
               **EELiftprR,**EELiftprL, **EELiftdnL, **EEYaw,**EERollR,**EERollL,**EEPitchR,**EEPitchL,**EEPitchL})
    
    #INIT Import_Air
    Import_Air=importAir()
    Air={'Air':{'velocity': 1.0, 'turbulence': 1.0}}
    g.add_node('Import_Air', funcobj=Import_Air, inputs={}, outputs={**Air})
    
    #Init Import Signal
    Import_Signal=importSignal()
    Sig={'Signal':{'rollctl': 1.0, 'pitchctl': 1.0,'yawctl': 1.0,'liftprctl': 1.0,\
                   'liftdnctl': 1.0,'rollexp': 1.0, 'pitchexp': 1.0,'yawexp': 1.0,'liftprexp': 1.0,'liftdnexp': 1.0}}
    g.add_node('Import_Signal', funcobj=Import_Signal, inputs={}, outputs={**Sig})
    
    #Init Distribute Signal
    Distribute_Signal=distributeSig()
    SigLiftdnR={'SigLiftdnR':{'ctl': 1.0, 'exp': 1.0}}
    SigLiftdnL={'SigLiftdnL':{'ctl': 1.0, 'exp': 1.0}}
    SigLiftprR={'SigLiftprR':{'ctl': 1.0, 'exp': 1.0}}
    SigLiftprL={'SigLiftprL':{'ctl': 1.0, 'exp': 1.0}}
    SigYaw={'SigYaw':{'ctl': 1.0, 'exp': 1.0}}
    SigRollR={'SigRollR':{'ctl': 1.0, 'exp': 1.0}}
    SigRollL={'SigRollL':{'ctl': 1.0, 'exp': 1.0}}
    SigPitchR={'SigPitchR':{'ctl': 1.0, 'exp': 1.0}}
    SigPitchL={'SigPitchL':{'ctl': 1.0, 'exp': 1.0}}
    g.add_node('Distribute_Signal', funcobj=Distribute_Signal, inputs={**Sig}, outputs={**SigLiftdnR,**SigLiftdnL,**SigLiftprR,**SigLiftprL, \
               **SigYaw,**SigRollR,**SigRollL,**SigPitchR,**SigPitchL})
    
    #Init Affect Roll Right
    Affect_Roll_r=affectDOF('roll','R')
    ForceRollR={'ForceRollR':{'dev':1.0, 'exp':1.0}}
    HealthRollR={'HealthRollR':{'state':1.0}}
    MSigRollR={'MSigRollR':{'maint':1.0}}
    g.add_node('Affect_Roll_Right', funcobj=Affect_Roll_r, inputs={**EERollR,**Air,**SigRollR}, outputs={**Air, **ForceRollR, **HealthRollR})
    
    Sense_Health_Roll_r=senseHealth('roll','R')
    g.add_node('Sense_Health_Roll_Right',funcobj=Sense_Health_Roll_r, inputs={**HealthRollR}, outputs={**MSigRollR})
    
    #Init Affect Roll Left
    Affect_Roll_l=affectDOF('roll','L')
    ForceRollL={'ForceRollL':{'dev':1.0, 'exp':1.0}}
    HealthRollL={'HealthRollL':{'state':1.0}}
    MSigRollL={'MSigRollL':{'maint':1.0}}
    g.add_node('Affect_Roll_Left', funcobj=Affect_Roll_l, inputs={**EERollL,**Air,**SigRollL}, outputs={**Air, **ForceRollL, **HealthRollL})
    
    Sense_Health_Roll_l=senseHealth('roll','L')
    g.add_node('Sense_Health_Roll_Left',funcobj=Sense_Health_Roll_l, inputs={**HealthRollL}, outputs={**MSigRollL})
    
    #Init Affect Pitch Right
    Affect_Pitch_r=affectDOF('pitch','R')
    ForcePitchR={'ForcePitchR':{'dev':1.0, 'exp':1.0}}
    HealthPitchR={'HealthPitchR':{'state':1.0}}
    MSigPitchR={'MSigPitchR':{'maint':1.0}}
    g.add_node('Affect_Pitch_Right', funcobj=Affect_Pitch_r, inputs={**EEPitchR,**Air,**SigPitchR}, outputs={**Air, **ForcePitchR, **HealthPitchR})
    
    Sense_Health_Pitch_r=senseHealth('pitch','R')
    g.add_node('Sense_Health_Pitch_Right',funcobj=Sense_Health_Pitch_r, inputs={**HealthPitchR}, outputs={**MSigPitchR})
    
    #Init Affect Pitch Left
    Affect_Pitch_l=affectDOF('pitch','L')
    ForcePitchL={'ForcePitchL':{'dev':1.0, 'exp':1.0}}
    HealthPitchL={'HealthPitchL':{'state':1.0}}
    MSigPitchL={'MSigPitchL':{'maint':1.0}}
    g.add_node('Affect_Pitch_Left',  funcobj=Affect_Pitch_l, inputs={**EEPitchL,**Air,**SigPitchL}, outputs={**Air, **ForcePitchL, **HealthPitchL})
    
    Sense_Health_Pitch_l=senseHealth('pitch','L')
    g.add_node('Sense_Health_Pitch_Left',funcobj=Sense_Health_Pitch_l, inputs={**HealthPitchL}, outputs={**MSigPitchL})
    
    #Init Affect Yaw
    Affect_Yaw=affectDOF('yaw','C')  
    ForceYawC={'ForceYawC':{'dev':1.0, 'exp':1.0}}
    HealthYawC={'HealthYawC':{'state':1.0}}
    MSigYaw={'MSigYaw':{'maint':1.0}}
    #ForceYawC={'ForceYawC':{'force':1.0}}
    g.add_node('Affect_Yaw', funcobj=Affect_Yaw, inputs={**EEYaw,**Air,**SigYaw}, outputs={**Air, **ForceYawC, **HealthYawC})
    
    Sense_Health_Yaw=senseHealth('yaw','C')
    g.add_node('Sense_Health_Yaw',funcobj=Sense_Health_Yaw, inputs={**HealthYawC}, outputs={**MSigYaw})
    
    #Init Affect liftpr Right
    Affect_Liftpr_r=affectDOF('liftpr','R')
    ForceLiftprR={'ForceLiftprR':{'dev':1.0, 'exp':1.0}}
    HealthLiftprR={'HealthLiftprR':{'state':1.0}}
    MSigLiftprR={'MSigLiftprR':{'maint':1.0}}
    g.add_node('Affect_Liftpr_Right', funcobj=Affect_Liftpr_r, inputs={**EELiftprR,**Air,**SigLiftprR}, outputs={**Air, **ForceLiftprR, **HealthLiftprR})
    
    Sense_Health_Liftpr_r=senseHealth('liftpr','R')
    g.add_node('Sense_Health_Liftpr_Right',funcobj=Sense_Health_Liftpr_r, inputs={**HealthLiftprR}, outputs={**MSigLiftprR})
    
    #Init Affect liftpr Left
    Affect_Liftpr_l=affectDOF('liftpr','L')
    ForceLiftprL={'ForceLiftprL':{'dev':1.0, 'exp':1.0}}
    HealthLiftprL={'HealthLiftprL':{'state':1.0}}
    MSigLiftprL={'MSigLiftprL':{'maint':1.0}}
    g.add_node('Affect_Liftpr_Left', funcobj=Affect_Liftpr_l, inputs={**EELiftprL,**Air,**SigLiftprL}, outputs={**Air, **ForceLiftprL, **HealthLiftprL})
    
    Sense_Health_Liftpr_l=senseHealth('liftpr','L')
    g.add_node('Sense_Health_Liftpr_Left',funcobj=Sense_Health_Liftpr_l, inputs={**HealthLiftprL}, outputs={**MSigLiftprL})
    
    #Init Affect liftdn Right
    Affect_Liftdn_r=affectDOF('liftdn','R')
    ForceLiftdnR={'ForceLiftdnR':{'dev':1.0, 'exp':1.0}}
    HealthLiftdnR={'HealthLiftdnR':{'state':1.0}}
    MSigLiftdnR={'MSigLiftdnR':{'maint':1.0}}
    g.add_node('Affect_Liftdn_Right', funcobj=Affect_Liftdn_r, inputs={**EELiftdnR,**Air,**SigLiftdnR}, outputs={**Air, **ForceLiftdnR, **HealthLiftdnR})
    
    Sense_Health_Liftdn_r=senseHealth('liftdn','R')
    g.add_node('Sense_Health_Liftdn_Right',funcobj=Sense_Health_Liftdn_r, inputs={**HealthLiftdnR}, outputs={**MSigLiftdnR})
    
    #Init Affect liftdn Left
    Affect_Liftdn_l=affectDOF('liftdn','L')
    ForceLiftdnL={'ForceLiftdnL':{'dev':1.0, 'exp':1.0}}
    HealthLiftdnL={'HealthLiftdnL':{'state':1.0}}
    MSigLiftdnL={'MSigLiftdnL':{'maint':1.0}}
    g.add_node('Affect_Liftdn_Left', funcobj=Affect_Liftdn_l, inputs={**EELiftdnL,**Air,**SigLiftdnL}, outputs={**Air, **ForceLiftdnL, **HealthLiftdnL})
    
    Sense_Health_Liftdn_l=senseHealth('liftdn','L')
    g.add_node('Sense_Health_Liftdn_Left',funcobj=Sense_Health_Liftdn_l, inputs={**HealthLiftdnL}, outputs={**MSigLiftdnL})
    
    #Init Combine Forces
    Combine_Forces=combineforces()
    Moment={'Moment':{'roll':{'dev': 1.0, 'exp': 1.0}, 'pitch':{'dev': 1.0, 'exp': 1.0},'yaw':{'dev': 1.0, 'exp': 1.0}}}
    Force={'Force':{'drag':{'dev': 1.0, 'exp': 1.0}, 'lift':{'dev': 1.0, 'exp': 1.0}}}
    g.add_node('Combine_Forces', funcobj=Combine_Forces,\
               inputs={**ForceRollR,**ForceRollL,**ForcePitchR,**ForcePitchL,**ForceYawC,\
                       **ForceLiftprR,**ForceLiftprL,**ForceLiftdnR, **ForceLiftdnL},\
            outputs={**Moment, **Force})
      
    #Init Export Air
    Export_Air=exportAir()
    g.add_node('Export_Air', funcobj=Export_Air, inputs={**Air}, outputs={})
    
    
    #Init Export liftdn/liftpr
    Export_FM=exportForcesandMoments()
    g.add_node('Export_FM',funcobj=Export_FM, inputs={**Moment,**Force}, outputs={})
    
    #Init Sense health
    
    Export_Maint=exportMaint()
    g.add_node('Export_Maintenance', funcobj=Export_Maint, inputs={**MSigYaw,**MSigRollL, **MSigRollR, **MSigPitchL,\
                                                                   **MSigPitchR, **MSigLiftdnR, **MSigLiftdnL, **MSigLiftprR, \
                                                                   **MSigLiftprL}, outputs={})
    
    ##INITIALIZE EDGES
    #Air in flows
    g.add_edge('Import_Air', 'Affect_Roll_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Roll_Left', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Right', Air=Air['Air'])    
    g.add_edge('Import_Air', 'Affect_Pitch_Left', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Yaw', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Liftdn_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Liftdn_Left', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Liftpr_Right', Air=Air['Air'])
    g.add_edge('Import_Air', 'Affect_Liftpr_Left', Air=Air['Air'])
    #EE flows
    g.add_edge('Import_EE', 'Distribute_EE', EE=EE['EE'])
    
    g.add_edge('Distribute_EE', 'Affect_Roll_Right', EERollR=EERollR['EERollR'])
    g.add_edge('Distribute_EE', 'Affect_Roll_Left', EERollL=EERollL['EERollL'])    
    g.add_edge('Distribute_EE', 'Affect_Pitch_Right', EEPitchR=EEPitchR['EEPitchR'])    
    g.add_edge('Distribute_EE', 'Affect_Pitch_Left',EEPitchL=EEPitchL['EEPitchL'])
    g.add_edge('Distribute_EE', 'Affect_Yaw', EEYaw=EEYaw['EEYaw'])
    g.add_edge('Distribute_EE', 'Affect_Liftdn_Left', EELiftdnL=EELiftdnL['EELiftdnL'])
    g.add_edge('Distribute_EE', 'Affect_Liftdn_Right', EELiftdnR=EELiftdnR['EELiftdnR'])
    g.add_edge('Distribute_EE', 'Affect_Liftpr_Left', EELiftprL=EELiftprL['EELiftprL'])
    g.add_edge('Distribute_EE', 'Affect_Liftpr_Right', EELiftprR=EELiftprR['EELiftprR'])
    #Signal flows
    g.add_edge('Import_Signal', 'Distribute_Signal', Signal=Sig['Signal'])
    
    g.add_edge('Distribute_Signal', 'Affect_Roll_Right', SigRollR=SigRollR['SigRollR'])
    g.add_edge('Distribute_Signal', 'Affect_Roll_Left', SigRollL=SigRollL['SigRollL'])    
    g.add_edge('Distribute_Signal', 'Affect_Pitch_Right', SigPitchR=SigPitchR['SigPitchR'])    
    g.add_edge('Distribute_Signal', 'Affect_Pitch_Left', SigPitchL=SigPitchL['SigPitchL'])
    g.add_edge('Distribute_Signal', 'Affect_Yaw', SigYaw=SigYaw['SigYaw'])
    g.add_edge('Distribute_Signal', 'Affect_Liftdn_Right', SigLiftdnR=SigLiftdnR['SigLiftdnR'])
    g.add_edge('Distribute_Signal', 'Affect_Liftdn_Left', SigLiftdnL=SigLiftdnL['SigLiftdnL'])
    g.add_edge('Distribute_Signal', 'Affect_Liftpr_Right', SigLiftprR=SigLiftprR['SigLiftprR'])
    g.add_edge('Distribute_Signal', 'Affect_Liftpr_Left', SigLiftprL=SigLiftprL['SigLiftprL'])
    #Roll flows
    g.add_edge('Affect_Roll_Right','Combine_Forces',ForceRollR=ForceRollR['ForceRollR'])     
    g.add_edge('Affect_Roll_Left','Combine_Forces',ForceRollL=ForceRollL['ForceRollL'])
    #Pitch flows
    g.add_edge('Affect_Pitch_Right','Combine_Forces',ForcePitchR=ForcePitchR['ForcePitchR'])  
    g.add_edge('Affect_Pitch_Left','Combine_Forces',ForcePitchL=ForcePitchL['ForcePitchL'])
    #liftpr flows
    g.add_edge('Affect_Liftpr_Right','Combine_Forces',ForceLiftprR=ForceLiftprR['ForceLiftprR'])  
    g.add_edge('Affect_Liftpr_Left','Combine_Forces',ForceLiftprL=ForceLiftprL['ForceLiftprL'])
    #liftdn flows
    g.add_edge('Affect_Liftdn_Right','Combine_Forces',ForceLiftdnR=ForceLiftdnR['ForceLiftdnR'])  
    g.add_edge('Affect_Liftdn_Left','Combine_Forces',ForceLiftdnL=ForceLiftdnL['ForceLiftdnL'])
    #roll, pitch, yaw flows
    g.add_edge('Affect_Yaw','Combine_Forces',ForceYawC=ForceYawC['ForceYawC'])
    g.add_edge('Combine_Forces', 'Export_FM',Force=Force['Force'], Moment=Moment['Moment'])
    #Air flows 
    g.add_edge('Affect_Roll_Right', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Roll_Left', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Right', 'Export_Air', Air=Air['Air'])    
    g.add_edge('Affect_Pitch_Left', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Yaw', 'Export_Air', Air=Air['Air'])
    g.add_edge('Affect_Liftdn_Right', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Liftdn_Left', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Liftpr_Right', 'Export_Air', Air=Air['Air']) 
    g.add_edge('Affect_Liftpr_Left', 'Export_Air', Air=Air['Air']) 
    
    #Health flows
    g.add_edge('Affect_Roll_Right', 'Sense_Health_Roll_Right', HealthRollR=HealthRollR['HealthRollR'])
    g.add_edge('Affect_Roll_Left',  'Sense_Health_Roll_Left', HealthRollL=HealthRollL['HealthRollL'])   
    g.add_edge('Affect_Pitch_Right',  'Sense_Health_Pitch_Right', HealthPitchR=HealthPitchR['HealthPitchR'])   
    g.add_edge('Affect_Pitch_Left', 'Sense_Health_Pitch_Left', HealthPitchL=HealthPitchL['HealthPitchL'])
    g.add_edge('Affect_Yaw', 'Sense_Health_Yaw', HealthYawC=HealthYawC['HealthYawC'])
    g.add_edge('Affect_Liftdn_Right', 'Sense_Health_Liftdn_Right', HealthLiftdnR=HealthLiftdnR['HealthLiftdnR']) 
    g.add_edge('Affect_Liftdn_Left', 'Sense_Health_Liftdn_Left', HealthLiftdnL=HealthLiftdnL['HealthLiftdnL']) 
    g.add_edge('Affect_Liftpr_Right', 'Sense_Health_Liftpr_Right', HealthLiftprR=HealthLiftprR['HealthLiftprR']) 
    g.add_edge('Affect_Liftpr_Left', 'Sense_Health_Liftpr_Left', HealthLiftprL=HealthLiftprL['HealthLiftprL']) 
    
    #Maintenance Signal flows
    g.add_edge('Sense_Health_Roll_Right', 'Export_Maintenance', MSigRollR=MSigRollR['MSigRollR'])
    g.add_edge('Sense_Health_Roll_Left', 'Export_Maintenance', MSigRollL=MSigRollL['MSigRollL'])   
    g.add_edge('Sense_Health_Pitch_Right', 'Export_Maintenance', MSigPitchR=MSigPitchR['MSigPitchR'])   
    g.add_edge('Sense_Health_Pitch_Left', 'Export_Maintenance', MSigPitchL=MSigPitchL['MSigPitchL'])
    g.add_edge('Sense_Health_Yaw', 'Export_Maintenance', MSigYaw=MSigYaw['MSigYaw'])
    g.add_edge('Sense_Health_Liftdn_Right', 'Export_Maintenance', MSigLiftdnR=MSigLiftdnR['MSigLiftdnR']) 
    g.add_edge('Sense_Health_Liftdn_Left', 'Export_Maintenance', MSigLiftdnL=MSigLiftdnL['MSigLiftdnL']) 
    g.add_edge('Sense_Health_Liftpr_Right', 'Export_Maintenance', MSigLiftprR=MSigLiftprR['MSigLiftprR']) 
    g.add_edge('Sense_Health_Liftpr_Left', 'Export_Maintenance', MSigLiftprL=MSigLiftprL['MSigLiftprL']) 
    
    ##INITALIZE PROPOGATION GRAPHS
    backgraph=g.reverse(copy=True)
    forwardgraph=g
    fullgraph=nx.compose(backgraph, forwardgraph)
    
    return [forwardgraph,backgraph,fullgraph]
        