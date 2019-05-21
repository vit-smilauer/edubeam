"""
Test of the grid solution using example 1 from http://www.ce.memphis.edu/7117/notes/presentations/chapter_05b.pdf
"""

import sys
sys.path.append('..')
import ebfem

solver = ebfem.LinearStaticSolver()
domain = ebfem.Domain(type='grid2d')
session = ebfem.Session(domain,solver)

material = ebfem.Material(label='material',e=206842718400,alpha=12e-6,d=2400,g=82737087360)
domain.addMaterial(material)

print domain.materials

cs = ebfem.CrossSection(label='cs',a=0.35,iy=0.0001664925704,h=0.7,j=0.00004578545686)
domain.addCrossSect(cs)

loadCase = ebfem.LoadCase(label = "lc1")
domain.addLoadCase(loadCase)


n1 = domain.addNode(label='n1',coords=(6.096,3.048,0.),bcs={'z':False,'X':False,'Y':False})
n2 = domain.addNode(label='n2',coords=(0.,6.096,0.),bcs={'z':True,'X':True,'Y':True})
n3 = domain.addNode(label='n3',coords=(0.,0.,0.),bcs={'z':True,'X':True,'Y':True})
n4 = domain.addNode(label='n4',coords=(6.096,0.,0.),bcs={'z':True,'X':True,'Y':True})

e1 = ebfem.BeamGrid2d(label='e1',nodes=[n1,n2],mat=material,cs=cs,domain=domain)
e2 = ebfem.BeamGrid2d(label='e2',nodes=[n1,n3],mat=material,cs=cs,domain=domain)
e3 = ebfem.BeamGrid2d(label='e3',nodes=[n1,n4],mat=material,cs=cs,domain=domain)

l1 = domain.addNodalLoad(label='F1',where=n1,value={'fz':444.82216e3,'mx':0,'my':0},loadCase=loadCase)

solver.solve()

print 'solution: ',solver.r['lc1'][0:3]
print 'should be:',[2.83*0.0254,0.0295,-0.0169]
