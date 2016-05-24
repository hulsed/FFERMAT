# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:25:55 2016

@author: arlittr

Machinery for applying simple grammar rules to networkx functional models

The documentation below is more brainstorm than accurate. Expect a rewrite once 
    I nail down how it should work.

Right now Function_flow_UniversalID_OptionalLocalID
OptionalLocalID only needed to match multiple wildcards

[function]_[flow]_[UniversalID]_u[functionid]_l[flowid]

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

import copy
import networkx as nx
import networkx.algorithms.isomorphism as iso
import ibfm_utility
import os
import random
from collections import defaultdict
import string

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
#        for n in self.rhs.nodes():
#            self.rhs.node
#        #ensure unique keys for parallel edges on rhs
#        for n1,n2 in set(self.lhs.edges()).intersection(self.rhs.edges())      
#        
#        for n1,n2 in set(self.rhs.edges()):
#            if (n1,n2) in self.lhs.edges()
#            for a in N.edge[n1][n2].values():
#                if a['wid']
#            
#            if self.lhs[a['wid'] for a in N.edge[n1][n2].values()]
#            
#            
#            if e['wid'] in self.lhs.edges(data=True):
        #Do something to set keys according to whether new or old edge/node(?)
        
    def rule2graph(self,path):
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
        matchattr -- attribute to match on
        '''
        
        wildcards = ['*','*_*']
        self.lhs.withWildcards = self.lhs
        self.lhs.withoutFunctionWildcards = copy.deepcopy(self.lhs)
        self.lhs.withoutObjWildcards = copy.deepcopy(self.lhs)
        
        for n in self.lhs.nodes():
            if self.lhs.withoutFunctionWildcards.node[n]['function'] in wildcards:
                self.lhs.withoutFunctionWildcards.remove_node(n)


#Each new unique local id in the lhs defines a pattern in the lhs
#Need to look at each structural mapping and decide whether it complies with the
#  the local id pattern 
#Remove any structural mapping that doesn't comply with all local id patterns
#Keep all structural mappings that comply with all local id patterns
        

#content mappings: verb and obj must match
#verb mappings: verb 

#        for n in self.lhs.nodes():
#            if self.lhs.withoutObjWildcards.node[n]['obj'] in wildcards:
#                self.lhs.withoutObjWildcards.remove_node(n)
        
        #Find all structural matches
        GM_structural = iso.DiGraphMatcher(graph,self.lhs)
        
        #Create graph matcher between graph and lhs
        GM_content = iso.DiGraphMatcher(graph,self.lhs.withoutFunctionWildcards,
                                node_match=iso.categorical_node_match(['function'],[None]),
                                edge_match=iso.categorical_edge_match([edgematchattr],[None]))
        
#        GM_verb_match = iso.DiGraphMatcher(graph,self.lhs.withoutObjWildcards,
#                                node_match=iso.categorical_node_match(['obj'],[None]),
#                                edge_match=iso.categorical_edge_match([edgematchattr],[None]))
                                
        structural_mappings = [im for im in GM_structural.subgraph_isomorphisms_iter()]
        content_mappings = [im for im in GM_content.subgraph_isomorphisms_iter()]
       
#        obj_mappings = [im for im in GM_verb_match.subgraph_isomorphisms_iter()]
 
#       #Keep portions of object mappings that contain wildcard characters for the verb     
#        obj_mappings = []
#        append_flag = True
#        for im in GM_verb_match.subgraph_isomorphisms_iter():
#            print('im:',im)
#            for k,v in im.items():
#                print(v)
#                if self.lhs.node[v]['verb'] != '*':
#                    append_flag = False
#                    break
#            if append_flag == True:
#                obj_mappings.append(im)
#            append_flag = True
        
#        for om in object_mappings:
            
        
#        print('structural mappings:',structural_mappings)
#        print('content mappings:',content_mappings)
#        print('object mappings:',obj_mappings)
        
        full_content_mappings = content_mappings #+ obj_mappings #+ verb_mappings + obj_mappings
        
        #List of dicts that show mappings where key = graph node and value = lhs node
        self.recognize_mappings = [sm for sm in structural_mappings 
            for fcm in full_content_mappings if fcm.items() <= sm.items()]      
            
        
    def apply(self,graph,location=0,nodematchattr='obj',edgematchattr='flowType'):
        '''
        Required arguments:
        graph -- a Networkx directed graph
        mapping -- a single Dict where keys are source graph node IDs and 
            values are lhs node IDs
        '''

        if len(self.recognize_mappings) > 0:
            reverse_mappings = {v: k for k, v in self.recognize_mappings[location].items()}
            this_rhs = nx.relabel_nodes(self.rhs,reverse_mappings)
            #ensure that new nodes have unique keys
            #important when applying the same grammar more than once
            for n in this_rhs.nodes():
                if n in graph and n in self.nodes_to_add:
                    n_new = n+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                    nx.relabel_nodes(this_rhs,{n:n_new},copy=False)
            combined_graph = nx.compose(this_rhs,graph) #defaulting to attributes in graph
        else:
            raise Exception('No mappings found')
        
#        print('combined:',combined_graph.nodes(data=True))
#        print('to remove:',self.nodes_to_remove)
        
        #Delete nodes omitted from rhs
#        print('Nodes to remove:',self.nodes_to_remove)
#        print('Reverse Mappings:',reverse_mappings.keys())

        for n in self.nodes_to_remove:
#            print('Node:',n)
            
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
                
        return combined_graph
        
#    def categorical_node_match(attr, default):
#        if nx.utils.is_string_like(attr):
#            def match(data1, data2):
#                return data1.get(attr, default) == data2.get(attr, default)
#        else:
#            attrs = list(zip(attr, default)) # Python 3
#    
#            def match(data1, data2):
#                return all(data1.get(attr, d) == data2.get(attr, d) for attr, d in attrs)
#        return match  
        
class Ruleset(object):
    def __init__(self,path):
        '''
        Optional arguments:
        rules -- an iterable List(?) of Rules
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
        
