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
  filename = 'FunctionalModels/small_eps_2.csv'
  g = ibfm_utility.ImportFunctionalModel(filename,type='dsm')
  print('g nodes:',g.nodes(data=True))
  ibfm_utility.plotPgvGraph(g,'plots/beforeRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
  r1 = ibfm_utility.grammars.Rule('protect','ibfm_utility/rules/AddParallelAnyElectricalEnergy/lhs.csv','ibfm_utility/rules/AddParallelAnyElectricalEnergy/rhs.csv')
  r1.recognize(g)
  print('lhs:',r1.lhs.nodes(data=True))
  print('r1 mappings:',r1.recognize_mappings)
  g2=r1.apply(g)
  ibfm_utility.plotPgvGraph(g2,filename='plots/afterRule.svg',
                            promoteNodeLabels='function',
                            printRelationships='flowType')
  eps = ibfm.Experiment(g)
  #Run with 2 then 3 simultaneous faults
  eps.run(2)
  eps.run(3)