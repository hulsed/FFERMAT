'''ibfm.py
Inherent Behavior in Functional Models

Author: Matthew G McIntire
2016
'''
printWarnings = False
print_iterations = False
run_parallel = False
n_workers = 3

from math import inf
from time import time
import networkx as nx
import multiprocessing

def resetClock():
  '''Reset the global clock variable to zero for a new simulation.'''
  global last_clock,clock
  last_clock = 0
  clock = 0
resetClock()

def all_subclasses(cls):
  '''Return all subclasses of a class recursively.

  Written by Vebjorn Ljosa on Stack Overflow
  '''
  return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


class State(float):
  '''Ordinal type for qualitatively representing bond values'''
  def __new__(cls,value=None):
    '''Return a new State object.

    Keyword arguments:
    value=None -- If State() is called, rather than a subclass, value will be
                  used to determine the appropriate subclass
    '''
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
  '''Abstract class for bond-independent behavior application and testing.

  Required methods:
  apply(self) -- Assign states to bonds using self.in_bond.setFlow(state) and
                 self.out_bond.setEffort(state). Used by modes.
  test(self) -- Return boolean indicating presence of behavior. Used by
                conditions.
  '''
  def __init__(self,in_bond=None,out_bond=None):
    '''Return a Behavior object.

    Required arguments:
    in_bond and/or out_bond -- Bond objects to test states of and apply states
                               to. Args may be single bonds or lists of bonds.
                               The bonds implicitly decide the bond types of
                               the behavior.
    '''
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
    '''Return hash to identify unique Behavior objects.

    Used by dictionaries in NetworkX.
    '''
    return hash((self.__class__,id(self.in_bond),id(self.out_bond)))
  def __eq__(self,other):
    '''Return boolean to identify unique Behavior objects.

    Used by dictionaries in NetworkX.
    '''
    return (self.__class__ == other.__class__ and self.in_bond is other.in_bond
            and self.out_bond is other.out_bond)

class ModeHealth(object):
  pass

class Mode(object):
  '''Abstract class for operational modes that functions may use.

  Required methods:
  behaviors(self) -- yield Behavior objects.
  '''
  def __init__(self,name,function,health,**attr):
    '''Return a Mode object.

    Required arguments:
    name -- a unique name (for easier to read function definitions)
    function -- the object the mode belongs to (for access to its bonds),
    health -- a ModeHealth subclass designating the health of the function
              represented by the mode.
    '''
    self.name = name
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.health = health
    self.attr = attr
  def __repr__(self):
    return self.__class__.__name__
  def __hash__(self):
    '''Return hash to identify unique Mode objects.

    Used by dictionaries in NetworkX.
    '''
    return hash((self.__class__,self.health))
  def __eq__(self,other):
    '''Return boolean to identify unique Mode objects.

    Used by dictionaries in NetworkX.
    '''
    return self.__class__ == other.__class__ and self.health == other.health
  def reset(self):
    '''Reset the Mode object for a new simulation.

    Required because Mode objects share NetworkX graphs with Condition
    objects, which have their timers reset, and this is easier than generating
    a different iterator for only Condition objects.
    '''
    pass

class Logical(object):
  '''Abstract class for a logical operator

  Required methods:
  test(self) -- return a boolean
  '''
  def __init__(self,behaviors):
    self.behaviors = behaviors
  def __hash__(self):
    '''Return hash to identify unique Logical objects.

    Used by dictionaries in NetworkX.
    '''
    return hash((self.__class__,*self.behaviors))
  def __eq__(self,other):
    '''Return boolean to identify unique Logical objects.

    Used by dictionaries in NetworkX.
    '''
    return self.__class__ == other.__class__ and self.behaviors == other.behaviors

class Or(Logical):
  def test(self):
    for behavior in self.behaviors:
      if behavior.test():
        return True
    return False


