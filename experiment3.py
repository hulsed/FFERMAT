# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 14:48:33 2018

@author: hulsed
"""

import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm
import importlib

importlib.reload(ibfm)
importlib.reload(io)

e1=ibfm.Experiment('eps_simple')
e1.run(1)

functions, fxnscores, fxnprobs, failutility, fxncost = io.scorefxns(e1)