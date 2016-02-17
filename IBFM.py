from math import inf

class Transition (object):
  def __init__(self, condition, nextMode, delay):
    self.condition = condition
    self.nextMode = nextMode
    self.delay = delay
    self.clock = 0
  def resetClock(self):
    self.clock = 0
  def delayRemaining(self):
    return max(0,self.delay - self.clock)

class Is (object):
  def __init__(self, thing, mode_class):
    self.thing = thing
    self.mode_class = mode_class
  def __bool__ (self):
    return isinstance(self.thing.mode,self.mode_class)

class Not(Is):
  def __bool__(self):
    return not super().__bool__()

class Or (Is):
  def __init__(self, conditions):
    self.conditions = conditions
  def __bool__ (self):
    return any(self.conditions)

class And (Is):
  def __init__(self, conditions):
    self.conditions = conditions
  def __bool__ (self):
    return all(self.conditions)

class Mode (object):
  health = ""
  def __init__(self):
    self.transitions = []
    self.minimum_delay = 0
  def __bool__(self):
    # Used in Function.setMode(),Thing.addMode()
    return True
  def __repr__(self):
    return self.__class__.__name__
  def resetClock(self):
    self.minimum_delay = inf
    for transition in self.transitions:
      transition.resetClock()
  def next(self,time_advance=0):
    self.minimum_delay = inf
    for transition in self.transitions:
      if transition.condition:
        transition.clock += time_advance
        if not transition.delayRemaining():
          self.resetClock()
          return transition.nextMode
        else:
          self.minimum_delay = min(self.minimum_delay,transition.delayRemaining())
      else:
        transition.resetClock()
    return self
  def addTransition(self,transition):
    self.transitions.append(transition)
  def isMode(self,class_name):
    return isinstance(self,class_name)
  def isExactMode(self,class_name):
    return self.__class__ is class_name

#======= Subclasses of Mode ===================

class Nominal(Mode):
  health = "Nominal"

class OffNominal(Mode):
  pass

class Degraded(OffNominal):
  health = "Degraded"

class Lost(OffNominal):
  health = "Lost"

class NoFlow(Mode):
  health = "No Flow"

class NominalNoFlow(Nominal):
  pass

class Stopped(NoFlow):
  pass

class OpenCircuit(Nominal,NoFlow):
  pass

class ClosedCircuit(Nominal):
  pass

class Close(Nominal):
  pass

class Reset(Nominal):
  pass

class Empty(Nominal):
  pass

class On(Nominal):
  pass

class Off(Nominal):
  pass


#======= Subclasses of Degraded and Lost (Failure Modes) ===================

class Inefficient(Degraded):
  pass

class High(Degraded):
  pass

class Low(Degraded):
  pass

class Early(Degraded):
  pass

class Late(Degraded):
  pass

class Hot(Degraded):
  pass

class Cold(Degraded):
  pass

class Underdraw(Degraded):
  pass

class Overdraw(Degraded):
  pass

class FailedOpenCircuit(Lost,OpenCircuit):
  pass

class FailedClosedCircuit(Lost,ClosedCircuit):
  pass

class ShortCircuit(Lost,Overdraw):
  pass

class FailedHigh(Lost):
  pass

class FailedLow(Lost):
  pass

class FailedEarly(Lost):
  pass

class FailedLate(Lost):
  pass

class FailedHot(Lost):
  pass

class FailedEmpty(Lost):
  pass

class FailedNoFlow(Lost,NoFlow):
  pass

class DriftHigh(Lost):
  pass

class DriftLow(Lost):
  pass

class StuckHigh(Lost):
  pass

class StuckLow(Lost):
  pass

#############################################################

class Interface(object):
  def __init__(self,function):
    self.function = function
    self.flow = None
  def isMode(self,class_name):
    return self.mode.isMode(class_name)

class Inflow(Interface):
  pass

class Outflow(Interface):
  pass

