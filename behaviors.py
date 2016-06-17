# -*- coding: utf-8 -*-
"""
behaviors for use by modes and conditions
"""

class ZeroEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Zero())
  def test(self):
    return self.in_bond.effort == Zero()
class AnyZeroEffort(Behavior):
  def test(self):
    for bond in self.in_bonds:
      if bond.effort == Zero():
        return True
    return False
class AnyNonZeroEffort(Behavior):
  def test(self):
    for bond in self.in_bonds:
      if bond.effort != Zero():
        return True
    return False
class NoZeroEffort(Behavior):
  def test(self):
    for bond in self.in_bonds:
      if bond.effort == Zero():
        return False
    return True
class AllZeroEffort(Behavior):
  def apply(self):
    for bond in self.out_bonds:
      bond.setEffort(Zero())
  def test(self):
    for bond in self.in_bonds:
      if bond.effort != Zero():
        return False
    return True
class ZeroFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(Zero())
  def test(self):
    return self.out_bond.flow == Zero()
class AllZeroFlow(Behavior):
  def apply(self):
    for bond in self.in_bonds:
      bond.setFlow(Zero())
class NonZeroEffort(Behavior):
  def test(self):
    return self.in_bond.effort != Zero()
class LowEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Low())
  def test(self):
    self.in_bond.effort <= Low()
class NominalEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Nominal())
  def test(self):
    return self.in_bond.effort == Nominal()
class AllNominalEffort(Behavior):
  def apply(self):
    for bond in self.out_bonds:
      bond.setEffort(Nominal())
  def test(self):
    for bond in self.in_bonds:
      if bond.effort != Nominal():
        return False
    return True
class NonNominalEffort(Behavior):
  def test(self):
    return self.in_bond.effort != Nominal()
class NominalFlow(Behavior):
  def test(self):
    return self.out_bond.flow == Nominal()
class HighEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(High())
  def test(self):
    return self.in_bond.effort >= High()
class HighestEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Highest())
  def test(self):
    return self.in_bond.effort >= Highest()
class HighEffortOut(Behavior):
  def test(self):
    return self.out_bond.effort >= High()
class HighestEffortOut(Behavior):
  def test(self):
    return self.out_bond.effort >= Highest()

class HighFlow(Behavior):
  def test(self):
    return self.out_bond.flow >= High()
class HighestFlow(Behavior):
  def test(self):
    return self.out_bond.flow >= Highest()
class AnyHighestFlow(Behavior):
  def test(self):
    for bond in self.out_bonds:
      if bond.flow >= Highest():
        return True
    return False
class EqualEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(self.in_bond.effort)
class BranchEqualEffort(Behavior):
  def apply(self):
    for bond in self.out_bonds:
      bond.setEffort(self.in_bond.effort)
class EqualFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(self.out_bond.flow)
class IncreasedFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(State(self.out_bond.flow+1))
class DecreasedFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(State(max(0,self.out_bond.flow-1)))
class IncreasedEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(State(self.in_bond.effort+1))
class DecreasedEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(State(max(0,self.in_bond.effort-1)))
class TranslateFlowToEffort(Behavior):
  def apply(self):
    self.out_bonds[1].setEffort(self.out_bonds[0].flow)
class TranslateIncreasedFlowToEffort(Behavior):
  def apply(self):
    self.out_bonds[1].setEffort(State(self.out_bonds[0].flow+1))
class TranslateDecreasedFlowToEffort(Behavior):
  def apply(self):
    self.out_bonds[1].setEffort(State(max(0,self.out_bonds[0].flow-1)))
class ReflectiveFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(self.in_bond.effort)
class LessReflectiveFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(State(max(0,self.in_bond.effort-1)))
  def test(self):
    return self.out_bond.flow < self.out_bond.effort
class MuchLessReflectiveFlow(Behavior):
  def test(self):
    return self.out_bond.flow < self.out_bond.effort -1
class FreeFlow(Behavior):
  def apply(self):
    if self.in_bond.effort:
      self.in_bond.setFlow(Highest())
    else:
      self.in_bond.setFlow(Zero())
class HighestEffortAmplification(Behavior):
  def apply(self):
    if self.in_bond.effort:
      self.out_bond.setEffort(Highest())
    else:
      self.out_bond.setEffort(Zero())
class InverseFlow(Behavior):
  def apply(self):
    if self.out_bond.flow > Nominal():
      self.in_bond.setFlow(Low())
    elif self.out_bond.flow < Nominal():
      self.in_bond.setFlow(High())
    else:
      self.in_bond.setFlow(Nominal())
class TranslateInverseFlowToEffort(Behavior):
  def apply(self):
    if self.out_bonds[0].flow > Nominal():
      self.out_bonds[1].setEffort(Low())
    elif self.out_bonds[0].flow < Nominal():
      self.out_bonds[1].setEffort(High())
    else:
      self.out_bonds[1].setEffort(Nominal())
class MinimumEffort(Behavior):
  '''Takes the minimum effort from all in bonds and sets the out bond.'''
  def apply(self):
    value = max(0,min([bond.effort for bond in self.in_bonds]))
    self.out_bond.setEffort(State(value))
class DecreasedMinimumEffort(Behavior):
  def apply(self):
    value = max(0,min([bond.effort-1 for bond in self.in_bonds]))
    self.out_bond.setEffort(State(value))
class MaximumFlow(Behavior):
  def apply(self):
    value = max([bond.flow for bond in self.out_bonds])
    self.in_bond.setFlow(State(value))
class MaximumEffort(Behavior):
  def apply(self):
    value = max([bond.effort for bond in self.in_bonds])
    self.out_bond.setEffort(State(value))
class EqualFlowFromMaximumEffort(Behavior):
  def apply(self):
    max_effort = max([bond.effort for bond in self.in_bonds])
    for bond in self.in_bonds:
      if bond.effort == max_effort:
        bond.setFlow(self.out_bond.flow)
      else:
        bond.setFlow(Zero())