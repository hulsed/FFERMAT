# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 14:34:50 2017

@author: hulsed
"""

'''This is an example of how to represent a functional model and
then experiment on it using IBFM

'''
from multiprocessing import *
import ibfm

if __name__ == '__main__':

  eps = ibfm.Experiment('simple_controller')
  #Run with 2 then 3 simultaneous faults
  eps.run(1)
  eps.run(2)
  #eps.run(3)
  #eps.run(4)
  
  
  #note: scenarios used are found in eps.scenarios
  #more information using eps.getScenarios()
  #end states are given by: list(map(eps.runOneScenario,eps.scenarios))