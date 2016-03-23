from math import inf
import networkx as nx

def resetClock():
  global last_clock,clock
  last_clock = 0
  clock = 0
resetClock()

printWarnings = False

class State(float):
  def __new__(cls,value=None):
    if cls is State:
      for subclass in State.__subclasses__():
        if subclass.value == value:
          cls = subclass
          break
      else:
        lowest_value = 0
        highest_value = 0
        for subclass in State.__subclasses__():
          if subclass.value < lowest_value:
            lowest_value = subclass.value
            lowest_cls = subclass
          if subclass.value > highest_value:
            highest_value = subclass.value
            highest_cls = subclass
        if value > highest_value:
          cls = highest_cls
          value = highest_value
        elif value < lowest_value:
          cls = lowest_cls
          value = lowest_value
        else:
          raise Exception('Undefined State value')
    return float.__new__(cls,cls.value)
  def __repr__(self):
    return self.__class__.__name__
  def __str__(self):
    return self.__class__.__name__

#############################  States  #######################################
class Negative(State):
  value = -1
class Zero(State):
  value = 0
class Low(State):
  value = 1
class Nominal(State):
  value = 2
class High(State):
  value = 3
class Highest(State):
  value = 4

class Behavior(object):
  def __init__(self,in_bond=None,out_bond=None):
    try:
      self.in_bond = in_bond[0]
      self.in_bonds = in_bond
    except TypeError:
      self.in_bond = in_bond
    try:
      self.out_bond = out_bond[0]
      self.out_bonds = out_bond
    except TypeError:
      self.out_bond = out_bond
  def __hash__(self):
    return hash((self.__class__,id(self.in_bond),id(self.out_bond)))
  def __eq__(self,other):
    return (self.__class__ == other.__class__ and self.in_bond is other.in_bond
            and self.out_bond is other.out_bond)

class ModeHealth(object):
  pass

class Mode(object):
  def __init__(self,name,function,health,**attr):
    self.name = name
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.health = health
    self.attr = attr
  def __repr__(self):
    return self.__class__.__name__
  def __eq__(self,other):
    return self.__class__ == other.__class__ and self.health == other.health
  def __hash__(self):
    return hash((self.__class__,self.health))
  def reset(self):
    pass

class Condition(object):
  def __init__(self,function,delay=0,logical_not=False):
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.delay = delay
    self.reset()
    if logical_not:
      self.test = lambda: not self.behavior().test
    else:
      self.test = self.behavior().test
  def reset(self):
    self.timer = inf
    self.time = clock
  def time_remaining(self):
    if last_clock != self.time and clock != self.time:
      self.timer = inf
    self.time = clock
    if self.test():
      self.timer = min(self.timer,self.delay+clock)
    else:
      self.timer = inf
    return self.timer

