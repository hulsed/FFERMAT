'''This is an example of how to represent a functional model and
then experiment on it using IBFM

'''

import ibfm

if __name__ == '__main__':

  eps = ibfm.Experiment('eps_small')
  #Run with 2 then 3 simultaneous faults
  eps.run(2)
  #eps.run(3)
  eps.exportScenariosAndResults('eps_old.pickle')
