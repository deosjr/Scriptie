from helper_functions import *
import argparser
import sys

drawn = []
texlist = []
vertices = {}


class ProofStructure(object):

    def __init__(self, formula, vertex):
        self.formula = formula
        self.main = vertex
        self.tensors = []
        self.links = []
        self.order = [0]
        self.hypotheses = []
        self.conclusions = []
        
    def print_debug(self):
        print ""
        print [x.main for x in self.hypotheses]
        print [x.main for x in self.conclusions]
        print [(x.top.alpha,x.bottom.alpha) for x in self.links]
        
    def add_tensor(self, tensor):
        self.tensors.append(tensor)
        tensor.index = len(self.tensors) - 1
        tensor.alpha = len(self.tensors)

    def add_link(self, link):
        self.links.append(link)
        
    def add_atom(self, atom, hypo):
        if hypo:
            self.conclusions.append(atom)
        else:
            self.hypotheses.append(atom)
            
    def bijection(self):
        count = 0
        for link in self.links:
            if link.is_command():
                count += 1
            else:
                count -= 1
        return count == 0
        
    def connected(self):
        #TODO
        return True
        
    def join(self, module):
        # Temporary fix on order for printing
        if module.tensors:
            higher_order = [x + len(self.order) for x in module.order]
            for t in module.tensors:
                t.alpha += len(self.order)
            self.order += higher_order
        self.tensors += module.tensors
        self.links += module.links
        
        module = None
        
    def toTeX(self, first):    
        global texlist, drawn
        # Erase file
        if first:
            f = open('formula.tex', 'w')
            f.close()
        
        drawn = []
        texlist = []
        
        # Write to formula.tex
        # Header
        f = open('formula.tex', 'a')
        
        rotate = ""
        
        if not first:
            f.write("\n")
        else:
            f.write('\documentclass[tikz]{standalone}\n\n')
            f.write('\usepackage{tikz-qtree}\n')
            f.write('\usepackage{stmaryrd}\n\n')
            f.write('\\begin{document}\n\n')
            
            # Toggle rotation
            p = argparser.Parser()
            args = p.get_arguments()
            if args.rotate:
                rotate = "rotate=270,"
                
        # Tikzpicture
            
        f.write('\\begin{tikzpicture}[')
        f.write(rotate)
        f.write('scale=.8,')
        f.write('cotensor/.style={minimum size=2pt,fill,draw,circle},\n')
        f.write('tensor/.style={minimum size=2pt,fill=none,draw,circle},')
        f.write('sibling distance=1.5cm,level distance=1cm,auto]\n\n')

        x = 0
        y = 0
        
        if not self.tensors:
            f.write(self.main.toTeX(x, y, self.main.main, self))
           
        else:   
            # Shuffle self.tensors according to order
            self.tensors = map(lambda x: self.tensors[x],self.order)
            previous_tensor = None
        
        for tensor in self.tensors:
            
            if previous_tensor is not None:
                (x_adj,y_adj) = adjust_xy(previous_tensor, tensor)
                x += x_adj
                y += y_adj
            
            f.write('{0} at ({1},{2}) {{}};\n'.format(tensor.toTeX(),x,y))
            f.write(tensor.hypotheses_to_TeX(x, y))
            f.write(tensor.conclusions_to_TeX(x, y))
            y -= 3
            previous_tensor = tensor
         
        for line in texlist:
            f.write(line)
            
        for l in self.links:
            f.write(l.draw_line())
                
        f.write('\n\end{tikzpicture}\n\n')
        f.close()
        
        
def adjust_xy(previous, current): 
    if isinstance(previous, OneHypothesis):
        if previous.bottomLeft.conclusion is current:
            if isinstance(current, OneHypothesis):
                if current.top.hypothesis is previous:
                    return (-1,1)
            else:
                if current.topRight.hypothesis is previous:
                    return (-2,1)
        elif previous.bottomRight.conclusion is current:
            if isinstance(current, OneHypothesis):
                if current.top.hypothesis is previous:
                    return (1,1)
            else:
                if current.topLeft.hypothesis is previous:
                    return (2,1)
    else:
        if previous.bottom.conclusion is current:
            if isinstance(current, TwoHypotheses):
                if current.topLeft.hypothesis is previous:
                    return (1,1)
                elif current.topRight.hypothesis is previous:
                    return (-1,1)
    return (0,0)
        

