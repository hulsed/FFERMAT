'''This is an example of how to represent a functional model in NetworkX and
then experiment on it using IBFM

'''

import ibfm
import networkx as nx

if __name__ == '__main__':
  g = nx.DiGraph()
  #Battery 1
  g.add_node('importCE1',function='ImportChemicalEnergy')
  g.add_node('CEtoEE1',function='ConvertChemicalToElectricalEnergy')
  g.add_node('exportHE1',function='ExportHeatEnergy')
  g.add_edge('importCE1','CEtoEE1',bond='ChemicalEnergy')
  g.add_edge('CEtoEE1','exportHE1',bond='Heat')
  #Circuit Protection 1
  g.add_node('protectEE1',function='ProtectElectricalEnergy')
  g.add_edge('CEtoEE1','protectEE1',bond='Electrical')
  #Branch
  g.add_node('branchEE1',function='BranchElectricalEnergy')
  g.add_edge('protectEE1','branchEE1',bond='Electrical')
  #Relay 1
  g.add_node('importBS1',function='ImportBinarySignal')
  g.add_node('actuateEE1',function='ActuateElectricalEnergy')
  g.add_edge('branchEE1','actuateEE1',bond='Electrical')
  g.add_edge('importBS1','actuateEE1',bond='Signal')
  #Inverter 1
  g.add_node('protectEE2',function='ProtectElectricalEnergy')
  g.add_node('invertEE1',function='InvertElectricalEnergy')
  g.add_node('exportHE2',function='ExportHeatEnergy')
  g.add_node('protectEE3',function='ProtectElectricalEnergy')
  g.add_edge('actuateEE1','protectEE2',bond='Electrical')
  g.add_edge('invertEE1','exportHE2',bond='Heat')
  g.add_edge('protectEE2','invertEE1',bond='Electrical')
  g.add_edge('invertEE1','protectEE3',bond='Electrical')
  #Branch
  g.add_node('branchEE2',function='BranchElectricalEnergy')
  g.add_edge('protectEE3','branchEE2',bond='Electrical')
  #Pump 1
  g.add_node('EEtoME1',function='ConvertElectricalToMechanicalEnergy')
  g.add_node('exportHE3',function='ExportHeatEnergy')
  g.add_node('importM1',function='ImportMaterial')
  g.add_node('transportM1',function='TransportMaterial')
  g.add_node('exportM1',function='ExportMaterial')
  g.add_edge('branchEE2','EEtoME1',bond='Electrical')
  g.add_edge('EEtoME1','exportHE3',bond='Heat')
  g.add_edge('importM1','transportM1',bond='Material')
  g.add_edge('EEtoME1','transportM1',bond='MechanicalEnergy')
  g.add_edge('transportM1','exportM1',bond='Material')
  #Fan 1
  g.add_node('EEtoME2',function='ConvertElectricalToMechanicalEnergy')
  g.add_node('exportHE4',function='ExportHeatEnergy')
  g.add_node('importM2',function='ImportMaterial')
  g.add_node('transportM2',function='TransportMaterial')
  g.add_node('exportM2',function='ExportMaterial')
  g.add_edge('branchEE2','EEtoME2',bond='Electrical')
  g.add_edge('EEtoME2','exportHE4',bond='Heat')
  g.add_edge('importM2','transportM2',bond='Material')
  g.add_edge('EEtoME2','transportM2',bond='MechanicalEnergy')
  g.add_edge('transportM2','exportM2',bond='Material')
  #Light 1
  g.add_node('EEtoOE1',function='ConvertElectricalToOpticalEnergy')
  g.add_node('exportHE5',function='ExportHeatEnergy')
  g.add_node('exportOE1',function='ExportOpticalEnergy')
  g.add_edge('branchEE2','EEtoOE1',bond='Electrical')
  g.add_edge('EEtoOE1','exportHE5',bond='Heat')
  g.add_edge('EEtoOE1','exportOE1',bond='OpticalEnergy')

  #Relay 2
  g.add_node('importBS2',function='ImportBinarySignal')
  g.add_node('actuateEE2',function='ActuateElectricalEnergy')
  g.add_edge('branchEE1','actuateEE2',bond='Electrical')
  g.add_edge('importBS2','actuateEE2',bond='Signal')
  #Inverter 2
  g.add_node('protectEE4',function='ProtectElectricalEnergy')
  g.add_node('invertEE2',function='InvertElectricalEnergy')
  g.add_node('exportHE6',function='ExportHeatEnergy')
  g.add_node('protectEE5',function='ProtectElectricalEnergy')
  g.add_edge('actuateEE2','protectEE4',bond='Electrical')
  g.add_edge('invertEE2','exportHE6',bond='Heat')
  g.add_edge('protectEE4','invertEE2',bond='Electrical')
  g.add_edge('invertEE2','protectEE5',bond='Electrical')
  #Branch
  g.add_node('branchEE3',function='BranchElectricalEnergy')
  g.add_edge('protectEE5','branchEE3',bond='Electrical')
  #Pump 1
  g.add_node('EEtoME3',function='ConvertElectricalToMechanicalEnergy')
  g.add_node('exportHE7',function='ExportHeatEnergy')
  g.add_node('importM3',function='ImportMaterial')
  g.add_node('transportM3',function='TransportMaterial')
  g.add_node('exportM3',function='ExportMaterial')
  g.add_edge('branchEE3','EEtoME3',bond='Electrical')
  g.add_edge('EEtoME3','exportHE7',bond='Heat')
  g.add_edge('importM3','transportM3',bond='Material')
  g.add_edge('EEtoME3','transportM3',bond='MechanicalEnergy')
  g.add_edge('transportM3','exportM3',bond='Material')
  #Fan 1
  g.add_node('EEtoME4',function='ConvertElectricalToMechanicalEnergy')
  g.add_node('exportHE8',function='ExportHeatEnergy')
  g.add_node('importM4',function='ImportMaterial')
  g.add_node('transportM4',function='TransportMaterial')
  g.add_node('exportM4',function='ExportMaterial')
  g.add_edge('branchEE3','EEtoME4',bond='Electrical')
  g.add_edge('EEtoME4','exportHE8',bond='Heat')
  g.add_edge('importM4','transportM4',bond='Material')
  g.add_edge('EEtoME4','transportM4',bond='MechanicalEnergy')
  g.add_edge('transportM4','exportM4',bond='Material')
  #Light 1
  g.add_node('EEtoOE2',function='ConvertElectricalToOpticalEnergy')
  g.add_node('exportHE9',function='ExportHeatEnergy')
  g.add_node('exportOE2',function='ExportOpticalEnergy')
  g.add_edge('branchEE3','EEtoOE2',bond='Electrical')
  g.add_edge('EEtoOE2','exportHE9',bond='Heat')
  g.add_edge('EEtoOE2','exportOE2',bond='OpticalEnergy')

  eps = ibfm.Experiment(g)
  #Run with 2 simultaneous faults
  eps.run(2)