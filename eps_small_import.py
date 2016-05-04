'''This is an example of how to import a functional model from csv

'''

import sys
sys.path.append('ibfm_utility')

import ibfm
import ibfm_utility


if __name__ == '__main__':
  filename = 'FunctionalModels/small_eps.csv'
  g = ibfm_utility.ImportFunctionalModel(filename,type='dsm')
  ibfm_utility.plotPgvGraph(g,
                            promoteNodeLabels='function',
                            printRelationships='flowType')
  eps = ibfm.Experiment(g)
  #Run with 2 then 3 simultaneous faults
  eps.run(2)
  eps.run(3)