class Vertex(object):

    def __init__(self, formula=None, hypo=None):
        global vertices
        self.set_hypothesis(None)
        self.set_conclusion(None)
        self.alpha = len(vertices)
        self.is_value = True       # if False then is_context
        vertices[self.alpha] = self
        if formula is not None:
            self.main = formula
            self.attach(formula, hypo)
            
    def set_hypothesis(self, hypo):
        self.hypothesis = hypo
        
    def set_conclusion(self, con):
        self.conclusion = con
        
    def toTeX(self, x, y, tensor, struc): 
        global texlist, drawn
        co = ""
        if tensor is not self.main:
            if tensor.is_cotensor() and tensor.arrow is self.alpha:
                co = "[->]"
            line = "\draw{0} ({1}) -- ({2});\n".format(co,"t"+
                    str(tensor.alpha),"v"+str(self.alpha))
            # TODO: curved links are broken, self.hypo can be a Link
            #if self.internal() and self.conclusion is tensor:
            #    if struc.order.index(tensor.index) != struc.order.index(self.hypothesis.index) + 1:
            #        line = self.curved_tentacle(tensor, self.hypothesis)
            texlist.append(line)
            if self.alpha in drawn:
                return ""
            drawn.append(self.alpha)
        label = operators_to_TeX(self.main)
        tex = "\\node ({0}) at ({1},{2}) {{${3}$}};\n".format("v"+str(self.alpha), 
                x, y, label)
        return tex
        
    def curved_tentacle(self, tensor, prev_tensor): 
        co = ""
        if tensor.is_cotensor() and tensor.arrow is self.alpha:
            co = "[->]"
        start = "\draw{0} ({1}) ..controls ".format(co, "t"+str(tensor.alpha))
        direction = "west"
        if isinstance(tensor, TwoHypotheses):
            if tensor.topRight is self:
                direction = "east"
        elif isinstance(prev_tensor, OneHypothesis):
            if prev_tensor.bottomRight is self:
                direction = "east"
        controls = "+(north {0}:4) and +(south {0}:4.0)".format(direction)
        end = ".. ({0});\n".format("v"+str(self.alpha))
        line = start + controls + end
        return line
        
    def internal(self):
        return ((isinstance(self.hypothesis, Tensor) or
                    isinstance(self.hypothesis, Link)) and 
                    (isinstance(self.conclusion, Tensor) or
                    isinstance(self.conclusion, Link)))
                    
    def is_hypothesis(self):
        return (isinstance(self.hypothesis, str) or (self.hypothesis is None))
    
    def is_conclusion(self):
        return (isinstance(self.conclusion, str) or (self.conclusion is None))  
        
    def is_lexical_item(self):
        return (self.is_hypothesis() and self.is_conclusion())
            
    def attach(self, label, hypo):
        if hypo:
            self.set_hypothesis(label)
        else:
            self.set_conclusion(label)
            
    # This is the source of the recursion        
    def unfold(self, formula, hypo, structure, i=None):
        regexp = re.compile(
        r"""(\(.+\)|[\w'{}|$]+)                     #left formula
            (\*|\\|/|\(\*\)|\(/\)|\(\\\))           #main connective
            (\(.+\)|[\w'{}|$]+)$                    #right formula
        """, re.X)
        search = regexp.match(formula)
        try:
            (left, connective, right) = search.groups()
        except AttributeError: 
            print "Syntax error in formula"
            sys.exit()
        vertex = Vertex(formula)
        if hypo:
            link = Link(self.alpha,vertex.alpha)
        else:
            link = Link(vertex.alpha,self.alpha)
        (premises, geometry) = type(connective,hypo)
        if premises == 1:
            t = (OneHypothesis(left, right, geometry, vertex, structure, hypo, i))
        else:
            t = (TwoHypotheses(left, right, geometry, vertex, structure, hypo, i))
        if not link.contract():
            structure.add_link(link)
                                    
                               
class Tensor(object):

    def __init__(self):
        print "error"
        
    def toTeX(self):
        co = ''
        if self.is_cotensor():
            co = 'co'
        return '\\node [{0}tensor] ({1})'.format(co,"t"+str(self.alpha))
        
    def parse_geometry(self, geometry, vertex):
        index = geometry.find("<")
        if index > -1:
            self.arrow = vertex.alpha
        geometry = geometry.replace("<", "")
        return geometry
        
    def get_lookup(self, left, right, vertex):
        lookup = {
            'f':(Tensor.attach,vertex),
            'l':(Tensor.eval_formula,left),
            'r':(Tensor.eval_formula,right),
            'v':True,       #TODO
            'e':False       #TODO
        }
        return lookup
        
    def set_structure(self, struc, hypo, origin_index):
        if origin_index is not None:
            new = len(struc.order)
            origin_index = struc.order.index(origin_index)
            if hypo:
                struc.order.insert(origin_index + 1,new)
            else:
                struc.order.insert(origin_index,new)
        struc.add_tensor(self)
        self.structure = struc
        
    def is_cotensor(self):
        return hasattr(self, 'arrow')
        
    def attach(self, vertex, hypo, is_value):
        vertex.attach(self, not hypo)
        vertex.is_value = is_value
        return vertex
        
    def eval_formula(self, part, hypo, is_value):
        if simple_formula(part):
            atom = Vertex(part, hypo)
            self.structure.add_atom(atom, not hypo)
            return self.attach(atom, hypo, is_value)
        else:
            vertex = Vertex() 
            self.attach(vertex, hypo, is_value)
            part = part[1:-1]
            vertex.unfold(part, not hypo, self.structure, self.index)
            # Toggle abstract
            p = argparser.Parser()
            args = p.get_arguments()
            if args.abstract:
                vertex.main = "."
            else:
                vertex.main = part
            return vertex
            
  