#    def set_population_random(self,graph,breadth,depth,rule_history=['root','root','g',[]]):
#        self.population = build_population_random(self,graph,breadth,depth,rule_history=['root','root','g',[]])
        
    def build_population_random(self,graph,breadth,depth,rule_history=['root','root','groot',[]]):
        
        if depth == 0:
            return rule_history
        depth-=1
        
        print(rule_history)
        
        for b in range(breadth):
            
            #select rule                
#            rule = random.choice(list(self.rules.values()))
            print([v.name for v in self.rules.values()])
            rule = [v for v in self.rules.values()][0] #debug
            print(rule)
            
            #recognize rule locations
            rule.recognize(graph)               
                            
            if len(rule.recognize_mappings)>0:
                #select rule location
#                location = random.choice(range(len(rule.recognize_mappings)))
                location = 0 #debug
                
                #apply rule
                g_new = rule.apply(graph,location=location)
              
                #Add member to population
                print(rule_history)
                rule_history[-1].append(rule.name)
                rule_history[-1].append(location)
                rule_history[-1].append(graph)
                rule_history[-1].append([])
                self.build_population_random(g_new,breadth,depth,rule_history[-1])
        return rule_history
 
    def build_population_random_stack(self,graph,breadth,depth):
        pop = Tree()
        parent_address = 'root'
#        parent_rule_history = 'root'
#        parent_location_history = 'root'
        parent_graph = graph
#        parent_beam = [parent_address]
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
#            parent_graph = pop[parent_address]['graph']  
            
            
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
#                    location = 0 #debug
                    
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
                
#                #If there are no more parents, escape loop
#                if len(parent_beam) == 0:
#                    beamIsNotDone = False
#                    parent_graph = g_new
        return pop
              

    def get_population(self,pop):
        for k in pop.keys():
            yield k,pop[k]['rule'],pop[k]['location'],pop[k]['graph']

#    def iterativePreOrder(root, add_child):
#        if not root:
#            return
#    
#        prev = None
#        curr = root
#        _next = None
#    
#        while curr:
#            if not prev or prev.left == curr or prev.right == curr:
#                func(curr)
#                if curr.left:
#                    _next = curr.left
#                else:
#                    _next = curr.right if curr.right else curr.parent
#    
#            elif curr.left == prev:
#                _next = curr.right if curr.right else curr.parent
#    
#            else:
#                _next = curr.parent
#    
#            prev = curr
#            curr = _next
    
                    
    #            
#    def pop_list(self,nodes=None, parent=None, node_list=None):
#        if parent is None:
#            return node_list
#        node_list.append([])
#        for node in nodes:
#            if node['parent'] == parent:
#                node_list[-1].append(node)
#            if node['id'] == parent:
#                parent = node['parent']
#        return pop_list(nodes, parent, node_list)


def Tree(): 
    return defaultdict(Tree)       

class Node(object):
    def __init__(self,graph,rule='Root',location=None,parent=None,children=[]):
        self.graph = graph
        self.rule = rule
        self.location = location
        self.parent = parent
        self.children = children
        
    def __str__(self):
        return str(self.graph)
    
    def add_child(self,graph,rule,location):
        self.children.append(Node(graph,rule=rule,location=location,parent=self))
    
    def print_tree(self):
        if self == None: 
            return
        print(self.rule,self.location)
        for a in self.children:
            a.print_tree()       
            

