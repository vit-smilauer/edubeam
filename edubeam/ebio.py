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
# ebio.py file
# this file provides input/output functions, particulary
# functions for saving and loading sessions to/from various
# formats
#
##################################################################

"""
EduBeam module providing input/output functionality
"""

from ebinit import version, EduBeamError, logger, langStr
import os
import sys

##################################################
#
# general I/O classes
#
##################################################
class FileReader:
    """Abstract class for file reading
    
    :param file file: file name or opened file for reading
    """
    def __init__(self,file):
        self.file = file
        self.line = None
        self.lineSplit = []   
    def readLine(self,splitStr=None):
        self.line = self.file.readline()
        self.lineSplit = self.line.split(splitStr)
        return self.line
    def close(self):
        self.file.close()
    def readChar(self):
        return self.file.read(1)

class FileWriter:
    """Abstract class for file writing
    
    :param file file: file name or opened file for writing
    """
    def __init__(self,file):
        if hasattr(file,'write'):
            self.file = file
        else:
            self.file = open(file,'w')
    def writeLine(self,string=''):
        self.file.write(string)
        self.file.write('\n')
    def writeLines(self,lines):
        for line in lines:
            self.writeLine(line)
    def close(self):
        self.file.close()


##################################################
#
# config I/O
#
##################################################
def loadConfiguration(fileName='eb.cfg'):
    """Loads saved setup (colors etc.)
    
    :param str fileName: named of file where setup is saved (default is ~/.eb.cfg)
    :rtype: EduBeamSettings
    """
    try:
        # http://python-forum.com/pythonforum/viewtopic.php?f=3&t=8190&p=38102
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        # http://docs.python.org/library/sys.html#sys.platform
        platform = sys.platform
        if platform == 'linux2': # hidden file on linux system
            fileName = '.'+fileName
        path = os.path.join(home,fileName)
        with open(path, 'r') as f:
            try:
                import xml.etree.ElementTree as et
                tree = et.ElementTree()
                tree.parse(f)
                f.close()
                dicts = {}
                root = tree.getroot()
                for settingDict in root:
                    dct = {}
                    for setting in settingDict:
                        dct[setting.tag] = eval(setting.get('val'))
                    dicts[settingDict.tag] = dct
            except Exception:
                from ebinit import langStr
                logger.error( langStr('Corrupted input data', 'Chybná vstupní data') )
                import traceback
                logger.error( traceback.format_exc() )
                return {}
            return dicts
    except IOError:
        return {}

def saveConfiguration(dicts,fileName='eb.cfg'):
    """Saves setup (colors etc.) to given file. Returs False if ok, True otherwise
    
    :param tuple(dict) dicts: dictionaries of global settings to be saved (globalSettings, globalGridSettings, globalSizesScales, globalFlags)
    :param str fileName: named of file to save setup (default is ~/eb.cfg)
    :returns: *(bool)* blablabla bla
    """
    globalSettings = {}
    globalGridSettings  = {}
    globalSizesScales  = {}
    globalFlags = {}
    
    try:
        # http://python-forum.com/pythonforum/viewtopic.php?f=3&t=8190&p=38102
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        # http://docs.python.org/library/sys.html#sys.platform
        platform = sys.platform
        if platform == 'linux2': # hide eb.cfg on linux system
            fileName = '.'+fileName
        path = os.path.join(home,fileName)
        with open(path, 'w') as f:
            import xml.dom.minidom
            import time
            t = time.localtime()
            f.write('<?xml version="1.0" ?>\n<!--\nEduBeam settings\nsaved in version %s on %04d-%02d-%02d at %02dh:%02dm:%02ds\n-->\n'%(version,t[0],t[1],t[2],t[3],t[4],t[5]))
            f.write('<settings>\n')
            # globalSettings
            f.write('\t<globalSettings>\n')
            for key,val in globalSettings.items():
                f.write('\t\t<%s val="%s"/>\n'%(key,val))
            f.write('\t</globalSettings>\n')
            # globalGridSettings
            f.write('\t<globalGridSettings>\n')
            for key,val in globalGridSettings.items():
                f.write('\t\t<%s val="%s"/>\n'%(key,val))
            f.write('\t</globalGridSettings>\n')
            # globalSizesScales
            f.write('\t<globalSizesScales>\n')
            for key,val in globalSizesScales.items():
                f.write('\t\t<%s val="%s"/>\n'%(key,val))
            f.write('\t</globalSizesScales>\n')
            # globalFlags
            f.write('\t<globalFlags>\n')
            for key,val in globalFlags.items():
                f.write('\t\t<%s val="%s"/>\n'%(key,val))
            f.write('\t</globalFlags>\n')
            #
            f.write('</settings>\n')
            #
            f.close()
        if platform == 'win32':
            try:
                os.popen('attrib +h %s'%fileName) # hide eb.cfg on Windows
                # TODO need to be tested
            except:
                pass
        return 0
    except IOError:
        return 1



