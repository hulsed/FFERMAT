# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:25:55 2016

@author: arlittr

Machinery for applying simple grammar rules to networkx functional models

Networkx graphs are created with dummy node names, where attribute "function" 
    contains the useful function information


Write rules in source directory using spreadsheets
   all rules are stored as DSM representations of functional models (.csv)
   all rules have a left hand side (lhs) and right hand side (rhs)
       rules/rule1name/lhs.csv (left hand side)
       rules/rule1name/rhs.csv (right hand side)
    
Rule naming conventions
    Every function and flow must contain a function/flow name and a unique ID
        These UIDs will be used to fill a 'mappingUID' attribute on each node
    Terminology: Functions contain both a function and flow - a verb and object
    Function format: function-uid_flow-uid
    Flow format: flow-uid
    
    LHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword '*-UID' (e.g., Anyfunction_1) as wildcard function
        Use keyword '*-UID' (e.g., Anyflow_1) as wildcard flow
        TODO: implement functional basis hierarchy for wildcards (E.g., TransferAnyEnergy, AnySeparateAnyMaterial)
    Function blocks must contain a function and a flow, Examples:
        Protect-1_*-2
        *-1_ElectricalEnergy-2
        Protect-1_ElectricalEnergy_2
        *-1_*-2
    RHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword 'Samefunction_UID' to copy from lhs 'Anyfunction_UID' keyword
        Use keyword 'Sameflow_UID' to copy from 'Anyflow_UID' keyword
    End each new function block with a + (ProtectElectricalEnergy+)
    End each explicitly removed function block with a - (maybe? or just don't have it in the RHS?)
    End each new flow with a + (ElectricalEnergy+,MechanicalEnergy+)
        Note that muliple flows can exist in the same cell
    End each explicitly deleted flow with a - (ElectricalEnergy-,MechanicalEnergy-)

"""

import networkx as nx
import networkx.algorithms.isomorphism as iso
import ibfm_utility

class Rule(object):
    def __init__(self,name,lhspath,rhspath):
        '''
        Required arguments:
        name -- a unique name
        lhspath -- path to lhs rule, use to make a Networkx directed left hand side graph
        rhspath -- path to rhs rule, use to make a Networkx directed right hand side graph
        '''
        self.name = name
        self.set_lhs(lhspath)
        self.set_rhs(rhspath)
        self.anchor_nodes = set(self.lhs.nodes()).intersection(self.rhs.nodes())
        self.nodes_to_add = set(self.rhs.nodes()).difference(self.lhs.nodes())
        self.nodes_to_remove = set(self.lhs.nodes()).difference(self.rhs.nodes())
    
    def set_lhs(self,path):
        self.lhs = self.rule2graph(path)
    
    def set_rhs(self,path):
        self.rhs = self.rule2graph(path)
        
    def rule2graph(self,path):
        #Get graph
        G = ibfm_utility.ImportFunctionalModel(path,type='dsm')
        #Redo function attributes and uids
        for n,attr in G.nodes_iter(data=True):
            verb,obj = attr['function'].split('_')
            verb,verbid = verb.split('-')
            obj,objid = obj.split('-')
            G.node[n]['verb'] = verb
            G.node[n]['obj'] = obj
            G.node[n]['verbid'] = verbid
            G.node[n]['objid'] = objid
        for e1,e2,key,attr in G.edges_iter(data=True,keys=True):
            obj,objid = attr['flowType'].split('-')
            G.edge[e1][e2][key]['obj'] = obj
            G.edge[e1][e2][key]['objid'] = objid
        return G
        
    def recognize(self,graph,matchattr='function'):
        '''
        Return a list of node id tuples that match the rule
        Required arguments:
        graph -- a Networkx directed graph
        matchattr -- attribute to match on
        '''
        #Create graph matcher between graph and lhs
        GM = iso.DiGraphMatcher(graph,self.lhs,node_match=iso.categorical_node_match([matchattr],['none']))
        #List of dicts that show mappings where key = graph node and value = lhs node
        mappings = [im for im in GM.subgraph_isomorphisms_iter()]
        return mappings        
        
    def apply(self,graph,mapping,matchattr='function'):
        '''
        Required arguments:
        graph -- a Networkx directed graph
        mapping -- a single Dict where keys are source graph node IDs and 
            values are rhs node IDs
        '''
        
        #Create mapping between nodes in source graph and lhs-rhs mapping
        
        
        
        #ALIGN: Create mapping between old nodes and new nodes        
        for n in graph.nodes_iter():
            for m in self.rhs.nodes_iter():
                
        #ADDITIONS
        
        
        #DELETIONS
        
        #Create dictionary of wildcard functions and flows from lhs
#        wildcard = '*'
#        d = {}
#        for n,attr in self.lhs.nodes(data=True):
#            function,flow, = attr[matchattr].split('_')
#            if wildcard in attr[matchattr]
#            
        
        #Replace entire recognized lhs with rhs
        #add new subgraph
        #identify which nodes in new subgraph match those in old subgraph
        #connect edges
        #delete old subgraph
    
        
class Ruleset(object):
    def __init__(self,rules={}):
        '''
        Optional arguments:
        rules -- an iterable List(?) of Rules
        '''
        self.rules = rules
    def add_rule(self,rule):
        self.rules[rule.name]['lhs'] = rule.lhs
        self.rules[rule.name]['rhs'] = rule.rhs
        
    def remove_rule(self,name):
        del self.rules[name]
        
    def get_rule(self,name):
        return self.rules[name]
        

        