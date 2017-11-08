# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:05:16 2017

@author: hulsed
"""

from multiprocessing import *
import networkx as nx
import ibfm
import ibfmOpt

if __name__ == '__main__':
    
    #t,s=ibfmOpt.policy2strs([1,2,3],3)
    ibfmOpt.changeController()