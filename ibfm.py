'''ibfm.py
Inherent Behavior in Functional Models

Author: Matthew G McIntire
2016
'''

#These flags can be changed in the file or at runtime after import ibfm
track_states = False
printWarnings = False
print_iterations = False
print_scenarios = False
run_parallel = False
n_workers = 3

from math import inf
from time import time
from glob import glob
import networkx as nx
import re
#import multiprocessing
import pickle

class InconsistencyError(Exception):
  pass
class ModelError(Exception):
  pass

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

def getSubclass(cls,name):
  '''Return the subclass of cls named name'''
  for c in all_subclasses(cls):
    if c.__name__ == name:
      return c

class State(float):
  '''Ordinal type for qualitatively representing flow values'''
  def __new__(cls,value=None,flow=None):
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
  def __init__(self,value=None,flow=None):
    self.flow = flow
  def __repr__(self):
    return self.__class__.__qualname__
  def __str__(self):
    return self.__class__.__qualname__
  @staticmethod
  def getMethod(string):
    '''Return a lambda method that returns the state specified in string.'''
    state_class = getSubclass(State,string)
    try:
      state = state_class()
      return lambda: [state]
    except TypeError:
      return None
  @classmethod
  def getUnaryMethod(cls,string):
    '''Return the appropriate single-argument operator specified by string.'''
    if string == 'effort':
      return cls.setValueToEffort
    if string == 'rate':
      return cls.setValueToRate
    if string == 'max':
      return cls._max
    if string == 'min':
      return cls._min
    if string == '++':
      return cls._increment
    if string == '--':
      return cls._decrement
    if string == 'invert':
      return cls._inverse
    if string == 'any':
      return cls._any
    if string == 'all':
      return cls._all
    if string == 'not':
      return cls._not
    return None
  @classmethod
  def getBinaryMethod(cls,string):
    '''Return the appropriate double-argument operator specified by string.'''
    if string == ',':
      return cls._combine
    if string == '*':
      return cls._times
    if string == '==':
      return cls._eq
    if string == '!=':
      return cls._neq
    if string == '>=':
      return cls._geq
    if string == '<=':
      return cls._leq
    if string == '<':
      return cls._lt
    if string == '>':
      return cls._gt
    if string == 'and':
      return cls._and
    if string == 'or':
      return cls._or
    return None
  @classmethod
  def getSetMethod(cls,string):
    '''Return the appropriate method for setting either the effort or rate of
    the flow specified during simulation.'''
    if string == 'effort':
      return cls.setEffort
    elif string == 'rate':
      return cls.setRate
  @staticmethod
  def setValueToEffort(states):
    '''Set the value of each state in states to the effort of its flow'''
    return [State(state.flow.effort,state.flow) for state in states]
  @staticmethod
  def setValueToRate(states):
    '''Set the value of each state in states to the rate of its flow'''
    return [State(state.flow.rate,state.flow) for state in states]
  @staticmethod
  def _max(states):
    value = max(states)
    return [state for state in states if state == value]
  @staticmethod
  def _min(states):
    value = min(states)
    return [state for state in states if state == value]
  @staticmethod
  def _increment(states):
    return [State(state+1,state.flow) for state in states]
  @staticmethod
  def _decrement(states):
    return [State(state-1,state.flow) for state in states]
  @staticmethod
  def _inverse(states):
    for i,state in enumerate(states):
      if state == Zero():
        states[i] = Highest(flow = state.flow)
      elif state == Low():
        states[i] = High(flow = state.flow)
      elif state >= High():
        states[i] = Low(flow = state.flow)
    return states
  @staticmethod
  def _any(x):
    return [any(x)]
  @staticmethod
  def _all(x):
    return [all(x)]
  @staticmethod
  def _not(xs):
    return [not x for x in xs]
  @staticmethod
  def _combine(x1,x2):
    return x1+x2
  @staticmethod
  def _times(x1s,x2s):
    if len(x1s) == 1:
      if x1s[0].flow == None:
        return [State(x1s[0]*x2,x2.flow) for x2 in x2s]
      if all([x2.flow == None for x2 in x2s]):
        return [State(x1s[0]*x2,x1s[0].flow) for x2 in x2s]
      return [State(x1s[0]*x2) for x2 in x2s]
    if len(x2s) == 1:
      if x2s[0].flow == None:
        return [State(x2s[0]*x1,x1.flow) for x1 in x1s]
      if all([x1.flow == None for x1 in x1s]):
        return [State(x2s[0]*x1,x2s[0].flow) for x1 in x1s]
      return [State(x2s[0]*x1) for x1 in x1s]
    if len(x1s) == len(x2s):
      return [State(x1*x2) for x1,x2 in zip(x1s, x2s)]
    raise Exception('Unforseen multiplication case!')
  @staticmethod
  def _eq(x1s,x2s):
    if len(x2s) == 1:
      return [x2s[0] == x1 for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] == x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 == x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen eq case')
  @staticmethod
  def _neq(x1s,x2s):
    if len(x2s) == 1:
      return [x2s[0] != x1 for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] != x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 != x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen neq case')
  @staticmethod
  def _geq(x1s,x2s):
    if len(x2s) == 1:
      return [x1 >= x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] >= x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 >= x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen geq case')
  @staticmethod
  def _leq(x1s,x2s):
    if len(x2s) == 1:
      return [x1 <= x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] <= x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 <= x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen leq case')
  @staticmethod
  def _gt(x1s,x2s):
    if len(x2s) == 1:
      return [x1 > x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] > x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 > x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen gt case')
  @staticmethod
  def _lt(x1s,x2s):
    if len(x2s) == 1:
      return [x1 < x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] < x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 < x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen lt case')
  @staticmethod
  def _and(x1s,x2s):
    if len(x2s) == 1:
      return [x1 and x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] and x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 and x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen and case')
  @staticmethod
  def _or(x1s,x2s):
    if len(x2s) == 1:
      return [x1 or x2s[0] for x1 in x1s]
    if len(x1s) == 1:
      return [x1s[0] or x2 for x2 in x2s]
    if len(x1s) == len(x2s):
      return [x1 or x2 for x1,x2 in zip(x1s,x2s)]
    raise Exception('Unforseen or case')
  @staticmethod
  def setRate(lhs,rhs):
    value = rhs[0]
    for state in rhs[1:]:
      if value != state:
        print(rhs)
        print([state for state in rhs])
        raise InconsistencyError()
    for state in lhs:
      state.flow.setRate(value)
  @staticmethod
  def setEffort(lhs,rhs):
    value = rhs[0]
    for state in rhs[1:]:
      if value != state:
        print(rhs)
        print([state for state in rhs])
        raise InconsistencyError()
    for state in lhs:
      state.flow.setEffort(value)

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