class Condition(object):
  '''Abstract class for a condition to advance to another mode.

  Required methods:
  behavior(self) -- Return a Behavior object.
  '''
  def __init__(self,function,delay=0,logical_not=False):
    '''Return a Condition object

    Required arguments:
    function -- the object it belongs to (for access to its bonds)
    delay -- the amound of time the condition must be met for a mode change.
    logical_not -- boolean flag indicating whether the condition should be
                   logically negated.
    '''
    self.out_bond = function.out_bond
    self.in_bond = function.in_bond
    self.delay = delay
    self.reset()
    if logical_not:
      self.test = lambda: not self.behavior().test
    else:
      self.test = self.behavior().test
  def reset(self):
    '''Resets the delay timer.
    '''
    self.timer = inf
    self.time = clock
  def time_remaining(self):
    '''Returns the time remaining before mode change.

    Calculates the time under current conditions before the condition is
    met. Returns 0 if the condition test has been met for self.delay amount of
    time, inf if the condition test has not been met, and the remaining time
    otherwise.
    '''
    if last_clock != self.time and clock != self.time:
      self.timer = inf
    self.time = clock
    if self.test(): #This is where the actual test method is called.
      self.timer = min(self.timer,self.delay+clock)
    else:
      self.timer = inf
    return self.timer

class Function(object):
  '''Abstrct class for functions in the functional model.

  Required methods:
  construct(self) -- call self.addMode(name,health,mode_class,default=False) and
                     self.addCondition(source_modes,condition,next_mode,delay=0)
                     repeatedly to specify all of the modes and conditions
                     attainable by the function. The default default is the
                     first given mode with health=Operational.
  '''
  def __init__(self,model,name=None,allow_faults=True,**attr):
    '''Return a Function object

    Required arguments:
    name -- a unique name for use in defining bonds
    allow_faults -- a flag to allow degraded and failure modes to be tested in
                    experiments. If False, off-nominal modes may still be
                    entered conditionally during simulation.
    '''
    self.allow_faults = allow_faults
    self.attr = attr
    self.default = None
    #The graph containing the conditional relationships between the modes
    self.condition_graph = nx.DiGraph()
    #The graph containing the behaviors enacted by each mode
    self.behavior_graph = nx.DiGraph()
    self.in_bond = {}
    self.out_bond = {}
    self.modes = []
    if name != None:
      if name not in model.names:
        model.names.append(name)
      else:
        raise Exception(name+' already used as a function name.')
    else:
      for n in range(1,10):
        name = self.__class__.__name__+format(n,'01d')
        if name not in model.names:
          model.names.append(name)
          break
      else:
        raise Exception('Too many ' +self.__class__.__name__+' functions.  '+
        'Raise the limit.')
    self.name = name
  def __repr__(self):
    return self.name
  def __hash__(self):
    '''Return hash to identify unique Function objects.

    Used by dictionaries in NetworkX.
    '''
    return hash(self.name)
  def __eq__(self,other):
    '''Return boolean to identify unique Function objects.

    Used by dictionaries in NetworkX.
    '''
    return repr(self) == repr(other) or self.name == str(other)
  def reset(self):
    '''Reset all modes and set mode to default.'''
    self.mode = self.default
    for node in self.condition_graph.nodes_iter():
      node.reset()
  def addOutBond(self,bond):
    '''Attach an outflow bond to the function.'''
    self._addBond(bond,bond.__class__,self.out_bond)
  def addInBond(self,bond):
    '''Attach an inflow bond to the function.'''
    self._addBond(bond,bond.__class__,self.in_bond)
  def _addBond(self,bond,bond_class,bonds):
    '''Add a bond to the bonds dictionary (recursively).

    Makes sure the bond is reachable by its class or any of its superclasses
    as the key.
    '''
    previous = bonds.get(bond_class)
    if previous:
      previous.append(bond)
    else:
      bonds[bond_class] = [bond]
    if Bond not in bond_class.__bases__:
      for base in bond_class.__bases__:
        self._addBond(bond,base,bonds)
  def addMode(self,name,health,mode_class,default=False,**attr):
    '''Add a mode to the function.

    Required arguments:
    name -- a unique identifier for the mode to be used in calls to
            self.addCondition()
    health -- a ModeHealth subclass designating the health of the function
              when represented by the mode.
    mode_class -- the Mode subclass representing the mode being added
    default -- whether the mode should be the default for the function. The
               default default is the first given mode with health=Operational.
    '''
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
    '''Return the function mode with the given name, if it exists.'''
    for mode in self.modes:
      if mode.name == name:
        return mode
  def addCondition(self,source_modes,condition,next_mode,delay=0):
    '''Add a conditional change to the function from one mode to another.

    Required arguments:
    source_modes -- a list of names of modes from which the condition is applied.
    condition -- the Condition subclass representing the condition being added.
    next_mode -- the name of the mode assigned to the function should be
                condition be satisfied.
    '''
    condition = condition(self,delay)
    if type(source_modes) is not list:
      source_modes = [source_modes]
    next_mode = self.getMode(next_mode)
    self.condition_graph.add_edge(condition,next_mode)
    for sourceMode in source_modes:
      sourceMode = self.getMode(sourceMode)
      self.condition_graph.add_edge(sourceMode,condition)
  def step(self):
    '''Evaluate the function.

    Test each condition reachable from the current mode.  If there is only one,
    advance to its child mode.  If there is more than one, fork the simulation,
    advancing to each mode in a different fork. <------------------------------ IMPLEMENT THIS!
    In any case, finish by applying the behavior defined by the current mode.
    '''
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
  def getSubclass(name):
    for subclass in all_subclasses(Function):
      if subclass.__name__ == name:
        return subclass
    return None