class Thing (object):
  def __init__(self,default=None):
    self.modes = []
    self.default = default
  def step(self,time_advance=0):
    self.mode = self.mode.next(time_advance)
    self.health = self.mode.health
    self.consequences()
    return self.mode.minimum_delay
  def isMode(self,class_name):
    return self.mode.isMode(class_name)
  def getMode(self,mode_class):
    for mode in self.modes:
      if isinstance(mode,mode_class):
        return mode
    return False
  def getExactMode(self,mode_class):
    for mode in self.modes:
      if mode.isExactMode(mode_class):
        return mode
    return False
  def addMode(self,mode_class):
    mode = self.getExactMode(mode_class)
    if not mode:
      mode = mode_class()
      self.modes.append(mode)
    return mode
  def addModes(self,mode_classes):
    for mode_class in mode_classes:
      self.addMode(mode_class)
  def getModeClasses(self):
    mode_classes = []
    for mode in self.modes:
      mode_classes.append(mode.__class__)
    return mode_classes
  def add(self,mode_classes,condition,next_mode_class,delay=0):
    if not len(mode_classes):
      mode_classes = self.getModeClasses()
    next_mode = self.addMode(next_mode_class)
    for mode_class in mode_classes:
      mode = self.addMode(mode_class)
      mode.addTransition(Transition(condition,next_mode,delay))
  def resetMode(self):
    if self.default != None:
      for mode in self.modes:
        if isinstance(mode,self.default):
          self.mode = mode
          return
      raise Exception(str(self.default)+" mode not found in "+self.name)
    self.mode = self.modes[0]


class Flow (Thing):
  def __init__(self, source, drain, default_mode_class=None):
    super().__init__(default_mode_class)
    self.source = source
    source.flow = self
    self.drain = drain
    drain.flow = self
    self.make()
  def make(self):
    self.add([Nominal,Degraded],Or([Is(self.source,Lost),
             Is(self.source,NoFlow)]),NoFlow)
    self.add([Degraded,NoFlow],Is(self.source,Nominal),Nominal)
    self.add([Nominal,NoFlow],Is(self.source,Degraded),Degraded)
  def consequences(self):
    self.source.mode = self.drain.mode = self.mode
#======== Subclasses of Flow (Level 1) ==================

class Material(Flow):
    pass

class Energy(Flow):
    pass

class Signal(Flow):
  def make(self):
    self.addModes([Off,On,NoFlow])
  def consequences(self):
    try:
      self.drain.mode = self.mode = self.source.mode
    except AttributeError:
      self.source.mode = self.drain.mode = self.mode



#======== Subclasses of Material (Level 2-3) ===============

class Human(Material):
    pass

class Gas(Material):
    pass

class Liquid(Material):
    pass

class Solid(Material):
    pass

class Object(Solid):
    pass

class Particular(Solid):
    pass

class Composite(Solid):
    pass

class Plasma(Material):
    pass

class Mixture(Material):
    pass

class LiquidLiquid(Mixture):
    pass

class GasGas(Mixture):
    pass

class SolidSolid(Mixture):
    pass

class SolidLiquid(Mixture):
    pass

class SolidGas(Mixture):
    pass

class LiquidGas(Mixture):
    pass

class SolidLiquidGas(Mixture):
    pass

class Colloidal(Mixture):
  pass

#======== Subclasses of Energy (Level 2-3) ===============

class HumanEnergy(Energy):
  pass

class Acoustic(Energy):
  pass

class Biological(Energy):
  pass

class Chemical(Energy):
  pass

class Electrical(Energy):
  def make(self):
    self.addModes([Nominal,High,Low,Overdraw,Underdraw,ShortCircuit,
                   OpenCircuit,NoFlow])
    self.add([],Is(self.drain,OpenCircuit),OpenCircuit)
    self.add([],Is(self.drain,ShortCircuit),ShortCircuit)
    self.add([],Is(self.source,NoFlow),NoFlow)
    self.add([],Is(self.drain,Overdraw),Overdraw)
    self.add([],Is(self.drain,Underdraw),Underdraw)
    self.add([],Is(self.source,High),High)
    self.add([],Is(self.source,Low),Low)
    self.add([],Is(self.source,Nominal),Nominal)
    self.add([],Is(self.drain,Nominal),Nominal)

class Electromagnetic(Energy):
  pass

class Optical(Electromagnetic):
  pass

class Solar(Electromagnetic):
  pass

class Hydraulic(Energy):
  pass

class Magnetic(Energy):
  pass

class Mechanical(Energy):
  pass

class Rotational(Mechanical):
  pass

class Pneumatic(Energy):
  pass

class Nuclear(Energy):
  pass

class Thermal(Energy):
  pass

#======== Subclasses of Signal (Level 2-3) ===============

class Status(Signal):
  pass

class Auditory(Status):
  pass