class ModeHealth(object):
  pass
class Operational(ModeHealth):
  pass
class Degraded(ModeHealth):
  pass
class Failed(ModeHealth):
  pass

class ModeConditionParent(object):
  '''Superclass for the Mode and Condition classes.

  Contains methods used by both Mode and Condition objects.
  '''
  def stack(self,x):
    '''Take a list of strings and functions and fold it into a single function.

    Recursivley identifies keywords in x as operators in order to construct a
    single function out of an ibfm expression in mode and condition definitions.
    '''
    # Check if done
    if len(x) == 1:
      if callable(x[0]):
        return x[0]
      else:
        raise Exception('Unexpected: '+str(x[0])+' in '+self.__class__.__name__)
    # Collapse parentheses
    count = 0
    for i,element in enumerate(x):
      if element == '(':
        count = count + 1
        if count == 1:
          i1 = i
      elif element == ')':
        count = count - 1
        if count == 0:
          return self.stack(x[:i1]+[self.stack(x[i1+1:i])]+x[i+1:])
    if count:
      raise Exception('Mismatched parenthesis in ' + self.__class__.__name__)
    # Stack Unary Operators from both ends
    for i in [-1,0]:
      f = State.getUnaryMethod(x[i])
      if f:
        x.pop(i)
        g = self.stack(x)
        if not callable(g):
          raise Exception('Unforseen stack case: '+str(x))
        return self.getLambda(f,g)
    # Stack binary operators
    for i in [-2,1]:
      f = State.getBinaryMethod(x[i])
      if f:
        g = self.stack(x[:i])
        h = self.stack(x[i+1:])
        return self.getLambda(f,g,h)
    raise Exception('Unforseen stack case: '+str(x))
  def getLambda(self,f=None,g=None,h=None,arg=None):
    '''A lambda factory to ensure proper argument closure.'''
    if arg:
      if f:
        return lambda: f(arg)
      else:
        return lambda: arg
    if h:
      return lambda: f(g(),h())
    if g:
      return lambda: f(g())
    raise Exception('Unforseen getLambda')
  def flowAndStateMethods(self,behavior,optional=False):
    '''Replaces ibfm references to states and flows with the appropriate objects.

    Behavior is a list of strings, some of which refer to states and flows.
    Each reference to a state or flow is replaced by a method which returns the
    state or flow refered to.
    '''
    # Replace strings with flow and state object methods
    with_methods = []
    flow_class = None
    flow = None
    for element in behavior:
      if flow_class: #If a flow class is already identified
        if element == 'input':
          flow = self.in_flow[flow_class]
        elif element == 'output':
          flow = self.out_flow[flow_class]
        else:
          raise Exception('Expected "input" or "output" following '+
          flow_class.__name__+' in '+str(self)+' '+
          self.__class__.__name__+' definition.')
        if flow == None:
          raise ModelError('Expected '+flow_class.__name__+' '+element+' in '+
            self.function.name)
        flow_class = None
      elif flow: #If a flow class and its direction have been identified
        if element == 'effort':
          f = self.getLambda(f=State.setValueToEffort,arg=flow)
        elif element == 'rate':
          f = self.getLambda(f=State.setValueToRate,arg=flow)
        else:
          raise Exception('Expected "effort" or "rate" following the input/output of '+
            flow_class.__name__+' in '+str(self)+' '+
            self.__class__.__name__+' definition.')
        with_methods.append(f)
        flow = None
      else:
        #Test for references to a state
        f = State.getMethod(element)
        if f:
          with_methods.append(f)
        else:
          #Test for references to a flow
          flow_class = Flow._subclasses.get(element)
          if not flow_class:
            if element in ['input','output']:
              raise Exception(element+' not following flow type in '+str(self)+
              ' '+self.__class__.__name__+' definition.')
            #Everything else gets passed through unchanged.
            with_methods.append(element)
    if flow:
      #The effort/rate distinction has already been identifed in self.behavior(s)
      with_methods.append(self.getLambda(arg=flow))
    return with_methods

