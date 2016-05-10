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
        Use keyword 'Anyfunction_UID' (e.g., Anyfunction_1) as wildcard function
        Use keyword 'Anyflow_UID' (e.g., Anyflow_1) as wildcard flow
        TODO: implement functional basis hierarchy for wildcards (E.g., TransferAnyEnergy, AnySeparateAnyMaterial)
    Function blocks must contain a function and a flow, Examples:
        ProtectAnyflow_1
        Anyfunction_1ElectricalEnergy
        ProtectElectricalEnergy
        Anyfunction_1Anyflow_1
    RHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword 'Samefunction_UID' to copy from lhs 'Anyfunction_UID' keyword
        Use keyword 'Sameflow_UID' to copy from 'Anyflow_UID' keyword
    End each new function block with a +
    End each explicitly removed function block with a - (maybe? or just don't have it in the RHS?)
    End each new flow with a + (ElectricalEnergy+,MechanicalEnergy+)
        Note that muliple flows can exist in the same cell
    End each explicitly deleted flow with a - (ElectricalEnergy-,MechanicalEnergy-)

"""

import networkx as nx

class Rule(object):
    def __init__(self,name,lhs,rhs):
        '''
        Required arguments:
        name -- a unique name
        lhs -- a Networkx directed left hand side graph
        rhs -- a Networkx directed right hand side graph
        '''
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
    def recognize(self,graph):
        '''
        Return a list of node id tuples that match the rule
        Required arguments:
        graph -- a Networkx directed graph
        '''
        
        #Get list of functions in lhs
        function_list = [n['function'] for n in self.lhs.nodes_iter()]
        #If set of all lhs functions not in graph, break
        if not set(function_list).issubset([n['function'] for n in graph.nodes_iter()]):
            return []
        #Get qty of each lhs node type in that exists in graph
        function_qtys =[]
        for f in function_list:
            function_qty = len([a for a in nx.get_node_attributes(graph,'function').values() if a in function_list])
            function_qtys.append((function_qty,f))
        function_qtys.sort()
        rarest_lhs_function = 
        #Using node type of smallest qty, construct candidate subgraphs =size(LHS)
        
        #Test whether each subgraph is isomorphic to graph      
        #Return list of matching node ids in graph
        
        return matches
    def apply(self,graph):
        '''
        Return a list of node id tuples that match the rule
        Required arguments:
        graph -- a Networkx directed graph
        '''
        
        #Create dictionary of wildcard functions and flows from lhs
        
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
        

        