##################################################
#
# XML support
#
##################################################

def xmlStringFromDomain(domain):
    """Returs xml representation of passed Domain
    
    :param Domain domain: given domain
    :rtype: str
    """
    import xml.dom.minidom
    import time
    from ebinit import smart_str
    #
    def createDomElem(name,attrs={},parent=None):
        ret = doc.createElement(name)
        parent = parent if parent else doc
        parent.appendChild(ret)
        for attr,val in attrs.items():
           #encoding and decoding does not work here for non-ASCII characters. It is necessary to return a byte string.
           #print(smart_str(attr), type(smart_str(attr)), smart_str(val), type(smart_str(val)))
           attrS = smart_str(attr)
           valS = smart_str(val) 
           #ret.setAttribute('1', '2')
           #Need to pass everything as strings, not bytes
           ret.setAttribute( attrS.decode() if isinstance(attrS, bytes) else attrS, valS.decode() if isinstance(valS, bytes) else valS )
        return ret

    t = time.localtime()
    doc = xml.dom.minidom.Document()
    doc.appendChild(doc.createComment('\nEduBeam session\nsaved in version %s on %04d-%02d-%02d at %02dh:%02dm:%02ds\n'%(version,t[0],t[1],t[2],t[3],t[4],t[5])))
    
    session = createDomElem('session',{'version':version})
    d = createDomElem('domain',dict(cName=domain.__class__.__name__),parent=session)
    materials = createDomElem('materials',parent=d)
    for m in domain.materials.values():
        createDomElem(m.__class__.__name__,m.dict(),materials)
    crossSects = createDomElem('crossSects',parent=d)
    for cs in domain.crossSects.values():
        createDomElem(cs.__class__.__name__,cs.dict(),crossSects)
    nodes = createDomElem('nodes',parent=d)
    for n in domain.nodes.values():
        createDomElem(n.__class__.__name__,n.dict(),nodes)
    elements = createDomElem('elements',parent=d)
    for e in domain.elements.values():
        createDomElem(e.__class__.__name__,e.dict(),elements)
    loadCases = createDomElem('loadCases',parent=d)
    for lc in domain.loadCases.values():
        lcDom = createDomElem(lc.__class__.__name__,lc.dict(),loadCases)
        for container in (lc.nodalLoads,lc.elementLoads,lc.prescribedDspls):
            for val in container.values():
                createDomElem(val.__class__.__name__,val.dict(),lcDom)
    return doc.toprettyxml(encoding="utf-8") # do not use utf-8 as a parameter: encoding='utf-8'