class OneHypothesis(Tensor):

    def __init__(self, left, right, geometry, vertex, struc, hypo, i):
        Tensor.set_structure(self, struc, hypo, i)
        geometry = Tensor.parse_geometry(self, geometry, vertex)
        lookup = Tensor.get_lookup(self, left, right, vertex)
        (function,arg) = lookup[geometry[0]]
        self.top = function(self, arg, 1, lookup[geometry[3]])
        (function,arg) = lookup[geometry[1]]
        self.bottomLeft = function(self, arg, 0, lookup[geometry[4]])
        (function,arg) = lookup[geometry[2]]
        self.bottomRight = function(self, arg, 0, lookup[geometry[5]])
        
    def get_hypotheses(self):
        return [self.top]
        
    def get_conclusions(self):
        return [self.bottomLeft, self.bottomRight]
        
    def num_hyp(self):
        return 1
    
    def num_con(self):
        return 2
        
    def hypotheses_to_TeX(self, x, y):
        return self.top.toTeX(x, y + 1, self, self.structure)
        
    def conclusions_to_TeX(self, x, y):
        s1 = self.bottomLeft.toTeX(x - 1, y - 1, self, self.structure)
        s2 = self.bottomRight.toTeX(x + 1, y - 1, self, self.structure)
        return s1 + s2
        
    def replace(self, replace, vertex):
        if self.top == replace:
            self.top = vertex
        elif self.bottomLeft == replace:
            self.bottomLeft = vertex
        elif self.bottomRight == replace:
            self.bottomRight = vertex
    
    
class TwoHypotheses(Tensor):

    def __init__(self, left, right, geometry, vertex, struc, hypo, i):
        Tensor.set_structure(self, struc, hypo, i)
        geometry = Tensor.parse_geometry(self, geometry, vertex)
        lookup = Tensor.get_lookup(self, left, right, vertex)
        (function,arg) = lookup[geometry[0]]
        self.topLeft = function(self, arg, 1, lookup[geometry[3]])
        (function,arg) = lookup[geometry[1]]
        self.topRight = function(self, arg, 1, lookup[geometry[4]])
        (function,arg) = lookup[geometry[2]]
        self.bottom = function(self, arg, 0, lookup[geometry[5]])
        
    def get_hypotheses(self):
        return [self.topLeft, self.topRight]
        
    def get_conclusions(self):
        return [self.bottom]
      
    def num_hyp(self):
        return 2
    
    def num_con(self):
        return 1
        
    def hypotheses_to_TeX(self, x, y):
        s1 = self.topLeft.toTeX(x - 1, y + 1, self, self.structure)
        s2 = self.topRight.toTeX(x + 1, y + 1, self, self.structure)
        return s1 + s2
    
    def conclusions_to_TeX(self, x, y):
        return self.bottom.toTeX(x, y - 1, self, self.structure)
      
    def replace(self, replace, vertex):
        global vertices, removed
        if self.topLeft == replace:
            self.topLeft = vertex
        elif self.topRight == replace:
            self.topRight = vertex
        elif self.bottom == replace:
            self.bottom = vertex
        vertices[replace.alpha] = None
        
        
class Link(object):
    
    def __init__(self, top, bottom):
        global vertices
        self.top = vertices[top]
        self.bottom = vertices[bottom]
        self.top.set_conclusion(self)
        self.bottom.set_hypothesis(self)
        
    def contract(self):
        global vertices, removed
        if self.top.is_value == self.bottom.is_value:
            if not isinstance(self.bottom.conclusion, Tensor):
                vertices[self.bottom.alpha] = None
            else:
                self.top.set_conclusion(self.bottom.conclusion)
                self.bottom.conclusion.replace(self.bottom, self.top)
            return True
        return False
        
    def is_command(self):
        if self.top.is_value:
            return True
        return False
        
    def draw_line(self):
        if (self.top.alpha in drawn) and (self.bottom.alpha in drawn):
            top = "v" + str(self.top.alpha)
            bottom = "v" + str(self.bottom.alpha)
            line = "\draw[dotted] ({0}) -- ({1});\n".format(top, bottom)
            return line
        else:
            return ""
