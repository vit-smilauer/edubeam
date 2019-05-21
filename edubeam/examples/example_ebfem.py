#!/usr/bin/python
############################################################
#
# This script demonstrate how to use EduBeam (specifically
# EBFEM module) with python. Run this example with command
# [python] example_ebgem.py
#
############################################################
import sys
sys.path.append('..')
import ebfem

print '__________________________________________________'
print
print '      EduBeam - EBFEM python module example'
print '             (C) 2012  EduBeam team'
print '__________________________________________________'
print

# solver, domain, session
solver = ebfem.LinearStaticSolver()
domain = ebfem.Domain()
session = ebfem.Session(domain,solver)

# materials
conc = ebfem.Material(label='conc',e=30e9,alpha=12e-6,d=2400) # materials (as well as all other domain menmers) can be created either with ebfem.Something (specifically ebfem.Material) ...
domain.addMaterial(conc)                                      # ... and then added to domain by addSomathing (specifically addMaterial) ...
steel = domain.addMaterial(label='steel',e=210e9,alpha=12e-6,d=7600)  # ... or you can directly use addSomathing (specifically addMaterial) method
print domain.materials

# cross section
cs1 = ebfem.CrossSection(label='cs1',a=2850e-6,iy=19.4e-6,h=.2) # IPE200
domain.addCrossSect(cs1)
cs2 = domain.crossSects['DefaultCS'] # the cross sections (as well as all other domain members) are accesible by their labels

# load cases
lc1 = ebfem.LoadCase(label='lc1')
domain.addLoadCase(lc1)
lc2 = domain.addLoadCase(label='lc22222')
lc3 = ebfem.LoadCase(label='lc3',domain=domain) # note 'domain' keyword, no domain.addLoadCase needed afterwards

# nodes
n1 = domain.addNode(label='n1',coords=(0.,0.,0.),bcs={'x':True,'z':True,'Y':False})
n2 = ebfem.Node(label='n2',coords=(0.,0.,-1.),domain=domain) # 'domain' keyword again..
n3 = ebfem.Node(label='nnnnn3',coords=(3.,0.,-2.),bcs={'x':True,'z':True,'Y':True})
domain.addNode(n3)

# elements
e1 = ebfem.Beam2d(label='e1',nodes=['n1',n2],mat=conc,cs='DefaultCS',domain=domain) # no need of domain.addElement if domain is specified in Beam2d initialization
e2 = domain.addElement(label='e2',nodes=['n2',n3],mat='steel',cs=cs1)

# loads
l1 = domain.addNodalLoad(label='F1',where=n2,value={'fx':20,'fz':0,'my':0},loadCase=lc1)
l2 = domain.addElementLoad(label='L1',where=e2,value={'fx':0,'fz':10,'dTc':0,'dTg':0},loadCase=lc2)
p3 = domain.addPrescribedDspl(label='P1',where=n1,value={'x':0.,'z':0.01,'Y':0.},loadCase=lc3)

# solution
solver.solve()

# save session
session.save('test_a.xml')

# results
# TODO

print
print 'End of example script, good bye'
print

