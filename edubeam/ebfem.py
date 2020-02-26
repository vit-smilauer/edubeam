# -*- coding: utf-8 -*

#
#          EduBeam is an education project to develop a free structural
#                   analysis code for educational purposes.
#
#                             (c) 2011 Borek Patzak 
#
#       EduBeam is free software; you can redistribute it and/or modify it 
#         under the terms of the GNU General Public License as published 
#        by the Free Software Foundation; either version 2 of the License, 
#                        or (at your option) any later version.
#
# EduBeam is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details. You should have received a copy of 
# the GNU General Public License along with File Hunter; if not, write to 
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

##################################################################
#
# ebfem.py file
# defines EduBeam computational part
#
##################################################################

"""
EduBeam module providing computational part of the program
"""


from ebinit import *

try:
    from numpy import *
except ImportError:
    logger.fatal( langStr('Required Numerical Python (numpy) package not present', 'Potřebný balík Numerical Python (numpy) nenalezen') )
    raise ImportError


def keyExists(instances, key):
    """Checks whether a key exists in a dictionary or in a list of dictionaries
    :param instances: list of dictionary entries to search
    """
    if isinstance(instances, dict):
        instances = (instances,)
    for dictionary in instances:
        for label in dictionary.iterkeys():
            if label == key:
                return 1
    return 0
        


def giveNewLabel(instances, flag=''):
    """gives new nodal or element load label
    :param instances: list of dictionary entries to search
    :rtype: str
    """
    if flag == 'newNum':
        if len(instances) == 0:
            return str('1')
        else:
            #find maximum number at the end of string from all instances
            maxNum = 0
            if isinstance(instances, dict):
                instances = (instances,)
            for dictionary in instances:
                for label in dictionary.iterkeys():
                    m = re.match(r".*?([0-9]+)", label) # match the longest number at the end
                    if m:
                        n = m.group(1)
                        if n.isdigit() and int(n) > maxNum:
                            maxNum = int(n)
            return str(maxNum+1)
        return str('')
    
def giveLabel(dictNew, flag=''):
    """Returns labels in dictionaries
    :param superClass required for load labels, which are stored under loadCases
    """
    if len(dictNew) == 0:
        if flag == 'newNum':
            return str(1)
        else:
            return str('')
    if flag == 'first':
        return list(dictNew)[0]
    if flag == 'last':
            #dictionary items are not in the same order as inserted
            #return max(dictNew.keys())
        return sorted(dictNew.keys(), key=lambda n: natural_key(n))[-1]
    if flag == 'newNum':
        maxNum = 0
        for n,value in dictNew.items():
            if n.isdigit() and int(n) > maxNum:
                maxNum = int(n)
        return str(maxNum+1)
    logger.error( langStr('Missing argument', 'Chybí argument') )

class BBox:
   """Representation of bounding box"""
   def __init__(self, p1, p2):
      self.v1 = p1
      self.v2 = p2
   def isInside(self, p):
      if ((p[0]>=self.v1[0]) and (p[0]<=self.v2[0]) and
          (p[2]>=self.v1[2]) and (p[2]<=self.v2[2])):
          return True
      return False