class Olfactory(Status):
  pass

class Tactile(Status):
  pass

class Taste(Status):
  pass

class Visual(Status):
  pass

class Control(Signal):
  pass

class Analog(Control):
  pass

class Discrete(Control):
  pass


class Function (Thing):
  def __init__(self,default = None,allow_faults = True):
    super().__init__(default)
    self.allow_faults = allow_faults
    self.interface()
  def setMode(self,name):
    success = False
    for mode in self.modes:
      if isinstance(mode,name):
        if success:
          raise Exception(str(self)+" has more than one mode of class "+
                          name.__name__)
        success = mode
    if not success:
      raise Exception(str(self)+" has no mode of class "+name.__name__)
    self.mode = success


#======== Subclasses of Function (Level 1) ===============

class Branch(Function):
  pass

class Channel(Function):
  def interface(self):
    self.primary_inflow = Inflow(self)
    self.primary_outflow = Outflow(self)

class Connect(Function):
  pass

class ControlMagnitude(Function):
  def interface(self):
    self.primary_inflow = Inflow(self)
    self.primary_outflow = Outflow(self)
    self.primary_control = Inflow(self)

class Convert(Function):
  def interface(self):
    self.primary_inflow = Inflow(self)
    self.primary_outflow = Outflow(self)
    self.waste_heat = Outflow(self)

class Provision(Function):
  pass

class Sense(Function):
  pass

class Indicate(Function):
  pass

class Process(Function):
  pass

class Support(Function):
  pass

#======== Subclasses of Function (Level 2) ===============

class Separate(Branch):
  pass

class Distribute(Branch):
  pass

class Import(Channel):
  def interface(self):
    self.primary_outflow = Outflow(self)
  def consequences(self):
    if self.isMode(Lost):
      self.primary_outflow.mode = NoFlow()
    else:
      self.primary_outflow.mode = self.mode

class Export(Channel):
  def interface(self):
    self.primary_inflow = Inflow(self)
  def consequences(self):
    self.primary_inflow.mode = self.mode

class Transfer(Channel):
  pass

class Guide(Channel):
  pass

class Couple(Connect):
  pass

class Mix(Connect):
  pass

class Actuate(ControlMagnitude):
  pass

class Regulate(ControlMagnitude):
  pass

class Change(ControlMagnitude):
  pass

class Stop(ControlMagnitude):
  pass

class Store(Provision):
  pass

class Supply(Provision):
  pass

class Detect(Sense):
  pass

class Measure(Sense):
  pass

class Track(Indicate):
  pass

class Display(Indicate):
  pass

class Stabilize(Support):
  pass

class Secure(Support):
  pass

class Position(Support):
  pass

#======== Subclasses of Function (Level 3) ===============

class Divide(Separate):
  pass

class Extract(Separate):
  pass

class Remove(Separate):
  pass

class Transport(Transfer):
  pass

class Transmit(Transfer):
  pass

class Translate(Guide):
  pass

class Rotate(Guide):
  pass

class AllowDOF(Guide):
  pass

class Join(Couple):
  pass

class Link(Couple):
  pass

class Increase(Regulate):
  pass

class Decrease(Regulate):
  pass

class Increment(Change):
  pass

class Decrement(Change):
  pass

class Shape(Change):
  pass

class ConditionFlow(Change):
  pass

class Prevent(Stop):
  pass

class Inhibit(Stop):
  pass

class Contain(Store):
  pass

class Collect(Store):
  pass

#======== Flow-Specific Function Consequences ===============
class ElectricalTwoNode(object):
  def consequences(self):
    inflow = self.primary_inflow
    outflow = self.primary_outflow
    if self.isMode(ClosedCircuit):
      if outflow.isMode(ShortCircuit) or outflow.isMode(OpenCircuit):
        inflow.mode = outflow.mode
      elif inflow.isMode(NoFlow):
        outflow.mode = inflow.mode
      elif outflow.isMode(Overdraw) or outflow.isMode(Underdraw):
        inflow.mode = outflow.mode
      else:
        outflow.mode = inflow.mode
    elif self.isMode(OpenCircuit):
      inflow.mode = OpenCircuit()
      outflow.mode = NoFlow()
    elif self.isMode(ShortCircuit):
      inflow.mode = ShortCircuit()
      outflow.mode = NoFlow()

#======== Flow-Specific Subclasses of Function ===============

