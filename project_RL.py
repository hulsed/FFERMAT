#ROB 537
#Project
#RL algorithm (action-value learner) for use with our project

import numpy
import ibfmOpt
import ibfm
import importlib

#RL knobs
num_steps=25

#softmax selection knobs
tau=1

#select which signal type for which you are optimizing the control
signal=1

if signal == 1:
elif signal == 2:
	policy_action_1=[1,1,3]
	policy_action_2=[1,2,3]
	policy_action_3=[1,3,3]
elif signal ==3:
	policy_action_1=[1,2,1]
	policy_action_2=[1,2,2]
	policy_action_3=[1,2,3]

#actions
    importlib.reload(ibfm)
    #change to mode 1
    policy=[2,2,3]
    ibfmOpt.changeController(policy)
    exp1= ibfm.Experiment('simple_controller')
    exp1.run(1)
    scenscore,reward=ibfmOpt.score(exp1)
    return reward

    importlib.reload(ibfm)
    #change to mode 2
    policy=[1,2,3]
    ibfmOpt.changeController(policy)
    exp2= ibfm.Experiment('simple_controller')
    exp2.run(1)
    scenscore,reward=ibfmOpt.score(exp2)
    return reward

    importlib.reload(ibfm)
    #change to mode 3
    policy=[3,2,3]
    ibfmOpt.changeController(policy)
    exp3= ibfm.Experiment('simple_controller')
    exp3.run(1)
    scenscore,reward=ibfmOpt.score(exp3)
    return reward

#initial V values
value_action_1=[numpy.random.random(1)]
value_action_2=[numpy.random.random(1)]
value_action_3=[numpy.random.random(1)]

#counts for each action
count_action1=0
count_action2=0
count_action3=0

#initialize probability vector
p=[0,0,0]

t=0
while t<num_steps:

	#select action via softmax
	values=[value_action_1[-1],value_action_2[-1],value_action_3[-1]]
	sum_exp_values=0
	for i in range(0,3):
		sum_exp_values+=numpy.exp(values[i]/tau)
	for i in range(0,3):
		p[i]=numpy.exp(values[i]/tau)/sum_exp_values
	random_number=numpy.random.random(1)
	for i in range(0,3):
		random_number-=p[i]
		if random_number<=0:
			action_taken=i+1
			break

	if action_taken==1:
		#action 1
		count_action1+=1
		if count_action1>1:
			new_value_action_1=value_action_1[(count_action1-1)-1]+(1/float(count_action1))*(reward_action_1-value_action_1[(count_action1-1)-1])
			value_action_1.append(new_value_action_1)
	elif action_taken==2:
		#action 2
		count_action2+=1
		if count_action2>1:
			new_value_action_2=value_action_2[(count_action2-1)-1]+(1/float(count_action2))*(reward_action_2-value_action_2[(count_action2-1)-1])
			value_action_2.append(new_value_action_2)
	elif action_taken==3:
		#action 3
		count_action3+=1
		if count_action3>1:
			new_value_action_3=value_action_3[(count_action3-1)-1]+(1/float(count_action3))*(reward_action_3-value_action_3[(count_action3-1)-1])
			value_action_3.append(new_value_action_3)
	
	t=t+1
	print(action_taken)