class Bond(object):
  '''Superclass for bonds in the functional model.'''
  def __init__(self,source,drain):
    self.source = source
    self.drain = drain
    self.name = source.name+'_'+drain.name
    self.reset()
  def __repr__(self):
    return self.__class__.__name__
  def reset(self,effort=Zero(),flow=Zero()):
    '''Set the effort and flow of the bond to Zero() unless otherwise specified.'''
    self.effort = effort
    self.flow = flow
    self.effort_queue = None
    self.flow_queue = None
  def setEffort(self,value):
    '''Set the effort of the bond to value. Queued until step(self) is called.'''
    if printWarnings and not self.effort_queue is None:
      print('Warning! Competing causality in '+self.name+' effort.')
    self.effort_queue = value
  def setFlow(self,value):
    '''Set the flow of the bond to value. Queued until step(self) is called.'''
    if printWarnings and not self.flow_queue is None:
      print('Warning! Competing causality in '+self.name+' flow.')
    self.flow_queue = value
  def step(self):
    '''Resolve the effort and flow values in the bond.'''
    if self.effort != self.effort_queue:
      self.effort = self.effort_queue
      if printWarnings and self.flow != self.flow_queue:
        print('Warning! Overlapping causality in '+self.name)
    self.flow = self.flow_queue
    self.effort_queue = self.flow_queue = None
  def getSubclass(name):
    for subclass in all_subclasses(Bond):
      if subclass.__name__ == name:
        return subclass
    return None