def loadDomainFromXmlFile(f,newDomain=None):
    """Returns newDomain as a result of parsed xmlString structure
    
    :param file f: opend file-like object with saved domain
    :param Domain newDomain: if not None, the xml file is parsed to newDomain. Else new Domain object is created and returned
    :rtype: Domain
    """
    import xml.etree.ElementTree as et
    from ebfem import Domain,Material,CrossSection,Node,Beam2d,NodalLoad,ElementLoad,LoadCase
    tree = et.ElementTree()
    tree.parse(f)
    session = tree.getroot()
    domain = session.find('domain')
    materials    = domain.find('materials')
    crossSects   = domain.find('crossSects')
    nodes        = domain.find('nodes')
    elements     = domain.find('elements')
    domainNodalLoads   = domain.find('nodalLoads') # version 2.2.6
    domainElementLoads = domain.find('elementLoads') # version 2.2.6
    loadCases = domain.find('loadCases')
    newDomain = newDomain if newDomain else Domain()
    newDomain.reset(verbose=False)
    newDomain.delPredefinedItems()
    pDspls = {} # for version 2.2.6
    #
    # default values are for backward compatibility
    for m in materials:
        if m.tag == 'Material':
            label = m.get('label')
            e     = m.get('e')
            alpha = m.get('alpha')
            g = m.get('g',e)
            d = m.get('d')
            newDomain.addMaterial(label=label ,e=e, g=g, alpha=alpha, d=d, verbose=False)
    for cs in crossSects:
        if cs.tag == 'CrossSection':
            label = cs.get('label')
            a     = cs.get('a')
            iy    = cs.get('iy')
            iz    = cs.get('iz',1)
            dyz   = cs.get('dyz',0)
            h     = cs.get('h')
            k     = cs.get('k',1e12) # set k to very hifh number if not present, for backward compatibility
            newDomain.addCrossSect(label=label, a=a, iy=iy, iz=iz, dyz=dyz, h=h, k=k,verbose=False)
    for n in nodes:
        if n.tag == 'Node':
            label  = n.get('label')
            coords = n.get('coords')
            bcs    = n.get('bcs')
            pDspl  = n.get('pDspl')
            if coords:
                coords = list(eval(coords))
            if bcs:
                bcs = eval(bcs)
                if isinstance(bcs,(list,tuple)): # version 2.2.6
                    bcs = {'x':bcs[0],'z':bcs[1],'Y':bcs[2]}
            newDomain.addNode(label=label, coords=coords, bcs=bcs, verbose=False)
            if pDspl:
                pDspl = eval(pDspl)
                if isinstance(pDspl,(list,tuple)): # version 2.2.6
                    pDspl = {'x':pDspl[0],'z':pDspl[1],'Y':pDspl[2]}
                pDspls[label] = pDspl
    for e in elements:
        if e.tag == 'Beam2d':
            label = e.get('label')   
            nodes = list(eval(e.get('nodes')))
            mat = e.get('mat')
            cs = e.get('cs')
            hinges = e.get('hinges')
            if hinges:
                hinges = eval(hinges)
            newDomain.addElement(label=label, nodes=nodes, mat=mat, cs=cs, hinges=hinges, verbose=False)
    if loadCases is not None:
        for lc in loadCases:
            if lc.tag == 'LoadCase':
                label = lc.get('label')
                newDomain.addLoadCase(label=label, verbose=False)
                # TODO activeLoadCase
                alc = newDomain.loadCases[label]
                newDomain.activeLoadCase = alc
                alc.displayFlag = True
                for load in lc:
                    if load.tag == 'NodalLoad':
                        label = load.get('label')
                        where  = load.get('where')
                        value = load.get('value')
                        loadCase = load.get('loadCases')
                        if not loadCase:
                            loadCase = newDomain.activeLoadCase
                        if value:
                            value = eval(value)
                        newDomain.addNodalLoad(label=label, where=where, value=value, loadCase=loadCase, verbose=False)
                    if load.tag == 'PrescribedDisplacement':
                        label = load.get('label')
                        where  = load.get('where')
                        value = load.get('value')
                        loadCase = load.get('loadCases')
                        if not loadCase:
                            loadCase = newDomain.activeLoadCase
                        if value:
                            value = eval(value)
                        newDomain.addPrescribedDspl(label=label, where=where, value=value, loadCase=loadCase, verbose=False)
                    if load.tag=='ElementLoad':
                        label = load.get('label')
                        where  = load.get('where')
                        value = load.get('value')
                        loadCase = load.get('loadCases')
                        if value:
                            value = eval(value)
                            # following is for backward compatibility
                            if 'dta' in value:
                                value['dTc'] = value.pop('dta')
                            if 'dtt' in value:
                                value['dTg'] = value.pop('dtt')
                            if 'dTh' in value:
                                value['dTg'] = value.pop('dTh')
                            if not 'type' in value: # version 3.3.0
                               value['type'] = 'Uniform'
                               value['dir'] = 'Local Z'
                               value['magnitude'] = value['fz']
                               value['perX'] = False
                               value['Fx'] = 0
                               value['Fz'] = 0
                               value['DistF'] = 0
                        if load.tag=='ElementLoad':
                            newDomain.addElementLoad(label=label, where=where, value=value, loadCase=loadCase, verbose=False)
    else: # version 2.2.6
        label = 'Default_loadcase'
        newDomain.addLoadCase(label=label, verbose=False)
        alc = newDomain.loadCases[label]
        newDomain.activeLoadCase = alc
        alc.displayFlag = True
        for load in domainNodalLoads:
            if load.tag == 'NodalLoad':
                label = load.get('label')
                node  = load.get('where')
                value = load.get('value')
                loadCase = load.get('loadCases')
                if not loadCase:
                    loadCase = newDomain.activeLoadCase
                if value:
                    value = eval(value)
                    if isinstance(value,(tuple,list)):
                        # version 2.2.6
                        value = {'fx':value[0],'fz':value[1],'my':value[2]}
                newDomain.addNodalLoad(label=label, where=node, value=value, loadCase=loadCase, verbose=False)
        for load in domainElementLoads:
            if load.tag=='DistributedLoad' or load.tag=='TemperatureLoad' or load.tag=='ElementLoad':
                # version 2.2.6
                label = load.get('label')
                elem  = load.get('where')
                value = load.get('value')
                loadCase = load.get('loadCases')
                if not loadCase:
                    loadCase = newDomain.activeLoadCase
                if value:
                    value = eval(value)
                if load.tag=='ElementLoad':
                    newDomain.addElementLoad(label=label, where=elem, value=value, loadCase=loadCase, verbose=False)
                if load.tag=='DistributedLoad':
                    # version 2.2.6
                    value = {'fx':value[0], 'fz':value[1], 'dTc':0., 'dTg':0.}
                    newDomain.addElementLoad(label=label, where=elem, value=value, loadCase=loadCase, verbose=False)
                if load.tag=='TemperatureLoad':
                    # version 2.2.6
                    value = {'fx':0., 'fz':0., 'dTc':value[0], 'dTg':value[1]}
                    newDomain.addElementLoad(label=label, where=elem, value=value, loadCase=loadCase, verbose=False)
    #
    newDomain.postLoad(pDspls=pDspls)
    return newDomain



