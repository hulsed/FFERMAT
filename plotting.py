# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 14:24:49 2018

@author: hulsed
"""
import matplotlib.pyplot as plt
plt.figure(1)


x=range(20)
plt.plot(x, (fithist1+100000000), 'ro-', x, (fithist5)/5+100000000, 'g^:', x, (fithist10)/10+100000000, 'bs--', x, (fithist50)/50+100000000, 'mp-.')

plt.title('Optimization of Resilient Parameters Across Mission Utilities')
plt.xlabel('Generations (of population 20)')
plt.ylabel('Scaled Design Scoring ($/utility)')
plt.legend(['$100M utility','$500M utility','$1B utility','$5B utility'])
plt.xticks(range(0,21,5))
plt.minorticks_on()
plt.grid()
plt.show()