class Function(object):
  names = []
  def __init__(self,name=None,allow_faults=True,**attr):
    self.allow_faults = allow_faults
    self.attr = attr
    self.default = None
    self.condition_graph = nx.DiGraph()
    self.behavior_graph = nx.DiGraph()
    self.in_bond = {}
    self.out_bond = {}
    self.modes = []
    if name != None:
      if name not in Function.names:
        Function.names.append(name)
      else:
        raise Exception(name+' already used as a function name.')
    else:
      for n in range(1,10):
        name = self.__class__.__name__+format(n,'01d')
        if name not in Function.names:
          Function.names.append(name)
          break
      else:
        raise Exception('Too many ' +self.__class__.__name__+' functions.  '+
        'Raise the limit.')
    self.name = name
  def __repr__(self):
    return self.name
  def __hash__(self):
    return hash(self.name)
  def __eq__(self,other):
    return repr(self) == repr(other) or self.name == str(other)
  def reset(self):
    self.mode = self.default
    for node in self.condition_graph.nodes_iter():
      node.reset()
  def addOutBond(self,bond):
    self._addBond(bond,self.out_bond)
  def addInBond(self,bond):
    self._addBond(bond,self.in_bond)
  def _addBond(self,bond,bonds):
    previous = bonds.get(bond.__class__)
    if previous:
      previous.append(bond)
    else:
      bonds[bond.__class__] = [bond]
  def addMode(self,name,health,mode_class,default=False,**attr):
    mode = mode_class(name,self,health(),**attr)
    self.modes.append(mode)
    if default or (self.default == None and health == Operational):
      self.default = mode
    self.condition_graph.add_node(mode)
    try:
      for behavior in mode.behaviors():
        self.behavior_graph.add_edge(mode,behavior)
    except KeyError as error:
      raise Exception("{0} missing {1} bond.".format(self,error.args[0]))
  def getMode(self,name):
    for mode in self.modes:
      if mode.name == name:
        return mode
  def addCondition(self,sourceModes,condition,nextMode,delay=0):
    condition = condition(self,delay)
    if type(sourceModes) is not list:
      sourceModes = [sourceModes]
    nextMode = self.getMode(nextMode)
    self.condition_graph.add_edge(condition,nextMode)
    for sourceMode in sourceModes:
      sourceMode = self.getMode(sourceMode)
      self.condition_graph.add_edge(sourceMode,condition)
  def step(self):
    transition = False
    minimum_timer = inf
    for condition in self.condition_graph.successors_iter(self.mode):
      timer = condition.time_remaining()
      minimum_timer = min(minimum_timer,timer)
      if timer <= clock:
        if timer < clock:
          raise Exception('Missed condition')
        if not transition:
          transition = True
          self.mode = self.condition_graph.successors(condition)[0]

    for behavior in self.behavior_graph.successors_iter(self.mode):
      behavior.apply()
    return minimum_timer

class Bond(object):
  def __init__(self):
    self.reset()
  def __repr__(self):
    return self.__class__.__name__
  def reset(self,effort=Zero(),flow=Zero()):
    self.effort = effort
    self.flow = flow
    self.effort_queue = None
    self.flow_queue = None
  def setEffort(self,value):
    if printWarnings and not self.effort_queue is None:
      print('Warning! Competing causality in '+self.name+' effort.')
    self.effort_queue = value
  def setFlow(self,value):
    if printWarnings and not self.flow_queue is None:
      print('Warning! Competing causality in '+self.name+' flow.')
    self.flow_queue = value
  def step(self):
    if self.effort != self.effort_queue:
      self.effort = self.effort_queue
      if printWarnings and self.flow != self.flow_queue:
        print('Warning! Overlapping causality in '+self.name)
    self.flow = self.flow_queue
    self.effort_queue = self.flow_queue = None

class Model(object):
  def __init__(self):
    self.graph = nx.MultiDiGraph()
    self.functions = self.graph.nodes_iter
    self.construct()
    self.connect()
    self.reset()
    self.run()
    self.nominal_state = self.getState()
  def bonds(self,functions=False):
    if functions:
      for in_function,out_function,attr in self.graph.edges_iter(data=True):
        yield (attr[Bond],in_function,out_function)
    else:
      for _,_,attr in self.graph.edges_iter(data=True):
        yield attr[Bond]
  def reset(self):
    resetClock()
    for function in self.functions():
      function.reset()
    for bond in self.bonds():
      bond.reset()
  def connect(self):
    for bond,in_function,out_function in self.bonds(functions=True):
      in_function.addOutBond(bond)
      out_function.addInBond(bond)
    for function in self.functions():
      function.construct()
  def addFunction(self,function):
    self.graph.add_node(function)
  def addBond(self,bond,in_function_name,out_function_name):
    bond.name = in_function_name+'_'+out_function_name
    self.graph.add_edge(self.getFunction(in_function_name),
      self.getFunction(out_function_name),attr_dict={Bond:bond})
  def getFunction(self,name):
    for function in self.functions():
      if function.name == name:
        return function
  def step(self):
    self.stepFunctions()
    self.resolveBonds()
  def resolveBonds(self):
    for bond in self.bonds():
#      print(bond.name+'\t'+str(bond.effort)+' '+str(bond.flow))
      bond.step()
  def stepFunctions(self):
    self.minimum_timer = inf
    for function in self.functions():