class Model(object):
  '''Class for functional models.

  Replaceable methods:
  construct(self) -- Call self.addFunction(function) and
                     self.addBond(in_function_name,out_function_name) repeatedly
                     to describe the functions and bonds that make up the
                     functional model.
  '''
  def __init__(self,graph=None):
    '''Construct the model and run it under nominal conditions.

    Keyword Arguments:
    graph -- a NetworkX graph representing the functional model
    '''
    #This graph contains all of the functions as nodes and bonds as edges.
    self.names = []
    self.imported_graph = graph
    self.graph = nx.MultiDiGraph()
    self.functions = self.graph.nodes_iter #for code readability
    self.construct()
    self.connect()
    self.reset()
    self.run()
    self.nominal_state = self.getState()
  def construct(self):
    '''Construct a model from an imported graph.

    Replace this method when defining models as subclasses.
    '''
    #Find keys
    function_key = None
    bond_key = None
    for _,data in self.imported_graph.nodes_iter(data=True):
      for key in data:
        if Function.getSubclass(data[key]) is not None:
          function_key = key
          break
      if function_key:
        break
    else:
      raise Exception('No defined function names found.')
    for _,_,data in self.imported_graph.edges_iter(data=True):
      for key in data:
        if Bond.getSubclass(data[key]) is not None:
          bond_key = key
          break
      if bond_key:
        break
    else:
      raise Exception('No defined bond names found.')
    #Build model
    for node,data in self.imported_graph.nodes_iter(data=True):
      function = Function.getSubclass(data[function_key])
      if function is None:
        raise Exception(data[function_key]+' is not a defined function name.')
      self.addFunction(function(self,node))
    for node1,node2,data in self.imported_graph.edges_iter(data=True):
      bond_class = Bond.getSubclass(data[bond_key])
      if bond_class is None:
        raise Exception(data[bond_key]+' is not a defined bond name.')
      self.addBond(bond_class,node1,node2)
  def bonds(self,functions=False):
    '''Generate bonds for iterating.

    NetworkX does not allow edges to be arbitrary objects; objects must be
    stored as edge attributes.
    '''
    if functions:
      for in_function,out_function,attr in self.graph.edges_iter(data=True):
        yield (attr[Bond],in_function,out_function)
    else:
      for _,_,attr in self.graph.edges_iter(data=True):
        yield attr[Bond]
  def reset(self):
    '''Reset the clock, all functions, and all bonds.'''
    resetClock()
    for function in self.functions():
      function.reset()
    for bond in self.bonds():
      bond.reset()
  def connect(self):
    '''Finish initialization of each function.

    Give each function handles to every bond connected to it, then run each
    function's construct method to initialize its modes and conditions.
    '''
    for bond,in_function,out_function in self.bonds(functions=True):
      in_function.addOutBond(bond)
      out_function.addInBond(bond)
    for function in self.functions():
      function.construct()
  def addFunction(self,function):
    '''Add function to the graph of the functional model.'''
    self.graph.add_node(function)
  def addBond(self,bond_class,in_function_name,out_function_name):
    '''Add bond to the graph of the functional model.

    Required arguments:
    bond -- the bond to be added
    in_function_name -- the id of the function that supplies effort to the bond
    out_function_name -- the id of the function that accepts flow from the bond
    '''
    in_function = self.getFunction(in_function_name)
    out_function = self.getFunction(out_function_name)
    bond = bond_class(in_function,out_function)
    bond.name = in_function_name+'_'+out_function_name
    self.graph.add_edge(in_function,out_function,attr_dict={Bond:bond})
  def getFunction(self,name):
    '''Return the function with the given id.'''
    for function in self.functions():
      if function.name == name:
        return function
  def step(self):
    '''Perform one iteration of the functional model as a state machine.'''
    self.stepFunctions()
    self.resolveBonds()
  def resolveBonds(self):
    '''Resolve the effort and flow values in each bond.'''
    for bond in self.bonds():
      if print_iterations:
        print(bond.name+'\t'+str(bond.effort)+' '+str(bond.flow))
      bond.step()
  def stepFunctions(self):
    '''Evaluate each function.'''
    self.minimum_timer = inf
    for function in self.functions():
      if print_iterations:
        print(function.name+'\t'+str(function.mode))
      timer = function.step()
      self.minimum_timer = min(self.minimum_timer,timer)
  def run(self,lifetime=inf):
    '''Simulate the functional model as a state machine with pseudotime.

    Keyword arguments:
    lifetime=inf -- the time at which the simulation should stop, regardless of
                    whether the model has reached steady state.
    '''
    global last_clock, clock
    resetClock()
    self.states = [self.getState()]
    self.timings = [clock]
    while clock < lifetime:
      self.runTimeless() #This can update self.minimum_timer
      last_clock = clock
      clock = self.minimum_timer
  def runTimeless(self):
    '''Simulate the functional model as a timeless state machine.

    Iterates the simulation without advancing the clock until steady state is
    reached.
    '''
    finished = False
    i = 0
    while not finished:
      if print_iterations:
        print("Iteration "+str(i))
      i = i+1
      self.step()
      self.timings.append(clock)
      self.states.append(self.getState())
      if self.states[-1] == self.states[-2]:
        finished = True
        if print_iterations:
          print("Iteration "+str(i)+" same as "+str(i-1))
  def loadState(self,state):
    '''Set state as the current state of the model.

    Required arguments:
    state -- a dictionary of values for functions and bonds. Keys are function
             and bond objects, function values are mode objects, and bond values
             are two-element lists containing an effort value and a flow value.
             Overwrites current state, so any functions or bonds not included in
             the argument are left alone.
    '''
    for function in self.functions():
      if state.get(function) != None:
        function.mode = state[function]
    for bond in self.bonds():
      if state.get(bond) != None:
        bond.effort = state[bond][0]
        bond.flow = state[bond][1]
  def loadNominalState(self):
    '''Set the nominal state as the current state of the model.'''
    self.loadState(self.nominal_state)
  def getState(self):
    '''Return the current state of the model.

    Return a dictionary of values for functions and bonds. Keys are function and
    bond objects, function values are mode objects, and bond values are two-
    element lists containing an effort value and a flow value.
    '''
    state = {}
    for function in self.functions():
      state[function] = function.mode
    for bond in self.bonds():
      state[bond] = [bond.effort,bond.flow]
    return state
  def printState(self,i=None,bonds=False,state=None):
    '''Print a state of the model to the console.

    Keyword Arguments:
    i=None -- an integer specifying which iteration of the current simulation
              to print
    bonds=False -- a flag whether to print bond values alongside function values.
    state -- a state dictionary of the current model to print

    If neither i nor state is specified, the current state of the model will be
    printed.
    '''
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
    '''Print the entire iteration history of the current simulation.

    Keyword Arguments:
    bonds=False -- a flag whether to print bond values alongside function values.
    '''
    for i in range(len(self.states)):
      self.printState(i,bonds)

