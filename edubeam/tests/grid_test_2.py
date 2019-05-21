"""
Test of the grid solution WIH ELEMENT LOADS using example 3 from https://mech.fsv.cvut.cz/homeworks/student/SM3-J2-1/10_Rosty.pdf
"""

import sys
sys.path.append('..')
import ebfem

solver = ebfem.LinearStaticSolver()
domain = ebfem.Domain(type='grid2d')
session = ebfem.Session(domain,solver)

material = ebfem.Material(label='material',e=20.e9,alpha=12e-6,d=2400,g=8.333e9)
domain.addMaterial(material)

cs = ebfem.CrossSection(label='cs',a=0.35,iy=1.728e-4,h=0.7,j=1.747e-4) # includeing torisonal stiffness
cs = ebfem.CrossSection(label='cs',a=0.35,iy=1.728e-4,h=0.7,j=1e-9)     # neglecting torsional stiffness (as computed in original example)
domain.addCrossSect(cs)

loadCase = ebfem.LoadCase(label = "lc1")
domain.addLoadCase(loadCase)
domain.activeLoadCase = loadCase

n1 = domain.addNode(label='n1',coords=(0.,0.,0.),bcs={'z':True,'X':True,'Y':True})
n2 = domain.addNode(label='n2',coords=(6.,0.,0.),bcs={'z':True,'X':False,'Y':False})
n3 = domain.addNode(label='n3',coords=(3.,0.,0.),bcs={'z':False,'X':False,'Y':False})
n4 = domain.addNode(label='n4',coords=(3.,-4.,0.),bcs={'z':True,'X':True,'Y':True})

e1 = ebfem.BeamGrid2d(label='e1',nodes=[n1,n3],mat=material,cs=cs,domain=domain)
e2 = ebfem.BeamGrid2d(label='e2',nodes=[n3,n2],mat=material,cs=cs,domain=domain)
e3 = ebfem.BeamGrid2d(label='e3',nodes=[n3,n4],mat=material,cs=cs,domain=domain)

l1 = domain.addElementLoad(label='f1',where=e3,value={'magnitude':5000,'dir':'Z','perX':False},loadCase=loadCase)

solver.solve()

print 'solution: ',solver.r['lc1'][0:3]
f1,r1 = e1.computeEndValues(solver.r['lc1']) 
f2,r2 = e2.computeEndValues(solver.r['lc1']) 
f3,r3 = e3.computeEndValues(solver.r['lc1']) 
print
print 'ac_My: {:02e} (should be +7.72e3)'.format(f1[2])
print 'ac_Mx: {:02e} (should be 0)'.format(f1[1])
print 'ac_Fz: {:02e} (should be -4.72e3)'.format(f1[0])
print 'ca_My: {:02e} (should be +6.44e3)'.format(f1[5])
print 'ca_Mx: {:02e} (should be 0)'.format(f1[4])
print 'ca_Fz: {:02e} (should be +4.72e3)'.format(f1[3])
#
print
print 'cb_My: {:02e} (should be -6.44e3)'.format(f2[2])
print 'cb_Mx: {:02e} (should be 0)'.format(f2[1])
print 'cb_Fz: {:02e} (should be +2.14e3)'.format(f2[0])
print 'bc_My: {:02e} (should be 0)'.format(f2[5])
print 'bc_Mx: {:02e} (should be 0)'.format(f2[4])
print 'bc_Fz: {:02e} (should be -2.14e3)'.format(f2[3])
#
print
print 'cd_My: {:02e} (should be 0)'.format(f3[2])
print 'cd_Mx: {:02e} (should be 0)'.format(f3[1])
print 'cd_Fz: {:02e} (should be -6.87e3)'.format(f3[0])
print 'dc_My: {:02e} (should be -12.52e3)'.format(f3[5])
print 'dc_Mx: {:02e} (should be 0)'.format(f3[4])
print 'dc_Fz: {:02e} (should be +13.13e3)'.format(f3[3])