##################################################
#
# spreadsheet support
#
##################################################
def saveNotebook(self, file, fFormat):
    """Saves whole notebook to .xls file (if xlwt extansion is loaded) or current sheet to .csv file
    
    :param Notebook self: notebook to be saved
    :param file file: file opened for writing
    :param str fFormat: format of saving. Crrently 'xls' and 'csv' options are supported
    """
    from ebinit import sheetExportFormats
    if fFormat=='xls' and 'xls' in sheetExportFormats:
        nPages = self.nb.GetPageCount()
        from ebinit import xlwt
        wb = xlwt.Workbook()
        for i in range(nPages):
            page = self.nb.GetPage(i)
            name = self.nb.GetPageText(i)
            sheet = wb.add_sheet(name)
            for row in range(page.GetNumberRows()):
                for col in range(page.GetNumberCols()):
                    sheet.write(row, col, page.GetCellValue(row,col) )
        wb.save(file)
    elif fFormat=='csv':
        from ebinit import csv
        nPages = self.nb.GetPageCount()
        page = self.nb.GetCurrentPage()
        pageNb = -1
        for i in range(nPages):
            if self.nb.GetPage(i) is page:
                pageNb = i
        if pageNb==-1:
            logger.warning( langStr('No active sheet to save', 'Žádný aktivní list k uložení' ) )
            return
        name = self.nb.GetPageText(pageNb)
        nRows, nCols = page.GetNumberRows(), page.GetNumberCols()
        data = [ [page.GetCellValue(row,col) for col in range(nCols)] for row in range(nRows)]
        csv.writer(file).writerows(data)
    else:
        raise EduBeamError
        print('Notebook.save: wrong file format')