class Material:
    """A class representing linear elastic material
    
    :param str label: string label of receiver
    :param float|int|str e: Young's modulus of receiver [Pa]
    :param float|int|str g: Shear modulus of receiver [Pa]
    :param float|int|str alpha: thermal dillatation coefficient [K-1]
    :param float|int|str d: mass density of receiver [kg/m3]
    :param Domain domain: new domain of receiver
    """

    label = None
    """*(str)* string label"""
    e = None
    """*(float)* Young's modulus [Pa]"""
    g = None
    """*(float)* Shear modulus [Pa]"""
    alpha = None
    """*(float)* thermal dillatation coefficient [K-1]"""
    d = None
    """*(float)* mass density [kg/m3]"""
    domain = None
    """*(Domain)* domain which receiver belongs to"""

    def __init__(self, label='material', e=1., g=1.e+10, alpha=1., d=1., domain=None):
        initFail = self.change(label=label, e=e, g=g, alpha=alpha, d=d, domain=domain, fromInit=True)
        if initFail:
            raise EduBeamError
            print('Material.__init__')

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label, e=self.e, g=self.g, alpha=self.alpha, d=self.d, domain=self.domain.label if self.domain else '')

    def change(self, label=None, e=None, g=None, alpha=None, d=None, domain=None, fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another material with this label already exists, returns 1
        :param float|int|str e: new Young's modulus of receiver [Pa]. > 0.
        :param float|int|str g: new Shear modulus of receiver [Pa]. > 0.
        :param float|int|str alpha: new thermal dillatation coefficient of receiver [K-1]. > 0.
        :param float|int|str d: new mass density of receiver [kg/m3]. > 0.
        :param Domain domain: new domain of receiver
        :rtype: bool
        """
        label = label if label else self.label
        domain = domain if domain and isinstance(domain,Domain) else self.domain
        if label!=self.label or domain is not self.domain:
            if domain:
                if label in domain.materials:
                    logger.error( langStr('Material %s already exists in the materials %s', 'Materiál %s již existuje v materiálech %s') % ( label, sorted(domain.materials.keys()) ) )
                    return 1
        e = float(e) if e is not None else self.e
        if e <= 0.0:
            logger.warning( langStr('Young\'s modulus of Material %s nonpositive', 'Youngův modul pružnosti materiálu %s nekladný') %self.label )
            return 1
        g = float(g) if g is not None else self.g
        if g <= 0.0:
            logger.warning( langStr('Shear modulus of Material %s nonpositive', 'Smykový modul pružnosti materiálu %s nekladný') %self.label )
            return 1
        alpha = float(alpha) if alpha is not None else self.alpha
        if alpha <= 0.0:
            logger.warning( langStr('Thermal dilatation coefficient of Material %s nonpositive', 'Teplotní roztažnost materiálu %s nekladná') %self.label )
            return 1
        d = float(d) if d is not None else self.d
        if d <= 0.0:
            logger.warning( langStr('Mass density modulus of Material %s nonpositive', 'Objemová tíha materiálu %s nekladná') %self.label )
            return 1
        self.e = e
        self.g = g
        self.alpha = alpha
        self.d = d
        if label!=self.label or domain is not self.domain:
            if self.domain:
                self.domain.materials.pop(self.label,None)
            elif domain:
                domain.materials[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Material %s renamed to %s', 'Materiál %s přejmenován na %s') % (self.label, label) )
            domain.materials[label] = self
        self.label = label
        self.domain = domain
        return 0

    def __str__(self):
        return self.label


class CrossSection:
    """A class representing beam cross section
    
    :param str label: string label of receiver
    :param float|int|str a: cross section area of receiver [m2]. > 0.0
    :param float|int|str iy: area moment of inertia (second moment of area) with respect to y axis [m4]. > 0.0
    :param float|int|str iz: area moment of inertia (second moment of area) with respect to z axis [m4]. > 0.0
    :param float|int|str dyz: product moment of area with respect to yz axes [m4]
    :param float|int|str h: height of receiver [m]
    :param float|int|str k: Timoshenko's shear coefficient [-]
    :param Domain domain: new domain of receiver
    """

    label = None
    """*(str)* String label"""
    domain = None
    """*(Domain)* Domain which receiver belongs to"""
    a = None
    """*(float)* area [m2]"""
    iy = None
    """*(float)* area moment of inertia (second moment of area) with respect to y axis [m4]"""
    iz = None
    """*(float)* area moment of inertia (second moment of area) with respect to z axis [m4]"""
    dyz = None
    """*(float)* product moment of area with respect to yz axes [m4]"""
    h = None
    """*(float)* height [m]"""
    k = None
    """*(float)* Timoshenko\'s shear coefficient [m]"""
    j = None
    """*(float)* torsional stiffness moment [m4]"""

    def __init__(self, label='crossection', a=1., iy=1., iz=1., dyz=0., h=1., k=1., j=1., domain=None):
        self.domain = domain
        initFail = self.change(label=label, a=a, iy=iy, iz=iz, dyz=dyz, h=h, k=k, j=j, domain=domain, fromInit=True)
        if initFail:
            raise EduBeamError
            print('CrossSection.__init__')

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label,a=self.a,iy=self.iy,iz=self.iz,dyz=self.dyz,h=self.h, k=self.k, j=self.j, domain=self.domain.label if self.domain else '')

    def change(self,label=None,a=None,iy=None,iz=None,dyz=None,h=None,k=None,j=None,domain=None, fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another cross section with this label already exists, returns 1
        :param float|int|str a: new cross section area of receiver [m2]. > 0.0
        :param float|int|str iy: new second moment of area of receiver with respect to y axis [m4]. > 0.0
        :param float|int|str iz: new second moment of area of receiver with respect to z axis [m4]. > 0.0
        :param float|int|str dyz: new product moment of area of receiver with respect to yz axis [m4]
        :param float|int|str h: new height of receiver [m]
        :param float|int|str k: Timoshenko's shear coefficient [-]
        :param float|int|str j: torsional stiffness moment [m4]
        :param Domain domain: new domain of receiver
        :rtype: bool
        """
        label = label if label else self.label
        domain = domain if domain and isinstance(domain,Domain) else self.domain
        if label!=self.label or domain is not self.domain:
            if domain:
                if label in domain.crossSects:
                    logger.error( langStr('CrossSection %s already exists in the crossSects %s', 'Průřez %s již existuje v průřezech %s') % ( label, sorted(domain.crossSects.keys()) ) )
                    return 1
        a = float(a) if a is not None else self.a
        if a <= 0.0:
            logger.warning( langStr('Area of CrossSection %s nonpositive', 'plocha průřezu %s nekladná') % self.label )
            return 1
        iy = float(iy) if iy is not None else self.iy
        if iy <= 0.0:
            logger.warning( langStr('Moment of inertia y of CrossSection %s nonpositive', 'Moment setrvačnosti y průřezu %s nekladný') % self.label )
            return 1
        iz = float(iz) if iz is not None else self.iz
        if iz <= 0.0:
            logger.warning( langStr('Moment of inertia z of CrossSection %s nonpositive', 'Moment setrvačnosti z průřezu %s nekladný') % self.label )
            return 1
        dyz = float(dyz) if dyz is not None else self.dyz
        h = float(h) if h is not None else self.h
        if h <= 0.0:
            logger.warning( langStr('Height of CrossSection %s nonpositive', 'výška průřezu %s nekladná') % self.label )
            return 1
        k = float(k) if k is not None else self.k
        if k <= 0.0:
            logger.warning( langStr('Timoshenko\'s shear coefficient of CrossSection %s must be > 0', 'Timoshenkův smykový součinitel průřezu musí být > 0') % self.label )
            return 1
        j = float(j) if j is not None else self.j
        if j <= 0.0:
            logger.warning( langStr('Torsional stiffness moment of CrossSection %s must be > 0', 'Moment tuhosti v kroucení průřezu %s musí být > 0') % self.label )
            return 1
        self.a = a
        self.iy = iy
        self.iz = iz
        self.dyz = dyz
        self.h = h
        self.k = k
        self.j = j
        if label!=self.label or domain is not self.domain:
            if self.domain:
                self.domain.crossSects.pop(self.label,None)
            if domain:
                domain.crossSects[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('CrossSection %s renamed to %s', 'Průřez %s přejmenován na %s') % (self.label, label) )
        self.label = label
        self.domain = domain
        return 0

    def __str__(self):
        return self.label




class Node:
    """A class representing a FE node
    bcs and pDspl: x,y,z for displacement, X,Y,Z for rotations
    
    :param str label: string label of receiver
    :param [float,float,float] coords: coordinates of receiver [m]
    :param dict bcs: applied Dirrichlet's boundary conditions (supports).
    :param Domain domain: new domain of receiver
    """

    label = None
    """*(str)* string label"""
    domain = None
    """*(Domain)* domain which receiver belongs to"""
    coords = None
    """*([float,float,float])* coordinates [m]"""
    bcs = None
    """*({'x':bool,'z':bool,'Y':bool})* applied supports. 'x' = x displacement, 'z' = z displacement, 'Y' = y rotation"""

    def __init__(self, label='node', coords=[0.,0.,0.], bcs={'x':False,'z':False,'Y':False}, domain=None):
        self.domain = domain
        initFail = self.change(label=label,coords=coords,bcs=bcs,domain=domain, fromInit=True)
        if initFail:
            raise EduBeamError
            print('Node.__init__')
        self.loc = None

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label,coords=self.coords,bcs=self.bcs, domain=self.domain.label if self.domain else '')

    def change(self,label=None,coords=None,bcs=None,domain=None,fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another node with this label already exists, returns 1
        :param [float,float,float] coords: new coordinates of receiver [m]
        :param dict bcs: new applied Dirrichlet's boundary conditions (supports) of receiver.
        :param Domain domain: new domain of receiver
        :rtype: bool
        """
        label = label if label else self.label
        domain = domain if domain and isinstance(domain,Domain) else self.domain
        if label!=self.label or domain is not self.domain:
            if domain:
                if label in domain.nodes:
                    logger.error( langStr('Node %s already exists in the nodes %s', 'Uzel %s existuje v uzlech %s') % ( label, sorted(domain.nodes.keys()) ) )
                    return 1
        self.coords = [float(coord) for coord in coords]                     if coords is not None else self.coords if self.coords is not None else [0., 0., 0.]
        self.bcs    = dict( (key,bool(val)) for key,val in bcs.items() ) if bcs    is not None else self.bcs    if self.bcs    is not None else {'x':False,'z':False,'Y':False}
        if label!=self.label or domain is not self.domain:
            if self.domain:
                self.domain.nodes.pop(self.label,None)
            if domain:
                domain.nodes[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Node %s renamed to %s', 'Uzel %s přejmenován na %s') % (self.label, label) )
        self.label = label
        self.domain = domain
        return 0

    def giveDofName(self,dof):
        """Returns string name of passed dof
        
        :param int|str dof: degree of freedom to be named
        :rtype: str
        """
        if isinstance(dof,(str,unicode)):
            if dof=='x': return 'x'
            if dof=='y': return 'y'
            if dof=='z': return 'z'
            if dof=='X': return 'X'
            if dof=='Y': return 'Y'
            if dof=='Z': return 'Z'
            return None
        elif isinstance(dof,int):
            if dof==0: return 'x'
            if dof==1: return 'x'
            if dof==2: return 'z'
            if dof==3: return 'X'
            if dof==4: return 'Y'
            if dof==5: return 'Z'
            return None
        return None

    def hasPrescribedBcInDof(self,dof):
        """returns True if there is applied support in corresponding DOF
        
        :param int|str dof: degree of freedom if interest
        :rtype: bool
        """
        dof = self.giveDofName(dof)
        return self.bcs[dof]

    def giveBCs(self):
        """Returns tuple of bools ('x','z','Y') of BCs
        
        :rtype: (bool,bool,bool)
        """
        return (self.bcs['x'], self.bcs['z'], self.bcs['Y'])

    def hasAnyPrescribedBC(self):
        return self.bcs['x'] or self.bcs['z'] or self.bcs['Y']

    def __str__(self):
        return self.label


class Element:
    """A class representing Finite Element
    
    :param str label: string label of receiver
    :param [Node|str] nodes: nodes of receiver
    :param Material|str mat: material of receiver
    :param CrossSection|str cs: cross section of receiver
    :param Domain domain: new domain of receiver
    """

    label = None
    """*(str)* string label"""
    domain = None
    """*(Domain)* domain which receiver belongs to"""
    nodes = None
    """*([Node])* list of nodes of receiver"""
    mat = None
    """*(Material)* material"""
    cs = None
    """*(CrossSection)* cross section"""

    def __init__(self, label='element', nodes=None, mat=None, cs=None, domain=None):
        self.domain = domain
        initFail = self.change(label=label, nodes=nodes, mat=mat, cs=cs,domain=domain, fromInit=True)
        if initFail:
            raise EduBeamError
            print('Element.__init__')

    def giveNewNodes(self,nodes):
        """Returns list of Node instances if successful, None otherwise
        
        :param str|Node nodes: list of new nodes
        :rtype: [Node] | None
        """
        if not nodes:
            logger.error( langStr('No nodes specified','Žádné uzly nespecifikovány') )
            return None
        ret = []
        for node in nodes:
            if isinstance(node,Node):
                ret.append(node)
            elif isinstance(node,(str,unicode)):
                if not self.domain:
                    logger.error( langStr('No domain to get node by string label from ...','Žádná síť, z které by mohl být uzel získán na základě názvu ...') )
                    return None
                node = self.domain.nodes.get(node)
                if node:
                    ret.append(node)
                else:
                    logger.error( langStr('self.domain.nodes has no key %s','self.domain.nodes nemá položku') % node )
                    logger.error( langStr('Wrong nodes', 'Chybně zadané uzly') )
                    return None
            else:
                logger.error( langStr('Unsupported type of node: %s','Nepodporovaný typ uzlu: %s') % node )
                return None
        return ret

    def giveNewMat(self,mat):
        """Returns Material instances if successful, None otherwise
        
        :param str|Material mat: new material
        :rtype: Material | None
        """
        if not mat:
            logger.error( langStr('No matrial specified','Žádný materiál nespecifikován') )
            return None
        if isinstance(mat,Material):
            return mat
        if isinstance(mat,(str,unicode)):
            if not self.domain:
                logger.error( langStr('No domain to get material by string label from ...','Žádná síť, z které by mohl být materiál získán na základě názvu ...') )
                return None
            mat = self.domain.materials.get(mat)
            if mat:
                return mat
            logger.error( langStr('self.domain.materials has no key %s','self.domain.materials nemá položku %s') % mat )
            logger.error( langStr('Material not found in %s', 'Materiál nenalezen v %s') % (sorted(self.domain.materials.keys())) )
            return None
        logger.error( langStr('Unsupported type of material: %s','Nepodporovaný typ materiálu: %s') % mat )
        return None

    def giveNewCS(self,cs):
        """Returns CrossSection instances if successful, None otherwise
        
        :param str|CrossSection cs: new cross section
        :rtype: CrossSection | None
        """
        if not cs:
            logger.error( langStr('No cross section specified','Žádný průřez nespecifikován') )
            return None
        if isinstance(cs,CrossSection):
            return cs
        if isinstance(cs,(str,unicode)):
            if not self.domain:
                logger.error( langStr('No domain to get cross section by string label from ...','Žádná síť, z které by mohl být průřez získán na základě názvu ...') )
                return None
            cs = self.domain.crossSects.get(cs)
            if cs:
                return cs
            logger.error( langStr('self.domain.crossSects has no key %s','self.domain.crossSects nemá položku %s') % cs )
            logger.error( langStr('CrossSection not found in %s', 'Průřez nenalezen v %s') % (sorted(self.domain.crossSects.keys())) )
            return None
        logger.error( langStr('Unsupported type of cross section: %s','Nepodporovaný typ průřezu: %s') % cs )
        return None

    def checkNodes(self,nodes):
        pass

    def change(self,label=None,nodes=None,mat=None,cs=None,domain=None,fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another element with this label already exists, returns 1
        :param [Node|str] nodes: list of new nodes of receiver
        :param Material|str mat: new material of receiver
        :param CrossSection|str cs: new cross section of receiver
        :param Domain domain: new domain of receiver
        :rtype: bool
        """
        label = label if label else self.label
        domain = domain if domain and isinstance(domain,Domain) else self.domain
        if label!=self.label or domain is not self.domain:
            if domain:
                if label in self.domain.elements:
                    logger.error( langStr('Element with label %s already exists in the elements %s', 'Prvek se jménem %s již existuje v prvcích %s') % ( label, sorted(self.domain.elements.keys()) ) )
                    return 1
        nodes = self.giveNewNodes(nodes) if nodes else self.nodes
        if self.checkNodes(nodes):
            return 1
        mat = self.giveNewMat(mat) if mat else self.mat
        cs = self.giveNewCS(cs) if cs else self.cs
        if not nodes or not mat or not cs:
            return 1
        self.nodes = nodes
        self.mat = mat
        self.cs = cs
        if label!=self.label or domain is not self.domain:
            if self.domain:
                self.domain.elements.pop(self.label,None)
            if domain:
                domain.elements[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Element %s renamed to %s','Prvek %s přejmenován na %s') % (self.label, label) )
        self.label = label
        self.domain = domain
        return 0

    def giveLocationArray(self):
        """Return element code numbers"""
        loc = []
        for n in self.nodes:
            loc += n.loc
        return loc

    def __str__(self):
        return self.label

    def dict(self):
        """
        returns dictionary of attributes saved to xml file

        :rtype: dict
        """
        return dict(label=self.label, nodes=[n.label for n in self.nodes], mat=self.mat.label, cs=self.cs.label, domain=self.domain.label if self.domain else '')


class Beam2d(Element):
    """A class representing 2D beam Element
    
    :param str label: string label of receiver
    :param [Node|str] nodes: nodes of receiver
    :param Material|str mat: material of receiver
    :param CrossSection|str cs: cross section of receiver
    :param Domain domain: new domain of receiver
    :param [bool,bool] hinges: hinges possession of receiver
    """

    hinges = None
    """*([bool,bool])* hinges possession of receiver"""

    def __init__(self, label='beam2d', nodes=None, mat=None, cs=None, domain=None, hinges=[False,False]):
        Element.__init__(self, label=label, nodes=nodes, mat=mat, cs=cs, domain=domain)
        self.hinges = hinges
        # hinges = [bool,bool], hinges[0] express if beam is hinge conneted with nodes[0] or not, hinges[1] with nodes[1]

    def checkNodes(self,nodes):
        """Check nodes, returns 0 if ok, 1 otherwise
        """
        if nodes[0] is nodes[1]:
            logger.error( langStr('Coinciding nodes', 'Stejné uzly') )
            return 1
        return 0

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label,nodes=[n.label for n in self.nodes],mat=self.mat.label,cs=self.cs.label,hinges=self.hinges, domain=self.domain.label if self.domain else '')

    def computeDefl(self, rr=None, rl=None, nseg=20, fzloc=None, geom=None):
        """Computes nseg+1 values of local deflection, returns two lists of displacement values
        
        :rtype: [float],[float]
        """
        if not self.domain.session.solver.isSolved:
            raise EduBeamError
        if rl is None:
            rl = self.computeEndDspl(rr)
        l,dx,dz = geom if geom else self.computeGeom() 
        c = dx/l
        s = dz/l
        if fzloc is None:
            fzloc = 0.
            for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
                vxTmp, vzTmp = load.giveFxFzElemProjection(type=self.domain.type)
                fzloc += -s*vxTmp + c*vzTmp
        wret = [0. for i in range(nseg+1)]
        uret = [0. for i in range(nseg+1)]
        for i in range(nseg+1):
            xl = float(i)/float(nseg) #runs 0..1
            # components from end displacements
            wret[i] = (1.0-3.0*xl*xl+2.0*xl*xl*xl)*rl[1]+l*(-xl+2.0*xl*xl-xl*xl*xl)*rl[2]+(3.0*xl*xl-2.0*xl*xl*xl)*rl[4]+l*(xl*xl-xl*xl*xl)*rl[5]
            uret[i] = (1.-xl)*rl[0]+xl*rl[3]
            # components from distributed load
            wret[i] += fzloc*l*l*l*l * (xl*xl*xl*xl/24.-xl*xl*xl/12.+xl*xl/24.)/(self.mat.e*self.cs.iy)
            
            # components from a single force (deflection on a beam with clamped edges)
            for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
                if load.value['type'] == 'Force':#Force
                    Fxloc = c*load.value['Fx'] + s*load.value['Fz']
                    Fzloc = -s*load.value['Fx'] + c*load.value['Fz']
                    a = load.value['DistF']
                    b = l-a
                    Za=b/l*(a*(a-b)/l/l-1.)*Fzloc
                    Ma=a*b*b/l/l*Fzloc
                    EI = self.mat.e*self.cs.iy
                    EA = self.mat.e*self.cs.a
                    x = xl*l
                    if x<a:
                        uret[i] += b/l*Fxloc*x/EA
                    else:
                        uret[i] += ( b/l*Fxloc*a/EA - a/l*Fxloc*(x-a)/EA )
                    #Integration of beam curvature from known left reactions
                    wret[i] += (Za*x*x*x/6.+Ma*x*x/2. + ( Fzloc*(x-a)*(x-a)*(x-a)/6. if x>a else 0.))/EI
                #print Fzloc, Za, Ma, uret 

        return uret,wret

    def computeMoment(self, rr=None, F=None, nseg=20, fzloc=None, geom=None):
        """Computes >=nseg+1 values of local moment, returns list of distances and values M(x)"""
        if not self.domain.session.solver.isSolved:
            raise EduBeamError
        if F is None:
            F = self.computeEndForces(rr)
        l,dx,dz = geom if geom else self.computeGeom() 
        c = dx/l
        s = dz/l
        #Start with even distribution and add a position of a single force
        distances = linspace(0,l,nseg).tolist()
        if fzloc is None:
            fzloc = 0.
            for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
                vxTmp, vzTmp = load.giveFxFzElemProjection(type=self.domain.type)
                fzloc += -s*vxTmp + c*vzTmp
                if load.value['type'] == 'Force':#Force
                    distances.append(load.value['DistF'])
                    distances.sort()
        V0 = F[1]
        M0 = F[2]
                
        ret = []
        #Discontinuity where force applied
        for i in range(0, len(distances)):
            xl = distances[i]
            xl2 = xl*xl
            distances[i] = xl
            ret.append(0.5*fzloc*xl2 + V0*xl + M0)
            for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
                a = load.value['DistF']
                if load.value['type'] == 'Force' and xl>a:#Force
                    Fzloc = -s*load.value['Fx'] + c*load.value['Fz']
                    a = load.value['DistF']
                    b = l-a
                    ret[i] += Fzloc*(xl-a)
        #print self.label,distances
        return distances, ret

    def computeNormalForce(self, rr=None, F=None, nseg=20):
        """Computes >=nseg+1 values of local normal force, returns list of distances, values N(x) and where labels should be  plotted"""
        if not self.domain.session.solver.isSolved:
            raise EduBeamError
        if F is None:
            F = self.computeEndForces(rr)
        l,dx,dz = self.computeGeom() 
        c = dx/l
        s = dz/l
        fxloc = 0.
        #Start with even distribution and add a position of single forces
        distances = linspace(0,l,nseg).tolist()
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            vxTmp, vzTmp = load.giveFxFzElemProjection(type=self.domain.type)
            fxloc += c*vxTmp + s*vzTmp
            if load.value['type'] == 'Force':#Force
                distances.append(load.value['DistF'])
                distances.append(load.value['DistF']+0.001)
        distances.sort()
        #Array where to put numerical values
        labelMask = [0] * len(distances)
        labelMask[0] = 1
        labelMask[-1] = 1
        ret = []
        #Linear function
        for i in range(0, len(distances)):
            ret.append(-F[0]-fxloc*distances[i])
        #Discontinuity where force applied
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            if load.value['type'] == 'Force':#Force
                a=load.value['DistF']   
                Fxloc = c*load.value['Fx'] + s*load.value['Fz']
                for i in range(0, len(distances)):
                    if distances[i]==a:
                        labelMask[i] = 1
                        labelMask[i+1] = 1
                    if distances[i]>a:
                        ret[i] -= Fxloc
        #print self.label, distances,labelMask
        return distances, ret, labelMask
            

    def computeShearForce(self, rr=None, F=None, nseg=20):
        """Computes >=nseg+1 values of local shear force, returns list of distances, values V(x) and where labels should be  plotted"""
        
        if not self.domain.session.solver.isSolved:
            raise EduBeamError
        if F is None:
            F = self.computeEndForces(rr)
        l,dx,dz = self.computeGeom() 
        c = dx/l
        s = dz/l
        
        fzloc = 0.
        #Start with even distribution and add a position of single forces
        distances = linspace(0,l,nseg).tolist()
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            vxTmp, vzTmp = load.giveFxFzElemProjection(type=self.domain.type)
            fzloc += -s*vxTmp + c*vzTmp
            if load.value['type'] == 'Force':#Force
                distances.append(load.value['DistF'])
                distances.append(load.value['DistF']+0.001)
        distances.sort()
        #Array where to put numerical values
        labelMask = [0] * len(distances)
        labelMask[0] = 1
        labelMask[-1] = 1
        ret = []
        #Linear function
        for i in range(0, len(distances)):
            ret.append(-F[1]-fzloc*distances[i])
        #Discontinuity where force applied
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            if load.value['type'] == 'Force':#Force
                a=load.value['DistF']   
                Fzloc = -s*load.value['Fx'] + c*load.value['Fz']
                for i in range(0, len(distances)):
                    if distances[i]==a:
                        labelMask[i] = 1
                        labelMask[i+1] = 1
                    if distances[i]>a:
                        ret[i] -= Fzloc
        return distances, ret, labelMask            


    def computeLocalStiffness (self, l=None,ea=None,eiy=None,retCondenseSubMats=False):
        """Evaluates local stiffness matrix of element
        
        :param float l: precomputed length
        :param float ea: precomputed self.mat.e*self.cs.a
        :param float eiy: precomputed self.mat.e*self.cs.iy
        :param bool retCondenseSubMats: if true, also statically condensed submatrices (kaa,kab,kbb) with corresponding indices arrays a and b are returned
        :rtype: np.array(2d) | (np.array(2d),[int],[int],np.array(2d),np.array(2d),np.array(2d))
        """
        if l is None:
            l = self.computeLength()
        if ea is None:
            ea = self.mat.e*self.cs.a
        if eiy is None:
            eiy = self.mat.e*self.cs.iy
        l2 = l*l
        l3 = l2*l
        #Euler-Bernoulli beam without shear effect
        #answer=array([[ ea/l,          0.,         0.,     -ea/l,          0.,         0.],
                      #[ 0.  ,  12.*eiy/l3, -6.*eiy/l2,        0., -12.*eiy/l3, -6.*eiy/l2],
                      #[ 0.  ,  -6.*eiy/l2,  4.*eiy/l ,        0.,   6.*eiy/l2,  2.*eiy/l ],
                      #[-ea/l,          0.,         0.,      ea/l,          0.,         0.],
                      #[ 0.  , -12.*eiy/l3,  6.*eiy/l2,        0.,  12.*eiy/l3,  6.*eiy/l2],
                      #[ 0.  ,  -6.*eiy/l2,  2.*eiy/l ,        0.,   6.*eiy/l2,  4.*eiy/l ]])
        #Timoshenko's beam with shear effect
        #Source: H.P. Gavin: Structural Element: Stiffness, Mass, and Damping Matrices, CEE 541. Structural Dynamics, Duke University,2014
        fi=12.*self.mat.e*self.cs.iy/(self.cs.k*self.mat.g*self.cs.a*l*l)
        fi1=1.+fi
        answer=array([[ ea/l,              0.,                 0.,  -ea/l,               0.,                 0.],
                      [ 0.  ,  12.*eiy/l3/fi1,     -6.*eiy/l2/fi1,     0.,  -12.*eiy/l3/fi1,     -6.*eiy/l2/fi1],
                      [ 0.  ,  -6.*eiy/l2/fi1,  (4.+fi)*eiy/l/fi1,     0.,    6.*eiy/l2/fi1,  (2.-fi)*eiy/l/fi1],
                      [-ea/l,              0.,                 0.,   ea/l,               0.,                 0.],
                      [ 0.  , -12.*eiy/l3/fi1,      6.*eiy/l2/fi1,     0.,   12.*eiy/l3/fi1,      6.*eiy/l2/fi1],
                      [ 0.  ,  -6.*eiy/l2/fi1,  (2.-fi)*eiy/l/fi1,     0.,    6.*eiy/l2/fi1,  (4.+fi)*eiy/l/fi1]])
        
        # static condensation if some ends are hinges
        # a=nonzero force value, b=zero force(moment) value
        if self.hasHinges():
            if self.hinges[0] and self.hinges[1]:
                a = [0,1,3,4]
                b = [2,5]
            elif self.hinges[0]:
                a = [0,1,3,4,5]
                b = [2]
            elif self.hinges[1]:
                a = [0,1,2,3,4]
                b = [5]
            kaa = answer[ix_(a,a)]
            kab = answer[ix_(a,b)]
            kbb = answer[ix_(b,b)]
            k2 = kaa - dot(dot(kab, linalg.inv(kbb)), kab.transpose())
            answer = zeros((6,6))
            answer[ix_(a,a)] = k2
            if retCondenseSubMats:
                return answer,a,b,kaa,kab,kbb
        return answer

    def computeLocalInitialStressMatrix(self, l=None, N=None):
        """Evaluates local initial stress matrix of element
        
        :param float l: precomputed length
        :param N: normal force in element
        :rtype: np.array(2d) | (np.array(2d),[int],[int],np.array(2d),np.array(2d),np.array(2d))
        """
        if l is None:
            l = self.computeLength()
        l2 = l*l
        c = N/l
        #Euler-Bernoulli beam without shear effect
        #answer=array([[0.,      0.,          0.,      0.,         0.,         0.],
                      #[0.,   6./5.,      -l/10.,      0.,     -6./5.,     -l/10.],
                      #[0.,  -l/10.,   2.*l2/15.,      0.,      l/10.,    -l2/30.],
                      #[0.,      0.,          0.,      0.,         0.,         0.],
                      #[0.,  -6./5.,       l/10.,      0.,      6./5.,      l/10.],
                      #[0.,  -l/10.,     -l2/30.,      0.,      l/10.,   2*l2/15.]])
        #answer=answer*c
        #Timoshenko's beam with shear effect
        #Source: H.P. Gavin: Structural Element: Stiffness, Mass, and Damping Matrices, CEE 541. Structural Dynamics, Duke University,2014
        fi=12.*self.mat.e*self.cs.iy/(self.cs.k*self.mat.g*self.cs.a*l*l)
        fi2 = fi*fi
        answer=array([[0.,               0.,                             0.,  0.,              0.,                            0.],
                      [0.,   6./5.+2*fi+fi2,                         -l/10.,  0.,  -6./5-2*fi-fi2,                        -l/10.],
                      [0.,           -l/10.,  2.*l2/15.+l2*fi/6.+l2*fi2/12.,  0.,           l/10.,   -l2/30.-l2*fi/6.-l2*fi2/12.],
                      [0.,               0.,                             0.,  0.,              0.,                            0.],
                      [0.,  -6./5.-2*fi-fi2,                          l/10.,  0.,  6./5.+2*fi+fi2,                         l/10.],
                      [0.,           -l/10.,    -l2/30.-l2*fi/6.-l2*fi2/12.,  0.,            l/10., 2*l2/15.+l2*fi/6.+l2*fi2/12.]])
        answer=answer*(c/(1.+fi)/(1.+fi))
        
        cc=min(abs(answer[1,1]), abs(answer[2,2]))/1000.0
        answer[0,0]=cc
        answer[0,3]=-cc
        answer[3,0]=-cc
        answer[3,3]=cc

        # static condensation if some ends are hinges
        # a=nonzero force value, b=zero force(moment) value
        if self.hasHinges():
            (k,a,b,kaa,kab,kbb) = self.computeLocalStiffness (retCondenseSubMats=True)
            t=zeros((6, len(a)))
            
            t[ix_(a),0:len(a)]=identity(len(a))
            #print "t:",t
            #print (-1)*dot(linalg.inv(kbb),kab.transpose())
            #print "ti",t[ix_(b),:] 
            t[ix_(b),:]= (-1)*dot(linalg.inv(kbb),kab.transpose())
            #print "t:",t
            k2 = dot(t.transpose(),dot(answer,t))
            answer = zeros((6,6))
            answer[ix_(a,a)] = k2
            #print answer
        return answer

    def computeT(self, l=None,dx=None,dz=None):
        """Compute element transformation matrix from global to local cs
        
        :param float l: precomputed length
        :param float dx: precomputed dx
        :param float dz: precomputed dz
        :rtype: np.array(2d)
        """
        if l is None or dx is None or dz is None:
            l,dx,dz = self.computeGeom()
        c=dx/l
        s=dz/l
        t = array([[c ,s ,0., 0.,0.,0.],
                   [-s,c ,0., 0.,0.,0.],
                   [0.,0.,1., 0.,0.,0.],
                   [0.,0.,0., c ,s ,0.],
                   [0.,0.,0., -s,c ,0.],
                   [0.,0.,0., 0.,0.,1.]])
        return t

    def computeStiffness (self):
        """Compute element global stiffness matrix
        
        :rtype: np.array(2d)
        """
        l,dx,dz = self.computeGeom()
        ea = self.mat.e*self.cs.a
        eiy = self.mat.e*self.cs.iy
        #
        kl = self.computeLocalStiffness(l,ea,eiy)
        t  = self.computeT(l,dx,dz)
        k  = dot(dot(t.transpose(), kl), t)
        return k
 
    def computeInitialStressMatrix (self, N):
        """Compute element global stiffness matrix
        
        :rtype: np.array(2d)
        """
        l,dx,dz = self.computeGeom()
        #
        kl = self.computeLocalInitialStressMatrix(l,N)
        t  = self.computeT(l,dx,dz)
        k  = dot(dot(t.transpose(), kl), t)
        return k
         
    def computeEndValues(self, r):
        """Compute element local displacement and local end forces of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: ( np.array(1d), np.array(1d) )
        """
        l,dx,dz = self.computeGeom()
        ea = self.mat.e*self.cs.a
        eiy = self.mat.e*self.cs.iy
        t = self.computeT(l,dx,dz)
        loc = self.giveLocationArray()
        re = dot(t,r[loc])
        if self.hasHinges():
            kl,a,b,kaa,kab,kbb=self.computeLocalStiffness(l,ea,eiy,True)
        else:
            kl = self.computeLocalStiffness(l,ea,eiy)
        fe = dot(kl, re)
        bl = zeros(6)
        #blcc = zeros(6)
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            bl += load.giveLoadVectorForDoublyClampedBeam(type='beam2d')
        if self.hasHinges():
            re[ix_(b)] = dot(linalg.inv(kbb), -bl[ix_(b)] - dot(kab.transpose(), re[ix_(a)] ) )
            fe[ix_(a)] += bl[ix_(a)] - dot(dot(kab,linalg.inv(kbb)),bl[ix_(b)])
        else:
            fe += bl
        return fe,re

    def computeEndForces(self,r):
        """Compute local end forces of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: np.array(1d)
        """
        return self.computeEndValues(r)[0]

    def computeEndDspl(self,r):
        """Compute local end displacement of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: np.array(1d)
        """
        return self.computeEndValues(r)[1]

    def computeGeom(self):
        """Compute length and its coordinates components of receiver (l,dz,dz)
        
        :rtype: (float,float,float)
        """
        c1 = self.nodes[0].coords
        c2 = self.nodes[1].coords
        dx = c2[0]-c1[0]
        dz = c2[2]-c1[2]
        l = math.sqrt(dx*dx+dz*dz)
        return l,dx,dz

    def computeLength(self):
        """Compute length of receiver
        
        :rtype: float
        """
        return self.computeGeom()[0]

    def computeCenter(self):
        """Compute center of receiver
        
        :rtype: (float,float,float)
        """
        c1 = self.nodes[0].coords
        c2 = self.nodes[1].coords
        return (0.5*(c1[0]+c2[0]), 0.5*(c1[1]+c2[1]), 0.5*(c1[2]+c2[2]) )

    def hasHinges(self):
        """return True if receiver is hinged connected with at least one of its nodes, False otherwise
        
        :rtype: bool
        """
        return self.hinges[0] or self.hinges[1]

    def change(self,hinges=None,**kw):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another element with this label already exists, returns 1
        :param [Node|str] nodes: list of new nodes of receiver
        :param Material|str mat: new material of receiver
        :param CrossSection|str cs: new cross section of receiver
        :param Domain domain: new domain of receiver
        :param [bool,bool] hinges: new hinges of receiver
        :rtype: bool
        """
        if Element.change(self,**kw):
            # Element.change failed
            return 1
        if hinges:
            self.hinges = hinges
        return 0



class BeamGrid2d(Element):
    """A class representing grid beam Element
    
    :param str label: string label of receiver
    :param [Node|str] nodes: nodes of receiver
    :param Material|str mat: material of receiver
    :param CrossSection|str cs: cross section of receiver
    :param Domain domain: new domain of receiver
    :param [bool,bool] hinges: hinges possession of receiver

    TODO hinges?
    """

    hinges = None
    """*([bool,bool])* hinges possession of receiver"""

    def __init__(self, label='beamGrid2d', nodes=None, mat=None, cs=None, domain=None, hinges=[False,False]):
        Element.__init__(self, label=label, nodes=nodes, mat=mat, cs=cs, domain=domain)
        self.hinges = hinges
        # hinges = [bool,bool], hinges[0] express if beam is hinge connected with nodes[0] or not, hinges[1] with nodes[1]

    def checkNodes(self,nodes):
        """Check nodes, returns 0 if ok, 1 otherwise
        """
        if nodes[0] is nodes[1]:
            logger.error( langStr('Coinciding nodes', 'Stejné uzly') )
            return 1
        return 0

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label,nodes=[n.label for n in self.nodes],mat=self.mat.label,cs=self.cs.label,hinges=self.hinges, domain=self.domain.label if self.domain else '')

    def computeDefl(self, rr=None, rl=None, nseg=20, fzloc=None, geom=None):
        raise NotImplementedError

    def computeLocalInternalForces(self, rr=None, F=None, nseg=20, fzloc=None, geom=None):
        raise NotImplementedError

    def computeLocalStiffness (self, l=None,gj=None,eiy=None,retCondenseSubMats=False):
        """Evaluates local stiffness matrix of element
        
        :param float l: precomputed length
        :param float gj: precomputed self.mat.g*self.cs.j
        :param float eiy: precomputed self.mat.e*self.cs.iy
        :param bool retCondenseSubMats: if true, also statically condensed submatrices (kaa,kab,kbb) with corresponding indices arrays a and b are returned
        :rtype: np.array(2d) | (np.array(2d),[int],[int],np.array(2d),np.array(2d),np.array(2d))
        """
        if l is None:
            l = self.computeLength()
        if gj is None:
            gj = self.mat.g*self.cs.j
        if eiy is None:
            eiy = self.mat.e*self.cs.iy
        l2 = l*l
        l3 = l2*l
        #stiffness matrix for grids as in http://www.ce.memphis.edu/7117/notes/presentations/chapter_05b.pdf
        answer=array([[  12.*eiy/l3,    0., -6.*eiy/l2, -12.*eiy/l3,    0., -6.*eiy/l2],
                      [  0.        ,  gj/l,         0.,          0., -gj/l,         0.],
                      [ -6.*eiy/l2 ,    0.,   4.*eiy/l,   6.*eiy/l2,    0.,  2.*eiy/l ],
                      [ -12.*eiy/l3,    0.,  6.*eiy/l2,  12.*eiy/l3,    0.,  6.*eiy/l2],
                      [  0.        , -gj/l,         0.,          0.,  gj/l,         0.],
                      [ -6.*eiy/l2 ,    0.,  2.*eiy/l ,   6.*eiy/l2,    0.,  4.*eiy/l ]])
        
        # static condensation if some ends are hinges (only edited to reflect on positions of moment in grid matrix, lets hope it works)
        # a=nonzero force value, b=zero force(moment) value
        # TODO check
        if self.hasHinges():
            if self.hinges[0] and self.hinges[1]:
                a = [0,3]
                b = [1,2,4,5]
            elif self.hinges[0]:
                a = [0,3,4,5]
                b = [1,2]
            elif self.hinges[1]:
                a = [0,1,2,3]
                b = [4,5]
            kaa = answer[ix_(a,a)]
            kab = answer[ix_(a,b)]
            kbb = answer[ix_(b,b)]
            k2 = kaa - dot(dot(kab, linalg.inv(kbb)), kab.transpose())
            answer = zeros((6,6))
            answer[ix_(a,a)] = k2
            if retCondenseSubMats:
                return answer,a,b,kaa,kab,kbb
        return answer
    
    def computeLocalInitialStressMatrix(self, l=None, N=None):
        raise NotImplementedError

    def computeT(self, l=None,dx=None,dy=None):
        """Compute element transformation matrix from global to local cs
        
        :param float l: precomputed length
        :param float dx: precomputed dx
        :param float dz: precomputed dz
        :rtype: np.array(2d)
        """
        if l is None or dx is None or dy is None:
            l,dx,dy = self.computeGeom()
        c=dx/l
        s=dy/l
        #transformation matrix, as in http://www.ce.memphis.edu/7117/notes/presentations/chapter_05b.pdf
        t = array([[1.,0.,0., 0.,0.,0.],
                   [0.,c ,s, 0.,0.,0.],
                   [0.,-s ,c , 0.,0.,0.],
                   [0.,0.,0., 1.,0.,0.],
                   [0.,0.,0., 0.,c , s],
                   [0.,0.,0., 0.,-s ,c ]])
        return t

    def computeStiffness (self):
        """Compute element global stiffness matrix
        
        :rtype: np.array(2d)
        """
        l,dx,dy = self.computeGeom()
        gj = self.mat.g*self.cs.j
        eiy = self.mat.e*self.cs.iy
        #
        kl = self.computeLocalStiffness(l,gj,eiy)
        t  = self.computeT(l,dx,dy)
        k  = dot(dot(t.transpose(), kl), t)
        return k
 
    def computeInitialStressMatrix (self, N):
        raise NotImplementedError
         
    def computeEndValues(self, r):
        """Compute element local displacement and local end forces of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: ( np.array(1d), np.array(1d) )
        """
        l,dx,dz = self.computeGeom()
        gj = self.mat.g*self.cs.j
        eiy = self.mat.e*self.cs.iy
        t = self.computeT(l,dx,dz)
        loc = self.giveLocationArray()
        re = dot(t,r[loc])
        if self.hasHinges():
            raise NotImplementedError # TODO check?
        else:
            kl = self.computeLocalStiffness(l,gj,eiy)
        fe = dot(kl, re)
        bl = zeros(6)
        #blcc = zeros(6)
        for load in self.domain.giveElementLoadsOnElement(self,onlyActiveLC=True):
            bl += load.giveLoadVectorForDoublyClampedBeam(type='grid2d')
        if self.hasHinges():
            raise NotImplementedError # TODO check?
        else:
            fe += bl
        return fe,re

    def computeEndForces(self,r):
        """Compute local end forces of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: np.array(1d)
        """
        return self.computeEndValues(r)[0]

    def computeEndDspl(self,r):
        """Compute local end displacement of receiver
        
        :param np.array(1d) r: global strucutre vector of nodal displacements
        :rtype: np.array(1d)
        """
        return self.computeEndValues(r)[1]

    def computeGeom(self):
        """Compute length and its coordinates components of receiver (l,dx,dy)
        
        :rtype: (float,float,float)
        """
        c1 = self.nodes[0].coords
        c2 = self.nodes[1].coords
        dx = c2[0]-c1[0]
        dy = c2[1]-c1[1]
        l = math.sqrt(dx*dx+dy*dy)
        return l,dx,dy

    def computeLength(self):
        """Compute length of receiver
        
        :rtype: float
        """
        return self.computeGeom()[0]

    def computeCenter(self):
        """Compute center of receiver
        
        :rtype: (float,float,float)
        """
        c1 = self.nodes[0].coords
        c2 = self.nodes[1].coords
        return (0.5*(c1[0]+c2[0]), 0.5*(c1[1]+c2[1]), 0.5*(c1[2]+c2[2]) )

    def hasHinges(self):
        """return True if receiver is hinged connected with at least one of its nodes, False otherwise
        
        :rtype: bool
        """
        return self.hinges[0] or self.hinges[1]

    def change(self,hinges=None,**kw):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another element with this label already exists, returns 1
        :param [Node|str] nodes: list of new nodes of receiver
        :param Material|str mat: new material of receiver
        :param CrossSection|str cs: new cross section of receiver
        :param Domain domain: new domain of receiver
        :param [bool,bool] hinges: new hinges of receiver
        :rtype: bool
        """
        if Element.change(self,**kw):
            # Element.change failed
            return 1
        if hinges:
            self.hinges = hinges
        return 0





class GeneralBoundaryCondition:
    """Abstract class representing general boundary condition
    
    current implementation allows one BC to belong to exactly one entity (e.g. one NodalLoad belongs to one certain node, but one node can have more NodalLoads). This approach can be useful in loading cases approach (and their combinations).
    
    :param str label: string label of receiver
    :param unknown where: location of application
    :param dict value: value of receiver
    :param LoadCase loadCase: loadCase which BC belongs to
    """

    label = None
    """*(str)* string label"""
    where = None
    """*(unknown)* location of application"""
    value = dict()
    """*(unknown)* value"""
    loadCase = None
    """*(LoadCase)* load case"""

    def __init__(self, label='generalboundarycondition', where=None, value=None, loadCase=None):
        self.loadCase = loadCase
        self.value = dict() # ot to use global static value
        initFail = self.change(label=label, where=where, value=value, loadCase=loadCase, fromInit=True)
        if initFail:
            raise EduBeamError
            print('GeneralBoundaryCondition.__init__')

    def computeLoad(self,type=''):
        """Returns a tuple containing load code numbers and load values"""
        return ([],[])

    def dict(self):
        """returns dictionary of attributes saved to xml file"""
        return dict(label=self.label, where=self.where.label, value=self.value, loadCase=self.loadCase.label if self.loadCase else '')

    def change(self,label=None,where=None,value=None,loadCase=None):
        """Change receiver. Return 0 if successful, 1 otherwise"""
        raise NotImplementedError

    def giveNewWhere(self, where):
       """Returns location (Node, Element...) instance if successful, None otherwise"""
       raise NotImplementedError

    def giveNewElement(self,where):
        """Returns Element instance if successful, None otherwise
        
        :param str|Element where: element to be checked and returned
        :rtype: Element | None
        """
        if not where:
            logger.error( langStr('No element load specified','Žádné prvkové zatížení nespecifikováno') )
            return None
        if isinstance(where,Element):
            return where
        if isinstance(where,(str,unicode)):
            if not (self.loadCase and self.loadCase.domain):
                logger.error( langStr('No domain to get element load by string label from ...','Žádná síť, z které by mohlo být prvkové zatížení získáno na základě názvu ...') )
                return None
            where = self.loadCase.domain.elements.get(where)
            if where:
                return where
            logger.error( langStr('self.domain.elementLoads has no key %s','self.domain.elementLoads nemá položku %s') % where )
            return None
        logger.error( langStr('Unsupported type of element load: %s','Nepodporovaný typ uzlového zatížení: %s') % where )
        return None

    def giveNewNode(self,where):
        """Returns Node instance if successful, None otherwise
        
        :param str|Node where: node to be checked and returned
        :rtype: Node | None
        """
        if not where:
            logger.error( langStr('No nodal load specified','Žádné uzlové zatížení nespecifikováno') )
            return None
        if isinstance(where,Node):
            return where
        if isinstance(where,(str,unicode)):
            if not (self.loadCase and self.loadCase.domain):
                logger.error( langStr('No domain to get nodal load by string label from ...','Žádná síť, z které by mohlo být uzlové zatížení získáno na základě názvu ...') )
                return None
            where = self.loadCase.domain.nodes.get(where)
            if where:
                return where
            logger.error( langStr('self.domain.nodalLoads has no key %s','self.domain.nodalLoads nemá položku %s') % where )
            return None
        logger.error( langStr('Unsupported type of nodal load: %s','Nepodporovaný typ uzlového zatížení: %s') % where )
        return None
           
    def giveNewLoadCase(self,loadCase):
        """Returns LoadCase instance if successful, None otherwise
        
        :param LoadCase loadCase: loadCase to be checked and returned
        :rtype: LoadCase | None
        """
        if not loadCase:
            logger.error( langStr('No load case specified','Žádný zatěžovací stav nespecifikován') )
            return None
        if isinstance(loadCase,LoadCase):
            return loadCase
        if isinstance(loadCase,(str,unicode)):
            if not (self.loadCase and self.loadCase.domain):
                logger.error( langStr('No domain to get load case by string label from ...','Žádná síť, z které by mohl být zatěžovací stav získán na základě názvu ...') )
                return None
            loadCase = self.loadCase.domain.loadCases.get(loadCase)
            if loadCase:
                return loadCase
            logger.error( langStr('self.loadCase.domain.loadCases has no key %s','self.loadCase.domain.loadCases nemá položku %s') % loadCase )
            return None
        logger.error( langStr('Unsupported type of load case: %s','Nepodporovaný typ zatěžovacího stavu: %s') % loadCase )
        return None

    def __str__(self):
        return self.label





class NodalLoad(GeneralBoundaryCondition):
    """Class representing nodal load
    value = {'fx','fy','fz','mx','my','mz'}
    
    :param str label: string label of receiver
    :param Node|str where: node of application
    :param dict value: value of receiver {'fx':float,'fy':float,'fz':float,'mx':float,'my':float,'mz':float}
    :param LoadCase loadCase: loadCase which BC belongs to
    """

    label = None
    """*(str)* string label"""
    where = None
    """*(Node)* node of application"""
    value = dict(fx=0.,fy=0.,fz=0.,mx=0.,my=0.,mz=0.)
    """*(dict)* value"""
    loadCase = None
    """*(LoadCase)* load case"""

    def __init__(self, label='nodalload', where=None, value=None, loadCase=None):
        GeneralBoundaryCondition.__init__(self,label=label, where=where, value=value, loadCase=loadCase)

    def giveNewWhere(self,where):
        return self.giveNewNode(where)

    def change(self, label=None, where=None, value=None, loadCase=None, fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another nodal load with this label already exists, returns 1
        :param Node|str where: node of application
        :param dict value: value of receiver {'fx':float,'fy':float,'fz':float,'mx':float,'my':float,'mz':float}
        :param LoadCase loadCase: loadCase which BC belongs to
        :rtype: bool
        """
        label = label if label else self.label
        loadCase = self.giveNewLoadCase(loadCase) if loadCase else self.loadCase
        if label!=self.label or loadCase is not self.loadCase:
            if loadCase:
                if label in loadCase.nodalLoads:
                    logger.error( langStr('Nodal load with label %s already exists in the nodal loads %s', 'Uzlové zatížení se jménem %s již existuje v uzlových zatíženích %s') % ( label, sorted(loadCase.nodalLoads.keys()) ) )
                    return 1
        where = self.giveNewWhere(where) if where else self.where
        value = dict( (key,float(val)) for key,val in value.items() ) if value else self.value
        if not where or not value:
            return 1
        self.where = where
        self.value.update(value)
        if label!=self.label or loadCase is not self.loadCase:
            if self.loadCase:
                self.loadCase.nodalLoads.pop(self.label,None)
            if loadCase:
                loadCase.nodalLoads[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Nodal load %s renamed to %s', 'Uzlové zatížení %s přejmenováno na %s') % (self.label, label) )
        self.label = label
        self.loadCase = loadCase
        return 0

    def computeLoad(self,type=''):
        """Returns nodal load
        
        :rtype: ([int],(float))
        """
        if type == 'grid2d':
            return (self.where.loc, [self.value[i] for i in ('fz','mx','my')] )
        else:
            return (self.where.loc, [self.value[i] for i in ('fx','fz','my')] )
# TODO




class PrescribedDisplacement(GeneralBoundaryCondition):
    """Class representing prescribed displacement
    value = {'x','z','Y'}
    
    :param str label: string label of receiver
    :param Node|str where: node of application
    :param dict value: value of receiver {'x':float,'z':float,'Y':float}
    :param LoadCase loadCase: loadCase which BC belongs to
    """

    label = None
    """*(str)* string label"""
    where = None
    """*(Node)* node of application"""
    value = None
    """*(dict)* value"""
    loadCase = None
    """*(LoadCase)* load case"""

    def __init__(self, label='pdspl', where=None, value=None, loadCase=None):
        GeneralBoundaryCondition.__init__(self,label=label, where=where, value=value, loadCase=loadCase)

    def giveNewWhere(self,where):
        return self.giveNewNode(where)

    def change(self, label=None, where=None, value=None, loadCase=None, fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another prescribed displacement with this label already exists, returns 1
        :param Node|str where: node of application
        :param dict value: value of receiver {'x':float,'z':float,'Y':float}
        :param LoadCase loadCase: loadCase which BC belongs to
        :rtype: bool
        """
        label = label if label else self.label
        loadCase = self.giveNewLoadCase(loadCase) if loadCase else self.loadCase
        if label!=self.label or loadCase is not self.loadCase:
            if loadCase:
                if label in loadCase.prescribedDspls:
                    logger.error( langStr('Prescribed displacement with label %s already exists in the pDspls %s', 'Předepsané přemístění se jménem %s již existuje v přemístěních %s') % ( label, sorted(loadCase.prescribedDspls.keys()) ) )
                    return 1
        where = self.giveNewWhere(where) if where else self.where
        value = dict( (key,float(val)) for key,val in value.items() ) if value else self.value
        if not where or not value:
            return 1
        self.where = where
        self.value = value
        if label!=self.label or loadCase is not self.loadCase:
            if self.loadCase:
                self.loadCase.prescribedDspls.pop(self.label,None)
            if loadCase:
                loadCase.prescribedDspls[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Prescribed displacement %s renamed to %s', 'Uzlové zatížení %s přejmenováno na %s') % (self.label, label) )
        self.label = label
        self.loadCase = loadCase
        return 0

    def computeLoad(self,type=''):
        """Returns prescribed displacement
        
        :rtype: ([int],(float))
        """
        return (self.where.loc, [self.value[i] for i in ('x','z','Y')] )





class ElementLoad(GeneralBoundaryCondition):
    """A class representing element load
    value = {'type', 'dir', 'magnitude', 'perX', 'Fx', 'Fz', 'DistF', 'dTc', 'dTg'}
    'type' is uniform, local force, temperature
    'dir', 'magnitude', 'perX', 'Fx', 'Fz', 'DistF' are related to type = uniform or type = local force
    'dTc' axial change of temperature (mean)
    'dTg' temperature difference (transversal change of temperature on opposite edges of the beam), in local cs
    """

    label = None
    """*(str)* string label"""
    where = None
    """*(Element)* element of application"""
    value = dict(type='',dir='',magnitude=0.,perX=False,Fx=0.,Fz=0.,DistF=0.,dTc=0.,dTg=0.)
    """*(dict)* value"""
    loadCase = None
    """*(LoadCase)* load case"""

    def __init__(self, label='elementload', where=None, value=None, loadCase=None):
        GeneralBoundaryCondition.__init__(self,label=label, where=where, value=value, loadCase=loadCase)

    def giveNewWhere(self,where):
        return self.giveNewElement(where)

    def change(self, label=None, where=None, value=None, loadCase=None, fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another element load with this label already exists, returns 1
        :param Node|str where: node of application
        :param dict value: value of receiver TODO
        :param LoadCase loadCase: loadCase which BC belongs to
        :rtype: bool
        """
        label = label if label else self.label
        loadCase = self.giveNewLoadCase(loadCase) if loadCase else self.loadCase
        if label!=self.label or loadCase is not self.loadCase:
            if loadCase:
                if label in loadCase.elementLoads:
                    logger.error( langStr('Element load with label %s already exists in the element loads %s', 'Předepsané přemístění se jménem %s již existuje v předepsaných přemístěních %s') % ( label, sorted(loadCase.elementLoads.keys()) ) )
                    return 1
        where = self.giveNewWhere(where) if where else self.where
        value = dict( (key,val) for key,val in value.items() ) if value else self.value
        if not where or not value:
            return 1
        self.where = where
        self.value.update(value)
        if label!=self.label or loadCase is not self.loadCase:
            if self.loadCase:
                self.loadCase.elementLoads.pop(self.label,None)
            if loadCase:
                loadCase.elementLoads[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Element load %s renamed to %s', 'Předepsané přemístění %s přejmenováno na %s') % (self.label, label) )
        self.label = label
        self.loadCase = loadCase
        return 0

    def computeLoad(self,type=''):
        """compute equivalent nodal load
        
        :rtype: ([int],nb.array(1d))
        """
        t = self.where.computeT()
        l = self.where.computeLength()
        f = self.giveLoadVectorForDoublyClampedBeam(type=type)
        if not self.where.hasHinges(): # clamped-clamped
            # return -ret, because end values are opposite than their influence on nodes
            return (self.where.giveLocationArray(), -dot(t.transpose(), f) )
        kl,a,b,kaa,kab,kbb = self.where.computeLocalStiffness(retCondenseSubMats=True)
        ret = zeros(6)
        # following is result of static condensation
        ret[ix_(a)] = f[ix_(a)] - dot(dot(kab,linalg.inv(kbb)),f[ix_(b)])
        # return -ret, because end values are opposite than their influence on nodes
        return self.where.giveLocationArray(), -dot(t.transpose(), ret)

    def giveFxFzElemProjection(self,type=''):
        """Help function for uniformly distributed load"""
        l,dx,dz = self.where.computeGeom()
        cosBeam = dx/l
        sinBeam = dz/l
        vxTmp=0
        vzTmp=0
        if self.value['dir'] == 'X':
            vxTmp = self.value['magnitude']
        elif self.value['dir'] == 'Z':
            vzTmp = self.value['magnitude']
        elif self.value['dir'] == 'Local X':
            vxTmp = self.value['magnitude'] * cosBeam
            vzTmp = self.value['magnitude'] * sinBeam
        elif self.value['dir'] == 'Local Z':
            vxTmp = -self.value['magnitude'] * sinBeam
            vzTmp = self.value['magnitude'] * cosBeam
        #
        if type=='grid2d':
            vxTmp = 0.
        #
        if self.value['perX'] == 1:
            vxTmp = vxTmp*abs(cosBeam)
            vzTmp = vzTmp*abs(cosBeam)
        return (vxTmp, vzTmp)


    def giveLoadVectorForDoublyClampedBeam(self,type=''):
        if type == 'grid2d':
            l = self.where.computeLength()
            #Uniform load
            fx, fz = self.giveFxFzElemProjection()
            retf = array([ # return load in LCS
                    -0.5*l*fz,
                           0.,
                +1/12.*fz*l*l,
                    -0.5*l*fz,
                           0.,
                -1/12.*fz*l*l ])
            return retf
 
        ##########
        t = self.where.computeT()
        l = self.where.computeLength()
        
        #Uniform load
        valGlob = array(self.giveFxFzElemProjection(type=type))
        valLoc = dot(t[0:2,0:2], valGlob)
        retf = array([ # return load in LCS
            -0.5*l*valLoc[0],
            -0.5*l*valLoc[1],
            +1/12.*valLoc[1]*l*l,
            -0.5*l*valLoc[0],
            -0.5*l*valLoc[1],
            -1/12.*valLoc[1]*l*l ])
        
        #Distributed force
        a = self.value['DistF']
        b = l-a
        valGlob = array([ self.value['Fx'], self.value['Fz'] ])
        valLoc = dot(t[0:2,0:2], valGlob)
        retF = array([ # return load in LCS
            -b/l*valLoc[0],
            b/l*(a*(a-b)/l/l-1.)*valLoc[1],
            a*b*b/l/l*valLoc[1],
            -a/l*valLoc[0],
            a/l*(b*(b-a)/l/l-1.)*valLoc[1],
            -a*a*b/l/l*valLoc[1]])
        
        #Temperature
        e = self.where.mat.e
        alpha = self.where.mat.alpha
        a = self.where.cs.a
        iy = self.where.cs.iy
        h = self.where.cs.h
        rett = array([ # from temperature
            +e*a*alpha*self.value['dTc'],
            0.,
            +e*iy*alpha*self.value['dTg']/h,
            -e*a*alpha*self.value['dTc'],
            0.,
            -e*iy*alpha*self.value['dTg']/h ])
        return retf + retF + rett


class LoadCase:
    """ A class representing set of loads in load case
    
    :param str label: string label of receiver
    :param Domain domain: new domain of receiver
    """

    label = None
    """*(str)* String label"""
    domain = None
    """*(Domain)* Domain which receiver belongs to"""
    nodalLoads = None
    """*(dict)* dictionary of nodal loads"""
    elementLoads = None
    """*(dict)* dictionary of element loads"""
    prescribedDspls = None
    """*(dict)* dictionary of prescribed displacements"""
    displayFlag = None
    """*(bool)* display flag"""

    def __init__(self, label='loadcase', domain=None):
        initFail = self.change(label=label,domain=domain,fromInit=True)
        if initFail:
            raise EduBeamError
            print('LoadCase.__init__')
        self.nodalLoads = {}
        self.elementLoads = {}
        self.prescribedDspls = {}
        #display flag
        self.displayFlag = True

    def dict(self):
        """returns dictionary of attributes saved to xml file
        
        :rtype: dict
        """
        return dict(label=self.label, domain=self.domain.label if self.domain else '')

    def change(self,label=None,domain=None,fromInit=False):
        """Change receiver. Return False if successful, True otherwise
        
        :param str label: new string label of receiver. If another load case with this label already exists, returns 1
        :param Domain domain: new domain of receiver
        :rtype: bool
        """
        label = label if label else self.label
        domain = domain if domain and isinstance(domain,Domain) else self.domain
        if label!=self.label or domain is not self.domain:
            if domain:
                if label in domain.loadCases:
                    logger.error( langStr('LoadCase %s already exists in the load cases %s', 'Zatěžovací stav %s již existuje v Zatěžovacích stavech %s') % ( label, sorted(domain.loadCases.keys()) ) )
                    return 1
        if label!=self.label or domain is not self.domain:
            if self.domain:
                self.domain.loadCases.pop(self.label,None)
            if domain:
                domain.loadCases[label] = self
        if label != self.label and not fromInit:
            logger.info( langStr('Load case %s renamed to %s', 'Zatěžovací stav %s přejmenován na %s') % (self.label, label) )
        self.label = label
        self.domain = domain
        return 0

    def containsNodalLoad(self,load):
        return load in self.nodalLoads.values()

    def containsElementLoad(self,load):
        return load in self.elementLoads.values()

    def containsPrescribedDspl(self,pDspl):
        return pDspl in self.prescribedDspls.values()

    def contains(self,load):
        if self.containsNodalLoad(load):
            return True
        if self.containsElementLoad(load):
            return True
        if self.containsPrescribedDspl(load):
            return True
        return False

    def __str__(self):
        return self.label




class Domain:
    """A class representing the mesh
    
    :param str label: string label of receiver
    """

    label = None
    """*(str)* string label"""
    materials = None
    """*(dict)* dictionary of materials"""
    crossSects = None
    """*(dict)* dictionary of cross sections"""
    nodes = None
    """*(dict)* dictionary of nodes"""
    elements = None
    """*(dict)* dictionary of elements"""
    loadCases = None
    """*(dict)* dictionary of load cases"""
    activeLoadCase = None
    """*(LoadCase)* active load case"""
    session = None
    """*(Session)* session which receiver belongs to"""
    dofsNames = None

    def __init__(self,label='domain',type='beam2d'):
        self.label = label
        self.materials = {}
        self.crossSects = {}
        self.nodes = {}
        self.elements = {}
        # list of loadCases
        self.loadCases = {}
        self.activeLoadCase = None
        #self.nodalLoads = {}
        #self.elementLoads = {}
        self.session = None
        self.addPredefinedItems()
        self.type = type
        self.check()

    def check(self):
        if self.type == 'beam2d':
            self.dofsNames = ['x','z','Y']
        elif self.type == 'grid2d':
            self.dofsNames = ['z','X','Y']
        else:
            raise EduBeamError

    def addPredefinedItems(self):
        mat = Material(label='DefaultMat', e=30.e+6, g=10.e+6, alpha=12.e-6)
        self.materials[mat.label] = mat
        #default rectangle 0.2 x 0.3 m
        cs = CrossSection(label='DefaultCS', a=0.06, iy=4.5e-4, iz=2.0e-4, dyz=0., h=0.3, k=0.833333)
        self.crossSects[cs.label] = cs
        #create a default load case
        lc = LoadCase (label='Default_loadcase', domain=self)
        lc.displayFlag = True
        self.loadCases[lc.label] = lc
        self.activeLoadCase=lc

    def delPredefinedItems(self):
        self.materials.pop('DefaultMat',None)
        self.crossSects.pop('DefaultCS',None)
        self.loadCases.pop('Default_loadcase',None)
        self.activeLoadCase = None

    def giveMaterial(self,mat):
        """Returns Material instance if successful, None otherwise
        
        :param str|Material mat: given material to be returned
        :rtype: Material | None
        """
        if isinstance(mat,(str,unicode)):
            label = mat
            mat = self.materials.get(label)
            if not mat:
                logger.error( langStr('Material %s not found in the materials %s', 'Materiál %s nenalezen v materiálech %s') % (label, sorted(self.materials.keys())) )
            return mat
        if isinstance(mat,Material):
            return mat
        raise TypeError

    def giveCrossSection(self,cs):
        """Returns CrossSection instance if successful, None otherwise
        
        :param str|CrossSection cs: given cross section to be returned
        :rtype: CrossSection | None
        """
        if isinstance(cs,(str,unicode)):
            label = cs
            cs = self.crossSects.get(label)
            if not cs:
                logger.error( langStr('Cross section %s not found in the cross sections %s', 'Průřez %s nenalezen v průřezech %s') % (label, sorted(self.crossSects.keys())) )
            return cs
        if isinstance(cs,CrossSection):
            return cs
        raise TypeError

    def giveNode(self,node):
        """Returns Node instance if successful, None otherwise
        
        :param str|Node node: given node to be returned
        :rtype: Node | None
        """
        if isinstance(node,(str,unicode)):
            label = node
            node = self.nodes.get(label)
            if not node:
                logger.error( langStr('Node %s not found in the nodes %s', 'uzel %s nenalezen v uzlech %s') % (label, sorted(self.nodes.keys())) )
            return node
        if isinstance(node,Node):
            return node
        raise TypeError

    def giveElement(self,elem):
        """Returns Element instance if successful, None otherwise
        
        :param str|Element elem: given element to be returned
        :rtype: Element | None
        """
        if isinstance(elem,(str,unicode)):
            label = elem
            elem = self.elements.get(label)
            if not elem:
                logger.error( langStr('Element %s not found in the elements %s', 'Prvek %s nenalezen v prvcích %s') % (label, sorted(self.elements.keys())) )
            return elem
        if isinstance(elem,Element):
            return elem
        raise TypeError

    def giveLoadCase(self,lc):
        """Returns LoadCase instance if successful, None otherwise
        
        :param str|LoadCase lc: given load case to be returned
        :rtype: LoadCase | None
        """
        if isinstance(lc,(str,unicode)):
            label = lc
            lc = self.loadCases.get(label)
            if not lc:
                logger.error( langStr('Load case %s not found in the load cases %s', 'Zatěžovací stav %s nenalezen v zatěžovacích stavech %s') % (label, sorted(self.loadCases.keys())) )
            return lc
        if isinstance(lc,LoadCase):
            return lc
        raise TypeError

    def giveNodalLoad(self,load):
        """Returns NodalLoad instance if successful, None otherwise
        
        :param str|NodalLoad load: given nodal load to be returned
        :rtype: NodalLoad | None
        """
        if isinstance(load,(str,unicode)):
            for lc in self.loadCases.values():
                if load in lc.nodalLoads:
                    break
            label = load
            load = lc.nodalLoads.get(label)
            if not load:
                logger.error( langStr('Nodal load %s not found in the nodal loads %s', 'Uzlové zatížení %s nenalezeno v uzlových zatíženích %s') % (label, sorted(self.giveLabelsOfNodalLoads())) )
            return load
        if isinstance(load,NodalLoad):
            return load
        raise TypeError

    def givePrescribedDspl(self,pDspl):
        """Returns NodalLoad instance if successful, None otherwise
        
        :param str|PrescribedDisplacement pDspl: given prescribed displacement to be returned
        :rtype: NodalLoad | None
        """
        if isinstance(pDspl,(str,unicode)):
            for lc in self.loadCases.values():
                if pDspl in lc.prescribedDspls:
                    break
            label = pDspl
            pDspl = lc.prescribedDspls.get(label)
            if not pDspl:
                logger.error( langStr('Prescribed displacement %s not found in the prescribed displacements %s', 'Předepsané přemístění %s nenalezeno v předepsaných přemístěních %s') % (label, sorted(self.giveLabelsOfPrescribedDspls())) )
            return pDspl
        if isinstance(pDspl,PrescribedDisplacement):
            return pDspl
        raise TypeError

    def giveElementLoad(self,load):
        """Returns ElementLoad instance if successful, None otherwise
        
        :param str|ElementLoad load: given element load to be returned
        :rtype: ElementLoad | None
        """
        if isinstance(load,(str,unicode)):
            for lc in self.loadCases.values():
                if load in lc.elementLoads:
                    break
            label = load
            load = lc.elementLoads.get(label)
            if not load:
                logger.error( langStr('Element load %s not found in the nodal loads %s', 'Prvkové zatížení %s nenalezeno v prvkových zatíženích %s') % (load, sorted(self.giveLabelsOfElementLoads())) )
            return load
        if isinstance(load,ElementLoad):
            return load
        raise TypeError

    def addMaterial(self,mat=None,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add material to receiver. Return Material if successful, None otherwise
        
        :param Material mat: material to be added. If mat==None, new Material is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`Material`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`Material`
        :rtype: Material|None
        """
        isUndoable = isUndoable and self.session
        if not mat:
            # new material is constructed from **kw. Coinciding labels is controlled in Material.__init__
            kw['domain'] = self # make mat.domain == self
            try:
                mat = Material(**kw)
            except EduBeamError:
                return None
        else:
            # mat exists, chceck label coincidence
            if mat.label in self.materials:
                logger.error( langStr('Material %s already exists in %s, continuing', 'Materiál %s už existuje v %s, pokračuji') % (mat.label, sorted(self.materials.keys()) ) )
                return None
            self.materials[mat.label] = mat
            mat.domain = self
        if isUndoable:
            command = ('add',Domain.addMaterial,mat.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added Material %s: E=%s, G=%s, alpha=%s', 'Přidán materiál %s: E=%s, G=%s, alfa=%s') % (mat.label, mat.e, mat.g, mat.alpha) )
        return mat

    def addCrossSect(self,cs=None,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add cross section to receiver. Return CrossSection if successful, None otherwise
        
        :param CrossSection cs: cross section to be added. If cs==None, new CrossSection is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`CrossSection`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`CrossSection`
        :rtype: CrossSection|None
        """
        isUndoable = isUndoable and self.session
        if not cs:
            # new corss section is constructed from **kw. Coinciding labels is controlled in CrossSection.__init__
            kw['domain'] = self
            try:
                cs = CrossSection(**kw)
            except EduBeamError:
                return None
        else:
            # cs exists, chceck label coincidence
            if cs.label in self.crossSects:
                logger.error( langStr('CrossSection %s already exists in %s, continuing', 'Průřez %s už existuje v %s, pokračuji') % (cs.label, sorted(self.crossSects.keys()) ) )
                return None
            self.crossSects[cs.label] = cs
            cs.domain = self
        if isUndoable:
            command = ('add',Domain.addCrossSect,cs.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added CrossSection %s: A=%s, Iy=%s, h=%s, k=%s','Vložen průřez %s: A=%s, Iy=%s, h=%s, k=%s') % (cs.label, cs.a, cs.iy, cs.h, cs.k) )
        return cs

    def addNode(self,node=None,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add node to receiver. Return Node if successful, None otherwise
        
        :param Node node: node to be added. If node==None, new Node is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`Node`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`Node`
        :rtype: Node|None
        """
        isUndoable = isUndoable and self.session
        if not node:
            # new node is constructed from **kw. Coinciding labels is controlled in Node.__init__
            kw['domain'] = self
            try:
                node = Node(**kw)
            except EduBeamError:
                return None
        else:
            # node exists, chceck label coincidence
            if node.label in self.nodes:
                logger.error( langStr('Node %s already exists in %s, continuing', 'Uzel %s už existuje v %s, pokračuji') % (node.label, sorted(self.nodes.keys()) ) )
                return None
            self.nodes[node.label] = node
            node.domain = self
        if isUndoable:
            command = ('add',Domain.addNode,node.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added Node %s: x=%f z=%f','Vložen uzel %s: x=%f z=%f') % (node.label, node.coords[0], node.coords[2]) )
        return node

    def addElement(self,element=None,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add element to receiver. Return Element if successful, None otherwise
        
        :param Beam2d element: element to be added. If element==None, new Element is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`Element`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`Element`
        :rtype: Element|None
        """
        isUndoable = isUndoable and self.session
        if not element:
            # new element is constructed from **kw. Coinciding labels is controlled in Element.__init__
            kw['domain'] = self
            try:
                element = Beam2d(**kw)
            except EduBeamError:
                return None
        else:
            # element exists, chceck label coincidence
            if element.label in self.elements:
                logger.error( langStr('Element %s already exists in %s, continuing', 'Prvek %s už existuje v %s, pokračuji') % (element.label, sorted(self.elements.keys()) ) )
                return None
            self.elements[element.label] = element
            element.domain = self
        if isUndoable:
            command = ('add',Domain.addElement,element.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added Element %s: n1=%s, n2=%s, mat=%s, cs=%s','Přidán prvek %s: n1=%s, n2=%s, mat=%s, cs=%s') % (element.label, element.nodes[0], element.nodes[1], element.mat, element.cs) )
        return element

    def addLoadCase(self, lc=None, isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add load case to receiver. Return LoadCase if successful, None otherwise
        
        :param LoadCase lc: load case to be added. If ls==None, new LoadCase is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`LoadCase`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`LoadCase`
        :rtype: LoadCase|None
        """
        isUndoable = isUndoable and self.session
        if not lc:
            # new load case is constructed from **kw. Coinciding labels is controlled in LoadCase.__init__
            kw['domain'] = self
            try:
                lc = LoadCase(**kw)
            except EduBeamError:
                return None
        else:
            # load case exists, chceck label coincidence
            if lc.label in self.loadCases:
                logger.error( langStr('Load case %s already exists in %s, continuing', 'Zatěžovací stav %s už existuje v %s, pokračuji') % (lc.label, sorted(self.loadCases.keys()) ) )
                return None
            self.loadCases[lc.label] = lc
            lc.domain = self
        if not self.activeLoadCase:
            self.activeLoadCase = lc
        if isUndoable:
            command = ('add',Domain.addLoadCase,lc.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added load case %s', 'Přidán zatěžovací stav %s') % (lc.label) )
        return lc

    def addNodalLoad(self,load=None,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Add nodal load to receiver. Return NodalLoad if successful, None otherwise
        
        :param NodalLoad load: nodal load to be added. If load==None, new NodalLoad is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`NodalLoad`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`NodalLoad`
        :rtype: NodalLoad|None
        """
        isUndoable = isUndoable and self.session
        # check load case
        loadCase = kw.get('loadCase')
        if not loadCase:
            loadCase = self.activeLoadCase
        if isinstance(loadCase,LoadCase):
            pass
        elif isinstance(loadCase,(str,unicode)):
            loadCase = self.loadCases.get(loadCase)
            if not loadCase:
                logger.error( langStr('LoadCase not found in %s', 'Zatěžovací stav nenalezen v %s') % (sorted(self.loadCases.keys())) )
                return None
        kw['loadCase'] = loadCase
        # actual addLoad
        if not load:
            # new nodal load is constructed from **kw. Coinciding labels is controlled in NodalLoad.__init__
            try:
                load = NodalLoad(**kw)
            except EduBeamError:
                return None
        else:
            # nodal load exists, chceck label coincidence
            if load.label in loadCase.nodalLoads:
                logger.error( langStr('Nodal load %s already exists in %s, continuing', 'Uzlové zatížení %s už existuje v %s, pokračuji') % (load.label, sorted(loadCase.nodalLoads.keys()) ) )
                return None
            loadCase.nodalLoads[load.label] = load
            load.loadCase = loadCase
        if isUndoable:
            command = ('add',Domain.addNodalLoad,load.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added Nodal load %s on node %s: fx=%s, fy=%s, fz=%s, Mx=%s, My=%s, Mz=%s', 'Přidáno uzlové zatížení %s na uzel %s: fx=%s, fz=%s, My=%s') % (load.label, load.where, load.value['fx'], load.value['fy'], load.value['fz'], load.value['mx'], load.value['my'], load.value['mz']) )
        return load

    def addPrescribedDspl(self,pDspl=None,isUndoable=False,masterCommands=None,verbose=True,**kw):
        """Add prescribed displacement to receiver. Return PrescribedDisplacement if successful, None otherwise
        
        :param PrescribedDisplacement pDspl: prescribed displacement to be added. If pDspl==None, new PrescribedDisplacement is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`PrescribedDisplacement`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`PrescribedDisplacement`
        :rtype: PrescribedDisplacement|None
        """
        isUndoable = isUndoable and self.session
        # check load case
        loadCase = kw.get('loadCase')
        if not loadCase:
            loadCase = self.activeLoadCase
        if isinstance(loadCase,LoadCase):
            pass
        elif isinstance(loadCase,(str,unicode)):
            loadCase = self.loadCases.get(loadCase)
            if not loadCase:
                logger.error( langStr('LoadCase not found in %s', 'Zatěžovací stav nenalezen v %s') % (sorted(self.loadCases.keys())) )
                return None
        kw['loadCase'] = loadCase
        # actual addLoad
        if not pDspl:
            # new nodal pDspl is constructed from **kw. Coinciding labels is controlled in PrescribedDisplacement.__init__
            try:
                pDspl = PrescribedDisplacement(**kw)
            except EduBeamError:
                return None
        else:
            # prescribed displacement exists, chceck label coincidence
            if pDspl.label in loadCase.prescribedDspls:
                logger.error( langStr('Prescribed displacement %s already exists in %s, continuing', 'Předepsané přemístění %s už existuje v %s, pokračuji') % (pDspl.label, sorted(loadCase.prescribedDspls.keys()) ) )
                return None
            loadCase.prescribedDspls[pDspl.label] = pDspl
            pDspl.loadCase = loadCase
        if isUndoable:
            command = ('add',Domain.addPrescribedDspl,pDspl.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added prescribed displacement %s on node %s: ux=%s, uz=%s, phi_y=%s', 'Přidáno předepsané přemístění %s na uzel %s: u=%s, w=%s, phi=%s') % (pDspl.label, pDspl.where, pDspl.value['x'], pDspl.value['z'], pDspl.value['Y']) )
        return pDspl

    def addElementLoad(self,load=None,isUndoable=False,verbose=True,masterCommands=None,*args,**kw):
        """Add element load to receiver. Return ElementLoad if successful, None otherwise
        
        :param ElementLoad load: element load to be added. If load==None, new ElementLoad is constructed from kw and then added. Possible identical label issues are solved in :py:meth:`ElementLoad`
        :param bool isUndoable: if the action is undoable or not
        :param kw: for meaning of kw, see :py:class:`ElementLoad`
        :rtype: ElementLoad|None
        """
        isUndoable = isUndoable and self.session
        # check load case
        loadCase = kw.get('loadCase')
        if not loadCase:
            loadCase = self.activeLoadCase
        if isinstance(loadCase,LoadCase):
            pass
        elif isinstance(loadCase,(str,unicode)):
            loadCase = self.loadCases.get(loadCase)
            if not loadCase:
                logger.error( langStr('LoadCase not found in %s', 'Zatěžovací stav nenalezen v %s') % (sorted(self.loadCases.keys())) )
                return None
        kw['loadCase'] = loadCase
        # actual addLoad
        if not load:
            # new element load is constructed from **kw. Coinciding labels is controlled in ElementLoad.__init__
            try:
                load = ElementLoad(**kw)
            except EduBeamError:
                return None
        else:
            # element load exists, chceck label coincidence
            if load.label in loadCase.elementLoads:
                logger.error( langStr('Element load %s already exists in %s, continuing', 'Prvkové zatížení %s už existuje v %s, pokračuji') % (load.label, sorted(loadCase.elementLoads.keys()) ) )
                return None
            loadCase.elementLoads[load.label] = load
            load.loadCase = loadCase
        if isUndoable:
            command = ('add',Domain.addElementLoad,load.dict())
            if masterCommands is not None:
                masterCommands.append(masterCommands)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Added element load %s on element %s', 'Přidáno prvkové zatížení %s na prvek %s') % (load.label, load.where) )
        return load


    def delMaterial(self,mat,newMat=None,isUndoable=False,masterCommands=None,verbose=True):
        """Delete material from receiver. Return False if successful, True otherwise
        
        :param Material|str mat: material to be deleted
        :param Material|str newMat: material to be replaced instead of the deleted one
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        mat = self.giveMaterial(mat)
        if not mat:
            logger.error( langStr('Deleting of material failed: mat', 'Mazání materiálu selhalo: mat') )
            return 1
        commands = [] if masterCommands is None else masterCommands # for undoable version
        if newMat:
            newMat = self.giveMaterial(newMat)
            if not newMat:
                logger.error( langStr('Deleting of material failed: newMat', 'Mazání materiálu selhalo: newMat') )
                return 1
            for elem in self.giveElementsWithMat(mat):
                cmdKw = {}                                             # for undoable version
                cmdKw['old'] = elem.dict()                             # for undoable version
                elem.change(mat=newMat)
                cmdKw['new'] = elem.dict()                             # for undoable version
                commands.append(('change',Domain.changeElement,cmdKw)) # for undoable version
            logger.info( langStr('Material %s deleted and replaced with %s', 'Materiál %s smazán a nahražen %s') % (mat, newMat) )
        else:
            for elem in self.elements.values():
                if elem.mat is mat:
                    logger.error( langStr('Material %s is being used by element %s, deleting canceled','Materiál %s je používán prvkem %s, mazání zrušeno') % (mat.label, elem.label ) )
                    return 1
            if verbose:
                logger.info( langStr('Material %s deleted', 'Materiál %s smazán') % (mat.label) )
        commands.append(('del',Domain.delMaterial,mat.dict())) # for undoable version
        del self.materials[mat.label]
        if isUndoable and masterCommands is None:
            self.session.addCommands(commands)
        return 0

    def delCrossSect(self,cs,newCS=None,isUndoable=False,masterCommands=None,verbose=True):
        """Delete cross section from receiver. Return False if successful, True otherwise
        
        :param CrossSection|str cs: cross section to be deleted
        :param CrossSection|str newCS: cross section to be replaced instead of the deleted one
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        cs = self.giveCrossSection(cs)
        if not cs:
            logger.error( langStr('Deleting of cross section failed: cs', 'Mazání průřezu selhalo: cs') )
            return 1
        commands = [] if masterCommands is None else masterCommands # for undoable version
        if newCS:
            newCS = self.giveCrossSection(newCS)
            if not newCS:
                logger.error( langStr('Deleting of cross section failed: newCS', 'Mazání průřezu selhalo: newCS') )
                return 1
            for elem in self.giveElementsWithCS(cs):
                cmdKw = {}                                             # for undoable version
                cmdKw['old'] = elem.dict()                             # for undoable version
                elem.change(cs=newCS)
                cmdKw['new'] = elem.dict()                             # for undoable version
                commands.append(('change',Domain.changeElement,cmdKw)) # for undoable version
            logger.info( langStr('CrossSection %s deleted and replaced with %s', 'Průřez %s smazán a nahražen %s') % (cs, newCS) )
        else:
            for elem in self.elements.values():
                if elem.cs is cs:
                    logger.error( langStr('CrossSection %s is being used by elements %s, deleting canceled','Průřez %s je používán prvky %s, mazání zrušeno') % (cs.label, elem.label) )
                    return 1
            if verbose:
                logger.info( langStr('CrossSection %s deleted', 'Průřez %s smazán') % (cs.label) )
        commands.append(('del',Domain.delCrossSect,cs.dict())) # for undoable version
        del self.crossSects[cs.label]
        if isUndoable and masterCommands is None:
            self.session.addCommands(commands)
        return 0

    def delNode(self,node,isUndoable=False,masterCommands=None,verbose=True):
        """Delete node from receiver. Return False if successful, True otherwise
        
        :param Node|str node: node to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        node = self.giveNode(node)
        if not node:
            logger.error( langStr('Deleting of node failed', 'Mazání uzlu selhalo') )
            return 1
        commands = [] if masterCommands is None else masterCommands # for undoable version
        for elem in self.giveElementsWithNode(node):
            for load in self.giveElementLoadsOnElement(elem):
                self.delElementLoad(load,verbose=False,isUndoable=isUndoable,masterCommands=commands)
            self.delElement(elem,verbose=False,isUndoable=isUndoable,masterCommands=commands)
        for load in self.giveNodalLoadsOnNode(node):
            self.delNodalLoad(load,verbose=False,isUndoable=isUndoable,masterCommands=commands)
        commands.append(('del',Domain.delNode,node.dict())) # for undoable version)
        del self.nodes[node.label]
        if isUndoable and masterCommands is None:
            self.session.addCommands(commands)
        if verbose:
            logger.info( langStr('Node %s deleted', 'Uzel %s smazán') % (node.label) )
        return 0

    def delNodes(self,nodes,isUndoable=False,verbose=True,masterCommands=None):
        """Delete list of nodes. Return False if successful, True otherwise.

        :param [Node] nodes: list of nodes to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for node in nodes:
            if self.delNode(node,isUndoable=isUndoable,masterCommands=commands):
                # deleting failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.delNodes,{}))
            self.session.addCommands(commands)
        return 0

    def delElement(self,elem,isUndoable=False,masterCommands=None,verbose=True):
        """Delete element from receiver. Return False if successful, True otherwise
        
        :param Element|str elem: element to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        elem = self.giveElement(elem)
        if not elem:
            logger.error( langStr('Deleting of element failed', 'Mazání prvku selhalo') )
            return 1
        commands = [] if masterCommands is None else masterCommands # for undoable version
        for load in self.giveElementLoadsOnElement(elem):
            self.delElementLoad(load,verbose=False,isUndoable=isUndoable,masterCommands=commands)
        commands.append(('del',Domain.delElement,elem.dict())) # for undoable version
        del self.elements[elem.label]
        if isUndoable and masterCommands is None:
            self.session.addCommands(commands)
        if verbose:
            logger.info( langStr('Element %s deleted', 'Prvek %s smazán') % elem.label )
        return 0

    def delElements(self,elems,isUndoable=False,verbose=True,masterCommands=None):
        """Delete list of elems. Return False if successful, True otherwise.

        :param [Element] elems: list of elements to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for elem in elems:
            if self.delElement(elem,isUndoable=isUndoable,masterCommands=commands):
                # deleting failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.delElements,{}))
            self.session.addCommands(commands)
        return 0

    def delLoadCase(self,lc,newLC=None,isUndoable=False,verbose=True,masterCommands=None,forced=False):
        """Delete load case from receiver. Return False if successful, True otherwise
        
        :param LoadCase|str lc: load case to be deleted
        :param LoadCase|str newLC: load case to be replaced instead of the deleted one
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        lc = self.giveLoadCase(lc)
        if not lc:
            logger.error( langStr('Deleting of load case failed: lc', 'Mazání zatěžovacího stavu selhalo: lc') )
            return 1
        if lc is self.activeLoadCase and not forced:
            logger.error( langStr('Load case %s is active load case, deleting canceled', 'Zatěžovací stav %s je aktivní zatěžovací stav, mazání zrušeno') % (lc.label) )
            return 1
        commands = [] if masterCommands is None else masterCommands # for undoable version
        if newLC:
            newLC = self.giveLoadCase(newLC)
            if not newLC:
                logger.error( langStr('Deleting of load case failed: newLC', 'Mazání zatěžovacího stavu selhalo: newLC') )
                return 1
            for load in lc.nodalLoads.values():
                self.changeNodalLoad(load,loadCase=newLC,isUndoable=isUndoable,masterCommands=commands)
            for pDspl in lc.prescribedDspls.values():
                self.changePrescribedDspl(pDspl,loadCase=newLC,isUndoable=isUndoable,masterCommands=commands)
            for load in lc.elementLoads.values():
                self.changeElementLoad(load,loadCase=newLC,isUndoable=isUndoable,masterCommands=commands)
            logger.info( langStr('Load case %s deleted and replaced with %s', 'Zatěžovací stav %s smazán a nahražen %s') % (lc, newLC) )
        elif (lc.nodalLoads or lc.elementLoads) and not forced:
            logger.error( langStr('Load case %s not empty, deleting canceled', 'Zatěžovací stav není prázdný, mazání zrušeno') % (lc.label) )
            return 1
        else:
            for load in lc.nodalLoads.values():
                self.delNodalLoad(load,isUndoable=isUndoable,masterCommands=commands)
            for pDspl in lc.prescribedDspls.values():
                self.delPrescribedDspl(pDspl,isUndoable=isUndoable,masterCommands=commands)
            for load in lc.elementLoads.values():
                self.delElementLoad(load,isUndoable=isUndoable,masterCommands=commands)
            if verbose:
                logger.info( langStr('Load case %s deleted', 'Zatěžovací stav %s smazán') % lc.label )
        commands.append(('del',Domain.delLoadCase,lc.dict())) # for undoable version
        del self.loadCases[lc.label]
        if isUndoable and masterCommands is None:
            self.session.addCommands(commands)
        return 0

    def delNodalLoad(self,load,isUndoable=False,verbose=True,masterCommands=None):
        """Delete nodal load from receiver. Return False if successful, True otherwise
        
        :param NodalLoad|str load: nodal load to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        load = self.giveNodalLoad(load)
        if not load:
            logger.error( langStr('Deleting of nodal load failed', 'Mazání uzlového zatížení selhalo') )
            return 1
        del load.loadCase.nodalLoads[load.label]
        if isUndoable:
            command = ('del',Domain.delNodalLoad,load.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Nodal load %s deleted', 'Uzlové zatížení %s smazáno') % (load.label) )
        return 0

    def delNodalLoads(self,loads,isUndoable=False,verbose=True,masterCommands=None):
        """Delete list of nodal loads. Return False if successful, True otherwise.

        :param [NodalLoad] loads: list of nodal loads to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for load in loads:
            if self.delNodalLoad(load,isUndoable=isUndoable,masterCommands=commands):
                # deleting failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.delNodalLoads,{}))
            self.session.addCommands(commands)
        return 0

    def delPrescribedDspl(self,pDspl,isUndoable=False,verbose=True,masterCommands=None):
        """Delete prescribed displacement from receiver. Return False if successful, True otherwise
        
        :param PrescribedDisplacement|str pDspl: prescribed displacement to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        pDspl = self.givePrescribedDspl(pDspl)
        if not pDspl:
            logger.error( langStr('Deleting of prescribed displacement failed', 'Mazání předepsaného přemístění selhalo') )
            return 1
        del pDspl.loadCase.prescribedDspls[pDspl.label]
        if isUndoable:
            command = ('del',Domain.delPrescribedDspl,pDspl.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Prescribed displacement %s deleted', 'Předepsané přemístěních %s smazáno') % (pDspl.label) )
        return 0

    def delElementLoad(self,load,isUndoable=False,verbose=True,masterCommands=None):
        """Delete element load from receiver. Return False if successful, True otherwise
        
        :param ElementLoad|str load: element load to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        load = self.giveElementLoad(load)
        if not load:
            logger.error( langStr('Deleting of element load failed', 'Mazání prvkového zatížení selhalo') )
            return 1
        del load.loadCase.elementLoads[load.label]
        if isUndoable:
            command = ('del',Domain.delElementLoad,load.dict())
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Element load %s deleted', 'Prvkové zatížení %s smazáno') % load.label )
        return 0

    def delElementLoads(self,loads,isUndoable=False,verbose=True,masterCommands=None):
        """Delete list of element loads. Return False if successful, True otherwise.

        :param [ElementLoad] loads: list of element loads to be deleted
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for load in loads:
            if self.delElementLoad(load,isUndoable=isUndoable,masterCommands=commands):
                # deleting failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.delElementLoads,{}))
            self.session.addCommands(commands)
        return 0


    def changeMaterial(self,mat,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change material of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`Material.change`
        
        :param Material|str mat: material to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`Material.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        mat = self.giveMaterial(mat)
        if not mat:
            logger.error( langStr('Changing of material failed', 'Změna materiálu selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = mat.dict()
        if mat.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = mat.dict()
        if isUndoable:
            command = ('change',Domain.changeMaterial,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed material %s: E=%s, G=%s, alpha=%s', 'Změněn materiál %s: E=%s, G=%s, alfa=%s') % (mat.label, mat.e, mat.g, mat.alpha) )
        return 0

    def changeCrossSect(self,cs,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change cross section of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`CrossSection.change`
        
        :param CrossSection|str cs: cross section to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`CrossSection.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        cs = self.giveCrossSection(cs)
        if not cs:
            logger.error( langStr('Changing of cross section failed', 'Změna průřezu selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = cs.dict()
        if cs.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = cs.dict()
        if isUndoable:
            command = ('change',Domain.changeCrossSect,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed crossSection %s: A=%s, Iy=%s, h=%s, k=%s','Změněn průřez %s: A=%s, Iy=%s, h=%s, k=%s') % (cs.label, cs.a, cs.iy, cs.h, cs.k) )
        return 0

    def changeNode(self,node,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change node of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`Node.change`
        
        :param Node|str node: node to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`Node.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        node = self.giveNode(node)
        if not node:
            logger.error( langStr('Changing of node failed', 'Změna uzlu selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = node.dict()
        if node.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = node.dict()
        if isUndoable:
            command = ('change',Domain.changeNode,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed Node %s: x=%g z=%g','Změněn uzel %s: x=%g z=%g') % (node.label, node.coords[0], node.coords[2]) )
        return 0

    def changeNodes(self,nodes,bcs,isUndoable=False,verbose=True,masterCommands=None):
        """Change list of nodes. Return False if successful, True otherwise.
        
        :param [Node] nodes: list of nodes to be changed
        :param [(bool,bool,bool)] bcs: new bcs
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for node in nodes:
            if self.changeNode(node,bcs=bcs,isUndoable=isUndoable,masterCommands=commands):
                # changing failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.changeNodes,{}))
            self.session.addCommands(commands)
        return 0

    def changeElement(self,element,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change element of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`Element.change`
        
        :param Element|str element: element to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`Beam2d.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        element = self.giveElement(element)
        if not element:
            logger.error( langStr('Changing of element failed', 'Změna prvku selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = element.dict()
        if element.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = element.dict()
        if isUndoable:
            command = ('change',Domain.changeElement,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed Element %s: node1=%s, node2=%s, mat=%s, cs=%s','Změněn prvek %s: Uzel1=%s, Uzel2=%s, mat=%s, cs=%s') % (element.label, element.nodes[0], element.nodes[1], element.mat, element.cs) )
        return 0

    def changeElements(self,elems,mat,cs,hinges,isUndoable=False,verbose=True,masterCommands=None):
        """Change list of elements. Return False if successful, True otherwise.
        
        :param [Element] elems: list of elements to be changed
        :param [Material] mat: new material
        :param [CrossSection] cs: new cross section
        :param [bool,bool] hinges: new hinges
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for elem in elems:
            if self.changeElement(elem,mat=mat,cs=cs,hinges=hinges,isUndoable=isUndoable,masterCommands=commands):
                # changing failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.changeElements,{}))
            self.session.addCommands(commands)
        return 0

    def changeLoadCase(self,lc,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change load case of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`LoadCase.change`
        
        :param LoadCase|str lc: load case to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`LoadCase.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        lc = self.giveLoadCase(lc)
        if not lc:
            logger.error( langStr('Changing of load case failed', 'Změna zatěžovacího stavu selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = lc.dict()
        if lc.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = lc.dict()
        if isUndoable:
            command = ('change',Domain.changeLoadCase,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        return 0

    def changeNodalLoad(self,load,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change nodal load of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`NodalLoad.change`
        
        :param NodalLoad|str load: nodal load to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`NodalLoad.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        load = self.giveNodalLoad(load)
        if not load:
            logger.error( langStr('Changing of nodal load failed', 'Změna uzlového zatížení selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = load.dict()
        if load.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = load.dict()
        if isUndoable:
            command = ('change',Domain.changeNodalLoad,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed nodal load %s on node %s: fx=%g, fz=%g, My=%g', 'Změněno uzlové zatížení %s na uzlu %s: fx=%g, fz=%g, My=%g') % (load.label, load.where, load.value['fx'], load.value['fz'], load.value['my']) )
        return 0

    def changeNodalLoads(self,loads,value,isUndoable=False,verbose=True,masterCommands=None):
        """Change list of nodal loads. Return False if successful, True otherwise.
        
        :param [NodalLoad] loads: list of loads to be changed
        :param [dict] value: new load value
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for load in loads:
            if self.changeNodalLoad(load,value=value,isUndoable=isUndoable,masterCommands=commands):
                # changing failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.changeNodalLoads,{}))
            self.session.addCommands(commands)
        return 0

    def changePrescribedDspl(self,pDspl,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change prescribed displacement of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`PrescribedDisplacement.change`
        
        :param PrescribedDisplacement|str pDspl: prescribed displacement to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`PrescribedDisplacement.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        pDspl = self.givePrescribedDspl(pDspl)
        if not pDspl:
            logger.error( langStr('Changing of prescribed displacement failed', 'Změna uzlového zatížení selhala') )
            return 1
        cmdKw = {}
        cmdKw['old'] = pDspl.dict()
        if pDspl.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = pDspl.dict()
        if isUndoable:
            command = ('change',Domain.changePrescribedDspl,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed prescribed displacement %s on node %s: fx=%g, fz=%g, My=%g', 'Změněno předepsaného přemístění %s na uzlu %s: fx=%g, fz=%g, My=%g') % (pDspl.label, pDspl.where, pDspl.value['x'], pDspl.value['z'], pDspl.value['Y']) )
        return 0

    def changeElementLoad(self,load,isUndoable=False,verbose=True,masterCommands=None,**kw):
        """Change nodal load of receiver. Return False if successful, True otherwise. Possible identical label issues are controlled in :py:meth:`ElementLoad.change`
        
        :param ElementLoad|str load: element load to be changed
        :param bool isUndoable: if the action is undoable or not
        :param kw: see :py:meth:`ElementLoad.change`
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        load = self.giveElementLoad(load)
        if not load:
            logger.error( langStr('Changing of element load failed', 'Změna prvkového zatížení selhala') )
        cmdKw = {}
        cmdKw['old'] = load.dict()
        if load.change(**kw):
            # something failed in change method (e.g. identical label already exists)
            return 1
        cmdKw['new'] = load.dict()
        if isUndoable:
            command = ('change',Domain.changeElementLoad,cmdKw)
            if masterCommands is not None:
                masterCommands.append(command)
            else:
                self.session.addCommands((command,))
        if verbose:
            logger.info( langStr('Changed element load %s on element %s: fx=%g, fz=%g, dTc=%g, dTg=%g', 'Změněno prvkové zatížení %s na prvku %s: fx=%g, fz=%g, dTc=%g, dTg=%g') % (load.label, load.where, load.value['fx'], load.value['fz'], load.value['dTc'], load.value['dTg']) )
        return 0

    def changeElementLoads(self,loads,value,isUndoable=False,verbose=True,masterCommands=None):
        """Change list of element loads. Return False if successful, True otherwise.
        
        :param [ElementLoad] loads: list of loads to be changed
        :param [dict] value: new load value
        :param bool isUndoable: if the action is undoable or not
        :rtype: bool
        """
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        # loop over selected objects
        for load in loads:
            if self.changeElementLoad(load,value=value,isUndoable=isUndoable,masterCommands=commands):
                # changing failed
                return 1
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.changeElementLoads,{}))
            self.session.addCommands(commands)
        return 0


    def moveNodes(self,selection,dx,dy,dz,isUndoable=False,verbose=True,masterCommands=None):
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        changedNodes = []
        for item in selection:
            if not isinstance(item, Node):
                continue
            # move node
            coords = (item.coords[0]+dx,item.coords[1]+dy,item.coords[2]+dz) 
            if self.changeNode(item,coords=coords,verbose=False,isUndoable=isUndoable,masterCommands=commands):
                return 1
            changedNodes.append(item)
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.moveNodes,{}))
            self.session.addCommands(commands)
        if verbose:
            logger.info( langStr("Nodes","Uzly") + " %s moved by dx=%g dy=%g dz=%g"  % (", ".join(n.label for n in changedNodes),dx,dy,dz) )
        return 0

    def copyElements(self,selection,dx,dy,dz,nc,isUndoable=False,verbose=True,masterCommands=None):
        isUndoable = isUndoable and self.session
        commands = [] if masterCommands is None else masterCommands # for undoable version
        for icopy in range(nc+1):
            processedNodes = []
            # loop over selected objects
            for item in selection:
                if isinstance(item, Element):
                    logger.info( langStr("processing element: ", "zprcováván prvek: ") + item.label )
                    nodes=[]
                    #first loop over element nodes
                    for inode in item.nodes:
                        node,isNew = self.giveNewNonDuplicatedNode(inode, (inode.coords[0]+icopy*dx,inode.coords[1]+icopy*dy,inode.coords[2]+icopy*dz))
                        if isNew:
                            self.addNode(node,isUndoable=isUndoable,commands=masterCommands)
                        nodes.append(node)
                    logger.info( langStr("new nodes: ", "nové uzly: ") + str(nodes) )
                    #create new element
                    label = giveNewLabel(self.elements, 'newNum')
                    # check for duplicated element
                    ielem = self.checkDuplicatedElement (nodes)
                    if not ielem:
                        kw = dict(nodes=nodes, mat=item.mat, cs=item.cs, hinges=item.hinges, label=label)
                        self.addElement(isUndoable=isUndoable,masterCommands=commands,**kw)
                    #remember already processed nodes
                    processedNodes.extend(nodes)
        # loop over selection again, looking for standallone nodes (not connected to any selected elements)
            for item in selection:
                if isinstance(item, Node) and not item in processedNodes:
                    # copy node
                    coords = (item.coords[0]+icopy*dx,item.coords[1]+icopy*dy,item.coords[2]+icopy*dz) 
                    inode = self.checkDuplicatedPositionNode(coords)
                    if inode:
                        pass # do nothing, node already exist there
                    else:
                        label = giveNewLabel(self.nodes, 'newNum')
                        kw = dict(coords=coords, label=label, bcs=item.bcs)
                        self.addNode(isUndoable=isUndoable,masterCommands=commands,**kw)
        if isUndoable and masterCommands is None:
            commands.append(('other',Domain.copyElements,{}))
            self.session.addCommands(commands)

    def beCopyOf(self,anotherDomain,typeOfCopy='shallow'):
        """Reset receiver and copy all values from anotherDomain to receiver
        
        :param Domain anotherDomain: domain to copy from
        :param str typeOfCopy: type of copy (currently only 'shallow' option is implemented)
        """
        self.reset()
        self.delPredefinedItems()
        if typeOfCopy=='shallow':
            for mat in anotherDomain.materials.values():
                self.addMaterial(mat)
            for cs in anotherDomain.crossSects.values():
                self.addCrossSect(cs)
            for node in anotherDomain.nodes.values():
                self.addNode(node)
            for elem in anotherDomain.elements.values():
                self.addElement(elem)
            for lc in anotherDomain.loadCases.values():
                self.addLoadCase(lc)
        else:
            raise NotImplementedError

    def giveElementsWithMat(self,mat):
        """Returns elements possessing given material
        
        :param Material mat: given material
        :rtype: [Element]
        """
        return [elem for elem in self.elements.values() if elem.mat is mat]

    def giveElementsWithCS(self,cs):
        """Returns elements possessing given cross section
        
        :param CrossSection cs: given cross section
        :rtype: [Element]
        """
        return [elem for elem in self.elements.values() if elem.cs is cs]

    def giveElementsWithNode(self,node):
        """Returns elements possessing given node
        
        :param Node node: given node
        :rtype: [Element]
        """
        return [elem for elem in self.elements.values() if node in elem.nodes]

    def giveNodalLoadsOnNode(self,node,onlyActiveLC=False):
        """Returns nodal loads acting on given node
        
        :param Node node: given node
        :param bool onlyActiveLC: if True, loads only from self.activeLoadCase are retrned
        :rtype: [NodalLoad]
        """
        if isinstance(node,(str,unicode)):
            node = self.nodes.get(node)
            if not node:
                log.error( langStr('Wrong node','Špatný uzel') )
                return []
        if onlyActiveLC:
            if not self.activeLoadCase:
                logger.error( langStr('No active load case, select or create one', 'Nedefinovaný aktivní zatěžovací stav')  )
                return []
            return [load for load in self.activeLoadCase.nodalLoads.values() if load.where is node]
        return [load for lc in self.loadCases.values() for load in lc.nodalLoads.values() if load.where is node]

    def givePrescribedDsplsOnNode(self,node,onlyActiveLC=False):
        """Returns prescribed displacements acting on given node
        
        :param Node node: given node
        :param bool onlyActiveLC: if True, pDspls only from self.activeLoadCase are retrned
        :rtype: [NodalLoad]
        """
        if isinstance(node,(str,unicode)):
            node = self.nodes.get(node)
            if not node:
                log.error( langStr('Wrong node','Špatný uzel') )
                return []
        if onlyActiveLC:
            if not self.activeLoadCase:
                logger.error( langStr('No active load case, select or create one', 'Nedefinovaný aktivní zatěžovací stav')  )
                return []
            return [pDspl for pDspl in self.activeLoadCase.prescribedDspls.values() if pDspl.where is node]
        return [pDspl for lc in self.loadCases.values() for pDspl in lc.prescribedDspls.values() if pDspl.where is node]

    def giveElementLoadsOnElement(self,element,onlyActiveLC=False):
        """Returns element loads acting on given node
        
        :param Element element: given element
        :param bool onlyActiveLC: if True, loads only from self.activeLoadCase are retrned
        :rtype: [ElementLoad]
        """
        element = self.giveElement(element)
        if not element:
            logger.error( langStr('Wrong element','Špatný prvek') )
            return []
        if onlyActiveLC:
            if not self.activeLoadCase:
                logger.error( langStr('No active load case, select or create one', 'Nedefinovaný aktivní zatěžovací stav')  )
                return []
            return [load for load in self.activeLoadCase.elementLoads.values() if load.where is element]
        return [load for lc in self.loadCases.values() for load in lc.elementLoads.values() if load.where is element]

    def giveNodalLoads(self):
        """Returns list of all nodal loads from all load cases
        
        :rtype: [NodalLoad]
        """
        return [load for lc in self.loadCases.values() for load in lc.nodalLoads.values()]

    def givePrescribedDspls(self):
        """Returns list of all prescribed displacements from all load cases
        
        :rtype: [PrescribedDisplacement]
        """
        return [pDspl for lc in self.loadCases.values() for pDspl in lc.prescribedDspls.values()]

    def giveElementLoads(self):
        """Returns list of all element loads from all load cases
        
        :rtype: [ElementLoad]
        """
        return [load for lc in self.loadCases.values() for load in lc.elementLoads.values()]

    def giveLabelsOfNodalLoads(self):
        """Returns list of labels of all nodal loads from all load cases
        
        :rtype: [str]
        """
        return [key for lc in self.loadCases.values() for key in lc.nodalLoads]

    def giveLabelsOfPrescribedDspls(self):
        """Returns list of labels of all prescribed displacements from all load cases
        
        :rtype: [str]
        """
        return [key for lc in self.loadCases.values() for key in lc.prescribedDspls]

    def giveLabelsOfElementLoads(self):
        """Returns list of labels of all element loads from all load cases
        
        :rtype: [str]
        """
        return [key for lc in self.loadCases.values() for key in lc.elementLoads]

    def giveDimsOfBoundingCube(self):
        """computes dimensions of bounding cube (minimal axis aligned cube containing all nodes)
        
        :rtype: (float,float,float)
        """
        minx,maxx,miny,maxy,minz,maxz = 1e50,-1e50,1e50,-1e50,1e50,-1e50
        for node in self.nodes.values():
            c = node.coords
            if c[0] < minx: minx=c[0]
            if c[0] > maxx: maxx=c[0]
            if c[1] < miny: miny=c[1]
            if c[1] > maxy: maxy=c[1]
            if c[2] < minz: minz=c[2]
            if c[2] > maxz: maxz=c[2]
        return (maxx-minx,maxy-miny,maxz-minz)

    def giveMaxDim(self):
        """returns maximal number from bounding cube dimensions
        
        :rtype: float
        """
        return max(self.giveDimsOfBoundingCube())

    def reset(self,isUndoable=False,verbose=True,masterCommands=None):
        """Reset receiver (delete all containers etc.)
        
        :param bool isUndoable: if the action is undoable or not
        """
        isUndoable = isUndoable and self.session
        if isUndoable:
            commands = []
        for lc in list(self.loadCases.values()):
            for load in list(lc.nodalLoads.values()):
                if isUndoable:
                    commands.append(('del',Domain.delNodalLoad,load.dict()))
                self.delNodalLoad(load,verbose=False)
            for pDspl in list(lc.prescribedDspls.values()):
                if isUndoable:
                    commands.append(('del',Domain.delPrescribedDspl,pDspl.dict()))
                self.delPrescribedDspl(pDspl,verbose=False)
            for load in list(lc.elementLoads.values()):
                if isUndoable:
                    commands.append(('del',Domain.delElementLoad,load.dict()))
                self.delElementLoad(load,verbose=False)
            if isUndoable:
                commands.append(('del',Domain.delLoadCase,lc.dict()))
            self.delLoadCase(lc,verbose=False,forced=True)
        self.loadCases = {}
        for elem in list(self.elements.values()):
            if isUndoable:
                commands.append(('del',Domain.delElement,elem.dict()))
            self.delElement(elem,verbose=False)
        self.elements = {}
        for node in list(self.nodes.values()):
            if isUndoable:
                commands.append(('del',Domain.delNode,node.dict()))
            self.delNode(node,verbose=False)
        self.nodes = {}
        for mat in list(self.materials.values()):
            if isUndoable:
                commands.append(('del',Domain.delMaterial,mat.dict()))
            self.delMaterial(mat,verbose=False)
        self.materials = {}
        for cs in list(self.crossSects.values()):
            if isUndoable:
                commands.append(('del',Domain.delCrossSect,cs.dict()))
            self.delCrossSect(cs,verbose=False)
        self.crossSects = {}
        self.addPredefinedItems()
        if isUndoable:
            commands.append(('delall',Domain.reset,{}))
            self.session.addCommands(commands)
        if verbose:
            logger.info( langStr('Whole session deleted','Všechno smazáno') )

    def delete(self,verbose=True):
        """Delete receiver"""
        self.reset(verbose=verbose)
        self.delPredefinedItems()
        self.session = None

    def __str__(self):
        return self.label

    def changeActiveLoadCaseTo(self, lcLabel):
        alc = self.activeLoadCase
        self.activeLoadCase = self.loadCases.get(lcLabel,None)
        if not self.activeLoadCase:
            logger.error( langStr('Load case %s not found', 'Zatěžovací stav %s nenalezen') % (lcLabel) )
            self.activeLoadCase = alc
            return
        #logger.info( langStr('Active load case changed to %s', 'Aktivní zatěžovací stav změněn na %s') % (lcLabel) )
        session.glframe.loadCaseChoice.SetValue(self.activeLoadCase.label)

    def postLoad(self,*args,**kw):
        """Perform all needed actions after loading domain from saved file"""
        # change all node's pDspl dicts to PrescribedDisplacement instances
        pDspls = kw.get('pDspls')
        if pDspls:
            i = 0
            for node,val in pDspls.items():
                if any([float(v) for v in val.values()]): # at least one value is nonzero
                    i += 1
                    self.addPrescribedDspl(label='P_%d'%i,where=node,value=val)

    def checkDuplicatedPositionNode(self, position, tol=0.001):
        """Returns the node at given position, if exist, None otherwise"""
        (x,y,z)=position
        #simple linear search for coincident node
        for inode in self.nodes.values():
            #check for coincidence, based on coordinate differences, believed to be faster than computing distance
            if ((abs(inode.coords[0]-x)<=tol) and (abs(inode.coords[1]-y)<=tol) and (abs(inode.coords[2]-z)<=tol)):
                # node at given position already exist
                return inode
        return None

    def giveNewNonDuplicatedNode (self, node, newPosition, tol=0.001):
        """Returns the new node created at given position, cloning properties of given node,
        if there is not another node (check is made with given tolerance). 
        Otherwise, the existing node at given position is returned
        """
        inode = self.checkDuplicatedPositionNode(newPosition, tol)
        if inode:
            return inode,False
        else:
        #get next available label
            label = giveLabel(self.nodes,'newNum')
            inode = Node(label=label, coords=newPosition, bcs=node.bcs)
            return inode,True

    def checkDuplicatedElement(self, nodes):
        """Returns the element defined by the given nodes, None otherwise"""
         #simple linear search for duplicated element
        snodes = sorted(nodes)
        for ielem in self.elements.values():
            #check for coincidence, based on coordinate differences, believed to be faster than computing distance
            #quick check if at least one common node 
            if (ielem.nodes[0] in snodes):
                if (sorted(ielem.nodes) == snodes):
                    return ielem
        return None






class Solver:
    """Abstract class representing physical problem
    
    :param str label: string label of receiver
    """

    label = None
    """*(str)* string label"""
    isSolved = None
    """*(bool)* if the solver is solved or not"""
    session = None
    """*(Session)* session of receiver"""

    def __init__(self,label='solver'):
        self.label = label
        self.isSolved = False
        self.session = None

    def reset(self):
        self.isSolved = False

    def __str__(self):
        return self.label


    def lcsChanged(self):
        """ This is called when user selects another lcs; 
        the active LCS can be obtained from domain.
        Usually do nothing, but some solvers can switch to 
        self.solved=False
        """
        return


class LinearStaticSolver(Solver):
    """Class for solving linear elasticity
    
    :param str label: string label of receiver
    """

    domain = None
    """*(Domain)* domain being solved"""
    neq = None
    """*(int)* number of equations (free dofs)"""
    pneq = None
    """*(int)* number of prescribed dofs"""
    r = None
    """*({numpy.array})* dictionary of displacement vectors for each load case (keys of this dict are load cases labels)"""
    f = None
    """*({numpy.array})* dictionary of load vectors for each load case (keys of this dict are load cases labels)"""
    dofNames = None
    """*(dict)* disctionary of dof names"""

    def __init__(self,label='linearstaticsolver'):
        Solver.__init__(self,label=label)
        self.reset()
        self.neq = 0
        self.pneq = 0

    def solve(self,domain=None):
        """Solves the domain
        
        :param Domain domain: domain to be solved
        :rtype: bool
        """
        if not domain:
            if not self.session or not self.session.domain:
                print (domain, self.domain, self.session.domain)
                logger.error( langStr('LinearStaticSolver: No domain to solve...', 'Žádná síť pro řešení...') )
                return 1
        self.domain = domain if domain else self.session.domain
        # number equations first
        self.numberEquations()
        #assemble the system
        #assemble stiffness
        kuu,kpp,kup = self.assembleStiffnessMatrix()
        #check a near zero element in the stiffness matrix on the diagonal
        if self.checkStiffnessMatrixDiagonal(kuu):
            return 1
        # assemble load vector
        fu,fp = self.assembleLoadVectors()
        # set prescribed displacement
        ru,rp = self.assembleDsplVectors()
        
        # actual solving
        if self.solveLoadCases(kuu,kpp,kup,ru,rp,fu,fp):
            return 1
        
        # recover r
        self.recoverDsplVector(ru,rp)
        self.recoverLoadVector(fu,fp)
        # subtract non-nodal (continuous force and temperature loads)
        self.subtractForcesInReactions()
        #check if huge displacements exist, which points to nearly singular stiffness matrix
        if self.checkHugeDisplacements():
            return 1
        logger.info( langStr('Solution finished successfully', 'Úloha úspěšně vyřešena') )
                      
        if 0:#report output if desired
            fileHandle = open ( 'results.txt', 'w' ) 
            fileHandle.write('Node Location_array(numbers correspond to rows in stiffness matrix)\n')
            for node in sorted(self.domain.nodes.values(), key=lambda n: natural_key(n.label)):
                fileHandle.write("%s %s\n"% (node.label, node.loc))
            fileHandle.write('Reduced stiffness matrix\n')
            savetxt(fileHandle, kuu, fmt='%+1.4e', delimiter='   ')
            fileHandle.write('Determinant of reduced stiffness matrix %e\n' % linalg.det(kuu))
            fileHandle.write('Right hand side\n')
            savetxt(fileHandle, fu-dot(kup,rp), fmt='%+1.4e', delimiter='   ')
            fileHandle.write('Solution\n')
            savetxt(fileHandle, ru, fmt='%+1.4e', delimiter='   ')
            fileHandle.close()
        return 0

    def solveLoadCases(self,kuu,kpp,kup,ru,rp,fu,fp):
        lcLabels = self.domain.loadCases.keys()
        rhs = zeros((self.neq,len(lcLabels)))
        for i,lcLabel in enumerate(lcLabels):
            rhs[:,i] = fu[lcLabel] - dot(kup,rp[lcLabel])
        try:
            if self.neq>0:
                rulc = linalg.solve(kuu,rhs)
            else:
                rulc = zeros((0,len(lcLabels)))
            self.isSolved = True
        except (ValueError,linalg.LinAlgError):
            logger.error( langStr('Solution of linear system failed, wrong boundary conditions (supports)?', 'Řešení lineárního systému selhalo, chybně zadané okrajové podmínky (podpory)?') )
            self.isSolved = False
            return 1
        for i,lcLabel in enumerate(lcLabels):
            ru[lcLabel] = rulc[:,i]
            if self.pneq > 0:
                fp[lcLabel] = dot(kup.transpose(),ru[lcLabel]) + dot(kpp,rp[lcLabel])
        return 0

    def checkHugeDisplacements(self):
        """TODO
        
        :rtype: bool
        """
        locProblems = []
        nodeProblems = []
        MaxDisplacement = 0.
        for r in self.r.values():
            for i in range(r.shape[0]):
                if abs(r[i]) > 1.e+6:
                    locProblems.append(i)
                    if abs(r[i]) > abs(MaxDisplacement):
                        MaxDisplacement = abs(r[i])
        for j in locProblems:
            for node in self.domain.nodes.values():
                if node.loc.count(j):
                    if node.label not in nodeProblems:
                        nodeProblems.append(node.label)    
        #
        ret = 0
        if locProblems:
            nodeProblemsSorted = sorted(nodeProblems, key=lambda n: natural_key(n))
            if session.glframe: # we are in GUI
                from ebgui import wx
                dlg = wx.MessageDialog(parent=None, message=(langStr('Huge displacement %g within nodes: %s. Could be missing supports. Do you agree with such huge displacements?', 'Velká deformace %g nalezena mezi uzly %s. Pravděpodobně chybné podepření. Schvalujete takovéto velké deformace?') % (MaxDisplacement, ', '.join(nodeProblemsSorted))), caption=(langStr('Huge displacements','Velké deformace')), style=wx.YES_NO|wx.NO_DEFAULT)
                try:
                    result = dlg.ShowModal()
                    if  result == wx.ID_NO:
                        self.isSolved = False
                        ret = 1
                finally:
                    dlg.Destroy()
            else: # no GUI
                logger.warning( langStr("Huge displacement %g within nodes: %s. Could be missing supports", "Velká deformace %g nalezena mezi uzly %s. Pravděpodobně chybné podepření") % (MaxDisplacement, ', '.join(nodeProblemsSorted)) )
        return ret

    def subtractForcesInReactions(self):
        """TODO
        
        """
        for lc in self.domain.loadCases.values():
            flc = self.f[lc.label]
            #substract element loads in reactions
            for load in lc.elementLoads.values():
                (loc,value) = load.computeLoad(self.domain.type)
                size = len(loc)
                for i in range(size):
                    ii = loc[i]
                    if ii>=self.neq:
                        flc[ii] -= value[i]
            #substract nodal load acting in supported DOFs to account direct transfer of those into reaction force
            for load in lc.nodalLoads.values():
                (loc, value) = load.computeLoad(self.domain.type)
                size = len(loc)
                for i in range(size):
                    ii=loc[i]
                    if ii>=self.neq:
                        flc[ii] -= value[i]

    def recoverDsplVector(self,ru,rp):
        """TODO
        
        :param np.array ru: displacement vector of free DOFs
        :param np.array rp: displacement vector of prescribed DOFs
        """
        self.r = {}
        for lc in self.domain.loadCases.values():
            rlc = zeros(self.neq+self.pneq)
            rlc[0:self.neq] = ru[lc.label]
            rlc[self.neq:self.pneq+self.neq] = rp[lc.label]
            self.r[lc.label] = rlc

    def recoverLoadVector(self,fu,fp):
        """TODO
        
        :param np.array fu: load vector of free DOFs
        :param np.array fp: load vector of prescribed DOFs
        """
        self.f = {}
        for lc in self.domain.loadCases.values():
            flc = zeros(self.neq+self.pneq)
            flc[0:self.neq] = fu[lc.label]
            flc[self.neq:self.pneq+self.neq] = fp[lc.label]
            self.f[lc.label] = flc

    def checkStiffnessMatrixDiagonal(self,kuu):
        """Checks if there are 0 on diagonal. Returns True if yes, False if it is OK
        
        :param np.array(2d) kuu: matrix to be checked
        :rtype: bool
        """
        for i in range(kuu.shape[1]):
            if kuu[i,i]<1.e-8:
                for node in self.domain.nodes.values():
                    if node.loc.count(i):
                        break
                logger.warning( langStr('Stiffness matrix has zero element on diagonal position [%d,%d], check node %s','Matice tuhosti má nulový prvek na pozici diagonály [%d,%d], zkontrolujte uzel %s') % (i,i,node.label) )
                self.isSolved = False
                return 1
        return 0

    def assembleLoadVectors(self):
        """Assembles load vectors, returns (fu,fp), u stands for free DOFs, p for supported DOFs
        
        :rtype: (np.array,np.array,np.array)
        """
        # TODO
        fu = {}
        fp = {}
        for lc in self.domain.loadCases.values():
            fulc = zeros(self.neq)
            fplc = zeros(self.pneq)
            for container in (lc.nodalLoads,lc.elementLoads):
                for load in container.values():
                    loc,value = load.computeLoad(self.domain.type)
                    size = len(loc)
                    for i in range(size):
                        ii = loc[i]
                        if ii < self.neq:
                            fulc[ii] += value[i]
            fu[lc.label] = fulc
            fp[lc.label] = fplc
        return fu,fp

    def assembleDsplVectors(self):
        """Assembles displacement vectors, returns (ru,rp), u stands for free DOFs, p for supported DOFs
        
        :rtype: (np.array,np.array,np.array)
        """
        ru = {}
        rp = {}
        for lc in self.domain.loadCases.values():
            rulc = zeros(self.neq)
            rplc = zeros(self.pneq)
            #
            for pDspl in lc.prescribedDspls.values():
                loc,value = pDspl.computeLoad(self.domain.type)
                size = len(loc)
                for i in range(size):
                    ii = loc[i]
                    if ii >= self.neq:
                        rplc[ii-self.neq] = value[i] # NOT += ???
            ru[lc.label] = rulc
            rp[lc.label] = rplc
        return ru,rp

    def assembleStiffnessMatrix(self):
        """Assembles stiffness matrix, returns (kuu,kpp,kup), u stands for free DOFs, p for supported DOFs
        
        :rtype: (np.array,np.array,np.array)
        """
        kuu = zeros((self.neq,self.neq))
        kpp = zeros((self.pneq,self.pneq))
        kup = zeros((self.neq,self.pneq))
        for elem in self.domain.elements.values():
            loc = elem.giveLocationArray()
            k = elem.computeStiffness()
            size=len(loc)
            for i in range(size):
                ii = loc[i]
                if ii<self.neq:
                    for j in range(size):
                        jj = loc[j]
                        if jj<self.neq:
                            kuu[ii,jj] += k[i,j]
                        else:
                            kup[ii,jj-self.neq] += k[i,j]
                else:   #ii>=neq prescribed row
                    for j in range(size):
                        jj = loc[j]
                        if jj>=self.neq:
                            kpp[ii-self.neq,jj-self.neq] += k[i,j]
        return kuu,kpp,kup
        
    def numberEquations(self):
        self.neq = 0
        self.pneq = 0
        # loop over nodes and count equations
        for node in self.domain.nodes.values():
            for idof in self.domain.dofsNames:
                if node.hasPrescribedBcInDof(idof): # active support
                    self.pneq += 1
                else:
                    self.neq += 1
        #assign code numbers in 2nd pass
        ineq = 0 # unknowns numbering starts from 0..neq-1
        ipneq = self.neq #prescribed unknowns numbering starts neq..neq+pneq-1
        for node in self.domain.nodes.values():
            nodeLoc = []
            for idof in self.domain.dofsNames:
                if node.hasPrescribedBcInDof(idof): # support
                    nodeLoc.append(ipneq)
                    ipneq += 1
                else:
                    nodeLoc.append(ineq)
                    ineq += 1
            node.loc = nodeLoc
        logger.info( langStr('Number of equations (unknowns): %d\nNumber of prescribed DOFs: %d','Počet rovnic (neznámých): %d\nPočet předepsaných stupňů volnosti: %d') % (self.neq, self.pneq) )
        # node names
        self.dofNames = dict( (i,'') for i in range(self.neq+self.pneq) )
        for node in self.domain.nodes.values():
            self.dofNames[node.loc[0]] = node.label+'_x'
            self.dofNames[node.loc[1]] = node.label+'_z'
            self.dofNames[node.loc[2]] = node.label+'_Y'

    def giveActiveSolutionVector(self):
        # when combination of LCS active, shoud return combined solution vector
        if self.isSolved:
            return self.r[self.domain.activeLoadCase.label]
        else:
            return None



try:
    import scipy.linalg as LA
except ImportError as e:
    print(e)
    raise

class LinearStabilitySolver(Solver):
    """ Class implementing solver for linear stability problem
    """
    domain = None
    """*(Domain)* domain being solved"""
    linsolver = None
    """ Linear solver instance"""
    eigval = None
    """ eigen values (critical load levels)"""
    eigvec = None
    """ eigen vectors"""
    activeEigVal = 0
    """ active eigen value"""

    def __init__(self,label='linearstabilitysolver'):
        Solver.__init__(self,label=label)
        self.linsolver = LinearStaticSolver()
        self.reset()

    def solve(self,domain=None):
        """Solves the domain
        :param Domain domain: domain to be solved
        :rtype: bool
        """
        print ("LinearStabilitySolver::solve ", session, session.domain)
        if not domain:
            if not self.session or not self.session.domain:
                logger.error( langStr('LinearStabilitySolver: No domain to solve...', 'Žádná síť pro řešení...') )
                return 1
        self.domain = domain if domain else self.session.domain
        # solve the linear system first
        self.linsolver.solve(self.domain)
        # 
        # actual solving
        try:
            # assemble the system 
            k_uu,k_pp,k_up = self.linsolver.assembleStiffnessMatrix() # assemble stifness again (better reused form linsolver)
            ks_uu = self.assembleInitialStressMatrix(self.linsolver.r[session.domain.activeLoadCase.label]) # can throw value error
            self.eigval, self.eigvec =LA.eig(k_uu, ks_uu, left=False, right=True, overwrite_a=False, overwrite_b=False)
        except LA.LinAlgError as error:
            logger.error( langStr('Eigen problem solution failed\n', 'Chyba při řešení problému vlastních čísel\n') + str(error))
            self.isSolved = False
            return 1
        except ValueError as error:
            logger.error( langStr('Eigen problem solution failed\n', 'Chyba při řešení problému vlastních čísel\n') + str(error))
            self.isSolved = False
            return 1
           

        #sort eigenvalues and eigenvectors
        abseig=absolute(self.eigval)
        idx = abseig.argsort()   
        self.eigval = self.eigval[idx]
        self.eigvec = self.eigvec[:,idx]

        logger.info( langStr('Solution finished successfully', 'Úloha úspěšně vyřešena') )
        self.isSolved = True
        #print "Eigen values: ", self.eigval
                
    def recoverDsplVector(self,ru,rp):
        """TODO
        
        :param np.array ru: displacement vector of free DOFs
        :param np.array rp: displacement vector of prescribed DOFs
        """
        self.r = {}
        for lc in self.domain.loadCases.values():
            rlc = zeros(self.neq+self.pneq)
            rlc[0:self.neq] = ru[lc.label]
            rlc[self.neq:self.pneq+self.neq] = rp[lc.label]
            self.r[lc.label] = rlc

    def assembleInitialStressMatrix(self, r):
        """Assembles initial stress matrix, returns (ks_uu), u stands for part with free DOFs only
        :rtype: (np.array)
        """
        neq = self.linsolver.neq
        ks_uu = zeros((neq,neq))

        # get minimun nonzero normal element force
        _init = True
        minn = 0.0 # minn will be set to the first nonzero normal force; this is to handle the case when all normal forces are zero.
        elemn=[] # element nodal forces
        for elem in self.domain.elements.values():
            # compute average normal force on element
            nn = elem.computeNormalForce(self.linsolver.r[session.domain.activeLoadCase.label])
            n = 0.5*(nn[0]-nn[1]) # take an average value
            if abs(n) > 0.0:
                if _init:
                    minn = n
                    _init=False
                else:
                    minn = min(minn, abs(n))
            elemn.append(n)

        if minn <= 1.e-8:
            raise ValueError(langStr('Linear Stability: problem may be ill-posed (zero normal forces)\n', 'Problém může být špatně podmíněný (nulové normálové síly\n'))
        
        _i=0
        for elem in self.domain.elements.values():
            loc = elem.giveLocationArray()
            n = elemn[_i] # take cached value
            _i = _i+1 
            if abs(n) < minn:
                n = minn

            # print "n=", n
            k = elem.computeInitialStressMatrix(N=n)
            size=len(loc)
            for i in range(size):
                ii = loc[i]
                if ii<neq:
                    for j in range(size):
                        jj = loc[j]
                        if jj<neq:
                            ks_uu[ii,jj] += k[i,j]
        return ks_uu

    def giveActiveSolutionVector(self):
        if self.isSolved:
            r=zeros(self.linsolver.neq+self.linsolver.pneq)
            r[0:self.linsolver.neq] = self.eigvec[:, self.activeEigVal]
            return r
        else:
            return None

    def giveActiveEigenValue(self):
        if self.isSolved:
            return self.eigval[self.activeEigVal]
        return None
        
    def lcsChanged(self):
         self.reset()



class Session:
    """Class representing user session
    
    This class contains also history of commands
    to be able to undo/redo them. Session.commands
    has following structure:
    
    .. code-block:: python
    
        Session.commands = [
          [
            [ ['add', Domain.addNode, node.dict] ], 
            time,
            localtime
          ],
          [
            [ ['add', Domain.addNode, node.dict] ],
            time,
            localtime
          ],
          [
            [ ['add', Domain.addElement, element.dict] ],
            time,
            localtime
          ],
          [
            [
              ['del', Domain.delElement, element.dict], # before deleting node, all its elements are deleted, which is reflected here
              ['del', Domain.delNode, node.dict]
            ],
            time,
            localtime
          ]
    """

    inverseCommandMap = {
        Domain.addMaterial       : Domain.delMaterial,
        Domain.addCrossSect      : Domain.delCrossSect,
        Domain.addNode           : Domain.delNode,
        Domain.addElement        : Domain.delElement,
        Domain.addLoadCase       : Domain.delLoadCase,
        Domain.addNodalLoad      : Domain.delNodalLoad,
        Domain.addPrescribedDspl : Domain.delPrescribedDspl,
        Domain.addElementLoad    : Domain.delElementLoad,
        #
        Domain.delMaterial       : Domain.addMaterial,
        Domain.delCrossSect      : Domain.addCrossSect,
        Domain.delNode           : Domain.addNode,
        Domain.delElement        : Domain.addElement,
        Domain.delLoadCase       : Domain.addLoadCase,
        Domain.delNodalLoad      : Domain.addNodalLoad,
        Domain.delPrescribedDspl : Domain.addPrescribedDspl,
        Domain.delElementLoad    : Domain.addElementLoad,
    }
    """*(dict)* dictionary of commands and their inverse (for undo/redo)"""

    commandNames = {
        Domain.addMaterial       : langStr('add material','přidat materiál'),
        Domain.addCrossSect      : langStr('add cross section','přidat průřez'),
        Domain.addNode           : langStr('add node','přidat uzel'),
        Domain.addElement        : langStr('add element','přidat prvek'),
        Domain.addLoadCase       : langStr('add load case','přidat zatěžovací stav'),
        Domain.addNodalLoad      : langStr('add nodal load','přidat uzlové zatížení'),
        Domain.addPrescribedDspl : langStr('add prescribed displacement','přidat předepsané přemístění'),
        Domain.addElementLoad    : langStr('add element load','přidat prvkové zatížení'),
        #
        Domain.delMaterial       : langStr('delete material','smazat materiál'),
        Domain.delCrossSect      : langStr('delete cross section','smazat průřez'),
        Domain.delNode           : langStr('delete node','smazat uzel'),
        Domain.delElement        : langStr('delete element','smazat prvek'),
        Domain.delLoadCase       : langStr('delete load case','smazat zatěžovací stav'),
        Domain.delNodalLoad      : langStr('delete nodal load','smazat uzlové zatížení'),
        Domain.delPrescribedDspl : langStr('delete prescribed displacement','smazat předepsané přemístění'),
        Domain.delElementLoad    : langStr('delete element load','smazat prvkové zatížení'),
        #
        Domain.changeMaterial       : langStr('change material','změnit materiál'),
        Domain.changeCrossSect      : langStr('change cross section','změnit průřez'),
        Domain.changeNode           : langStr('change node','změnit uzel'),
        Domain.changeElement        : langStr('change element','změnit prvek'),
        Domain.changeLoadCase       : langStr('change load case','změnit zatěžovací stav'),
        Domain.changeNodalLoad      : langStr('change nodal load','změnit uzlové zatížení'),
        Domain.changePrescribedDspl : langStr('change prescribed displacement','změnit předepsané přemístění'),
        Domain.changeElementLoad    : langStr('change element load','změnit prvkové zatížení'),
        #
        Domain.moveNodes    : langStr('move nodes', 'přesunout uzly'),
        Domain.copyElements : langStr('copy elements', 'kopírovat prvky'),
        Domain.changeNodes  : langStr('change nodes', 'upravit uzly'),
        Domain.delNodes     : langStr('delete nodes', 'smazat uzly'),
        Domain.changeElements  : langStr('change elements', 'upravit prvky'),
        Domain.delElements     : langStr('delete elements', 'smazat prvky'),
        Domain.changeNodalLoads : langStr('change nodal loads', 'změnit uzlová zatížení'),
        Domain.delNodalLoads : langStr('delete nodal loads', 'smazat uzlová zatížení'),
        Domain.changeElementLoads : langStr('change element loads', 'změnit prvková zatížení'),
        Domain.delElementLoads : langStr('delete element loads', 'smazat prvková zatížení'),
        #
        Domain.reset : langStr('delete all','smazat všechno'),
    }
    """*(dict)* dictionary of command names (for undo/redo)"""

    commands = []
    """*(list)* List of command history"""
    commandsCounter = 0
    """*(int)* Commands counter (to track undo/redo)"""
    savedAtCounter = 0
    """*(int)* Laber indicating if and when the session was saved"""
    domain = None
    """*(Domain)* possessed domain"""
    solver = None
    """*(Solver)* possessed solver"""
    label = None
    """*(str)* string label"""
    glframe = None
    """*(GLFrame)* glframe associated with session. Also indicates presence of GUI"""

    def __init__(self,domain=None,solver=None,label='session'):
        self.label = label
        self.domain = domain
        if self.domain:
            self.domain.session = self
        self.solver = solver
        if self.solver:
            self.solver.session = self

    def setDomain(self,domain):
        """Assignes given domain to receiver
        
        :param Domain domain: given domain
        """
        if self.domain:
            self.domain.delete(verbose=False)
        self.domain = domain
        if self.domain:
            self.domain.session = self

    def setSolver(self, solver):
        """Sets session solver"""
        print ("Setting solver: old solver:", self.solver)
        self.solver = solver
        self.solver.session = self
        if self.solver:
            self.solver.domain = self.domain
            print ("Setting solver: ", self.solver, " domain: ", self.domain)
            self.solver.reset()
        

    def setGLFrame(self,glframe):
        """Assignes given glframe
        
        :param GLFrame glframe: given glframe
        """
        self.glframe = glframe

    def updateGLFrame(self):
        """Sets frame title according to saved.unsaved state and update loadCaseChoice"""
        if not self.glframe:
            return
        self.glframe.setFrameTitle(not self.isSaved())
        self.glframe.updateLoadCaseChoice()
        
    def resetCommnads(self):
        """Resets all commands history"""
        self.commands = []
        self.commandsCounter = 0
        self.savedAtCounter = 0 # session is considered as saved now

    def addCommands(self,commands):
        """Add commands to history (for undo/redo)
        
        :param list commands: commands to be added, in format [[[str,Domain.someMethod,dict]]]. See `Session`_ for example
        """
        if len(self.commands) != self.commandsCounter:
            # if new command is added, delete all redo actions from now on ...
            self.commands = self.commands[:self.commandsCounter]
            # ... and forget saved position if saved in deleted commands as it exists no longer
            if len(self.commands) < self.savedAtCounter:
                self.savedAtCounter = -1
        t = time.time()
        lt = time.localtime()
        self.commands.append((commands,t,lt))
        self.commandsCounter += 1
        self.updateGLFrame()

    def undo(self):
        """Undo one step"""
        if not self.canUndo():
            logger.info( langStr('No action to undo','Žádná akce, která by šla vzít zpět') )
            return
        if self.glframe:
            self.glframe.resetSolverAndPostprocessBox()
        commandType, name = self.giveTypeAndNameOfUndo()
        self.commandsCounter -= 1 # sets commandsCounter to item to be undone
        commands,t,lt = self.commands[self.commandsCounter] # set of commands
        msg = langStr('Undo: ','Zpět: ')
        if name:
            msg += name
        i = len(commands)
        while i:
            # undo set of commands (e.g. while deleting node, all its elements have to be deleted before and while undoing they have to be added afterwards
            i -= 1
            command = commands[i]
            self.doInverseCommand(command)
        # time
        dt = time.time() - t
        if dt > 90.:
            msg += langStr(' at',' v') + ' %02dh:%02dm:%02ds'%(lt[3],lt[4],lt[5])
        else:
            msg += langStr(' %d seconds ago',' před %d vteřinami') % dt
        logger.info( msg )
        # update GLFrame
        self.updateGLFrame()

    def redo(self):
        """Redo one step"""
        if not self.canRedo():
            logger.info( langStr('No action to redo','Žádná akce vpřed') )
            return
        if self.glframe:
            self.glframe.resetSolverAndPostprocessBox()
        commands,t,lt = self.commands[self.commandsCounter]
        msg = langStr('Redo: ','Vpřed: ')
        commandType, name = self.giveTypeAndNameOfRedo()
        if name:
            msg += name
        self.redoExtras(commandType)
        for command in commands:
            self.doCommand(command)
        self.commandsCounter += 1 # sets commandsCounter to next action
        dt = time.time() - t
        if dt > 90.:
            msg += langStr(' at',' v') + ' %02dh:%02dm:%02ds'%(lt[3],lt[4],lt[5])
        else:
            msg += langStr(' %d seconds ago',' před %d vteřinami') % dt
        logger.info( msg )
        self.updateGLFrame()

    def doCommand(self,command):
        """Execute given command"""
        type,cmd,kw = command
        if   type == 'add':
            cmd(self.domain,verbose=False,**kw)
        elif type == 'del':
            cmd(self.domain,kw['label'],verbose=False)
        elif type == 'change':
            cmd(self.domain,kw['old']['label'],verbose=False,**kw['new'])
        elif type == 'delall':
            pass
        elif type == 'other':
            pass

    def doInverseCommand(self,command):
        """Execute inverse of given command"""
        type,cmd,kw = command
        if   type == 'add':
            self.inverseCommandMap[cmd](self.domain,kw['label'],verbose=False)
        elif type == 'del':
            self.inverseCommandMap[cmd](self.domain,verbose=False,**kw)
        elif type == 'change':
            cmd(self.domain,kw['new']['label'],verbose=False,**kw['old'])
        elif type == 'delall':
            self.domain.delPredefinedItems()
        elif type == 'other':
            pass

    def giveTypeAndNameOfUndo(self):
        """Returns type and name of undo action according to :py:attr:`Session.commandNames`
        
        :rtype: (str,str)
        """
        if not self.canUndo():
            return '','' # we are in the beginning
        type,cmd,kw = self.commands[self.commandsCounter-1][0][-1]
        return type, self.commandNames.get(cmd, '')

    def giveTypeAndNameOfRedo(self):
        """Returns name of redo action according to :py:attr:`Session.commandNames`
        
        :rtype: (str,str)
        """
        if not self.canRedo():
            return '','' # we are at the end
        type,cmd,kw = self.commands[self.commandsCounter][0][-1]
        return type, self.commandNames.get(cmd, '')

    def giveNameOfUndo(self):
        """Returns type and name of undo action according to :py:attr:`Session.commandNames`
        
        :rtype: str
        """
        return self.giveTypeAndNameOfUndo()[1]

    def giveNameOfRedo(self):
        """Returns name of undo action according to :py:attr:`Session.commandNames`
        
        :rtype: str
        """
        return self.giveTypeAndNameOfRedo()[1]

    def giveTypeOfUndo(self):
        if not self.canUndo():
            return None # we are in the beginning
        return self.commands[self.commandsCounter-1][0][-1][1]
 
    def giveTypeOfRedo(self):
        if not self.canRedo():
            return '' # we are at the end
        return self.commands[self.commandsCounter][0][-1][1]

    def canUndo(self):
        """Returns True if receiver can undo an action, False otherwise
        
        :rtype: bool
        """
        return self.commandsCounter > 0

    def canRedo(self):
        """Returns True if receiver can redo an action, False otherwise
        
        :rtype: bool
        """
        return self.commandsCounter < len(self.commands)

    def undoExtras(self,type):
        """Performs some extra actions needed before actual undo command

        :param function name: type of action
        """
        pass

    def redoExtras(self,type):
        """Performs some extra actions needed before actual redo command

        :param function name: type of action
        """
        if type is 'delall':
            self.domain.addPredefinedItems()


    def isSaved(self):
        """Returns True if receiver is saved, False otherwise
        
        :rtype: bool
        """
        if self.commandsCounter == self.savedAtCounter:
            return True
        else:
            return False

    def setAsSaved(self):
        """Sets receiver to be saved"""
        self.savedAtCounter = self.commandsCounter

    def save(self,file):
        """Save session to defines file

        :param file|str file: opened file for writing or file name
        """
        try:
            if not hasattr(file,'write'):
                file = open(file,'wb')
            if file.name.lower().endswith('.xml'):
                from ebio import xmlStringFromDomain
                file.write(xmlStringFromDomain(self.domain))
            elif file.name.lower().endswith('oofem'):
                from ebio import OofemFileWriter
                OofemFileWriter(file).write(self.domain,fileName)
                file.close()
            else:
                logger.error( langStr('Wrong file format %s', 'Špatný formát souboru %s') % (file.name) )
                return True
            logger.info( langStr('Session successfully saved to file %s','Úloha úspěšně uložena do souboru %s') % (file.name) )
            return False
        except Exception:
            logger.error( langStr('Error during writing data', 'Chyba v průběhu zapisování dat') )
            import traceback
            logger.error( traceback.format_exc() )
            return True

    def load(self,file):
        """Loads session from file. Returns False if ok, True otherwise

        :param file|str file: opened file for reading or file name
        :rtype: bool
        """
        try:
            if not hasattr(file,'write'):
                file = open(file,'rb')
            if file.name.lower().endswith('.xml'):
                from ebio import loadDomainFromXmlFile
                newDomain = loadDomainFromXmlFile(file)
            elif file.name.lower().endswith('.oofem'):
                from ebio import OofemFileReader
                newDomain = OofemFileReader(file).read()
            else:
                logger.error( langStr('Wrong file format', 'Chybný fotmát souboru') ) 
                return True
            logger.info( langStr('File %s loaded successfully'%str(file.name),'Soubor %s úspěšně načten'%str(file.name)) )
            self.setDomain(newDomain)
            return False
        except Exception:
            logger.error( langStr('Corrupted input data', 'Chybná vstupní data') )
            import traceback
            logger.error( traceback.format_exc() )
            return True
  
    def __str__(self):
        return self.label




##################################################################
#
# initial instantiation of session
#
##################################################################
domain = Domain()
solver = LinearStaticSolver()
session = Session(domain=domain,solver=solver)
