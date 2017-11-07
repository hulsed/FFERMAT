# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 14:34:50 2017

@author: hulsed
"""

'''This is an example of how to represent a functional model and
then experiment on it using IBFM

'''
from multiprocessing import *
import networkx as nx
import ibfm
import ibfmOpt

if __name__ == '__main__':

  elm= ibfm.Experiment('simple_controller')
  #Run with 2 then 3 simultaneous faults
  elm.run(1)
  #eps.run(2)
  #eps.run(3)
  #eps.run(4)
  scenscore,score=ibfmOpt.score(elm)
  print(scenscore, score)
  
  #con.model.printStates(flows=True)
  #note: scenarios used are found in eps.scenarios
  #more information using eps.getScenarios()

  #end states are given by: list(map(eps.runOneScenario,eps.scenarios))
  # eps.model.states
  # eps.results
  # eps.getResults()
  #end states are given by: list(map(eps.runOneScenario,eps.scenarios))