#      print(function.name+'\t'+str(function.mode))
      timer = function.step()
      self.minimum_timer = min(self.minimum_timer,timer)
  def run(self,lifetime=inf):
    global last_clock, clock
    resetClock()
    self.states = [self.getState()]
    self.timings = [clock]
    while clock < lifetime:
      self.runTimeless()
      last_clock = clock
      clock = self.minimum_timer
  def runTimeless(self):
    finished = False
    i = 0
    while not finished:
#      print("Iteration "+str(i))
      i = i+1
      self.step()
      self.timings.append(clock)
      self.states.append(self.getState())
      if self.states[-1] == self.states[-2]:
        finished = True
#        print("Iteration "+str(i)+" same as "+str(i-1))
  def loadState(self,state):
    for function in self.functions():
      if state.get(function) != None:
        function.mode = state[function]
    for bond in self.bonds():
      if state.get(bond) != None:
        bond.effort = state[bond][0]
        bond.flow = state[bond][1]
  def loadNominalState(self):
    self.loadState(self.nominal_state)
  def getState(self):
    state = {}
    for function in self.functions():
      state[function] = function.mode
    for bond in self.bonds():
      state[bond] = [bond.effort,bond.flow]
    return state
  def printState(self,i=None,bonds=False,state=None):
    if state == None:
      try:
        if i==None:
          i = len(self.states)-1
        print("Iteration "+str(i)+" \t\tClock "+str(self.timings[i]))
        state = self.states[i]
      except:
        state = self.getState()
    for function in self.functions():
      if state.get(function):
        print(function.name+'\t'+str(state[function]))
    if bonds:
      for bond in self.bonds():
        if state.get(bond):
          print(bond.name+'\t'+str(state[bond]))
  def printStates(self,bonds=False):
    for i in range(len(self.states)):
      self.printState(i,bonds)

class Experiment(object):
  def __init__(self,model):
    self.scenarios = []
    self.model = model
  def allScenarios(self,functions,simultaneous_faults,current_scenario={}):
    simultaneous_faults -= 1
    for function in functions:
      if function.allow_faults:
        leftover_functions = [f for f in functions if f != function]
        for mode in function.modes:
          if isinstance(mode.health,Operational):
            continue
          new_scenario = current_scenario.copy()
          new_scenario[function] = mode
          self.scenarios.append(new_scenario)
          if simultaneous_faults and len(leftover_functions):
            self.allScenarios(leftover_functions,simultaneous_faults,new_scenario)
  def setExperiment(self,simultaneous_faults=2,sampling="full"):
    self.scenarios = []
    functions = [function for function in self.model.functions()]
    if sampling == "full":
      self.allScenarios(functions,simultaneous_faults)
  def findUniqueResults(self):
    self.findUnique(self.results)
  def findUniqueHealth(self):
    self.findUnique(self.health)
  def findUnique(self,data):
    self.unique = []
    for i,r in enumerate(data):
      for group in self.unique:
        if r == data[group[0]]:
          group.append(i)
          break
      else:
        self.unique.append([i])
  def run(self,simultaneous_faults=2,sampling="full"):
    self.results = []
    self.health = []
    #if not len(self.scenarios):
    self.setExperiment(simultaneous_faults,sampling)
    for i,scenario in enumerate(self.scenarios):
      #print('scenario '+str(i),end="\r")
      self.model.loadNominalState()
      self.model.loadState(scenario)
      self.model.run()
      self.results.append(self.model.getState())
#      self.health.append(self.model.getHealth())
    print(str(i+1)+' scenarios simulated')
    self.findUniqueResults()
    #print(str(self.unique))
    print(str(int(len(self.unique)))+' states or '+
      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
#    self.findUniqueHealth()
#    print(str(int(len(self.unique)))+' health states or '+
#      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
  def reviewScenarios(self):
    for scenario,result in zip(self.scenarios,self.results):
      print('Scenario:')
      self.model.printState(state=scenario)
      print('Result:')
      self.model.printState(state=result)
      input()

#############################  Behaviors  ####################################
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
class NonZeroEffort(Behavior):
  def test(self):
    return self.in_bond.effort != Zero()
class LowEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Low())
class NominalEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Nominal())
  def test(self):
    return self.in_bond.effort == Nominal()
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
class HighFlow(Behavior):
  def test(self):
    return self.out_bond.flow >= High()
