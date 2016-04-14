'''This is an example of how to represent a functional model in NetworkX and
then experiment on it using IBFM

'''

import ibfm
import networkx as nx

g = nx.DiGraph()
g.add_node('protectEE1',function='ProtectElectricalEnergy')
g.add_node('actuateEE1',function='ActuateElectricalEnergy')
g.add_node('importBS1',function='ImportBinarySignal')
g.add_node('importCE1',function='ImportChemicalEnergy')
g.add_node('CEtoEE1',function='ConvertChemicalToElectricalEnergy')
g.add_node('exportEE1',function='ExportElectricalEnergy')
g.add_node('exportHE1',function='ExportHeatEnergy')

g.add_edge('importCE1','CEtoEE1',bond='ChemicalEnergy')
g.add_edge('CEtoEE1','exportHE1',bond='Heat')
g.add_edge('CEtoEE1','protectEE1',bond='Electrical')
g.add_edge('protectEE1','actuateEE1',bond='Electrical')
g.add_edge('actuateEE1','exportEE1',bond='Electrical')
g.add_edge('importBS1','actuateEE1',bond='Signal')

eps = ibfm.Experiment(g)
#Run with 2 then 3 simultaneous faults
eps.run(2)
eps.run(3)