class Experiment(object):
  '''Run experiments on a functional model'''
  def __init__(self,model):
    '''Return an Experiment object.

    Required arguments:
    model -- the functional model to experiment on
    '''
    self.scenarios = []
    if isinstance(model,Model):
      self.model = model
    else:
      self.model = Model(model)
  def allScenarios(self,functions,simultaneous_faults,_current_scenario={}):
    '''Create full factorial list of scenarios (recursive).

    Required Arguments:
    functions -- iterator of functions from which draw faults
    simultaneous_faults -- the number of simultaneous faults allowed

    The current_scenario argument is only used by the method recursion.
    '''
    simultaneous_faults -= 1
    for function in functions:
      if function.allow_faults:
        leftover_functions = [f for f in functions if f != function]
        for mode in function.modes:
          if isinstance(mode.health,Operational):
            continue
          new_scenario = _current_scenario.copy()
          new_scenario[function] = mode
          self.scenarios.append(new_scenario)
          if simultaneous_faults and len(leftover_functions):
            self.allScenarios(leftover_functions,simultaneous_faults,new_scenario)
  def setExperiment(self,simultaneous_faults,sampling):
    '''Create a list of scenarios to as an experiment.

    Required Arguments:
    simultaneous_faults -- the number of simultaneous faults allowed
    sampling -- the sampling method used.  Currently, only "full" (full factorial)
                is available.
    '''
    self.scenarios = []
    functions = [function for function in self.model.functions()]
    if sampling == "full":
      self.allScenarios(functions,simultaneous_faults)
  def findUniqueResults(self):
    '''Use self.findUnique to identify scenarios with unique end states.'''
    self.findUnique(self.results)
  def findUniqueHealth(self):
    '''Use self.findUnique to identify scenarios with unique end health states.'''
    self.findUnique(self.health)
  def findUnique(self,data):
    '''Identify unique and redundant scenario endings.

    Required Arguments:
    data -- a list; each element represents one scenario.

    Populates self.unique, a list of lists. Each list represents a unique element
    in data, and is itself a list of indices corresponding to scenarios that
    produce that same output in data.
    '''
    self.unique = []
    for i,r in enumerate(data):
      for group in self.unique:
        if r == data[group[0]]:
          group.append(i)
          break
      else:
        self.unique.append([i])
  def run(self,simultaneous_faults=2,sampling="full"):
    '''Setup and run an experiment.

    Keyword Arguments:
    simultaneous_faults=2 -- the number of simultaneous faults allowed
    sampling="full" -- the sampling method used.  Currently, only "full" (full
                       factorial) is available.
    '''
    t1 = time()
    self.results = []
    #self.health = []
    #if not len(self.scenarios):
    self.setExperiment(simultaneous_faults,sampling)
    if run_parallel:
      pool = multiprocessing.Pool(n_workers)
    t2 = time()
    print('Experiment created in '+str(t2-t1)+' seconds.')
    t1 = time()
    if run_parallel:
      self.results = list(pool.map(self.runOneScenario,self.scenarios))
    else:
      self.results = list(map(self.runOneScenario,self.scenarios))