class HighestFlow(Behavior):
  def test(self):
    return self.out_bond.flow >= Highest()
class EqualEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(self.in_bond.effort)
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
    self.out_bond.setEffort(State(self.in_bond.flow+1))
class DecreasedEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(State(max(0,self.in_bond.flow-1)))
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
  def applay(self):
    if self.out_bond.flow > Nominal():
      self.in_bond.setFlow(Low())
    elif self.out_bond.flow < Nominal():
      self.in_bond.setFlow(High())
    else:
      self.in_bond.setFlow(Nominal())
class TranslateInverseFlowToEffort(Behavior):
  def applay(self):
    if self.out_bond[0].flow > Nominal():
      self.out_bond[1].setFlow(Low())
    elif self.out_bond[0].flow < Nominal():
      self.out_bond[1].setFlow(High())
    else:
      self.out_bond[1].setFlow(Nominal())

#############################  Mode Healths  #################################
class Operational(ModeHealth):
  pass
class Degraded(ModeHealth):
  pass
class Failed(ModeHealth):
  pass

#############################  Modes  ########################################
class OpenCircuit(Mode):
  def behaviors(self):
    try:
      yield ZeroEffort(out_bond=self.out_bond[Electrical])
    except KeyError:
      pass
    try:
      yield ZeroFlow(in_bond=self.in_bond[Electrical])
    except KeyError:
      pass
class ClosedCircuit(Mode):
  def behaviors(self):
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[Electrical])
    yield EqualFlow(self.in_bond[Electrical],self.out_bond[Electrical])
class ShortCircuit(Mode):
  def behaviors(self):
    yield FreeFlow(self.in_bond[Electrical])
    try:
      yield ZeroEffort(out_bond = self.out_bond[Electrical])
    except KeyError:
      pass
class NominalVoltageSource(Mode):
  def behaviors(self):
    yield NominalEffort(out_bond=self.out_bond[Electrical])
class LowVoltageSource(Mode):
  def behaviors(self):
    yield LowEffort(out_bond=self.out_bond[Electrical])
class HighVoltageSource(Mode):
  def behaviors(self):
    yield HighEffort(out_bond=self.out_bond[Electrical])
class ResistiveLoad(Mode):
  def behaviors(self):
    yield ReflectiveFlow(in_bond=self.in_bond[Electrical])
class NominalSignalSource(Mode):
  def behaviors(self):
    yield NominalEffort(out_bond=self.out_bond[Signal])
class ZeroSignalSource(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[Signal])
class HeatSink(Mode):
  def behaviors(self):
    yield ReflectiveFlow(in_bond=self.in_bond[Heat])
class InsulatedHeatSink(Mode):
  def behaviors(self):
    yield LessReflectiveFlow(in_bond=self.in_bond[Heat])
class NoHeatSink(Mode):
  def behaviors(self):
    yield ZeroFlow(in_bond=self.in_bond[Heat])
class NominalChemicalToElectricalEnergyConversion(Mode):
  def behaviors(self):
    yield TranslateFlowToEffort(out_bond=self.out_bond[Electrical]+
                                         self.out_bond[Heat])
    yield EqualEffort(self.in_bond[ChemicalEnergy],self.out_bond[Electrical])
    yield EqualFlow(self.in_bond[ChemicalEnergy],self.out_bond[Electrical])
class InefficientChemicalToElectricalEnergyConversion(Mode):
  def behaviors(self):
    yield TranslateIncreasedFlowToEffort(out_bond=self.out_bond[Electrical]+
                                         self.out_bond[Heat])
    yield EqualEffort(self.in_bond[ChemicalEnergy],self.out_bond[Electrical])
    yield IncreasedFlow(self.in_bond[ChemicalEnergy],self.out_bond[Electrical])