class Mode(ModeConditionParent):
  '''Class for operational modes that functions may use.
  '''
  _subclasses = {}
  def __init__(self,name,function,health,**attr):
    '''Return a Mode object.

    Required arguments:
    name -- a unique name (for easier to read function definitions)
    function -- the object the mode belongs to (for access to its flows),
    health -- a ModeHealth object designating the health of the function
              represented by the mode.
    '''
    self.name = name
    self.function = function
    self.out_flow = function.out_flow
    self.in_flow = function.in_flow
    self.health = health
    self.attr = attr
  def __repr__(self):
    return self.__class__.__qualname__
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
  def createSetMethod(self,setMethod,lhs,rhs):
    if not callable(lhs) or not callable(rhs) or not callable(setMethod):
      raise Exception('Bad creatSetMethod call')
    return lambda: setMethod(lhs(),rhs())
  def behaviors(self,mode=None):
    '''Yield Behavior methods.

    Runs recursively (but in a different subclass) when using the 'import'
    keyword.
    '''
    if mode == None:
      mode = self.__class__
    for behavior in mode._behaviors:
      optional = False
      if 'optional' == behavior[0].lower():
        optional = True
        behavior = behavior[1:]
      elif 'import' == behavior[0].lower():
        from_mode = Mode._subclasses[behavior[1]]
        if from_mode:
          yield from from_mode.behaviors(self,from_mode)
        else:
          raise Exception(behavior[1]+' is not a defined mode. '+str(self)+
            ' tried to use behaviors from it.')
        continue
      # Separate the left-hand side from the right-hand side of the assignment
      assignment = behavior.index('=')
      lhs = behavior[:assignment]
      rhs = behavior[assignment+1:]
      # Get value setter method
      setMethod = State.getSetMethod(lhs.pop())
      # Replace flows and states with appropriate methods
      try:
        lhs = self.flowAndStateMethods(lhs,optional)
        rhs = self.flowAndStateMethods(rhs,optional)
      except KeyError:
        if optional:
          continue
        else:
          raise
      # Replace everything else
      lhs = self.stack(lhs)
      rhs = self.stack(rhs)
      yield self.createSetMethod(setMethod,lhs,rhs)
  def textBehaviors(self,mode=None):
    if mode == None:
        mode = self
    for behavior in mode._behaviors:
      optional = 'required'
      if 'optional' == behavior[0].lower():
        optional = 'optional'
        behavior = behavior[1:]
      elif 'from' == behavior[0].lower():
        from_Mode = Mode._subclasses[behavior[1]]
        if from_Mode:
          yield from from_Mode.textBehaviors(self,from_Mode)
        else:
          print(behavior)
          raise Exception(behavior[1]+' is not a defined mode. '+str(self)+
            ' tried to use behaviors from it.')
        continue
      ins = []
      outs = []
      cls = getSubclass(Behavior,behavior[0])
      if not cls:
        raise Exception(behavior[0]+' is not a defined behavior.')
      try:
        for word in behavior[1:]:
          if word.lower() in 'inout':
            entry = word.lower()
          elif entry == 'in':
            ins.append(word)
          elif entry == 'out':
            outs.append(word)
          else:
            raise Exception('Looking for keywords in or out, found: '+word)
        yield (behavior[0],optional,ins,outs)
      except KeyError:
        if not optional:
          raise

  def reset(self):
    '''Reset the Mode object for a new simulation.

    Required because Mode objects share NetworkX graphs with Condition
    objects, which have their timers reset, and this is easier than generating
    a different iterator for only Condition objects.
    '''
    pass

