#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 18:16:39 2018

@author: daniel
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

g=nx.DiGraph()
g.add_node('inputfxn', funcdef='fxn1')
g.add_node('mainfxn', funcdef='fxn2')
g.add_node('outputfxn', funcdef='fxn3')

g.add_edge('inputfxn', 'mainfxn', flow='inflow')
g.add_edge('mainfxn','outputfxn', flow='outflow')

labels=dict()
for (u,v,label) in g.edges.data('flow'):
    labels[(u,v)]=label

edges=g.edges()


pos=nx.spring_layout(g)
nx.draw_networkx(g,pos)
nx.draw_networkx_edge_labels(g,pos,edge_labels=labels)
plt.show()

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
        self.faultmodes=[['infv','lowv','nov']]
    def detmode(self):
        if self.fault!='nom':
            self.mode=self.fault
    def behavior(self):
        if self.mode=='infv':
            self.EEout=np.inf
        elif self.mode=='nov':
            self.EEout=0.0
        elif self.mode=='lowv':
            self.EEout=0.5
        else:
            self.EEout=self.EEin
    def updatefxn(self,fault='nom'):
        self.fault=fault
        self.detmode()
        self.behavior()
        return self.EEout
        
class importWat:
    def __init__(self):
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.faultmodes=[['nowat','hiwat'],['highvisc','solids']]
    def detmode(self):
        if self.fault!='nom':
            self.mode=self.fault
    def behavior(self):
        if self.mode=='nowat':
            self.Watout['level']=0.0
        elif self.mode=='hiwat':
            self.Watout['level']=2.0
        if self.mode=='highvisc':
            self.Watout['visc']=2.0
        elif self.mode=='solids':
            self.Watout['visc']=np.inf
        
        self.Watout['flow']=self.Watout['level']/self.Watout['visc']
    def updatefxn(self,fault='nom'):
        self.fault=fault
        self.detmode()
        self.behavior()
        return self.Watout
    
class moveWat:
    def __init__(self):
        self.EEin=1.0
        self.Watin={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.Sigout=1.0
        self.Watout={'level':1.0, 'visc':1.0, 'flow':1.0}
        self.faultmodes=[['shortc','openc'],['jam','break', 'misalign'], ['poorsensing', 'nosensing']]
        self.faults=set()
        self.condmodes=[['jam','break'],['shortc','openc']]
        self.opermodes=['on','off']
        self.mechstate=1.0
        self.sensestate=1.0
    #modes caused by flows in and out of the model (and/or time later?)
    def triggermodes(self):
        if self.EEin==np.inf:
            self.faults.add('openc')
            self.faults.add('nosensing')
        if self.Watin['visc']==np.inf:
            self.faults.add('break')
            self.faults.add('openc')
        if self.Watin['level']==np.inf:
            self.faults.add('shortc')
            self.faults.add('nosensing')
    #determines the effect of fault modes on behavior function
    def detbehav(self):
        if self.faults.intersection(set['shortc','openc']):
            self.elecstate=0
        if self.faults.intersection(set(['break'])):
            self.mechstate=0
        elif self.faults.intersection(set(['jam', 'misalign'])):
            self.mechstate=0.5
        if self.faults.intersection(set(['nosensing'])):
            self.sensestate=0
        elif self.faults.intersection(set(['poorsensing'])):
            self.sensestate=0.5
    #calculates behavior
    def behavior(self):
        self.Watout['flow']=self.elecstate*self.mechstate*self.Watout['level']/self.Watout['visc']*self.EEin
        self.Sigout=self.elecstate*self.sensestate*self.EEin
        
    def updatefxn(self,fault='nom'):
        self.fault=fault
        self.detmode()
        self.behavior()
        return self.Watout


    