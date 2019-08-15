# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 14:41:50 2019

@author: dhulse
"""

import PyGnuplot as gp

#from mayavi import mlab
import numpy as np

import matplotlib.pyplot as plt

import numpy as np

from mpl_toolkits.mplot3d import Axes3D

from matplotlib.patches import Circle, Wedge, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import PatchCollection


u_area=np.array([[-300, -300,0],
                [-300, 300,0],
                [300, 300,0],
                [300, -300,0]])


fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')


ax.set_xlim3d(-300, 300)
ax.set_ylim3d(-300,300)
ax.set_zlim3d(0,200)

x = [-300,-300,300,300]
y = [-300,300,300,-300]
z = [0,0,0,0]
#verts = [list(zip(x,y,z))]
#ax.add_collection3d(Poly3DCollection(verts,color='r', zsort='min'))


#u = np.linspace(0, 2 * np.pi, 100)
#v = np.linspace(0, np.pi, 100)
#x = 10 * np.outer(np.cos(u), np.sin(v))
#y = 10 * np.outer(np.sin(u), np.sin(v))
#z = 10 * np.outer(np.ones(np.size(u)), np.cos(v))

myfig = mlab.figure(1, fgcolor=(0, 0, 0), bgcolor=(1, 1, 1))

mlab.axes(ranges=[-300, 300, -300, 300, 0, 300])
mlab.contour_surf(x,y,z, color=(0.0,0.0,0.0))

tr_x=[0,0,100]
tr_y=[0,0,0]
tr_z=[0,100,100]

mlab.plot3d(tr_x,tr_y,tr_z)


mlab.axes(figure=myfig)
mlab.show()

#plot trajectory

#ax.plot(trx,tr_y,trz)

