# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 10:18:54 2018

@author: Daniel Hulse
"""


import numpy as np
##BASIC OPERATIONS

#x1 takes precedence over x2 in deciding if num is inf or zero
def m2to1(x):
    if np.size(x)>2:
        x=[x[0], m2to1(x[1:])]
    if x[0]==np.inf:
        y=np.inf
    elif x[1]==np.inf:
        if x[0]==0.0:
            y=0.0
        else:
            y=np.inf
    else:
        y=x[0]*x[1]
    return y
#truncates value to 2 (useful if behavior unchanged by increases)
def trunc(x):
    if x>2.0:
        y=2.0
    else:
        y=x
    return y

def truncn(x, n):
    if x>n:
        y=n
    else:
        y=x
    return y

def dev(x):
    y=abs(abs(x-1.0)-1.0)
    return y

def rlc(x):
    y='NA'
    if x=='R':
        y='Right'
    if x=='L':
        y='Left'
    if x=='C':
        y='Center'
    return y

def square(center,xw,yw):
    square=[[center[0]-xw/2,center[1]-yw/2],\
            [center[0]+xw/2,center[1]-yw/2], \
            [center[0]+xw/2,center[1]+yw/2],\
            [center[0]-xw/2,center[1]+yw/2]]
    return square

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

def inrange(area, x, y):
    point=Point(x,y)
    polygon=Polygon(area)
    return polygon.contains(point)


