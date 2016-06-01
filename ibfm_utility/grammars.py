# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:25:55 2016

@author: arlittr

Machinery for applying simple grammar rules to networkx functional models


Function_flow_OptionalUniversalID_OptionalLocalID
OptionalLocalID only needed to match multiple wildcards
If OptionalLocalID is used, OptionalUniversalID is requried

[function]_[flow]_[UniversalID]_[LocalID]

Networkx graphs are created with dummy node names, where attribute "function" 
    contains the useful function information


Write rules in source directory using spreadsheets
   all rules are stored as DSM representations of functional models (.csv)
   all rules have a left hand side (lhs) and right hand side (rhs)
       rules/rule1name/lhs.csv (left hand side)
       rules/rule1name/rhs.csv (right hand side)
    
Rule naming conventions
    Every function must contain a function and flow name
    Every flowmust contain a flow name
    Functions and flows may optionally include a universal ID and a local ID
        for wildcard mapping
    Use '*' in the lhs or rhs to indicate that any function or flow is a match
    Use '^' in the rhs to indicate a new function or flow in the rhs
    Pair localids between * and ^ elements to enforce same type matching
    E.g., a node *_*_1_2 indicates any function and any flow, with universal ID
        1 and local ID 2. A second node Distribute_^_2_2 on the rhs indicates a new node to add,
        and the flow must match the flow recognized in node *_*_1_2
    Terminology: Functions contain both a function and flow - a verb and object
    Function format: function_flow_universalid_localid
    Flow format: flow_universalid_localid
    
    LHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        TODO: implement functional basis hierarchy for wildcards (E.g., TransferAnyEnergy, AnySeparateAnyMaterial)
    Function blocks must contain a function and a flow, Examples:
        Protect_*_1_1
        *_ElectricalEnergy_2_2
        Protect_ElectricalEnergy_3_3
        *_*_4_4
    RHS:
    For wildcard functions or flows (type doesn't matter, only structure)
        Use keyword '^' to copy from '*' keyword when localid is the same

"""

import copy
import networkx as nx
import networkx.algorithms.isomorphism as iso
import ibfm_utility
import os
import random
from collections import defaultdict
import string
import ibfm

class Rule(object):
    def __init__(self,name,lhspath,rhspath):
        '''
        Required arguments:
        name -- a unique name
        lhspath -- path to lhs rule, use to make a Networkx directed left hand side graph
        rhspath -- path to rhs rule, use to make a Networkx directed right hand side graph
        '''
        self.name = name
        self.lhs = self.rule2graph(lhspath)
        self.set_rhs(rhspath)
        self.anchor_nodes = set(self.lhs.nodes()).intersection(self.rhs.nodes())
        self.anchor_edges = set(self.lhs.edges()).intersection(self.rhs.edges())
        self.nodes_to_add = set(self.rhs.nodes()).difference(self.lhs.nodes())
        self.nodes_to_remove = set(self.lhs.nodes()).difference(self.rhs.nodes())
        self.edges_to_add = set(self.rhs.edges(keys=True)).difference(self.lhs.edges(keys=True))
        self.edges_to_remove = set(self.lhs.edges(keys=True)).difference(self.rhs.edges(keys=True))
    
    def __str__(self):
        return self.name    
    
    def set_lhs(self,path):
        self.lhs = self.rule2graph(path)
    
    def set_rhs(self,path):
        self.rhs = self.rule2graph(path)
        
    def rule2graph(self,path):
        """
        Convert lhs and rhs of rules into graphs
        Required arguments:
        path -- path containing lhs and rhs
        """
        #Get graph
        G = ibfm_utility.ImportFunctionalModel(path,type='dsm')
        #Redo function attributes and uids
        for n,attr in G.nodes_iter(data=True):
            verb,obj,*attrs = attr['function'].split('_')
            
            G.node[n]['verb'] = verb
            G.node[n]['obj'] = obj
            G.node[n]['function'] = verb+'_'+obj
            if len(attrs)==1:
                G.node[n]['universalid'] = attrs[0]
            if len(attrs)==2:
                G.node[n]['universalid'] = attrs[0]
                G.node[n]['localid'] = attrs[1]
            if len(attrs)==3:
                G.node[n]['universalid'] = attrs[0]
                G.node[n]['localid'] = attrs[1]+attrs[2]
                G.node[n]['verbid'] = attrs[1]
                G.node[n]['objid'] = attrs[2]
                
        for e1,e2,key,attr in G.edges_iter(data=True,keys=True):
            obj,*attrs = attr['flowType'].split('_')
            G.edge[e1][e2][key]['obj'] = obj
            if len(attrs)==1:
                G.edge[e1][e2][key]['universalid'] = attrs[0]
            if len(attrs)==2:
                G.edge[e1][e2][key]['universalid'] = attrs[0]
                G.edge[e1][e2][key]['localid'] = attrs[1]
        return G
        
    def recognize(self,graph,nodematchattr='function',edgematchattr='flowType'):
        '''
        Return a list of node id tuples that match the rule
        Required arguments:
        graph -- a Networkx directed graph
        nodematchattr -- node attribute to match on
        edgematchattr -- edge attribute to match on
        '''
        def node_function_match(label1,label2):
            function1,flow1 = label1.split('_')
            function2,flow2 = label2.split('_')
            functionIsWildcard = function1 == '*' or function2 == '*'
            flowIsWildcard = flow1 == '*' or flow2 == '*'
            if function1 == function2 and flow1 == flow2:
                return True
            elif function1 == function2 and flowIsWildcard:
                return True
            elif functionIsWildcard and flow1 == flow2:
                return True
            elif functionIsWildcard and flowIsWildcard:
                return True
            else:
                return False
                
        def edge_flow_match(label1,label2):
            flow1,*attr1 = label1.split('_')
            flow2,*attr2 = label2.split('_')
            flowIsWildcard = flow1 == '*' or flow2 == '*'
            if flow1 == flow2:
                return True
            elif flowIsWildcard:
                return True
            else:
                return False
        
        
        GM_content = iso.DiGraphMatcher(graph,self.lhs,
                                node_match=iso.generic_node_match('function',None,node_function_match),
                                edge_match=iso.generic_multiedge_match('flowType',None,edge_flow_match))    
        self.recognize_mappings = [im for im in GM_content.subgraph_isomorphisms_iter()]
        
        #TODO: Capability to *recognize* wildcards with same localid
        #eg: find 3 nodes in series that share same function
        #eg: force wildcard input flow to match a wildcard output flow
        
    def apply(self,graph,location=0,nodematchattr='obj',edgematchattr='flowType'):
        '''
        Required arguments:
        graph -- a Networkx directed graph
        mapping -- a single Dict where keys are source graph node IDs and 
            values are lhs node IDs
        '''
#       TODO: CLEAN
        if len(self.recognize_mappings) > 0:
            #pull out the single mapping dictionary of interest
            this_recognize_mapping = self.recognize_mappings[location] 
            this_rhs = copy.deepcopy(self.rhs)              
            
            #reverse mappings to match expected inputs for nx.relabel_nodes
            #and add additional mappings for new nodes to add
            reverse_mappings = {v: k for k, v in this_recognize_mapping.items()}
            for n in self.nodes_to_add:
                if '^' in this_rhs.node[n]['function']:
                    if 'localid' not in this_rhs.node[n]:
                        raise Exception('localid required to perform within-rule mappings using ^')
                    mapping_nodes = [n2 for n2 in this_rhs.nodes_iter() if this_rhs.node[n]['localid'] == this_rhs.node[n2]['localid'] and n!=n2]
                    if len(mapping_nodes) == 1:
                        mapping_node = mapping_nodes[0]
                        reverse_mappings[n] = reverse_mappings[mapping_node]
                        this_rhs.node[n]['function'] = graph.node[reverse_mappings[n]]['function']
                    else:
                        raise Exception('Each within-rule mapping must be one-to-one. Use unique localid pairs')
                
                #wildcard mappings for edges
                for n1,n2 in this_rhs.in_edges(n) + this_rhs.out_edges(n):
                    for k in this_rhs[n1][n2]:
                        if '^' in this_rhs[n1][n2][k]['flowType']:
                            print(this_rhs[n1][n2][k])
                            if 'localid' not in this_rhs[n1][n2][k]:
                                raise Exception('localid required to perform within-rule edge mappings using ^') 
                            mapping_edges = [(nstart,nend,k2) for nstart,nend in this_rhs.edges_iter() for k2 in this_rhs[nstart][nend] 
                                            if this_rhs[n1][n2][k]['localid'] == this_rhs[nstart][nend][k2]['localid'] and (n1,n2,k)!=(nstart,nend,k)]
                            for nstart,nend,k2 in mapping_edges:
                                print(n1,n2,k)
                                print(nstart,nend,k2)
                                this_rhs[n1][n2][k]['flowType'] = graph[reverse_mappings[nstart]][reverse_mappings[nend]][k2]['flowType']
                       
            #update function terms of nodes that contain wildcards
            for n in this_rhs.nodes_iter():
                if '*' in this_rhs.node[n]['function'] and n in reverse_mappings.keys():
                    reverse_mappings[n]
                    graph.node[reverse_mappings[n]]['function']
                    this_rhs.node[n]['function'] = graph.node[reverse_mappings[n]]['function']
            
            #make sure every new node has a unique id, then add them
            reverse_mapping_ids = copy.deepcopy(reverse_mappings)
            for k,v in reverse_mappings.items():
                if '^' in k:
                    #If you suspect node id collisions, try first line instead
                    reverse_mapping_ids[k] = v+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
#                    reverse_mapping_ids[k] = v+'_'+str(int(this_rhs.node[k]['universalid'])+len(graph.nodes())) 
            this_rhs = nx.relabel_nodes(this_rhs,reverse_mapping_ids)
            
            #merge graphs
            combined_graph = nx.compose(this_rhs,graph) #defaulting to attributes in graph
        else:
            raise Exception('No mappings found')
        
        #Delete nodes omitted from rhs
        for n in self.nodes_to_remove:
            
            if n in combined_graph:
                #Reconnect edges if they match flows on neighboring functions
                #This code got messy and horrible somewhere along the way...
                for p in combined_graph.predecessors(n):
                    if p not in self.rhs.nodes():
                        for s in combined_graph.successors(n):
                            for e in combined_graph.get_edge_data(p,n).values():
                                if e[edgematchattr] == combined_graph.node[s][nodematchattr] or e[edgematchattr].endswith('Signal'):
                                    attr = {edgematchattr:e[edgematchattr]}
                                    combined_graph.add_edge(p,s,attr_dict=attr)
                combined_graph.remove_node(n)
                
            elif n in reverse_mappings.keys():
                n = reverse_mappings[n]
                #Reconnect edges if they match flows on neighboring functions
                #This code got messy and horrible somewhere along the way...
                for p in combined_graph.predecessors(n):
                    if p not in self.rhs.nodes():
                        for s in combined_graph.successors(n):
                            for e in combined_graph.get_edge_data(p,n).values():
                                if e[edgematchattr] == combined_graph.node[s][nodematchattr] or e[edgematchattr].endswith('Signal'):
                                    attr = {edgematchattr:e[edgematchattr]}
                                    combined_graph.add_edge(p,s,attr_dict=attr)
                combined_graph.remove_node(n)
                
        #Delete edges omitted from rhs
        for n1,n2,k in self.edges_to_remove:
            combined_graph.remove_edge(reverse_mappings[n1],reverse_mappings[n2],k)
                
        return combined_graph
        
class Ruleset(object):
    def __init__(self,path):
        '''
        Required arguments:
        path -- the filepath on which the rules reside
        path should contain folders with unique rule names
        each rule folder must contain lhs.csv and rhs.csv
        '''
        self.rules = {}
        self.construct(path)
        
    def __iter__(self):
        for k in self.rules.keys():
            yield k
    
    def construct(self,path):
        ruleList = [path+r for r in os.listdir(path) 
            if os.path.isdir(os.path.join(path,r))]
        for ruleDir in ruleList:
            self.add_rule(ruleDir.split('/')[-1],ruleDir)

    def add_rule(self,name,path):
        self.rules[name] = Rule(name,os.path.join(path,'lhs.csv'),os.path.join(path,'rhs.csv'))
        
    def remove_rule(self,name):
        del self.rules[name]
        
    def get_rule(self,name):
        return self.rules[name]

    def build_population_random_stack(self,graph,breadth,depth):
        """
        Build population tree of a given breadth and depth using a breadth-first
        approach. Structure is singly linked where each child knows its parent
        Required arguments:
        graph -- seed graph from which to build population
        breadth -- breadth to expand each node
        depth -- depth of search tree (distance from leaves to root)
        Returns:
        pop -- a list of graphs in the newly generated population
        
        """
        pop = Tree()
        parent_address = 'root'
        parent_graph = graph
        beam = [parent_address]
        
        pop[parent_address]['graph'] = parent_graph 
        pop[parent_address]['rule'] = 'root'
        pop[parent_address]['location'] = 'root'
        pop[parent_address]['parent'] = None
        for d in range(depth):
            parent_beam = beam            
            beam = []
            node_id = 0
            beamIsNotDone = True    
            b = 1            
            
            while beamIsNotDone and len(parent_beam)>0:
                this_parent = parent_beam[-1]
                parent_graph = pop[this_parent]['graph']                      
                #select rule 
                rule = random.choice(list(self.rules.values()))
#                rule = [v for v in self.rules.values()][1] #debug
                 
                #recognize rule locations
                rule.recognize(parent_graph)  
                
                if len(rule.recognize_mappings)>0:
                    #select rule location
                    location = random.choice(range(len(rule.recognize_mappings)))
#                    location = 7 #debug
#                    location = len(rule.recognize_mappings)-1 #debug
                    
                    #apply rule
                    g_new = rule.apply(parent_graph,location=location)
                    
                    #construct address for new graph
                    address = parent_beam[-1] + '-' + str(node_id)
                    
                    #store new graph at new address
                    pop[address]['graph'] = g_new
                    pop[address]['rule'] = rule.name
                    pop[address]['location'] = location
                    pop[address]['parent'] = parent_beam[-1]
                    
                    #add new address to current beam
                    beam.append(address)
                    node_id+=1
                
                #If we've finished with this parent, move to the next one
                if b % breadth == 0:
                    del parent_beam[-1]
                    b = 0            
                b+=1
                
        return pop            

    def get_population(self,pop):
        for k in pop.keys():
            yield k,pop[k]['rule'],pop[k]['location'],pop[k]['graph']

def Tree(): 
    return defaultdict(Tree)

def check_model():
    """
    Check that the given graph can be simulated by ibfm code
    If not, automatically fix common errors
    If error is not fixed, discard
    """
    #Load functions.ibfm
    #Load modes.ibfm
    
    #Check for correct in/out of each function in model
    
    #IF mismatch, attempt to add/remove nodes to ensure compliance
    
    #Final model check, discard if not compliant