# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 14:24:49 2018

@author: hulsed
"""
import matplotlib.pyplot as plt
plt.figure(1)


x=range(20)
plt.plot(x, (fithist1), 'ro-', x, (fithist5)/5, 'g^:', x, (fithist10)/10, 'bs--', x, (fithist50)/50, 'mp-.')

plt.title('Optimization Across Worst Failure Costs')
plt.xlabel('Generations (of population 20)')
plt.ylabel('Scaled Score (\$ / \$failure)')
plt.legend(['$100M failure','$500M failure','$1B failure','$5B failure'])
plt.xticks(range(0,20,5))
plt.minorticks_on()
plt.grid()
plt.show()