class ChemicalEnergyLossNoElectricalConversion(Mode):
  def behaviors(self):
    yield FreeFlow(self.in_bond[ChemicalEnergy])
    yield HighestEffortAmplification(self.in_bond[ChemicalEnergy],
                                     self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[Electrical])
class NoChemicalToElectricalEnergyConversion(Mode):
  def behaviors(self):
    yield ZeroFlow(self.in_bond[ChemicalEnergy])
    yield ZeroEffort(out_bond=self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[Electrical])
class NominalElectricalToRotationalEnergyConversion(Mode):
  def behaviors(self):
    yield TranslateInverseFlowToEffort(out_bond=self.out_bond[RotationalEnergy]+
                                         self.out_bond[Heat])
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[RotationalEnergy])
    yield InverseFlow(self.in_bond[Electrical],self.out_bond[RotationalEnergy])
class ShortCircuitNoMechanicalEnergyConversion(Mode):
  def behaviors(self):
    yield FreeFlow(self.in_bond[Electrical])
    yield HighestEffortAmplification(self.in_bond[Electrical],
                                     self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[RotationalEnergy])
class OpenCircuitNoMechanicalEnergyConversion(Mode):
  def behaviors(self):
    yield ZeroFlow(self.in_bond[Electrical])
    yield ZeroEffort(out_bond=self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[RotationalEnergy])
class NominalChemicalEffortSource(Mode):
  def behaviors(self):
    yield NominalEffort(out_bond=self.out_bond[ChemicalEnergy])
class LowChemicalEffortSource(Mode):
  def behaviors(self):
    yield LowEffort(out_bond=self.out_bond[ChemicalEnergy])
class HighChemicalEffortSource(Mode):
  def behaviors(self):
    yield HighEffort(out_bond=self.out_bond[ChemicalEnergy])
class NoChemicalEffortSource(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[ChemicalEnergy])
class NominalVoltageSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[Signal])
class NominalCurrentSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield TranslateFlowToEffort(out_bond=self.out_bond[Electrical]+
                                self.out_bond[Signal])
class DriftingLowVoltageSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield DecreasedEffort(self.in_bond[Electrical],self.out_bond[Signal])
class DriftingLowCurrentSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield TranslateDecreasedFlowToEffort(out_bond=self.out_bond[Electrical]+
                                self.out_bond[Signal])
class DriftingHighVoltageSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield IncreasedEffort(self.in_bond[Electrical],self.out_bond[Signal])
class DriftingHighCurrentSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield TranslateIncreasedFlowToEffort(out_bond=self.out_bond[Electrical]+
                                self.out_bond[Signal])
class NoVoltageSensing(Mode):
  def behaviors(self):
    yield from ClosedCircuit.behaviors(self)
    yield ZeroEffort(out_bond=self.out_bond[Signal])
class NoCurrentSensing(NoVoltageSensing):
  pass
class HeatConductor(Mode):
  def behaviors(self):
    yield EqualEffort(self.in_bond[Heat],self.out_bond[Heat])
    yield EqualFlow(self.in_bond[Heat],self.out_bond[Heat])
class NominalTemperatureSensing(Mode):
  def behaviors(self):
    yield from HeatConductor.behaviors(self)
    yield EqualEffort(self.in_bond[Heat],self.out_bond[Signal])
class DriftingLowTemperatureSensing(Mode):
  def behaviors(self):
    yield from HeatConductor.behaviors(self)
    yield DecreasedEffort(self.in_bond[Heat],self.out_bond[Signal])
class DriftingHighTemperatureSensing(Mode):
  def behaviors(self):
    yield from HeatConductor.behaviors(self)
    yield IncreasedEffort(self.in_bond[Heat],self.out_bond[Signal])
class NoTemperatureSensing(Mode):
  def behaviors(self):
    yield from HeatConductor.behaviors(self)
    yield ZeroEffort(out_bond=self.out_bond[Signal])