#    for scenario in self.scenarios:
#      self.model.loadNominalState()
#      self.model.loadState(scenario)
#      self.model.run()
#      self.results.append(self.model.getState())
#      self.health.append(self.model.getHealth())
    t2 = time()
    print(str(len(self.scenarios))+' scenarios simulated in '+str(t2-t1)+' seconds.')
    self.findUniqueResults()
    #print(str(self.unique))
    print(str(int(len(self.unique)))+' states or '+
      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
#    self.findUniqueHealth()
#    print(str(int(len(self.unique)))+' health states or '+
#      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
  def runOneScenario(self,scenario):
    self.model.loadNominalState()
    self.model.loadState(scenario)
    self.model.run()
    return self.model.getState()
  def reviewScenarios(self):
    '''Print scenarios to the console one at a time.'''
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
  def test(self):
    self.in_bond.effort <= Low()
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
      for bond in self.out_bond[Electrical]:
        yield ZeroEffort(out_bond=bond)
    except KeyError:
      pass
    try:
      for bond in self.in_bond[Electrical]:
        yield ZeroFlow(in_bond=bond)
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
class NominalMaterialSource(Mode):
  def behaviors(self):
    yield NominalEffort(out_bond=self.out_bond[Material])
class NoMaterialSource(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[Material])
class NominalMaterialSink(Mode):
  def behaviors(self):
    yield ReflectiveFlow(in_bond=self.in_bond[Material])
class NoMaterialSink(Mode):
  def behaviors(self):
    yield ZeroFlow(in_bond=self.in_bond[Material])
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
class NominalInvertElectricalEnergy(Mode):
  def behaviors(self):
    yield NominalEffort(out_bond=self.out_bond[Electrical])
    yield NominalEffort(out_bond=self.out_bond[Heat])
    yield EqualFlow(self.in_bond[Electrical],self.out_bond[Electrical])
class NoInvertElectricalEnergy(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[Electrical])
    yield ZeroEffort(out_bond=self.out_bond[Heat])
    yield ZeroFlow(self.in_bond[Electrical])
class NominalElectricalToMechanicalEnergyConversion(Mode):
  def behaviors(self):
    yield TranslateInverseFlowToEffort(out_bond=self.out_bond[MechanicalEnergy]+
                                         self.out_bond[Heat])
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[MechanicalEnergy])
    yield InverseFlow(self.in_bond[Electrical],self.out_bond[MechanicalEnergy])