class Condition(ModeConditionParent):
  '''Class for a condition to advance to another mode.
  '''
  _subclasses = {}
  def __init__(self,function,delay=0,logical_not=False):
    '''Return a Condition object

    Required arguments:
    function -- the object it belongs to (for access to its flows)
    delay -- the amound of time the condition must be met for a mode change.
    logical_not -- boolean flag indicating whether the condition should be
                   logically negated.
    '''
    self.out_flow = function.out_flow
    self.in_flow = function.in_flow
    self.delay = delay
    self.reset()
    if logical_not:
      self.test = lambda: not self.behavior()
    else:
      self.test = self.behavior()
  def behavior(self,condition=None):
    if condition == None:
      condition = self.__class__
    if len(condition._behaviors) != 1:
      raise Exception('Conditions must have exactly one test behavior! '+
      condition.__name__+' does not.')
    behavior = condition._behaviors[0]
    if 'import' == behavior[0].lower():
      from_condition = Mode._subclasses[behavior[1]]
      if from_condition:
        return from_condition.behavior(self,from_condition)
      else:
        raise Exception(behavior[1]+' is not a defined condition. '+str(self)+
          ' tried to use the behavior from it.')
    behavior = self.flowAndStateMethods(behavior)
    test = self.stack(behavior)
    return lambda: test()[0]
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
  _subclasses = {}
  def __init__(self,model,name=None,allow_faults=True,**attr):
    '''Return a Function object

    Required arguments:
    name -- a unique name for use in defining flows
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
    self.in_flow = {}
    self.out_flow = {}
    self.all_flows = []
    self.modes = []
    if name != None:
      if name not in model.names:
        model.names.append(name)
      else:
        raise Exception(name+' already used as a function name.')
    else:
      for n in range(1,10):
        name = self.__class__.__qualname__+format(n,'01d')
        if name not in model.names:
          model.names.append(name)
          break
      else:
        raise Exception('Too many ' +self.__class__.__qualname__+' functions.  '+
        'Raise the limit.')
    self.name = name
  def __str__(self):
    return self.name
  def __repr__(self):
    return self.name
  def __hash__(self):
    '''Return hash to identify unique Function objects.

    Used by dictionaries in NetworkX.
    '''
    return hash(self.name)
  def __lt__(self,other):
    return str(self)<str(other)
  def __eq__(self,other):
    '''Return boolean to identify unique Function objects.

    Used by dictionaries in NetworkX.
    '''
    return repr(self) == repr(other) or self.name == str(other)
  def construct(self):
    '''Build the modes and conditions for the function.

    For functions defined in ibfm files.
    '''
    for mode in self.__class__._modes:
      ident = mode[0]
      health = getSubclass(ModeHealth,mode[1])
      mode_class = Mode._subclasses.get(mode[2])
      if mode_class is None:
        raise Exception(mode[2]+' is not a defined mode')
      self.addMode(ident,health,mode_class)
    for condition in self.__class__._conditions:
      entry = None
      delay = 0
      source_modes = []
      for word in condition:
        if word.lower() == 'to':
          entry = 'to'
        elif word.lower() == 'delay':
          entry = 'delay'
        elif entry == 'to':
          next_mode = word
          entry = 'class'
        elif entry == 'delay':
          delay = float(word)
        elif entry == 'class':
          condition_class = Condition._subclasses.get(word)
          if condition_class is None:
            raise Exception(condition[0]+condition[1]+condition[2]+condition[3]+' is not a defined mode')
        else:
          source_modes.append(word)
      self.addCondition(source_modes,condition_class,next_mode,delay=delay)
  def reset(self):
    '''Reset all modes and set mode to default.'''
    self.mode = self.default
    for node in self.condition_graph.nodes_iter():
      node.reset()
  def addOutFlow(self,flow):
    '''Attach an outflow flow to the function.

    Also fills out a list of all flows in or out of the function.
    '''
    self._addFlow(flow,flow.__class__,self.out_flow)
    self.all_flows.append(flow)
  def addInFlow(self,flow):
    '''Attach an inflow flow to the function.

    Also fills out a list of all flows in or out of the function.
    '''
    self._addFlow(flow,flow.__class__,self.in_flow)
    self.all_flows.append(flow)
  def _addFlow(self,flow,flow_class,flows):
    '''Add a flow to the flows dictionary (recursively).

    Makes sure the flow is reachable by its class or any of its superclasses
    as the key. Also fills out a list of all flows in or out of the function.
    '''
    previous = flows.get(flow_class)
    if previous:
      previous.append(flow)
    else:
      flows[flow_class] = [flow]
    if Flow not in flow_class.__bases__:
      for base in flow_class.__bases__:
        self._addFlow(flow,base,flows)
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
      raise Exception("{0} missing {1} flow.".format(self,error.args[0]))
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
      try:
        behavior()
      except:
        print(self)
        print(self.mode)
        raise
    return minimum_timer

class Flow(object):
  '''Superclass for flows in the functional model.'''
  _subclasses = {}
  def __init__(self,source,drain):
    self.source = source
    self.drain = drain
    self.name = source.name+'_'+drain.name+'_'+self.__class__.__name__
    self.reset()
    self.flow = self #For State.setValueToEffort and setValueToFlow
  def __repr__(self):
    return self.__class__.__qualname__
  def reset(self,effort=Zero(),rate=Zero()):
    '''Set the effort and rate of the flow to Zero() unless otherwise specified.'''
    self.effort = effort
    self.rate = rate
    self.effort_queue = None
    self.rate_queue = None
  def setEffort(self,value):
    '''Set the effort of the flow to value. Queued until step(self) is called.'''
    if printWarnings and not self.effort_queue is None:
      print('Warning! Competing causality in '+self.name+' effort.')
    self.effort_queue = value
  def setRate(self,value):
    '''Set the rate of the flow to value. Queued until step(self) is called.'''
    if printWarnings and not self.rate_queue is None:
      print('Warning! Competing causality in '+self.name+' rate.')
    self.rate_queue = value
  def step(self):
    '''Resolve the effort and rate values in the flow.'''
    changed = False
    if self.effort != self.effort_queue and self.effort_queue != None:
      self.effort = self.effort_queue
      changed = True
      if printWarnings and self.rate != self.rate_queue:
        print('Warning! Overlapping causality in '+self.name)
    if self.rate != self.rate_queue and self.rate_queue != None:
      self.rate = self.rate_queue
      changed =True
    self.effort_queue = self.rate_queue = None
    return changed
Flow._subclasses['Flow'] = Flow

class Model(object):
  '''Class for functional models.

  Replaceable methods:
  construct(self) -- Call self.addFunction(function) and
                     self.addFlow(in_function_name,out_function_name) repeatedly
                     to describe the functions and flows that make up the
                     functional model.
  '''
  _subclasses = {}
  def __init__(self,graph=None):
    '''Construct the model and run it under nominal conditions.

    Keyword Arguments:
    graph -- a NetworkX graph representing the functional model
    '''
    #This graph contains all of the functions as nodes and flows as edges.
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
    '''Construct a model from an imported graph or model defined in a .ibfm file.

    Replace this method when directly defining models as subclasses.
    '''
    if self.imported_graph:
      #Find keys
      function_key = None
      flow_key = None
      for _,data in self.imported_graph.nodes_iter(data=True):
        for key in data:
          if Function._subclasses.get(data[key]) is not None:
            function_key = key
            break
        if function_key:
          break
      else:
        raise Exception('No defined function names found.')
      for _,_,data in self.imported_graph.edges_iter(data=True):
        for key in data:
          if Flow._subclasses.get(data[key]) is not None:
            flow_key = key
            break
        if flow_key:
          break
      else:
        raise Exception('No defined flow names found.')
      #Build model
      for node,data in self.imported_graph.nodes_iter(data=True):
        function = Function._subclasses.get(data[function_key])
        if function is None:
          raise Exception(data[function_key]+' is not a defined function name.')
        self.addFunction(function(self,node))
      for node1,node2,data in self.imported_graph.edges_iter(data=True):
        flow_class = Flow._subclasses.get(data[flow_key])
        if flow_class is None:
          raise Exception(data[flow_key]+' is not a defined flow name.')
        self.addFlow(flow_class,node1,node2)
    else: #The model was defined in a .ibfm file
      for words in self.__class__._functions:
        ident = words[0]
        function = Function._subclasses[words[1]]
        self.addFunction(function(self,ident))
      for words in self.__class__._flows:
        ident = words[:2]
        flow = Flow._subclasses[words[2]]
        self.addFlow(flow,ident[0],ident[1])

  def flows(self,functions=False):
    '''Generate flows for iterating.

    NetworkX does not allow edges to be arbitrary objects; objects must be
    stored as edge attributes.
    '''
    if functions:
      for in_function,out_function,attr in self.graph.edges_iter(data=True):
        yield (attr[Flow],in_function,out_function)
    else:
      for _,_,attr in self.graph.edges_iter(data=True):
        yield attr[Flow]
  def reset(self):
    '''Reset the clock, all functions, and all flows.'''
    resetClock()
    for function in self.functions():
      function.reset()
    for flow in self.flows():
      flow.reset()
  def connect(self):
    '''Finish initialization of each function.

    Give each function handles to every flow connected to it, then run each
    function's construct method to initialize its modes and conditions.
    '''
    for flow,in_function,out_function in self.flows(functions=True):
      in_function.addOutFlow(flow)
      out_function.addInFlow(flow)
    for function in self.functions():
      function.construct()
  def addFunction(self,function):
    '''Add function to the graph of the functional model.'''
    self.graph.add_node(function)
  def addFlow(self,flow_class,in_function_name,out_function_name):
    '''Add flow to the graph of the functional model.

    Required arguments:
    flow -- the flow to be added
    in_function_name -- the id of the function that supplies effort to the flow
    out_function_name -- the id of the function that accepts rate from the flow
    '''
    in_function = self.getFunction(in_function_name)
    out_function = self.getFunction(out_function_name)
    flow = flow_class(in_function,out_function)
    flow.name = in_function_name+'_'+out_function_name
    self.graph.add_edge(in_function,out_function,attr_dict={Flow:flow})
  def getFunction(self,name):
    '''Return the function with the given id.'''
    for function in self.functions():
      if function.name == name:
        return function
  def step(self):
    '''Perform one iteration of the functional model as a state machine.'''
    self.stepFunctions()
    self.resolveFlows()
  def resolveFlows(self):
    '''Resolve the effort and rate values in each active flow.'''
    active_functions = []
    for flow in self.active_flows:
      changed = flow.step()
      if print_iterations:
        print(flow.name.ljust(35)+str(flow.effort).ljust(10)+str(flow.rate).ljust(10))
      if changed:
        active_functions.extend((flow.source,flow.drain))
    self.active_functions = set(active_functions)
  def stepFunctions(self):
    '''Evaluate each active function.'''
    active_flows = []
    for function in self.active_functions:
      timer = function.step() #This is the evaluation
      if print_iterations:
        print(function.name.ljust(20)+str(function.mode))
      if timer == inf:
        self.timers.pop(function,None) #Remove the function from timers
      else:
        self.timers[function] = timer #Add/update the function to timers
      active_flows.extend(function.all_flows)
    self.active_flows = set(active_flows)
  def run(self,lifetime=inf):
    '''Simulate the functional model as a state machine with pseudotime.

    Keyword arguments:
    lifetime=inf -- the time at which the simulation should stop, regardless of
                    whether the model has reached steady state.
    '''
    global last_clock, clock
    resetClock()
    if track_states:
      self.states = [self.getState()]
      self.timings = [clock]
    if print_iterations:
      print('Iteration 0')
      self.printState(flows=True)
    self.active_functions = self.functions()
    self.timers = {}
    i = 0
    while clock < lifetime:
      i = self.runTimeless(i)
      last_clock = clock
      minimum_timer_functions = {}
      timers_to_keep = {}
      minimum_timer = inf
      for function, timer in self.timers.items():
        if timer < minimum_timer:
          timers_to_keep.update(minimum_timer_functions)
          minimum_timer = timer
          minimum_timer_functions = {function:timer}
        elif timer == minimum_timer:
          minimum_timer_functions[function] = timer
        else:
          timers_to_keep[function] = timer
      clock = minimum_timer
      self.active_functions = minimum_timer_functions
      self.timers = timers_to_keep
      if print_iterations:
        input()
  def runTimeless(self,i=0):
    '''Simulate the functional model as a timeless state machine.

    Iterates the simulation without advancing the clock until steady state is
    reached.
    '''
    finished = False
    while not finished:
      i = i+1
      #print(str(i))
      if print_iterations:
        print("\nIteration "+str(i)+'    Clock: '+str(clock))
      self.step()
      if track_states:
        self.timings.append(clock)
        self.states.append(self.getState())
      if not self.active_functions:
        finished = True
    return i
  def loadState(self,state):
    '''Set state as the current state of the model.

    Required arguments:
    state -- a dictionary of values for functions and flows. Keys are function
             and flow objects, function values are mode objects, and flow values
             are two-element lists containing an effort value and a rate value.
             Overwrites current state, so any functions or flows not included in
             the argument are left alone.
    '''
    for obj in state:
      if isinstance(obj,Function):
        obj.mode = state[obj]
      elif isinstance(obj,Flow):
        obj.effort = state[obj][0]
        obj.rate = state[obj][1]
      else:
        raise Exception(str(obj)+' is not a function or a flow.')
  def loadNominalState(self):
    '''Set the nominal state as the current state of the model.'''
    self.loadState(self.nominal_state)
  def getStringState(self):
    '''Return the current state of the model as strings

    Return a dictionary of values for functions and flows. Keys are function and
    flow string representations, function values are modes, and flow values are
    two-element lists containing an effort value and a rate value.
    '''
  def getState(self):
    '''Return the current state of the model.

    Return a dictionary of values for functions and flows. Keys are function and
    flow objects, function values are mode objects, and flow values are two-
    element lists containing an effort value and a rate value.
    '''
    state = {}
    for function in self.functions():
      state[function] = function.mode
    for flow in self.flows():
      state[flow] = [flow.effort,flow.rate]
    return state
  def printState(self,i=None,flows=False,state=None):
    '''Print a state of the model to the console.

    Keyword Arguments:
    i=None -- an integer specifying which iteration of the current simulation
              to print
    flows=False -- a flag whether to print flow values alongside function values.
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
        print(function.name.ljust(20)+str(state[function]))
    if flows:
      for flow in self.flows():
        if state.get(flow):
          print(flow.name.ljust(35)+str(state[flow][0]).ljust(10)+str(state[flow][1]).ljust(10))
  def printStates(self,flows=False):
    '''Print the entire iteration history of the current simulation.

    Keyword Arguments:
    flows=False -- a flag whether to print flow values alongside function values.
    '''
    for i in range(len(self.states)):
      self.printState(i,flows)

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
    elif Model._subclasses.get(model):
      self.model = Model._subclasses.get(model)()
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
    functions.sort()
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
  def stringScenario(self,scenario):
    s = {}
    for key,value in scenario.items():
      s[key.name] = [value.name,value.health.__class__.__name__,value.__class__.__name__]
    return s
  def getScenarios(self):
    '''Return the scenarios in string form rather than ibfm objects'''
    y = []
    for scenario in self.scenarios:
      y.append(self.stringScenario(scenario))
    return y
  def getResults(self,return_functions=True,return_flows=True):
    '''Return the results in string form rather than ibfm objects'''
    y = []
    for result in self.results:
      r = {}
      for key,value in result.items():
        if return_functions and isinstance(key,Function):
          r[key.name] = [value.name,value.health.__class__.__name__,value.__class__.__name__]
        elif return_flows and isinstance(key,Flow):
          r[key.name] = [str(value[0]),str(value[1])]
      y.append(r)
    return y
  def exportScenariosAndResults(self,filename):
    pickle.dump([self.getScenarios(),self.getResults()],open(filename,'wb'))
  def findResults(self, data):
    '''Find scenarios that result in data'''
    function_name = data[0]
    mode_name = data[1]
    function = self.model.getFunction(function_name)
    found = []
    for i,result in enumerate(self.results):
      if result[function].__class__.__name__ == mode_name:
        found.append(i)
    return found
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
    print(str(len(self.scenarios))+' scenario experiment created in '+str(t2-t1)+' seconds.')
    #return
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
    return
