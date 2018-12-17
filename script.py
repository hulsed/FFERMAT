# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 09:41:32 2018

@author: Daniel Hulse
"""

import ffermat
#import pumpmodel


#ffermat.runlist(pumpmodel)

import controlsurfacemodel

[forwardgraph,backgraph,fullgraph]=controlsurfacemodel.initialize()
endflows, endfaults= ffermat.runlist(controlsurfacemodel)

#ffermat.runonefault(forwardgraph,backgraph,fullgraph,'Import_Signal','nosig')