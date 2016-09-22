# IBFM
Inherent Behavior in Functional Models

This python module is used for simulating failure behavior on functional models of complex engineered systems. Rather than simulating a system based on its constituent components, IBFM uses behavior associated with the functions that a component might fulfill. For instance, a circuit breaker and a fuse would both fulfill the function protect electrical energy.

## Installation
IBFM requires the NetworkX module as a dependency. Some python installations do not include NetworkX by default. Installation of IBFM consists of putting the folder containing `ibfm.py` and the `.ibfm` files into a folder in the python path. Additional `.ibfm` files may be loaded from the working directory.

## Running an Experiment
Assuming that the `ibfm.py` file is in the python path, the module may be loaded in the normal manner:
```python
import ibfm
Additional .ibfm files may be imported using the load method:
ibfm.load("myThings.ibfm")
```
An experiment on a model described in an imported .ibfm file may be created and run with the default settings by:
```python
ex = ibfm.Experiment("myModel")
ex.run()
```

## Program Structure
An experiment object is created with a single model. A model has multiple functions and flows. A function may have multiple modes and conditions, and has a current mode. A mode may have multiple applied behaviors. A condition has a single test behavior and an optional delay. A flow has two variables, an effort and a rate. Efforts and rates can be a qualitative state: zero, low, nominal, high, or highest.

## .ibfm Files
All models, functions, flows, modes, and conditions are defined in text files with the `.ibfm` extension. Definitions are begun by using the keyword corresponding to the desired object, followed by the desired name of the object. Object names may follow standard variable naming conventions. Alphanumeric characters and underscores are permitted. Any following block of indented lines describes the object in detail.

## Models
A simple functional model is defined as follows:
```
model Simple_System 
    function f1 ImportElectricalEnergy
    function f2 ExportElectricalEnergy
    flow f1 f2 Electrical
```
The first line contains the keyword `model` to let the program know that a model is being defined, followed by the intended model name. The indented lines indicate all of the functions and flows included in the functional model. Each line describing a function begins with the keyword `function`, followed by a unique within-model identifier for that particular function, followed by the name of the type of function. Each line describing a flow begins with the keyword `flow`, followed by the identifiers for the source and drain functions that the flow connects, followed by the name of the type of flow. All flows required by each function must be connected for the model to load properly.
Creating an experiment with this model would be accomplished with the following line:
```python
ex = ibfm.Experiment("Simple_System")
```

## Functions
The included function for actuating electrical energy is as follows: 
```
function ActuateElectricalEnergy
    mode 1 Operational ClosedCircuit
    mode 2 Operational OpenCircuit default
    mode 3 Failed ClosedCircuit
    mode 4 Failed OpenCircuit
    mode 5 Failed ShortCircuit
    condition NonZeroSignal 2 to 1
    condition ZeroSignal 1 to 2
    condition HighestCurrent 1 3 to 4 delay 1
    condition NonZeroVoltage 5 to 4 delay 1
```
Once again, the first line contains the keyword `function`, followed by the desired name of the function. The indented lines contain all of the modes and conditions of the function. Each line describing a mode begins with the keyword `mode`, followed by a unique within-function alphanumeric identifier, followed by the function health associated with the mode, followed by the name of the mode.  Available mode health states are `Operational`, `Degraded`, and `Failed`. Each line describing a condition begins with the key word `condition`, followed by the name of the condition, followed by the identifiers of each mode during which the condition should be tested, followed by the keyword `to`, followed by the mode to which the function should switch upon meeting the condition. This may be followed by an optional keyword `delay`, followed by a unit-less amount of time signifying how long the function should wait upon meeting the condition before switching to the destination mode.

## Flows
Flows are defined in a single line like this:
```
flow ChemicalEnergy Energy
```
The definition always begins with the keyword `flow`, followed by the desired name of the flow, followed by the name of its parent flow type. The top level flows are `Material`, `Energy`, and `Signal`. All other flows derive from them. 

