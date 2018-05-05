# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 13:50:37 2018

@author: hulsed
"""

import ibfmOpt as io
import numpy as np
from matplotlib import pyplot as plt
import ibfm
import importlib

importlib.reload(ibfm)
importlib.reload(io)

e1=ibfm.Experiment('monoprop5')
e1.run(1)