#    self.findUniqueHealth()
#    print(str(int(len(self.unique)))+' health states or '+
#      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
  def runOneScenario(self,scenario):
    if print_iterations:
      print(self.stringScenario(scenario))
    self.model.loadNominalState()
    self.model.loadState(scenario)
    if print_scenarios:
      print(scenario)
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



def load(filename):
  '''Load model, function, flow, mode, and condition definitions from a .ibfm file'''
  with open(filename,'r') as file:
    current = None #Variable for the class being defined
    first_line = False #True after reading the first line of a keyword
    indent = 0
    for i,line in enumerate(file):
      words = re.findall(r"[\w]+|==|!=|<=|>=|\+\+|--|[*=,()<>%$#/]",line)
      if not words: #Ignore blank lines
        continue
      word = words[0].lower()
      if word in '%$#/': #Allow many comment characters
        continue
      line = line.expandtabs(4)
      line_indent = len(line)-len(line.lstrip())
      if line_indent < indent: #Test for reduced indentation
        current = None
        indent = line_indent
      if current:
        if first_line:
          if line_indent == indent:
            raise Exception('Expected indent in line '+str(i+1)+' of '+filename)
          indent = line_indent
          first_line = False
        else:
          if line_indent > indent:
            raise Exception('Unexpected indent in line '+str(i+1)+' of '+filename)
        if Function in current.__bases__:
          if 'mode' == word:
            current._modes.append(words[1:])
          elif 'condition' == word:
            current._conditions.append(words[1:])
          else:
            raise Exception('Unknown function keyword: '+words[0]+' in line '+
            str(i+1)+' of: ' +filename)
        elif Mode in current.__bases__ or Condition in current.__bases__:
          current._behaviors.append(words)
        elif Model in current.__bases__:
          if 'function' == word:
            current._functions.append(words[1:])
          elif 'flow' == word or 'flow' == word:
            current._flows.append(words[1:])
          else:
            raise Exception('Unknown model keyword: '+words[0]+' in line '+
            str(i+1)+' of: ' +filename)
        else:
          raise Exception('What happened?')
      if not current:
        first_line = True
        if 'function' == word:
          current = type(words[1],(Function,),{'_modes':[],'_conditions':[]})
          Function._subclasses[words[1]] = current
        elif 'mode' == word:
          current = type(words[1],(Mode,),{'_behaviors':[]})
          Mode._subclasses[words[1]] = current
        elif 'condition' == word:
          current = type(words[1],(Condition,),{'_behaviors':[]})
          Condition._subclasses[words[1]] = current
        elif 'model' == word:
          current = type(words[1],(Model,),{'_functions':[],'_flows':[]})
          Model._subclasses[words[1]] = current
        elif 'flow' == word:
          Flow._subclasses[words[1]] = type(words[1],(Flow._subclasses[words[2]],),{})
        else:
          if first_line:
            pass #This is to get rid of an annoying warning in Spyder.
          raise Exception('Unknown keyword: '+words[0]+' in line '+str(i+1)+
          ' of: ' +filename)

