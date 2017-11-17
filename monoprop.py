# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 17:17:47 2017

@author: hulsed
"""

from multiprocessing import *
import networkx as nx
import ibfm
import ibfmOpt

if __name__ == '__main__':
    mono= ibfm.Experiment('monoprop')
    mono.run(1)