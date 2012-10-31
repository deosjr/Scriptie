from helper_functions import *
import argparser
import sys
import pyparsing

drawn = []
texlist = []
vertices = {}
removed = 0
polarity = {}
next_alpha = 0


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
        print [x.alpha for x in self.tensors]
        print self.order
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
        
    def join(self, module):
        # Temporary fix on order for printing
        if module.tensors:
            higher_order = [x + len(self.order) for x in module.order]
            for t in module.tensors:
                t.alpha += len(self.order)
            self.order += higher_order
        self.tensors += module.tensors
        self.links += module.links
        
        del module
        
    def contract(self):
        contracted = False
        
        for t in self.tensors:
            if t.is_cotensor():
                
                (complement, c_main, t_top, s) = t.contractions(self)
                if complement is not None:
                    # Simple contraction, L* and R(*)
                    link = None
                    if not s:
                        if t_top:
                            link = Link(t.arrow, c_main.alpha)
                        else:
                            link = Link(c_main.alpha, t.arrow)

                    # Generalized contraction, R/, R\, L(/) and L(\)
                    else:
                        link2 = None
                        if t_top:
                            link = Link(t.arrow, t.bottom.alpha)
                            link2 = Link(complement.top.alpha, c_main.alpha)
                        else:
                            link = Link(t.top.alpha, t.arrow)
                            link2 = Link(c_main.alpha, complement.bottom.alpha)
                        link2.collapse_link()
                            
                    link.collapse_link()
                    
                    # Removing the tensor
                    a = complement.alpha
                    self.tensors.remove(complement)
                    del complement
                    if a in self.order:
                        self.order.remove(a)
                        for i in range(len(self.order)):
                            if self.order[i] > a:
                                self.order[i] = self.order[i] - 1
                
                    # Removing the cotensor
                    a = t.alpha
                    self.tensors.remove(t)
                    del t
                    if a in self.order:
                        self.order.remove(a)
                        for i in range(len(self.order)):
                            if self.order[i] > a:
                                self.order[i] = self.order[i] - 1
                            
                    contracted = True
                    break                        
                
        if contracted:
            self.contract()
            
    def connected_acyclic(self):
        list = []
        for t in self.tensors:
            list.append(t)
        checklist = [(list[0], None)]
        connected_and_acyclic = True
        
        while checklist:
            (tensor, previous) = checklist[0]
            checklist.pop(0)
            n = tensor.neighbors()
            
            if previous is not None:
                test = len(n)
                n = [x for x in n if x is not previous]
                if test != (len(n) + 1):
                    # Cycle found
                    connected_and_acyclic = False
                    break 
            if tensor not in list:
                # Cycle found
                connected_and_acyclic = False
                break
            list.remove(tensor)
            for t in n:
                checklist.append((t, tensor))

        if list:
            # Disconnected part remains
            connected_and_acyclic = False
        return connected_and_acyclic            
        
    def toTeX(self, first):    
        global texlist, drawn
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
            f.write('\usepackage{stmaryrd}\n')
            f.write('\usepackage{scalefnt}\n')
            f.write('\usepackage{amssymb}\n\n')
            f.write('\\begin{document}\n\n')
            
            f.write('\\tikzstyle{mybox} = [draw=red, fill=blue!20, very thick,rectangle, rounded corners, inner sep=10pt, inner ysep=20pt]\n\n')
            
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
            #f.write(self.main.toTeX(x, y, self.main.main, self))
            f.write("\\node at (0,0) [")
            if self.main.hypothesis is not None:
                f.write("label=above:${0}$".format(operators_to_TeX(self.main.hypothesis)))
            if self.main.hypothesis is not None and self.main.conclusion is not None:
                f.write(", ")
            if self.main.conclusion is not None:
                f.write("label=below:${0}$".format(operators_to_TeX(self.main.conclusion)))
            f.write("] {.};\n")
           
        else:   
            # Shuffle self.tensors according to order
            # Trimming order to size instead of
            # losing myself in LaTeX-printing details
            self.order = [x for x in self.order if x < len(self.tensors)]
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
        global vertices, removed
        self.term = None
        self.set_hypothesis(None)
        self.set_conclusion(None)
        self.alpha = len(vertices) + removed
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
    
    # Important: use of hypo
    # l.top.get_term(False)
    # l.bottom.get_term(True)
    def get_term(self, hypo):
        global next_alpha
        if (self.term, hypo) in tensor_table:
            (p, _, t) = tensor_table[(self.term,hypo)]
            tensor = None
            if hypo:
                tensor = self.conclusion
            else:
                tensor = self.hypothesis           
            if tensor.is_cotensor() or isinstance(tensor, Link):
                self.term = chr(next_alpha + 96)
                next_alpha += 1
                return [self.term]
            left = ""
            right = ""
            if p == 1:
                if t[0] is 'l':
                    left = tensor.bottomLeft.get_term(True)
                if t[0] is 'r':
                    left = tensor.bottomRight.get_term(True)
                if t[0] is 't':
                    left = tensor.top.get_term(False)
                if t[1] is 'l':
                    right = tensor.bottomLeft.get_term(True)
                if t[1] is 'r':
                    right = tensor.bottomRight.get_term(True)
                if t[1] is 't':
                    right = tensor.top.get_term(False)
            if p == 2:
                if t[0] is 'l':
                    left = tensor.topLeft.get_term(False)
                if t[0] is 'r':
                    left = tensor.topRight.get_term(False)
                if t[0] is 'b':
                    left = tensor.bottom.get_term(True)
                if t[1] is 'l':
                    right = tensor.topLeft.get_term(False)
                if t[1] is 'r':
                    right = tensor.topRight.get_term(False)
                if t[1] is 'b':
                    right = tensor.bottom.get_term(True)
            if not simple_formula("".join(left)):
                left = ['('] + left + [')']
            if not simple_formula("".join(right)):
                right = ['('] + right + [')']
            return left + [self.term] + right
        return [self.term]
            
    # This is the source of the recursion        
    def unfold(self, formula, hypo, structure, i=None):
        try:
            [left, connective, right] = parse(formula)
        except pyparsing.ParseException: 
            syntax_error()
        vertex = Vertex(formula)
        if i is not None:
            self.term = connective
        vertex.term = connective
        if hypo:
            link = Link(self.alpha,vertex.alpha)
        else:
            link = Link(vertex.alpha,self.alpha)
        (premises, geometry, term_geo) = tensor_table[(connective,hypo)]
        if premises == 1:
            t = (OneHypothesis(left, right, geometry, vertex, structure, hypo, i))
        else:
            t = (TwoHypotheses(left, right, geometry, vertex, structure, hypo, i))
        t.term = term_geo
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
            'v':True,       
            'e':False       
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
        
    def attach(self, vertex, hypo, is_value, main=True):
        vertex.attach(self, not hypo)
        vertex.is_value = is_value
        if main:
            self.main = vertex
        return vertex
        
    def eval_formula(self, part, hypo, is_value):
        global next_alpha
        if simple_formula(part):
            atom = Vertex(part, hypo)
            self.structure.add_atom(atom, not hypo)
            atom.term = chr(next_alpha + 96)
            next_alpha += 1
            return self.attach(atom, hypo, is_value, False)
        else:
            vertex = Vertex() 
            self.attach(vertex, hypo, is_value, False)
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
            
    def neighbors(self):
        n = []
        for h in self.get_hypotheses():
            if isinstance(h.hypothesis, Tensor):
                n.append(h.hypothesis)
        for c in self.get_conclusions():
            if isinstance(c.conclusion, Tensor):
                n.append(c.conclusion)
        return n
        
    def non_main_connections(self):
        n = []
        for h in self.get_hypotheses():
            if not h is self.main:
                if isinstance(h.hypothesis, Tensor) or isinstance(h.hypothesis, Link):
                    n.append(h.hypothesis)
        for c in self.get_conclusions():
            if not c is self.main:
                if isinstance(c.conclusion, Tensor) or isinstance(c.conclusion, Link):
                    n.append(c.conclusion)
        return n
            
  
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
        global vertices, removed
        if self.is_cotensor() and self.arrow == replace.alpha:
            self.arrow = vertex.alpha
        if self.top == replace:
            self.top = vertex
        elif self.bottomLeft == replace:
            self.bottomLeft = vertex
        elif self.bottomRight == replace:
            self.bottomRight = vertex
        del vertices[replace.alpha]
        removed += 1
    
    # Can this cotensor contract?
    # If so, return the tensor it contracts with
    def contractions(self, net):
        if isinstance(self.bottomLeft.conclusion, TwoHypotheses):
            t = self.bottomLeft.conclusion
            if not t.is_cotensor():
                if self.bottomRight.conclusion is t:
                    # L*
                    return (t, t.bottom, True, [])
                    
                s = shortest_path(net, self, t)
                if only_grishin_tensors(s):
                    #R\   
                    return (t, t.topRight, False, s)
                
        elif isinstance(self.bottomRight.conclusion, TwoHypotheses):
            t = self.bottomRight.conclusion
            if not t.is_cotensor():
                s = shortest_path(net, self, t)
                if only_grishin_tensors(s):
                    #R/  
                    return (t, t.topLeft, False, s)
        
        return (None, None, None, None)           
        
    def get_term(self):
        if isinstance(self.term, str):
            t1 = None
            t2 = None
            if self.term[0] is 'l':
                t1 = self.bottomLeft.term
            if self.term[0] is 'r':
                t1 = self.bottomRight.term
            if self.term[0] is 't':
                t1 = self.top.term
            if self.term[1] is 'l':
                t2 = self.bottomLeft.term
            if self.term[1] is 'r':
                t2 = self.bottomRight.term
            if self.term[1] is 't':
                t2 = self.top.term
            self.term = ['\\frac{'] + [t1] + [t2] + ['}{'] + [self.main.term] + ['}']
        return self.term
        
    
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
        if self.is_cotensor() and self.arrow == replace.alpha:
            self.arrow = vertex.alpha
        if self.topLeft == replace:
            self.topLeft = vertex
        elif self.topRight == replace:
            self.topRight = vertex
        elif self.bottom == replace:
            self.bottom = vertex
        del vertices[replace.alpha]
        removed += 1
        
    # Can this cotensor contract?
    # If so, return the tensor it contracts with
    def contractions(self, net):
        if isinstance(self.topLeft.hypothesis, OneHypothesis):
            t = self.topLeft.hypothesis
            if not t.is_cotensor():
                if self.topRight.hypothesis is t:
                    # R(*)
                    return (t, t.top, False, [])
                    
                s = shortest_path(net, self, t)
                if only_lambek_tensors(s):
                    # L(\)
                    return (t, t.bottomRight, True, s)
                
        elif isinstance(self.topRight.hypothesis, OneHypothesis):
            t = self.topRight.hypothesis
            if not t.is_cotensor():
                s = shortest_path(net, self, t)
                if only_lambek_tensors(s):
                    # L(/)
                    return (t, t.bottomLeft, True, s)
        
        return (None, None, None, None)  

    def get_term(self):
        if isinstance(self.term, str):
            t1 = None
            t2 = None
            if self.term[0] is 'l':
                t1 = self.topLeft.term
            if self.term[0] is 'r':
                t1 = self.topRight.term
            if self.term[0] is 'b':
                t1 = self.bottom.term
            if self.term[1] is 'l':
                t2 = self.topLeft.term
            if self.term[1] is 'r':
                t2 = self.topRight.term
            if self.term[1] is 'b':
                t2 = self.bottom.term
            self.term = ['\\frac{'] + [t1] + [t2] + ['}{'] + [self.main.term] + ['}']
        return self.term
        
        