class ImportChemicalEnergy(Import):
  def make(self):
    self.addModes([Nominal,Degraded,Lost])

class ImportElectricalEnergy(Import):
  def make(self):
    self.addModes([Nominal,High,Low,Lost])

class ImportDiscreteSignal(Import):
  def make(self):
    self.addModes([Off,On,Lost])

class ExportElectricalEnergy(Export):
  def make(self):
    self.addModes([Nominal,FailedOpenCircuit,ShortCircuit])

class ProtectElectricalEnergy(Inhibit,ElectricalTwoNode):
  def make(self):
    self.addModes([ClosedCircuit,OpenCircuit,FailedClosedCircuit,
                   FailedOpenCircuit,ShortCircuit])
    self.add([ClosedCircuit],Is(self.primary_outflow,Overdraw),OpenCircuit)

class ActuateElectricalEnergy(Actuate,ElectricalTwoNode):
  def make(self):
    self.addModes([OpenCircuit,ClosedCircuit,FailedOpenCircuit,
                   FailedClosedCircuit,ShortCircuit])
    self.add([OpenCircuit],Is(self.primary_control,On),ClosedCircuit)
    self.add([ClosedCircuit],Is(self.primary_control,Off),OpenCircuit)
    self.add([ClosedCircuit],And([Not(self.primary_inflow,NoFlow),
             Is(self.primary_outflow,ShortCircuit)]),FailedOpenCircuit,delay=.1)

class ConvertChemicalToElectricalEnergy(Convert):
  def make(self):
    self.addModes([Nominal,Inefficient,FailedHot,Lost])
    self.add([Nominal,Inefficient],And(Is(self.waste_heat,Lost),
             Not(self.primary_outflow,NoFlow)),FailedHot)
  def consequences(self):
    if self.primary_inflow.isMode(NoFlow):
      self.primary_outflow.mode = self.waste_heat.mode = NoFlow()
    elif self.isMode(Nominal):
      if self.primary_outflow.isMode(Overdraw):
        self.primary_inflow.mode = Overdraw()
        self.waste_heat.mode = High()
      elif self.primary_outflow.isMode(OpenCircuit):
        self.primary_inflow.mode = self.waste_heat.mode = NoFlow()
      elif self.primary_inflow.isMode(Nominal):
        self.primary_outflow.mode = self.waste_heat.mode = Nominal()
      elif self.primary_inflow.isMode(Degraded):
        self.primary_outflow.mode = self.wast_heat.mode = Low()
      else:
        raise Exception("Not implemented")
    elif self.isMode(Inefficient):
      if self.primary_outflow.isMode(OpenCircuit):
        self.primary_inflow.mode = self.waste_heat.mode = NoFlow()
      elif (self.primary_outflow.isMode(Overdraw) or
            self.primary_inflow.isMode(Nominal)):
        self.primary_inflow.mode = Overdraw()
        self.waste_heat.mode = High()
      else:
        raise Exception("Not implemented")
    else:
      self.primary_inflow.mode = Stopped()
      self.primary_outflow.mode = self.waste_heat = NoFlow()



class SenseVoltage:
  pass

class SenseTemperature(Sense):
  def make(self):
    self.addModes([Nominal,DriftHigh,DriftLow,StuckHigh,StuckLow,Lost])

##############################################################

class Model(object):
  def __init__(self):
    self.functions = {}
    self.flows = []
    self.make()
    for name in self.functions:
      self.functions[name].make()
      self.functions[name].name = name
    for flow in self.flows:
      flow.name = flow.source.function.name + '_' + flow.drain.function.name
    self.resetModes()
  def addFlow(self,flow,name=None):
    flow.name = name
    self.flows.append(flow)
  def resetModes(self):
    for name in self.functions:
      self.functions[name].resetMode()
    for flow in self.flows:
      flow.resetMode()
      flow.consequences()
  def setModes(self,function_modes):
    for name in function_modes:
      self.functions[name].setMode(function_modes[name])
  def step(self,time_advance=0):
    self.stepFunctions(time_advance)
    self.stepFlows()
  def stepFunctions(self,time_advance=0):
    self.minimum_delay = inf
    for name in self.functions:
      time = self.functions[name].step(time_advance)
      self.minimum_delay = min(self.minimum_delay,time)
      print(name+'\t'+str(self.functions[name].mode))
  def stepFlows(self):
    for flow in self.flows:
      flow.step()
      print(flow.name+'\t'+str(flow.mode))
  def run(self,lifetime=inf):
    self.minimum_delay = 0
    while self.minimum_delay < lifetime:
      self.runTimeless()
  def runTimeless(self):
    finished = False
    self.step(self.minimum_delay)
    old_state = self.getState()
    i = 0
    while not finished:
      i = i+1
      print("Iteration "+str(i))
      self.step()
      new_state = self.getState()
      if new_state == old_state:
        finished = True
      else:
        old_state = new_state
  def getState(self):
    state = {}
    for name in self.functions:
      function = self.functions[name]
      state[name] = str(function.mode)
    for flow in self.flows:
      state[flow.name] = str(flow.mode)
    return state
  def getHealth(self):
    health = {}
    for name in self.functions:
      function = self.functions[name]
      health[name] = str(function.health)
    for flow in self.flows:
      health[flow.name] = str(flow.health)
    return health

