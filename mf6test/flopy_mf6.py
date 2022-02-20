import os
import flopy
import matplotlib.pyplot as plt

exe_name="C:\\thepathtoextractedmodflowfolder\\mf6.2.2\\bin\\mf6.exe" # windows
#exe_name="mf6" # or the program, linux

ws = './mymodel'
name = 'mymodel'

sim  = flopy.mf6.MFSimulation(sim_name=name, sim_ws=ws, exe_name=exe_name)
tdis = flopy.mf6.ModflowTdis(sim)
ims  = flopy.mf6.ModflowIms(sim)
gwf  = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
dis  = flopy.mf6.ModflowGwfdis(gwf, nrow=10, ncol=10)
ic   = flopy.mf6.ModflowGwfic(gwf)
npf  = flopy.mf6.ModflowGwfnpf(gwf, save_specific_discharge=True)
chd  = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=[[(0, 0, 0), 1.],
                                                       [(0, 9, 9), 0.]])
path        = os.getcwd()
route       = os.path.join(path, name)
model_name  = os.path.join(route, name)
budget_file = model_name + '.bud'
head_file   = model_name + '.hds'
oc          = flopy.mf6.ModflowGwfoc(gwf,
                            budget_filerecord=budget_file,
                            head_filerecord=head_file,
                            saverecord=[('HEAD', 'ALL'), ('BUDGET', 'ALL')])
sim.write_simulation()
sim.run_simulation()

head  = flopy.utils.HeadFile(head_file).get_data()
bud   = flopy.utils.CellBudgetFile(budget_file)
spdis = bud.get_data(text='DATA-SPDIS')[0]
pmv   = flopy.plot.PlotMapView(gwf)
pmv.plot_array(head)
pmv.plot_grid(colors='white')
pmv.contour_array(head, levels=[.2, .4, .6, .8], linewidths=3.)
pmv.plot_specific_discharge(spdis, color='white')

plt.show()
