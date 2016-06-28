# -*- coding: utf-8 -*-
"""
Created on Thu May 12 18:05:13 2016

@author: arlittr
"""

'''
This file is a testbed for validating grammars

'''

import sys
sys.path.append('ibfm_utility')

import ibfm
import ibfm_utility
import os

def test_rule(rulename,rulepath,g):
    ibfm_utility.plotPgvGraph(g,'plots/beforeRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
    r = ibfm_utility.grammars.Rule(rulename,os.path.join(rulepath,'lhs.csv'),os.path.join(rulepath,'rhs.csv'))
    r.recognize(g)
    g = r.apply(g)
#    g = r.apply(g,1)
    print(r.recognize_mappings)
    ibfm_utility.plotPgvGraph(g,filename='plots/afterRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')

if __name__ == '__main__':
    #get seed functional model
    filename = 'FunctionalModels/eps.csv'
    g = ibfm_utility.ImportFunctionalModel(filename,type='dsm')
    
    #test given rule
#    rulename = 'AddSeriesAnyElectricalEnergy'
#    rulepath = 'ibfm_utility/rules/testRules/AddSeriesAnyElectricalEnergy/'
#    test_rule(rulename,rulepath,g)
    
    #create population from ruleset
    ruleset_path = 'ibfm_utility/rules/ruleset/'        
    rs = ibfm_utility.grammars.Ruleset(ruleset_path)
    breadth = 3
    depth = 3
    pop = rs.build_population_random_stack(g,breadth,depth) 
  
    #graph each member of population
    path = 'plots/graph_population/'
    extension = '.svg'
    for f in os.listdir(path): 
        if f.endswith(extension):
            os.remove(os.path.join(path,f)) 
    for label,rulename,location,graph in rs.get_population(pop):
        print(label,rulename,location,graph)
        path = 'plots/graph_population/'
        extension = '.svg'
        filename = '-'.join([str(label),rulename,str(location)])
        ibfm_utility.plotPgvGraph(graph,filename=os.path.join(path,filename)+extension,
                            promoteNodeLabels='function',
                            printRelationships='flowType')
    
#    #Create and run experiments (broken until we resolve FunctionFlow vs Function_Flow convention)
#    eps = ibfm.Experiment(g)
#    #Run with 2 then 3 simultaneous faults
#    eps.run(2)
#    eps.run(3)