##################################################
#
# OOFEM support
#
##################################################

class OofemFileWriter(FileWriter):
    """File writer for 2d beam structures into OOFEM input file"""
    def write(self,domain,name=''):
        """
        :param Domain domain: domain to be saved
        :param str name: name of output file (1st line)
        """
        name = name+'.out' if name else 'edubeam.out'
        import time
        t = time.localtime()
        #
        lines = [ # lines to write
            name,
            'EduBeam session, saved in version %s on %04d-%02d-%02d at %02dh:%02dm:%02ds'%(version,t[0],t[1],t[2],t[3],t[4],t[5]),
            'LinearStatic nSteps %d'%(len(domain.loadCases)),
            'Domain 2dBeam',
            'OutputManager tstep_all dofman_all element_all',
            '#### DOMAIN SIZE RECORD TO BE ADDED LATER ####'
        ]
        #
        nodes  = [domain.nodes[key] for key in sorted(domain.nodes) ]
        elems  = [domain.elements[key] for key in sorted(domain.elements) ]
        mats   = [domain.materials[key] for key in sorted(domain.materials) ]
        css    = [domain.crossSects[key] for key in sorted(domain.crossSects) ]
        lcs    = [domain.loadCases[key] for key in sorted(domain.loadCases) ]
        nLoads = domain.giveNodalLoads()
        eLoads = domain.giveElementLoads()
        pDspls = domain.givePrescribedDspls()
        bcs    = []
        nbc    = 2
        #
        for i,node in enumerate(nodes):
            c = node.coords
            pDspls = domain.givePrescribedDsplsOnNode(node)
            bcStr = ''
            if node.hasAnyPrescribedBC():
                bcStr = ' bc 3'
                nbcs = [0,0,0]
                for j,key in enumerate(('x','z','Y')):
                    for pDspl in pDspls:
                        if pDspl.value[key]:
                            nbcs[j] = nbc
                            bcs.append(pDspl.value[key])
                            nbc += 1
                for j in range(3):
                    if nbcs[j]==0 and node.hasPrescribedBcInDof(j):
                        nbcs[j] = 1
                bcStr += ' %d %d %d'%(nbcs[0],nbcs[1],nbcs[2])
            lines.append('node %d coords 3 %g 0. %g%s'%(i+1,c[0],c[2],bcStr))
        for i,node in enumerate(nodes):
            loads = domain.giveNodalLoadsOnNode(node)
            loadStr = ''
            if loads:
                loadStr += ' load %d'%len(loads)
                for load in loads:
                    loadStr += ' %d'%(len(bcs)+2+nLoads.index(load))
            lines[6+i] = lines[6+i] + loadStr
        for i,elem in enumerate(elems):
            n1,n2 = nodes.index(elem.nodes[0])+1, nodes.index(elem.nodes[1])+1
            mat = mats.index(elem.mat)+1
            cs = css.index(elem.cs)+1
            loads = domain.giveElementLoadsOnElement(elem)
            hingesStr = ''
            if elem.hasHinges():
                if elem.hinges[0] and elem.hinges[1]:
                    hingesStr = ' dofsToCondense 2 3 6'
                elif elem.hinges[0]:
                    hingesStr = ' dofsToCondense 1 3'
                elif elem.hinges[1]:
                    hingesStr = ' dofsToCondense 1 6'
            loadStr = ''
            if loads:
                loadStr += ' bodyLoads %d'%len(loads)
                for load in loads:
                    n = len(pDspls)+len(nLoads)+2+2*eLoads.index(load)
                    loadStr += ' %d'%n
                loadStr += ' boundaryLoads %d'%(2*len(loads))
                for load in loads:
                    n = len(pDspls)+len(nLoads)+2+2*eLoads.index(load)+1
                    loadStr += ' %d %d'%(n,1)
            lines.append('beam2d %d nodes 2 %d %d mat %d crossSect %d%s%s'%(i+1,n1,n2,mat,cs,hingesStr,loadStr))
        for i,cs in enumerate(css):
            lines.append('simpleCS %d area %g Iy %g beamShearCoeff 1e18 thick %g'%(i+1,cs.a,cs.iy,cs.h))
        for i,mat in enumerate(mats):
            lines.append('isoLE %d d %g E %g n 0. tAlpha %g'%(i+1,mat.d,mat.e,mat.alpha))
        lines.append('BoundaryCondition 1 loadTimeFunction 1 prescribedValue 0.0')
        ibc = 1
        for bc in bcs:
            ibc += 1
            lines.append('BoundaryCondition %d loadTimeFunction 1 prescribedValue %g'%(ibc,bc))
        for load in nLoads:
            ibc += 1
            lc = lcs.index(load.loadCase)+1
            c1,c2,c3 = load.value['fx'],load.value['fz'],load.value['my']
            lines.append('NodalLoad %d loadTimeFunction %d components 3 %g %g %g'%(ibc,lc,c1,c2,c3))
        for load in eLoads:
            lc = lcs.index(load.loadCase)+1
            fx,fz = load.value['fx'],load.value['fz']
            dTc,dTg = load.value['dTc'],load.value['dTg']
            ibc += 1
            lines.append('StructTemperatureLoad %d loadTimeFunction %d components 2 %g %g'%(ibc,lc,dTc,dTg))
            ibc += 1
            lines.append('ConstantEdgeLoad %d loadTimeFunction %d components 3 %g %g 0. loadType 3 ndofs 3'%(ibc,lc,fx,fz))
        for i,lc in enumerate(lcs):
            lines.append('PeakFunction %d t %d f(t) 1.'%(i+1,i+1))
        for line in lines:
            if line == '#### DOMAIN SIZE RECORD TO BE ADDED LATER ####':
                line = 'ndofman %d nelem %d ncrosssect %d nmat %d nbc %d nic 0 nltf %d'%(len(nodes),len(elems),len(css),len(mats),len(bcs)+len(nLoads)+2*len(eLoads)+1,len(lcs))
            self.writeLine(line)



