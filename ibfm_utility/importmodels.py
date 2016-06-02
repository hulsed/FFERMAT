# -*- coding: utf-8 -*-

"""
Created on Tue May  3 11:34:04 2016

@author: arlittr
"""

import networkx as nx
import numpy as np
import csv

def ImportFunctionalModel(path,type='dsm'):
    if type=='dsm':
        componentNames,M = readCFG(path)
        systemname = path.split('.')[-1].split('/')[-1]
        G = buildGraph(componentNames,M,systemname)
        splitFunctionAttr(G)
        return G
        
def readCFG(filename):
    with open(filename,'rU') as f:
        reader = csv.reader(f)
        thisfile = []
        for r in reader:
            thisfile.append(r)    
            
   #Get the top row from the CFG and use as component list
    components = thisfile[0][1:]
    components = [''.join(c.split()) for c in components]
    
    #Get the rest of the CFG matrix
    M = thisfile[1:]
    M = [row[1:] for row in M]
    M = [[''.join(a.strip().split()) for a in row] for row in M]
    
    return components,M
     
def buildGraph(componentNames,M,systemname=None):
    componentNamesDictIterable = {}
    componentNamesCounter = {c:0 for c in componentNames}
    
    #make new graph
    G = nx.MultiDiGraph(system=systemname)
    
    #make nodes
    #Each node has unique ID of component type + dictionary key
    #function property gives component taxonomy type
    k=0
     
    try:
         #This code will become useful if we want to analyze multiple models at once
        for c in componentNames:
            nodeName = c+'_'+str(componentNamesCounter[c])
            inverseComponentDict = {v:k for k,v in componentNamesDict.items()}
            G.add_node(nodeName,function=inverseComponentDict[c],order=k,cid=componentNamesCounter[c])
            componentNamesDictIterable[k]=nodeName
            componentNamesCounter[c]+=1
            k+=1
    except:
#        print('componentNamesDict does not exist, using natural names')
        for c in componentNames:
            nodeName = c+'_'+str(componentNamesCounter[c])
            G.add_node(nodeName,function=c,order=k,cid=componentNamesCounter[c])
            componentNamesDictIterable[k]=nodeName
            componentNamesCounter[c]+=1
            k+=1
    
    #iterate over matrix to build connections
    M = np.array(M)
    it = np.nditer(M, flags=['multi_index'])
    while not it.finished:
        connection = str(it[0])
        if connection != '':
#             print connection,type(connection),it.multi_index[:],type(it.multi_index[0])
            connections = connection.split(',')
            for c in connections:
                #rebuild unique node IDs from type and key
                node1 = componentNamesDictIterable[it.multi_index[0]]
                node2 = componentNamesDictIterable[it.multi_index[1]]
                #create new edge
                G.add_edge(node1,node2,flowType=c)
        it.iternext()
    return G

def splitFunctionAttr(G):
    for n,attr in G.nodes_iter(data=True):
        verb,obj,*_ = attr['function'].split('_')
        G.node[n]['verb'] = verb
        G.node[n]['obj'] = obj
 
def componentNamesList2keys(componentNamesList):
    #creates a canonical dictionary of ids based on the functions or components that we read in
    componentNames = list(set([component for component in componentNamesList]))
    componentNames.sort()
    componentDict = {c:str(i) for i,c in zip(range(len(componentNames)),componentNames)}
    return [[componentDict[c] for c in componentsInOneProduct] for componentsInOneProduct in componentNamesList],componentDict