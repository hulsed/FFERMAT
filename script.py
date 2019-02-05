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
fullresults, summary = ffermat.runlist(controlsurfacemodel)

#ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','roll','NA','NA')
#endflows,endfaults,endclass=ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','liftdn','NA','NA')

ffermat.savereport(fullresults,summary, filename='report.txt')

#ffermat.runonefault(forwardgraph,backgraph,fullgraph,'Import_Signal','nosig')