class Link(object):
    
    def __init__(self, top, bottom):
        global vertices
        self.top = vertices[top]
        self.bottom = vertices[bottom]
        self.top.set_conclusion(self)
        self.bottom.set_hypothesis(self)
        
    def contract(self):
        if self.top.is_value == self.bottom.is_value:
            self.collapse_link()
            return True
        return False
        
    def collapse_link(self):
        global vertices, removed
        self.top.set_conclusion(self.bottom.conclusion)
        if not isinstance(self.bottom.conclusion, Tensor):
            self.top.term = self.bottom.term
            del vertices[self.bottom.alpha]
            removed += 1
        else:
            self.bottom.term = self.top.term
            self.bottom.conclusion.replace(self.bottom, self.top)
        
    def is_command(self):
        if self.top.is_value:
            return True
        return False
        
    # Meaning whether the atomic formula is 
    # positive (True) or negative (False)
    # Only callable for mu/comu links
    def positive(self):
        if self.is_command():
            return None
        if self.top.main in polarity:
            if polarity[self.top.main] is '+':
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
            

# Dijkstra's algorithm            
def shortest_path(proofnet, source, target):
    dist = {}
    previous = {}
    q = []
    
    for t in proofnet.tensors:
        # set distance to functional infinity
        dist[t] = len(proofnet.tensors)
        previous[t] = None
        q.append(t)
        
    dist[source] = 0
    
    while q:
        u = q[0]
        for t in q[1:]:
            if dist[t] < dist[u]:
                u = t
        q.remove(u)
        if u is target:
            break
            
        # This means there are tensors left 
        # that are unreachable from source
        if dist[u] == len(proofnet.tensors):
            break 
            
        n = u.neighbors()
        if u is source:
            n.remove(target)
            
        for v in n:
            if not v in q:
                continue
            alt = dist[u] + 1
            if alt < dist[v]:
                dist[v] = alt
                previous[v] = u
                
    s = []
    u = previous[target]
    
    while u in previous:
        if u is not source:
            s.insert(0,u)
        u = previous[u]
        
    return s


def only_grishin_tensors(path):
    only_grishin = True
    for t in path:
        if t.is_cotensor() or isinstance(t, TwoHypotheses):
            only_grishin = False
            break
    return only_grishin

def only_lambek_tensors(path):
    only_lambek = True
    for t in path:
        if t.is_cotensor() or isinstance(t, OneHypothesis):
            only_lambek = False
            break
    return only_lambek