class OofemFileReader(FileReader):
    """File writer for 2d beam structures into OOFEM input file"""
    def readLine(self,splitStr=None):  # TODO check why splitStr is not used here
        self.line = self.file.readline().lower()
        while self.line.lstrip().startswith('#'):
            self.line = self.file.readline().lower()
        self.lineSplit = self.line.split()
        return self.line

    def readWord(self,string,type,default=None):
        for i,word in enumerate(self.lineSplit):
            if word == string:
                return type(self.lineSplit[i+1])
        if default is not None:
            return default
        raise EduBeamError

    def readFloat(self,string,default=None):
        return self.readWord(string,float,default)

    def readInt(self,string,default=None):
        return self.readWord(string,int,default)

    def readStr(self,string,default=None):
        return self.readWord(string,str,default)

    def readWordArray(self, string, type, default=None):  # TODO solve built-in name type
        for i,word in enumerate(self.lineSplit):
            if word == string:
                l = int(self.lineSplit[i+1])
                ret = []
                for j in range(l):
                    ret.append(type(self.lineSplit[i+2+j]))
                return ret
        if default is not None:
            return default
        raise EduBeamError

    def readFloatArray(self,string,default=None):
        return self.readWordArray(string,float,default)

    def readIntArray(self,string,default=None):
        return self.readWordArray(string,int,default)

    def readStrArray(self,string,default=None):
        return self.readWordArray(string,str,default)

    def read(self,newDomain=None):
        from ebfem import Domain,Material,CrossSection,Node,Beam2d,NodalLoad,ElementLoad,LoadCase
        # *.out
        self.readLine()
        # comment
        self.readLine()
        # engng model
        self.readLine()
        if self.lineSplit[0] != 'linearstatic':
            raise EduBeamError
            print('OofemFileReader: unsupported EngngModel')
        nLCs = self.readInt('nsteps')
        nModules = self.readInt('nmodules',0)
        for i in range(nModules):
            self.readLine()
        # domain
        self.readLine()
        if self.lineSplit[1] != '2dbeam':
            raise EduBeamError
            print('OofemFileReader: unsupported Domain type')
        # output manager
        self.readLine()
        # nnode ...
        self.readLine()
        nNodes = self.readInt('ndofman')
        nElems = self.readInt('nelem')
        nCSs   = self.readInt('ncrosssect')
        nMats  = self.readInt('nmat')
        nBCs   = self.readInt('nbc')
        nodeKws  = []
        elemKws  = []
        csKws    = []
        matKws   = []
        bcKws       = {}
        nLoadPreKws = {}
        eLoadPreKws = {}
        bcPreKws    = {}
        lcKws    = []
        # nodes
        for i in range(nNodes):
            self.readLine()
            kw = {
                'label'  : self.readStr('node'),
                'coords' : self.readFloatArray('coords',[]),
                'loads'  : self.readStrArray('load',[]),
                'bcs'    : self.readStrArray('bc',[False,False,False]),
            }
            nodeKws.append(kw)
        # elems
        for i in range(nElems):
            self.readLine()
            h = self.readIntArray('dofstocondense',[])
            hinges = [True if 3 in h else False, True if 6 in h else False]
            l1 = self.readStrArray('bodyloads',[])
            l2 = self.readStrArray('boundaryloads',[])
            l2 = [l for i,l in enumerate(l2) if not i%2]
            loads = l1+l2
            kw = {
                'label' :  self.readStr('beam2d'),
                'nodes' :  self.readStrArray('nodes'),
                'mat'   :  self.readStr('mat'),
                'cs'    :  self.readStr('crosssect'),
                'hinges' : hinges,
                'loads' : loads,
            }
            elemKws.append(kw)   
        # cross sects
        for i in range(nCSs):
            self.readLine()
            kw = {
                'label' : self.readStr('simplecs'),
                'a'     : self.readFloat('area',None),
                'iy'    : self.readFloat('iy',None),
                'h'     : self.readFloat('thick',None),
            }
            csKws.append(kw)
        # materials
        for i in range(nMats):
            self.readLine()
            label = self.readStr('isole', None)
            if label is None:
                raise EduBeamError
                print('OofemFileReader: unsupported material')
            kw = {
                'label' : label,
                'e'     : self.readFloat('e'),
                'alpha' : self.readFloat('talpha'),
                'd'     : self.readFloat('d'),
            }
            matKws.append(kw)
        # loads and bcs
        for i in range(nBCs):
            self.readLine()
            if self.lineSplit[0] == 'boundarycondition':
                label = self.readStr('boundarycondition')
                value = self.readFloat('prescribedvalue')
                kw = {
                    'value': value,
                    'loadCase': self.readStr('loadtimefunction'),
                }
                bcPreKws[label] = kw
            elif self.lineSplit[0] == 'constantedgeload':
                value = self.readFloatArray('components')
                label = self.readStr('constantedgeload')
                kw = {
                    'loadCase'    : self.readStr('loadtimefunction'),
                    'value' : {'fx':value[0], 'fz':value[1], 'dTc':0., 'dTg':0.},
                }
                eLoadPreKws[label] = kw
            elif self.lineSplit[0] == 'structtemperatureload':
                value = self.readFloatArray('components')
                label = self.readStr('structtemperatureload')
                kw = {
                    'loadCase'    : self.readStr('loadtimefunction'),
                    'value' : {'fx':0., 'fz':0., 'dTc':value[0], 'dTg':value[1]},
                }
                eLoadPreKws[label] = kw
            elif self.lineSplit[0] == 'nodalload':
                value = self.readFloatArray('components')
                label = self.readStr('nodalload')
                kw = {
                    'loadCase'    : self.readStr('loadtimefunction'),
                    'value' : {'fx':value[0], 'fz':value[1], 'my':value[2]},
                }
                nLoadPreKws[label] = kw
            else:
                raise EduBeamError
                print('OofemFileReader: unsupported boundary condition (load)')
        for i in range(nLCs):
            self.readLine()
            label = self.readStr('peakfunction', None)
            if label is None:
                raise EduBeamError
                print('OofemFileReader: unsupported loadTimeFunction')
            lcKws.append({'label':label})
        # "redistribution" of nodal loads and bcs
        nLoadKws = []
        bcKws = []
        nl = 1
        nbc = 1
        for node in nodeKws:
            for nLoadLabel in node['loads']:
                load = nLoadPreKws[nLoadLabel]
                kw = dict( (key,val) for key,val in load.items() )
                kw['where'] = node['label']
                kw['label'] = 'F_%d'%nl
                nl += 1
                nLoadKws.append(kw)
            del node['loads']
            #
            bcs = node['bcs']
            bcLcs = list(set([bcPreKws[bc]['loadCase'] for bc in bcs if bc!='0']))
            for lc in bcLcs:
                kw = {
                    'where': node['label'],
                    'label': 'P_%g'%nbc,
                    'value': dict( (key, bcPreKws[i]['value'] if i!='0' and bcPreKws[i]['loadCase']==lc else 0.) for key,i in zip(('x','z','Y'),node['bcs']) ),
                    'loadCase': lc,
                }
                if any(val for val in kw['value'].values()):
                    bcKws.append(kw)
            node['bcs'] = {'x':bool(int(bcs[0])), 'z':bool(int(bcs[1])), 'Y':bool(int(bcs[2]))}
        # "redistribution" of element loads
        eLoadKws = []
        nl = 1
        for elem in elemKws:
            for eLoadLabel in elem['loads']:
                load = eLoadPreKws[eLoadLabel]
                kw = dict( (key,val) for key,val in load.items() )
                kw['where'] = elem['label']
                kw['label'] = 'L_%d'%nl
                nl += 1
                eLoadKws.append(kw)
            del elem['loads']
        #
        newDomain = newDomain if newDomain else Domain()
        newDomain.reset(verbose=False)
        newDomain.delPredefinedItems()
        for kw in matKws:
            newDomain.addMaterial(verbose=False,**kw)
        for kw in csKws:
            newDomain.addCrossSect(verbose=False,**kw)
        for kw in nodeKws:
            newDomain.addNode(verbose=False,**kw)
        for kw in elemKws:
            newDomain.addElement(verbose=False,**kw)
        for kw in lcKws:
            newDomain.addLoadCase(verbose=False,**kw)
        for kw in nLoadKws:
            newDomain.addNodalLoad(verbose=False,**kw)
        for kw in bcKws:
            newDomain.addPrescribedDspl(verbose=False,**kw)
        for kw in eLoadKws:
            newDomain.addElementLoad(verbose=False,**kw)
        alc = newDomain.loadCases[sorted(newDomain.loadCases.keys())[0]]
        newDomain.activeLoadCase = alc
        alc.displayFlag = True
        return newDomain