class ShortCircuitNoMechanicalEnergyConversion(Mode):
  def behaviors(self):
    yield FreeFlow(self.in_bond[Electrical])
    yield HighestEffortAmplification(self.in_bond[Electrical],
                                     self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[MechanicalEnergy])
class OpenCircuitNoMechanicalEnergyConversion(Mode):
  def behaviors(self):
    yield ZeroFlow(self.in_bond[Electrical])
    yield ZeroEffort(out_bond=self.out_bond[Heat])
    yield ZeroEffort(out_bond=self.out_bond[MechanicalEnergy])
class NominalElectricalToOpticalEnergyConversion(Mode):
  def behaviors(self):
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[OpticalEnergy])
    yield EqualEffort(self.in_bond[Electrical],self.out_bond[Heat])
    yield ReflectiveFlow(self.in_bond[Electrical])
class NoElectricalToOpticalEnergyConversion(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[OpticalEnergy])
    yield ZeroEffort(out_bond=self.out_bond[Heat])
    yield ZeroFlow(self.in_bond[Electrical])
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
class NominalTransportMaterial(Mode):
  def behaviors(self):
    yield MinimumEffort(self.in_bond[Energy]+self.in_bond[Material],
                    self.out_bond[Material])
    yield EqualFlow(self.in_bond[Material],
                    self.out_bond[Material])
    yield EqualFlow(self.in_bond[Energy],
                    self.out_bond[Material])
class RestrictedTransportMaterial(Mode):
  def behaviors(self):
    yield DecreasedMinimumEffort(self.in_bond[Energy]+self.in_bond[Material],
                    self.out_bond[Material])
    yield EqualFlow(self.in_bond[Material],
                    self.out_bond[Material])
    yield EqualFlow(self.in_bond[Energy],
                    self.out_bond[Material])
class BlockedTransportMaterial(Mode):
  def behaviors(self):
    yield ZeroEffort(out_bond=self.out_bond[Material])
    yield ZeroFlow(in_bond=self.in_bond[Material])
    yield ZeroFlow(in_bond=self.in_bond[Energy])
class NominalBranchElectricalEnergy(Mode):
  def behaviors(self):
    for bond in self.out_bond[Electrical]:
      yield EqualEffort(self.in_bond[Electrical],bond)
    yield MaximumFlow(self.in_bond[Electrical],self.out_bond[Electrical])
class BranchOpenCircuit(Mode):
  def behaviors(self):
    for bond in self.out_bond[Electrical]:
      yield ZeroEffort(out_bond=bond)
    yield ZeroFlow(self.in_bond[Electrical])
class NominalCombineElectricalEnergy(Mode):
  def behaviors(self):
    yield MaximumEffort(self.in_bond[Electrical],self.out_bond[Electrical])
    yield EqualFlowFromMaximumEffort(self.in_bond[Electrical],
                                     self.out_bond[Electrical])
class NominalExportOpticalEnergy(Mode):
  def behaviors(self):
    yield ReflectiveFlow(self.in_bond[OpticalEnergy])

#############################  Conditions  ###################################
class NominalVoltage(Condition):
  def behavior(self):
    return NominalEffort(self.in_bond[Electrical])
class HighCurrent(Condition):
  def behavior(self):
    return HighFlow(out_bond=self.out_bond[Electrical])

class NonZeroVoltage(Condition):
  def behavior(self):
    return NonZeroEffort(in_bond=self.in_bond[Electrical])

class HighestCurrent(Condition):
  def behavior(self):
    return HighestFlow(out_bond=self.out_bond[Electrical])

class LowVoltage(Condition):
  def behavior(self):
    return LowEffort(self.in_bond[Electrical])

class HighVoltage(Condition):
  def behavior(self):
    return HighEffort(self.in_bond[Electrical])

