# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 09:41:32 2018

@author: Daniel Hulse
"""

import ffermat
#import pumpmodel


#ffermat.runlist(pumpmodel)

import controlsurfacemodel_cbm as mdl

[forwardgraph,backgraph,fullgraph]=mdl.initialize()
fullresults, summary = ffermat.runlist(mdl)

#[forwardgraph,backgraph,fullgraph]=controlsurfacemodel.initialize()
#ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','liftup','Import_Signal','nosig')

#fxn=ffermat.getfxn(forwardgraph, 'Export_FM')
#fxn.Severity

#ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','roll','NA','NA')
#ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','forward','Import_Signal','nosig')
#endflows,endfaults,endclass=ffermat.runonefault(controlsurfacemodel, forwardgraph, backgraph, fullgraph, 'Import_Signal','liftdn','NA','NA')

ffermat.savereport(fullresults,summary, filename='report.txt')

#ffermat.runonefault(forwardgraph,backgraph,fullgraph,'Import_Signal','nosig')

#ffermat.runonefault(forwardgraph,backgraph,fullgraph,'Affect_Liftdn_Left')