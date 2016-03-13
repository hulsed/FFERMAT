from math import inf
import networkx as nx

def resetClock():
  global last_clock,clock
  last_clock = 0
  clock = 0
resetClock()

printWarnings = False

class Condition(object):
  def __init__(self,function,delay=0):
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.delay = delay
    self.reset()
    self.test = self.behavior().test
  def reset(self):
    self.countdown = inf
    self.time = clock
  def time_remaining(self):
    if last_clock != self.time:
      self.countdown = inf
    self.time = clock
    if self.test():
      self.countdown = min(self.countdown,self.delay)-(clock-last_clock)
    else:
      self.countdown = inf
    return self.countdown

class HighCurrent(Condition):
  def behavior(self):
    return HighFlow(out_bond=self.out_bond[Electrical])

class HighestCurrent(Condition):
  def behavior(self):
    return HighestFlow(out_bond=self.out_bond[Electrical])

class OnSignal(Condition):
  def behavior(self):
    return NominalEffort(in_bond=self.in_bond[Signal])

class OffSignal(Condition):
  def behavior(self):
    return ZeroEffort(in_bond=self.in_bond[Signal])

class State(float):
  def __new__(cls,value=None):
    if cls is State:
      for subclass in State.__subclasses__():
        if subclass.value == value:
          cls = subclass
          break
    return float.__new__(cls,cls.value)
  def __repr__(self):
    return self.__class__.__name__
  def __str__(self):
    return self.__class__.__name__
class Negative(State):
  value = -1
class Zero(State):
  value = 0
class Low(State):
  value = .5
class Nominal(State):
  value = 1
class High(State):
  value = 2
class Highest(State):
  value = 3

class ModeHealth(object):
  pass
class Operational(ModeHealth):
  pass
class Degraded(ModeHealth):
  pass
class Failed(ModeHealth):
  pass

class Mode(object):
  def __init__(self,function,health):
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.health = health
  def __repr__(self):
    return self.__class__.__name__
  def __eq__(self,other):
    return self.__class__ == other.__class__ and self.health == other.health
  def __hash__(self):
    return hash((self.__class__,self.health))
  def reset(self):
    pass

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


class ZeroEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Zero())
  def test(self):
    return self.in_bond.effort == Zero()

class ZeroFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(Zero())
  def test(self):
    return self.out_bond.flow == Zero()

class LowEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Low())

class NominalEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(Nominal())
  def test(self):
    return self.in_bond.effort == Nominal()

class NominalFlow(Behavior):
  def test(self):
    return self.out_bond.flow == Nominal()

class HighEffort(Behavior):
  def apply(self):
    self.out_bond.setEffort(High())

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

class ReflectiveFlow(Behavior):
  def apply(self):
    self.in_bond.setFlow(self.in_bond.effort)

class FreeFlow(Behavior):
  def apply(self):
    if self.in_bond.effort:
      self.in_bond.setFlow(Highest())
    else:
      self.in_bond.setFlow(Zero())


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
  def addMode(self,health,mode_class,default=False):
    mode = mode_class(self,health())
    self.modes.append(mode)
    if default or (self.default == None and health == Operational):
      self.default = mode
    self.condition_graph.add_node(mode)
    for behavior in mode.behaviors():
      self.behavior_graph.add_edge(mode,behavior)
  def addCondition(self,sourceModes,condition,nextMode,delay=0):
    condition = condition(self,delay)
    if type(sourceModes) is tuple:
      sourceModes = [sourceModes]
    nextMode = nextMode[1](self,nextMode[0])
    self.condition_graph.add_edge(condition,nextMode)
    for sourceMode in sourceModes:
      sourceMode = sourceMode[1](self,sourceMode[0])
      self.condition_graph.add_edge(sourceMode,condition)
  def step(self):
    transition = False
    minimum_delay = inf
    for condition in self.condition_graph.successors_iter(self.mode):
      delay = condition.time_remaining()
      minimum_delay = min(minimum_delay,delay)
      if delay <= 0:
        if delay < 0:
          raise Exception('Missed condition')
        if not transition:
          transition = True
          self.mode = self.condition_graph.successors(condition)[0]

    for behavior in self.behavior_graph.successors_iter(self.mode):
      behavior.apply()
    return minimum_delay

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

class Electrical(Bond):
  pass

class Signal(Bond):
  pass

class Model(object):
  def __init__(self):
    self.graph = nx.MultiDiGraph()
    self.functions = self.graph.nodes_iter
    self.construct()
    self.connect()
    self.reset()
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
    self.minimum_delay = inf
    for function in self.functions():
