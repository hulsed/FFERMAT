# -*- coding: utf-8 -*-
"""
behaviors for use by modes and conditions
"""
from ibfm import Behavior, State, Zero, Nominal, Low, High, Highest

class ZeroEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(Zero())
  def test(self):
    return self.in_flow.effort == Zero()
class AnyZeroEffort(Behavior):
  def test(self):
    for flow in self.in_flows:
      if flow.effort == Zero():
        return True
    return False
class AnyNonZeroEffort(Behavior):
  def test(self):
    for flow in self.in_flows:
      if flow.effort != Zero():
        return True
    return False
class NoZeroEffort(Behavior):
  def test(self):
    for flow in self.in_flows:
      if flow.effort == Zero():
        return False
    return True
class AllZeroEffort(Behavior):
  def apply(self):
    for flow in self.out_flows:
      flow.setEffort(Zero())
  def test(self):
    for flow in self.in_flows:
      if flow.effort != Zero():
        return False
    return True
class ZeroRate(Behavior):
  def apply(self):
    self.in_flow.setRate(Zero())
  def test(self):
    return self.out_flow.rate == Zero()
class AllZeroRate(Behavior):
  def apply(self):
    for flow in self.in_flows:
      flow.setRate(Zero())
class NonZeroEffort(Behavior):
  def test(self):
    return self.in_flow.effort != Zero()
class LowEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(Low())
  def test(self):
    self.in_flow.effort <= Low()
class NominalEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(Nominal())
  def test(self):
    return self.in_flow.effort == Nominal()
class AllNominalEffort(Behavior):
  def apply(self):
    for flow in self.out_flows:
      flow.setEffort(Nominal())
  def test(self):
    for flow in self.in_flows:
      if flow.effort != Nominal():
        return False
    return True
class NonNominalEffort(Behavior):
  def test(self):
    return self.in_flow.effort != Nominal()
class NominalRate(Behavior):
  def test(self):
    return self.out_flow.rate == Nominal()
class HighEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(High())
  def test(self):
    return self.in_flow.effort >= High()
class HighestEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(Highest())
  def test(self):
    return self.in_flow.effort >= Highest()
class HighEffortOut(Behavior):
  def test(self):
    return self.out_flow.effort >= High()
class HighestEffortOut(Behavior):
  def test(self):
    return self.out_flow.effort >= Highest()

class HighRate(Behavior):
  def test(self):
    return self.out_flow.rate >= High()
class HighestRate(Behavior):
  def test(self):
    return self.out_flow.rate >= Highest()
class AnyHighestRate(Behavior):
  def test(self):
    for flow in self.out_flows:
      if flow.rate >= Highest():
        return True
    return False
class EqualEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(self.in_flow.effort)
class BranchEqualEffort(Behavior):
  def apply(self):
    for flow in self.out_flows:
      flow.setEffort(self.in_flow.effort)
class EqualRate(Behavior):
  def apply(self):
    self.in_flow.setRate(self.out_flow.rate)
class IncreasedRate(Behavior):
  def apply(self):
    self.in_flow.setRate(State(self.out_flow.rate+1))
class DecreasedRate(Behavior):
  def apply(self):
    self.in_flow.setRate(State(max(0,self.out_flow.rate-1)))
class IncreasedEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(State(self.in_flow.effort+1))
class DecreasedEffort(Behavior):
  def apply(self):
    self.out_flow.setEffort(State(max(0,self.in_flow.effort-1)))
class TranslateRateToEffort(Behavior):
  def apply(self):
    self.out_flows[1].setEffort(self.out_flows[0].rate)
class TranslateIncreasedRateToEffort(Behavior):
  def apply(self):
    self.out_flows[1].setEffort(State(self.out_flows[0].rate+1))
class TranslateDecreasedRateToEffort(Behavior):
  def apply(self):
    self.out_flows[1].setEffort(State(max(0,self.out_flows[0].rate-1)))
class ReflectiveRate(Behavior):
  def apply(self):
    self.in_flow.setRate(self.in_flow.effort)
class LessReflectiveRate(Behavior):
  def apply(self):
    self.in_flow.setRate(State(max(0,self.in_flow.effort-1)))
  def test(self):
    return self.out_flow.rate < self.out_flow.effort
class MuchLessReflectiveRate(Behavior):
  def test(self):
    return self.out_flow.rate < self.out_flow.effort -1
class FreeRate(Behavior):
  def apply(self):
    if self.in_flow.effort:
      self.in_flow.setRate(Highest())
    else:
      self.in_flow.setRate(Zero())
class HighestEffortAmplification(Behavior):
  def apply(self):
    if self.in_flow.effort:
      self.out_flow.setEffort(Highest())
    else:
      self.out_flow.setEffort(Zero())
class InverseRate(Behavior):
  def apply(self):
    if self.out_flow.rate > Nominal():
      self.in_flow.setRate(Low())
    elif self.out_flow.rate < Nominal():
      self.in_flow.setRate(High())
    else:
      self.in_flow.setRate(Nominal())
class TranslateInverseRateToEffort(Behavior):
  def apply(self):
    if self.out_flows[0].rate > Nominal():
      self.out_flows[1].setEffort(Low())
    elif self.out_flows[0].rate < Nominal():
      self.out_flows[1].setEffort(High())
    else:
      self.out_flows[1].setEffort(Nominal())
class MinimumEffort(Behavior):
  '''Takes the minimum effort from all in flows and sets the out flow.'''
  def apply(self):
    value = max(0,min([flow.effort for flow in self.in_flows]))
    self.out_flow.setEffort(State(value))
class DecreasedMinimumEffort(Behavior):
  def apply(self):
    value = max(0,min([flow.effort-1 for flow in self.in_flows]))
    self.out_flow.setEffort(State(value))
class MaximumRate(Behavior):
  def apply(self):
    value = max([flow.rate for flow in self.out_flows])
    self.in_flow.setRate(State(value))
class MaximumEffort(Behavior):
  def apply(self):
    value = max([flow.effort for flow in self.in_flows])
    self.out_flow.setEffort(State(value))
class EqualRateFromMaximumEffort(Behavior):
  def apply(self):
    max_effort = max([flow.effort for flow in self.in_flows])
    for flow in self.in_flows:
      if flow.effort == max_effort:
        flow.setRate(self.out_flow.rate)
      else:
        flow.setRate(Zero())