class BranchHighestCurrent(Condition):
  def behavior(self):
    return Or([HighestFlow(out_bond=bond) for bond in self.out_bond[Electrical]])

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
class ImportMaterial(Function):
  def construct(self):
    self.addMode(1,Operational,NominalMaterialSource)
    self.addMode(2,Failed,NoMaterialSource)
class ExportMaterial(Function):
  def construct(self):
    self.addMode(1,Operational,NominalMaterialSink)
    self.addMode(2,Failed,NoMaterialSink)
class ExportOpticalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalExportOpticalEnergy)
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
class InvertElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalInvertElectricalEnergy)
    self.addMode(2,Operational,NoInvertElectricalEnergy)
    self.addMode(3,Failed,NoInvertElectricalEnergy)
    self.addCondition(1,LowVoltage,2)
    self.addCondition(1,HighVoltage,2)
    self.addCondition(2,NominalVoltage,1)
    self.addCondition(1,HighestCurrent,3)
class BranchElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalBranchElectricalEnergy)
    self.addMode(2,Failed,BranchOpenCircuit)
    self.addCondition(1,BranchHighestCurrent,2,delay=2)
class CombineElectricalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalCombineElectricalEnergy)
    self.addMode(2,Failed,OpenCircuit)
    self.addCondition(1,HighestCurrent,2,delay=2)
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
    self.addMode(1,Operational,NominalElectricalToMechanicalEnergyConversion)
    self.addMode(2,Failed,ShortCircuitNoMechanicalEnergyConversion)
    self.addMode(3,Failed,OpenCircuitNoMechanicalEnergyConversion)
    self.addCondition([1,2],Overheating,3,delay=10)
    self.addCondition([1,2],FastOverheating,3,delay=1)
class ConvertElectricalToOpticalEnergy(Function):
  def construct(self):
    self.addMode(1,Operational,NominalElectricalToOpticalEnergyConversion)
    self.addMode(2,Failed,NoElectricalToOpticalEnergyConversion)
    self.addCondition(1,HighVoltage,2,delay=1)
class TransportMaterial(Function):
  def construct(self):
    self.addMode(1,Operational,NominalTransportMaterial)
    self.addMode(2,Degraded,RestrictedTransportMaterial)
    self.addMode(3,Failed,BlockedTransportMaterial)
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
class Material(Bond):
  pass

class Energy(Bond):
  pass

class Electrical(Energy):
  pass

class Heat(Energy):
  pass

class ChemicalEnergy(Energy):
  pass

class MechanicalEnergy(Energy):
  pass

class OpticalEnergy(Energy):
  pass

class Signal(Bond):
  pass

##############################################################################
#####################      End of IBFM Definitions       #####################

'''Create list of available functions in file function_list.txt'''
with open('function_list.txt','w') as file:
  for c in all_subclasses(Function):
    file.write(c.__name__+'\n')

#class EPS(Model):
#  def construct(self):
#    self.addFunction(ProtectElectricalEnergy('protectEE1'))
#    self.addFunction(ActuateElectricalEnergy('actuateEE1'))
#    self.addFunction(ImportBinarySignal('importBS1'))
#    self.addFunction(ImportChemicalEnergy('importCE1'))
#    self.addFunction(ConvertChemicalToElectricalEnergy('CEtoEE1'))
#    self.addFunction(ExportElectricalEnergy('exportEE1'))
#    self.addFunction(ExportHeatEnergy('exportHE1'))
#    self.addBond(ChemicalEnergy,'importCE1','CEtoEE1')
#    self.addBond(Heat,'CEtoEE1','exportHE1')
#    self.addBond(Electrical,'CEtoEE1','protectEE1')
#    self.addBond(Electrical,'protectEE1','actuateEE1')
#    self.addBond(Electrical,'actuateEE1','exportEE1')
#    self.addBond(Signal,'importBS1','actuateEE1')
#
#eps = Experiment(EPS())
#for i in [2,2]:
#  eps.run(i)
#eps.reviewScenarios()