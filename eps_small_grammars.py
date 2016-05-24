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

if __name__ == '__main__':
  filename = 'FunctionalModels/eps.csv'
  g = ibfm_utility.ImportFunctionalModel(filename,type='dsm')
  print('g nodes:',g.nodes(data=True))
  ibfm_utility.plotPgvGraph(g,'plots/beforeRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
  r1 = ibfm_utility.grammars.Rule('AddParallelProtectEE','ibfm_utility/rules/ruleset/AddParallelProtectEE/lhs.csv','ibfm_utility/rules/ruleset/AddParallelProtectEE/rhs.csv')
  r1.recognize(g)
  print('lhs:',r1.lhs.nodes(data=True))
  print('r1 mappings:',r1.recognize_mappings)
  g2=r1.apply(g)
  ibfm_utility.plotPgvGraph(g2,filename='plots/afterRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
                            
  rs = ibfm_utility.grammars.Ruleset('/Volumes/SanDisk/Repos/IBFM/ibfm_utility/rules/ruleset/')
#  pop = rs.build_population_random(g,2,2)
  pop = rs.build_population_random_stack(g,2,3)
  print(pop)  
  
  for label,rulename,location,graph in rs.get_population(pop):
      print(label,rulename,location,graph)
      
      path = 'plots/graph_population/'
      extension = '.svg'
      filename = '-'.join([str(label),rulename,str(location)])
      ibfm_utility.plotPgvGraph(graph,filename=path+filename+extension,
                            promoteNodeLabels='function',
                            printRelationships='flowType')
#  print('pop:',pop)
#  for p in pop:
#      print('p:',p)
#      
#      filename = '-'.join([rule_location[0]+str(rule_location[1]) for rule_location in p[0]])
#      g = p[1]
#      ibfm_utility.plotPgvGraph(g,filename=path+filename+extension,
#                            promoteNodeLabels='function',
#                            printRelationships='flowType')
#      print(str(p))
  #Implement grammar Ruleset class and tree class such that
  #  a population tree is populated by randomly selecting rules from Ruleset
  #  Or just glom them all together without tree structure
  eps = ibfm.Experiment(g)
  #Run with 2 then 3 simultaneous faults
  eps.run(2)
  eps.run(3)