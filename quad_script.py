# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 10:29:45 2019

@author: dhulse
"""

import ffermat
import auxfunctions as aux
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import quad_mdl2 as mdl

graph=mdl.initialize()

#scenlist=ffermat.listinitfaults(graph, mdl.times)

endflows, endfaults, endclass, endgraph, nomgraph, flowhist3=ffermat.proponefault('AffectDOF', 'nom', mdl, time=6, track={'DOFs','Dir1', 'Env1'})
ffermat.showgraph(endgraph,nomgraph)
ffermat.plotflowhist(flowhist3, 'N/A', time=0)

#x=flowhist3['nominal']['Env1']['x']
#y=flowhist3['nominal']['Env1']['y']
#z=flowhist3['nominal']['Env1']['elev']
#
#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
#ax.set_xlim3d(-100, 100)
#ax.set_ylim3d(-100,100)
#ax.set_zlim3d(0,100)
#ax.plot(x,y,z)
#plt.close()

#Check various scenarios individually

endflows, endfaults, endclass, endgraph, nomgraph, flowhist=ffermat.proponefault('DistEE', 'short', mdl, time=5, track={'EE_1', 'Env1'})
ffermat.showgraph(endgraph,nomgraph)

ffermat.plotflowhist(flowhist, 'StoreEE short', time=5)

endflows, endfaults, endclass, endgraph, nomgraph, flowhist2=ffermat.proponefault('AffectDOF', 'RFshort', mdl, time=13, track={'DOFs', 'Env1'})
ffermat.showgraph(endgraph,nomgraph)
ffermat.plotflowhist(flowhist2, 'RFpropbreak', time=13)

xnom=flowhist2['nominal']['Env1']['x']
ynom=flowhist2['nominal']['Env1']['y']
znom=flowhist2['nominal']['Env1']['elev']

x=flowhist2['faulty']['Env1']['x']
y=flowhist2['faulty']['Env1']['y']
z=flowhist2['faulty']['Env1']['elev']

fig2 = plt.figure(2)
ax2 = fig2.add_subplot(111, projection='3d')
ax2.set_xlim3d(-100, 100)
ax2.set_ylim3d(-100,100)
ax2.set_zlim3d(0,100)
ax2.plot(xnom,ynom,znom)
ax2.plot(x,y,z)
ax2.set_title('Fault response to RFpropbreak fault at t=13')
ax2.legend(['Nominal Flightpath','Faulty Flighpath'], loc=4)

plt.show()
plt.close()

#fullresults=ffermat.proplist(mdl)
