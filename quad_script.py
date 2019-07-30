# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:29:45 2019

@author: dhulse
"""

import ffermat
#import pumpmodel
import quad_mdl as mdl

graph=mdl.initialize()

scenlist=ffermat.listinitfaults(graph)

fullresults=ffermat.proplist(mdl)