## Modes
Mode definitions are more complicated, as  all of the mode’s behaviors must be explicitly described. A simple mode definition example is the closed-circuit mode:
```
mode ClosedCircuit
    Electrical output effort = Electrical input effort
    Electrical input rate = Electrical output rate
```
As with the other objects, the first line consists of the appropriate keyword, in this case `mode`, followed by the desired name of the mode. Each indented line consists of a single assignment statement. The expression to the left of the assignment operator `=` is evaluated to determine the flow variable(s) being assigned to. The expression to the right of the assignment operator is evaluated to determine the state(s) to assign to the flow variable(s). Every flow in the statement must be referred to using three words: the flow type name, its direction, either `input or output`, and its variable, either `effort` or `flow`. 

More complex behaviors may be defined by using operators. A single unary operator is used in the definition of the open-circuit mode:
```
mode OpenCircuit
    optional Electrical output effort = Zero
    optional Electrical input rate = Zero
```
In this case, each assignment uses the `optional` operator. This causes the program to ignore a behavior when the function is not connected to an instance of each of the flows referred to in the statement. For instance, the function `ImportElectricalEnergy` uses the `OpenCircuit` mode, but it does not have an `Electrical` input flow, only an `Electrical` output flow. The program will produce an error if a mode refers to a flow not connected to a function when the `optional` keyword is not the first word in an assignment.

Also, this mode definition makes use of a constant state. Available states are `Zero`, `Low`, `Nominal`, `High`, and `Highest`.

The definition of the drifting low voltage sensing mode uses two unary operators:
```
mode DriftingLowVoltageSensing
    import ClosedCircuit
    Signal output effort = Electrical input effort --
```
The first one, the keyword ```import```, copies all of the statements from the definition of the mode directly following the keyword. In this case, the two statements from the `ClosedCircuit` mode are copied into the `DriftingLowVoltageSensing` mode. The second one, the decrement operator `--`, decreases the value of the state by one qualitative level. A full list of the operators and an explanation of the order of operations are given after the next section.

## Conditions
Condition definitions are similar to mode definitions. They name the condition being defined, and explicitly describe the behavior, but they only include a single behavior statement. Rather than being an assignment, the statement is a logical test. For example, the condition to test for a function being exposed to high voltage is:
```
condition HighVoltage
    Electrical input effort > Nominal
```
Logical operators may be combined to form more complex tests. All binary operators are evaluated from left to right, so parentheses may be required.

## Order of operations 
1. Special operators that must be used at the beginning of a statement:  
  `import` Use behavior statements from another mode definition.  
  `optional` Ignore behavior statement if flows are not available.
2. Parentheses `()` These take precedence over unary and binary operators. They must be used in matching pairs.
3. Binary operators evaluated from left to right. May be placed to left or right of operand:  
  `,` Combine flows/states into a single list  
  `*` Multiply states  
  `==` Test for equality  
  `!=` Test for inequality  
  `>=` Test for greater than or equal to  
  `<=` Test for less than or equal to  
  `>` Test for greater than  
  `<` Test for less than  
  `and` Logical and  
  `or` Logical or  
4. Unary operators evaluated from left to right after binary operators:  
  `effort` Switch the current variable of the flow to its effort.  
  `rate` Switch the current variable of the flow to its rate.  
  `max` Find the maximum value of the current variable of a set of flows, and return all of the flows with that value.  
  `min` Find the minimum value of the current variable of a set of flows, and return all of the flows with that value.  
  `++` Increase the value of the state by one qualitative level. Stops at Highest.  
  `--` Decrease the value of the state by one qualitative level. Stops at Zero.  
  `invert` Return the pseudo inverse of the state. Zero -> Highest, Low -> High, Nominal -> Nominal, High/Highest -> Low  
  `any` Logical any  
  `all` Logical all  