class Experiment(object):
  def __init__(self,model):
    self.scenarios = []
    self.model = model
  def allScenarios(self,functions,simultaneous_faults,current_scenario={}):
    simultaneous_faults -= 1
    for name in functions:
      if functions[name].allow_faults:
        leftover_functions = functions.copy()
        del leftover_functions[name]
        for mode in functions[name].modes:
          if not isinstance(mode,OffNominal):
            continue
          new_scenario = current_scenario.copy()
          new_scenario[name] = mode.__class__
          self.scenarios.append(new_scenario)
          if simultaneous_faults and len(leftover_functions):
            self.allScenarios(leftover_functions,simultaneous_faults,new_scenario)
  def setExperiment(self,simultaneous_faults=3,sampling="full"):
    self.scenarios = []
    if sampling == "full":
      self.allScenarios(self.model.functions,simultaneous_faults)
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
      self.model.resetModes()
      self.model.setModes(scenario)
      self.model.run()
      self.results.append(self.model.getState())
      self.health.append(self.model.getHealth())
    print(str(i+1)+' scenarios simulated')
    self.findUniqueResults()
    #print(str(self.unique))
    print(str(int(len(self.unique)))+' mode states or '+
      str(int(len(self.unique)*100/len(self.results)))+" percent unique")
    self.findUniqueHealth()
    print(str(int(len(self.unique)))+' health states or '+
      str(int(len(self.unique)*100/len(self.results)))+" percent unique")

class EPS(Model):
  class ActuatorLogic(Process):
    def interface(self):
      self.temperature1 = Inflow(self)
    def make(self):
      pass
  def make(self):
    self.functions["importEE1"] = ImportElectricalEnergy()
    self.functions["inhibitEE1"] = ProtectElectricalEnergy()
    self.functions["actuateEE1"] = ActuateElectricalEnergy()
    self.functions["exportEE1"] = ExportElectricalEnergy()
    self.functions["importControl1"] = ImportDiscreteSignal(default=On)
    self.flows.append(Electrical(self.functions["importEE1"].primary_outflow,
                                 self.functions["inhibitEE1"].primary_inflow))
    self.flows.append(Electrical(self.functions["inhibitEE1"].primary_outflow,
                                 self.functions["actuateEE1"].primary_inflow))
    self.flows.append(Electrical(self.functions["actuateEE1"].primary_outflow,
                                 self.functions["exportEE1"].primary_inflow))
    self.flows.append(Discrete(self.functions["importControl1"].primary_outflow,
                               self.functions["actuateEE1"].primary_control))
#for j in range(1):
#  eps = Experiment(EPS())
#  for i in [2]:
#    eps.run(i)
import pickle
#pickle.dump( eps.scenarios, open( "scenarios2.p", "wb" ) )
#pickle.dump( eps.results, open( "results2.p", "wb" ) )
s1 = pickle.load( open( "scenarios1.p", "rb" ) )
s2 = pickle.load( open( "scenarios2.p", "rb" ) )
r1 = pickle.load( open( "results1.p", "rb" ) )
r2 = pickle.load( open( "results2.p", "rb" ) )
bad = pickle.load( open("badscenarios.p","rb"))

i=[]
for i1,t1 in enumerate(s1):
  for i2,t2 in enumerate(s2):
    if t1==t2:
      i.append(i2)
      break

eps = EPS()
eps.setModes(bad[0])
eps.run()