def compareResults(filenames):
  n = 0
  o = []
  for filename in filenames:
    o.append(pickle.load(open(filename,'rb')))
  for i1,scenario1 in enumerate(o[0][0]):
    for i2,scenario2 in enumerate(o[1][0]):
      if scenario1 == scenario2:
        r1 = o[0][1][i1]
        r2 = o[1][1][i2]
        if r1 != r2:
          print('For scenario:')
          for key,value in scenario1.items():
            print(key+':'+str(value))
          print('Results:')
          for key,value in r1.items():
            print(key+':'+str(value))
            if value != r2[key]:
              print(key+':'+str(r2[key]))
          n = n+1
  print(str(n)+' results differ.')

##############################################################################
#####################      End of IBFM Definitions       #####################
'''load all .ibfm files in the path'''
files = glob('*.ibfm')
for file in files:
  load(file)
'''Create list of available functions in file function_list.txt'''
with open('function_list.txt','w') as file:
  l = []
  for c in all_subclasses(Function):
    l.append(c.__qualname__)
  l.sort()
  file.write('\n'.join(l))

'''Create a dictionary of all defined functions'''
functions = {}
for function in Function._subclasses:
  functions[function] = [(mode[2],mode[1]) for mode in Function._subclasses[function]._modes]

'''Create a dictionary of all defined modes'''
#modes = {}
#for mode in Mode._subclasses:
#    modes[mode] = [m for m in Mode._subclasses[mode].textBehaviors(Mode._subclasses[mode])]
