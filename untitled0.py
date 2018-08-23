#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 17:05:31 2018

@author: daniel
"""

def f1(num):
    a=1
    def f11(num,a):
        a=num
        if num>1:
            a=f12(num,a)
        return a
    def f12(num,a):
        a=num
        if num<1:
            a=f11(num,a)
        return a
    a=f11(num,a)
    return a