#      print(function.name+'\t'+str(function.mode))
      delay = function.step()
      self.minimum_delay = min(self.minimum_delay,delay)
  def run(self,lifetime=inf):
    global last_clock, clock
    resetClock()
    self.states = [self.getState()]
    self.timings = [clock]
    while clock < lifetime:
      self.runTimeless()
      last_clock = clock
      clock = clock+self.minimum_delay
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
  def getState(self):
    state = {}
    for function in self.functions():
      state[function] = function.mode
    for bond in self.bonds():
      state[bond] = [bond.effort,bond.flow]
    return state
  def printState(self,i=None,bonds=False):
    try:
      if i==None:
        i = len(self.states)-1
      print("Iteration "+str(i)+" \t\tClock "+str(self.timings[i]))
      state = self.states[i]
    except:
      state = self.getState()
    for function in self.functions():
      print(function.name+'\t'+str(state[function]))
    if bonds:
      for bond in self.bonds():
        print(bond.name+'\t'+str(state[bond]))
  def printStates(self,bonds=False):
    for i in range(len(self.states)):
      self.printState(i,bonds)

class ImportElectricalEnergy(Function):
  def construct(self):
    self.addMode(Operational,NominalVoltageSource)
    self.addMode(Degraded,LowVoltageSource)
    self.addMode(Degraded,HighVoltageSource)
    self.addMode(Failed,OpenCircuit)
class ExportElectricalEnergy(Function):
  def construct(self):
    self.addMode(Operational,ResistiveLoad)
    self.addMode(Failed,ShortCircuit)
    self.addMode(Failed,OpenCircuit)
class ImportBinarySignal(Function):
  def construct(self):
    self.addMode(Operational,NominalSignalSource)
    self.addMode(Failed,ZeroSignalSource)
class ProtectElectricalEnergy(Function):
  def construct(self):
    self.addMode(Operational,ClosedCircuit,default=True)
    self.addMode(Operational,OpenCircuit)
    self.addMode(Failed,ClosedCircuit)
    self.addMode(Failed,OpenCircuit)
    self.addMode(Failed,ShortCircuit)
    self.addCondition((Operational,ClosedCircuit),
                      HighCurrent,(Operational,OpenCircuit),delay=10)
    self.addCondition((Operational,ClosedCircuit),
                      HighestCurrent,(Operational,OpenCircuit))
    self.addCondition([(Failed,ClosedCircuit),(Failed,ShortCircuit)],
                      HighestCurrent,(Failed,OpenCircuit),delay=1)
class ActuateElectricalEnergy(Function):
  def construct(self):
    self.addMode(Operational,ClosedCircuit)
    self.addMode(Operational,OpenCircuit,default=True)
    self.addMode(Failed,ClosedCircuit)
    self.addMode(Failed,OpenCircuit)
    self.addMode(Failed,ShortCircuit)
    self.addCondition((Operational,OpenCircuit),
                      OnSignal,(Operational,ClosedCircuit))
    self.addCondition((Operational,ClosedCircuit),
                      OffSignal,(Operational,OpenCircuit))
    self.addCondition([(Operational,ClosedCircuit),(Failed,ClosedCircuit),
                       (Failed,ShortCircuit)],
                      HighestCurrent,(Failed,OpenCircuit),delay=1)

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
    self.model.reset()
    self.model.run()
    nominal_state = self.model.getState()
    #if not len(self.scenarios):
    self.setExperiment(simultaneous_faults,sampling)
    for i,scenario in enumerate(self.scenarios):
      #print('scenario '+str(i),end="\r")
      self.model.loadState(nominal_state)
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


class EPS(Model):
  def construct(self):
    self.addFunction(ProtectElectricalEnergy('protectEE1'))
    self.addFunction(ActuateElectricalEnergy('actuateEE1'))
    self.addFunction(ImportBinarySignal('importBS1'))
    self.addFunction(ImportElectricalEnergy('importEE1'))
    self.addFunction(ExportElectricalEnergy('exportEE1'))
    self.addBond(Electrical(),'importEE1','protectEE1')
    self.addBond(Electrical(),'protectEE1','actuateEE1')
    self.addBond(Electrical(),'actuateEE1','exportEE1')
    self.addBond(Signal(),'importBS1','actuateEE1')

eps = Experiment(EPS())
for i in [2,3,4,5]:
  eps.run(i)