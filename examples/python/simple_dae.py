# -*- coding: utf-8 -*-
from numpy import *
import numpy as NP
import matplotlib.pyplot as plt

# CasADi
from casadi import *

# Variables
t = SX("t")
x = SX("x")
l = SX("l")
z = SX("z")
u = SX("u")

# Differential equation
f = 3 * [0]
f[0] = -x + 0.5*x*x + u + 0.5*z
f[1] =  x*x + 3.0*u*u
f[2] =  z + exp(z) - 1.0 + x

# The right hand side of the ACADO functions
acado_in = ACADO_FCN_NUM_IN * [[]]
acado_in[ACADO_FCN_T] = [t]     # Time
acado_in[ACADO_FCN_XD] = [x,l]  # Differential states
acado_in[ACADO_FCN_XA] = [z]    # Algebraic state
acado_in[ACADO_FCN_U] = [u]     # Control
acado_in[ACADO_FCN_P] = []      # Parameter

# The DAE function
ffcn = SXFunction(acado_in,[f])
ffcn.setOption("ad_order",1)

## Objective function
mfcn = SXFunction(acado_in,[[l]])
mfcn.setOption("ad_order",1)

# Create ACADO solver
ocp_solver = AcadoInterface(ffcn,mfcn)

# Set options
t0 = 0.0
tf = 5.0
ocp_solver.setOption("start_time",t0)
ocp_solver.setOption("final_time",tf)

num_nodes = 20
ocp_solver.setOption("number_of_shooting_nodes",num_nodes)
#ocp_solver.setOption("max_num_iterations",30)
#ocp_solver.setOption("max_num_integrator_steps",10000)
#ocp_solver.setOption("dynamic_sensitivity","forward_sensitivities")
ocp_solver.setOption("kkt_tolerance",1e-5)
#ocp_solver.setOption("absolute_tolerance",1e-4)
#ocp_solver.setOption("integrator_tolerance",1e-8)
#ocp_solver.setOption("auto_init",True)
#ocp_solver.setOption("relaxation_parameter",1.5)

# Initialize
ocp_solver.init()

# Pass bounds
lbx0 = [1.0, 0.0, -NP.inf]
ubx0 = [1.0, 0.0, NP.inf]
ocp_solver.setInput(lbx0,ACADO_LBX0)
ocp_solver.setInput(ubx0,ACADO_UBX0)

# Solve
ocp_solver.solve()

# Time grid
t_opt = NP.linspace(t0,tf,num_nodes+1)

# Plot optimal state trajectory
x_opt = ocp_solver.getOutput(ACADO_X_OPT)
x_opt = array(x_opt) # create numpy array
x_opt = x_opt.reshape(num_nodes+1, 3)
plt.figure(1)
plt.clf()
plt.subplot(211)
plt.plot(t_opt,x_opt[:,0])
plt.title("DIFFERENTIAL STATE  x")

plt.subplot(212)
plt.plot(t_opt,x_opt[:,2])
plt.title("ALGEBRAIC STATE  z")

# Plot optimal control
u_opt = ocp_solver.getOutput(ACADO_U_OPT)
plt.figure(2)
plt.clf()
plt.plot(t_opt,u_opt)
plt.title("CONTROL u")

plt.show()


# State derivative
xdot = SX("xdot")
ldot = SX("ldot")

# The residual of the IDAS dae
dae_in = DAE_NUM_IN * [[]]
dae_in[DAE_T] = [t]     # Time
dae_in[DAE_Y] = [x,l]   # Differential states
dae_in[DAE_YDOT] = [xdot,ldot]   # Differential states
dae_in[DAE_Z] = [z]     # Algebraic state
dae_in[DAE_P] = [u]     # Control

# The DAE residual
dae_res = list(f)
dae_res[0] -= xdot
dae_res[1] -= ldot

# To make it work with a direct solver
#dae_res[2] -= 0.43*exp(z)

# The DAE residual function
dae = SXFunction(dae_in,[dae_res])
dae.setOption("ad_order",1)

# Create an integrator
integrator = IdasIntegrator(dae)

# Set options
integrator.setOption("abstol",1e-6)
integrator.setOption("reltol",1e-6)
#integrator.setOption("exact_jacobian",True)
integrator.setOption("stop_at_end",True)
#integrator.setOption("suppress_algebraic",True)
#integrator.setOption("linear_solver","dense")
integrator.setOption("linear_solver","iterative")

# Initialize the integrator
integrator.init()

# Initial state
xi = (1.0,0.0)

# Simulated trajectory
x_opt2 = array((num_nodes+1)*[xi])

# Loop over the time points
for i in range(num_nodes):
  # Set initial time
  ti = t_opt[i]
  integrator.setInput(ti,INTEGRATOR_T0)
  
  # Set stop time
  ts = t_opt[i+1]
  integrator.setInput(ts,INTEGRATOR_TF)

  # Set the control
  ui = u_opt[i]
  integrator.setInput(ui,INTEGRATOR_P)

  # Pass the state
  integrator.setInput(xi,INTEGRATOR_X0)
  
  # Integrate
  integrator.evaluate()
  
  # Get the state
  xi = integrator.getOutput(INTEGRATOR_XF)
  x_opt2[i+1] = xi

plt.figure(3)
plt.clf()
plt.subplot(121)
plt.plot(t_opt,x_opt[:,0])
plt.title("ACADO x")

plt.plot(t_opt,x_opt[:,1])
plt.title("ACADO l")

plt.subplot(122)
plt.plot(t_opt,x_opt2[:,0])
plt.title("CASADI x")

plt.plot(t_opt,x_opt2[:,1])
plt.title("CASADI l")


