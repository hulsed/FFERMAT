'''This is an example of how to represent a functional model in NetworkX and
then experiment on it using IBFM

'''

import ibfm
import networkx as nx

if __name__ == '__main__':

  eps = ibfm.Experiment('eps')
  #Run with 2 simultaneous faults
  eps.run(2)