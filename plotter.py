# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 14:55:44 2019

@author: dhulse
"""

import pydot

import quad_mdl2 as mdl

import networkx as nx

import ffermat as ff

g=mdl.initialize()

ff.showgraph(g)