#############################  Conditions  ###################################
class HighCurrent(Condition):
  def behavior(self):
    return HighFlow(out_bond=self.out_bond[Electrical])

class NonZeroVoltage(Condition):
  def behavior(self):
    return NonZeroEffort(in_bond=self.in_bond[Electrical])

class HighestCurrent(Condition):
  def behavior(self):
    return HighestFlow(out_bond=self.out_bond[Electrical])

class NominalSignal(Condition):
  def behavior(self):
    return NominalEffort(in_bond=self.in_bond[Signal])

class NonNominalSignal(Condition):
  def behavior(self):
    return NonNominalEffort(in_bond=self.in_bond[Signal])

class ZeroSignal(Condition):
  def behavior(self):
    return ZeroEffort(in_bond=self.in_bond[Signal])

class NonZeroSignal(Condition):
  def behavior(self):
    return NonZeroEffort(in_bond=self.in_bond[Signal])

class AnyZeroSignals(Condition):
  def behavior(self):
    return AnyZeroEffort(in_bond=self.in_bond[Signal])

class NoZeroSignals(Condition):
  def behavior(self):
    return NoZeroEffort(in_bond=self.in_bond[Signal])

class AnyNonZeroSignals(Condition):
  def behavior(self):
    return AnyNonZeroEffort(in_bond=self.in_bond[Signal])

class AllZeroSignals(Condition):
  def behavior(self):
    return AllZeroEffort(in_bond=self.in_bond[Signal])

class Overheating(Condition):
  def behavior(self):
    return HighEffort(in_bond=self.out_bond[Heat])

class FastOverheating(Condition):
  def behavior(self):
    return HighestEffort(in_bond=self.out_bond[Heat])

#############################  Functions  ####################################
class ImportElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalVoltageSource)
    self.addMode(2,Degraded,LowVoltageSource)
    self.addMode(3,Degraded,HighVoltageSource)
    self.addMode(4,Failed,OpenCircuit)
class ExportElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,ResistiveLoad)
    self.addMode(2,Failed,ShortCircuit)
    self.addMode(3,Failed,OpenCircuit)
class ImportChemicalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalChemicalEffortSource)
    self.addMode(2,Degraded,LowChemicalEffortSource)
    self.addMode(3,Failed,NoChemicalEffortSource)
class ImportBinarySignal(Function):
  def construct(self):
    self.addMode(1,Operational,NominalSignalSource)
    self.addMode(2,Failed,ZeroSignalSource)
class ExportHeatEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,HeatSink)
    self.addMode(2,Degraded,InsulatedHeatSink)
    self.addMode(3,Failed,NoHeatSink)
class ProtectElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,ClosedCircuit,default=True)
    self.addMode(2,Operational,OpenCircuit)
    self.addMode(3,Failed,ClosedCircuit)
    self.addMode(4,Failed,OpenCircuit)
    self.addMode(5,Failed,ShortCircuit)
    self.addCondition(1,HighCurrent,2,delay=10)
    self.addCondition(1,HighestCurrent,2)
    self.addCondition([3],HighestCurrent,4,delay=1)
    self.addCondition([5],NonZeroVoltage,4,delay=1)
class ActuateElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,ClosedCircuit)
    self.addMode(2,Operational,OpenCircuit,default=True)
    self.addMode(3,Failed,ClosedCircuit)
    self.addMode(4,Failed,OpenCircuit)
    self.addMode(5,Failed,ShortCircuit)
    self.addCondition(2,NonZeroSignal,1)
    self.addCondition(1,ZeroSignal,2)
    self.addCondition([1,3],HighestCurrent,4,delay=1)
    self.addCondition([5],NonZeroVoltage,4,delay=1)
class ConvertChemicalToElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalChemicalToElectricalEnergyConversion)
    self.addMode(2,Degraded,InefficientChemicalToElectricalEnergyConversion)
    self.addMode(3,Failed,ChemicalEnergyLossNoElectricalConversion)
    self.addMode(4,Failed,NoChemicalToElectricalEnergyConversion)
    self.addCondition([1,2,3],Overheating,4,delay=10)
    self.addCondition([1,2,3],FastOverheating,4,delay=1)
class ConvertElectricalToMechanicalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalElectricalToRotationalEnergyConversion)
    self.addMode(2,Failed,ShortCircuitNoMechanicalEnergyConversion)
    self.addMode(3,Failed,OpenCircuitNoMechanicalEnergyConversion)
    self.addCondition([1,2],Overheating,3,delay=10)
    self.addCondition([1,2],FastOverheating,3,delay=1)
class SenseVoltage(Function):
  def construct(self):
    self.addMode(1,Operational,NominalVoltageSensing)
    self.addMode(2,Degraded,DriftingLowVoltageSensing)
    self.addMode(3,Degraded,DriftingHighVoltageSensing)
    self.addMode(4,Failed,NoVoltageSensing)
class SenseCurrent(Function):
  def construct(self):
    self.addMode(1,Operational,NominalCurrentSensing)
    self.addMode(2,Degraded,DriftingLowCurrentSensing)
    self.addMode(3,Degraded,DriftingHighCurrentSensing)
    self.addMode(4,Failed,NoCurrentSensing)
class SenseTemperature(Function):
  def construct(self):
    self.addMode(1,Operational,NominalTemperatureSensing)
    self.addMode(2,Degraded,DriftingLowTemperatureSensing)
    self.addMode(3,Degraded,DriftingHighTemperatureSensing)
    self.addMode(4,Failed,NoTemperatureSensing)
class ProcessSignal(object):
  class IsNominal(Function):
    def construct(self):
      self.addMode(1,Operational,ZeroSignalSource)
      self.addMode(2,Operational,NominalSignalSource)
      self.addCondition(1,NominalSignal,2)
      self.addCondition(2,NonNominalSignal,1)
  class And(Function):
    def construct(self):
      self.addMode(1,Operational,ZeroSignalSource)
      self.addMode(2,Operational,NominalSignalSource)
      self.addCondition(1,NoZeroSignals,2)
      self.addCondition(2,AnyZeroSignals,1)
  class Or(Function):
    def construct(self):
      self.addMode(1,Operational,ZeroSignalSource)
      self.addMode(2,Operational,NominalSignalSource)
      self.addCondition(1,AnyNonZeroSignals,2)
      self.addCondition(2,AllZeroSignals,1)
  class Not(Function):
    def construct(self):
      self.addMode(1,Operational,ZeroSignalSource)
      self.addMode(2,Operational,NominalSignalSource)
      self.addCondition(1,ZeroSignal,2)
      self.addCondition(2,NonZeroSignal,1)

#############################  Bonds  ########################################
class Electrical(Bond):
  pass

class Heat(Bond):
  pass

class ChemicalEnergy(Bond):
  pass

class RotationalEnergy(Bond):
  pass

class Signal(Bond):
  pass

##############################################################################
#####################      End of IBFM Definitions       #####################

class EPS(Model):
  def construct(self):
    self.addFunction(ProtectElectricalEnergy('protectEE1'))
    self.addFunction(ActuateElectricalEnergy('actuateEE1'))
    self.addFunction(ImportBinarySignal('importBS1'))
    self.addFunction(ImportChemicalEnergy('importCE1'))
    self.addFunction(ConvertChemicalToElectricalEnergy('CEtoEE1'))
    self.addFunction(ExportElectricalEnergy('exportEE1'))
    self.addFunction(ExportHeatEnergy('exportHE1'))
    self.addBond(ChemicalEnergy(),'importCE1','CEtoEE1')
    self.addBond(Heat(),'CEtoEE1','exportHE1')
    self.addBond(Electrical(),'CEtoEE1','protectEE1')
    self.addBond(Electrical(),'protectEE1','actuateEE1')
    self.addBond(Electrical(),'actuateEE1','exportEE1')
    self.addBond(Signal(),'importBS1','actuateEE1')

eps = Experiment(EPS())
for i in [2]:
  eps.run(i)
#eps.reviewScenarios()