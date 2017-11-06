# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 11:34:44 2017

@author: hulsed
"""
import os
import sys
import fileinput

def changeController():
    filename='functions.ibfm'
    function='ControlElectrical'
    infunction=0
    inmodes=['1','2','3']
    outmodes=['1','2','3']
    newline=''
    
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as thefile:
        for line in thefile:
            if 'function' in line and function in line:
                #print('function found')
                infunction=1
            elif 'function' in line:
                #print('other function')
                infunction=0
            elif 'condition' in line and infunction==1:
                if 'LowSignal' in line:
                    newline='    condition ' + inmodes[0] + ' to ' + outmodes[0] + ' LowSignal' + '\n'
                elif 'HighSignal' in line:
                    newline='    condition ' + inmodes[1] + ' to ' + outmodes[1] + ' HighSignal' + '\n'
                elif 'NominalSignal' in line:
                    newline='    condition ' + inmodes[2] + ' to ' + outmodes[2] + ' NominalSignal' + '\n'
                #print(line)
                line=newline
            print(line, end='')
                #print(newline)
                #cond=cond+1
                #thefile.write(line)
    tempfile.close()
    return 0

def policy2Controller:
    
    return 0
    