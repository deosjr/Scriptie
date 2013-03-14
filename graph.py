# Working assumptions : 
# 1 - All components are connected by mu/comu-links
# 2 - All components have a single command link attached (not true)

import classes_linear as classes
from helper_functions import *
import term


class Graph(object):

    def __init__(self, components, cotensors, mu_comu, command):
        self.components = components
        self.cotensors = cotensors
        self.mu_comu = mu_comu
        self.command = command
        self.component_nodes = [None for x in components]
        self.cotensor_nodes = [None for x in cotensors]
        self.mu_comu_edges = [None for x in mu_comu]
        self.command_edges = [None for x in command]
        for c in components:
            self.add_component_node(c, components.index(c))
        for co in cotensors:
            self.add_cotensor_node(co, cotensors.index(co))
        for m in mu_comu:
            self.add_mu_comu_edge(m, mu_comu.index(m))
        for comm in command:
            self.add_command_edge(comm, command.index(comm))
        
        for co in self.cotensor_nodes:
            co.get_attached()
   
    def add_component_node(self, c, i):
        component_node = Component(self, c, i)
        self.component_nodes[i] = component_node
    
    def add_cotensor_node(self, c, i):
        cotensor_node = Cotensor(self, c, i)
        self.cotensor_nodes[i] = cotensor_node
    
    def add_mu_comu_edge(self, m, i):
        mu_comu_edge = Mu_Comu(self, m, i)
        self.mu_comu_edges[i] = mu_comu_edge
    
    def add_command_edge(self, c, i):
        command_edge = Command(self, c, i)
        self.command_edges[i] = command_edge

    def get_starting_point(self, mu_vis):
        return [x for x in self.component_nodes if x.get_outgoing(mu_vis)]
        
    def match(self):
        return self.recursive_match([],{},[],[],[],[])
    
    def recursive_match(self, match, subs, comp_vis, cot_vis, comm_vis, mu_vis):
        
        if [x for x in self.mu_comu_edges if not x in mu_vis]:
            
            comp = self.get_starting_point(mu_vis)
            if not comp:
                comp = [x for x in self.component_nodes if not x in comp_vis]
            
            temp_match = []
            
            for c in comp:
                y = self.match_body(c, match, subs, comp_vis, cot_vis, comm_vis, mu_vis)
                if y:
                    temp_match.extend(y)
            return temp_match
        return [match]
            
    def match_body(self, comp, match, subs, comp_vis, cot_vis, comm_vis, mu_vis):
        
        c_match = [x for x in match]
        compvis = [x for x in comp_vis]
        cotvis = [x for x in cot_vis]
        commvis = [x for x in comm_vis]
        muvis = [x for x in mu_vis]
        
        # Temporary hack, should not be allowed
        if not hasattr(comp, 'command'):
            return [match]

        comm = comp.command
        if comp in compvis:
            comm = subs[comp].command
            compvis.append(subs[comp])
        else:
            compvis.append(comp)
        
        if comm in commvis:
            return []
        
        c_match.append(comm.command)
        commvis.append(comm)
        
        for c in [x for x in self.cotensor_nodes if not x in cotvis]:
            if c.attachable(compvis + cotvis + commvis + muvis):
                c_match.append(c.cotensor)
                cotvis.append(c)
        
        m = []
        outgoing = False
        if comp.get_outgoing(muvis):
            m = comp.get_outgoing(muvis)
            outgoing = True
        else:
            leftover_mu = [x for x in self.mu_comu_edges if not x in muvis]
            for mu in leftover_mu:
                if mu.origin in compvis + cotvis:
                    m.append(mu)
                elif mu.destination in compvis + cotvis:
                    m.append(mu)
                    
        if not m:
            return []
        
        temp_match = []
        for mu in m:
            x = c_match + [mu.mu_comu]
            mvis = muvis + [mu]
            s = {}
            for k,v in subs.items():
                s[k] = v
            if outgoing:
                s[comp] = mu.destination
            y = self.recursive_match(x, s, compvis, cotvis, commvis, mvis)
            if y:
                temp_match.extend(y)
        
        return temp_match

    def to_TeX(self, matching, cgraph):
        f = open('formula.tex', 'a')
        f.write("{\\scalefont{0.7}\n")
        f.write("\\begin{tikzpicture}\n")
        f.write("\\node [mybox] (box){\n")
        f.write("\\begin{minipage}{0.70\\textwidth}\n")
        f.write("\\begin{center}\n")
        
        non_empty_match = [x for x in matching if not x == []]
        
        if not non_empty_match:
            f.write('$' + operators_to_TeX(cgraph.main.hypothesis) + '$')
        
        for m in non_empty_match:

            term = self.linear_term(m) 
            
            f.write("$")

            for x in term:
                f.write(term2tex(x))
                f.write(" ")
            f.write("$\n\n")
            f.write("\\vspace{5mm}\n")
        
        f.write("\end{center}\n")
        f.write("\end{minipage}\n\n};\n")
        f.write("\end{tikzpicture}}\n")
        f.close()

    def linear_term(self, m):
        term = []
        subs = []
        
        while m:
            # Command
            comlink = m.pop(0)
            left = comlink.top.get_term(False).term2list()
            right = comlink.bottom.get_term(True).term2list()
            harpoon = ['/|']
            if comlink.positive():
                harpoon = ['|`']
            # TODO: substitutions (method of Term object?)
                for x in subs:
                    if x in left:
                        insertion = ['('] + term + [')']
                        index = left.index(x)
                        left = left[:index] + insertion + left[index+1:]
                        break   # Because more than one substitution is not possible, right?
            else:
                for x in subs:
                    if x in right:
                        insertion = ['('] + term + [')']
                        index = right.index(x)
                        right = right[:index] + insertion + right[index+1:]
                        break   # Because more than one substitution is not possible, right?
            
            term = ['<'] + left + harpoon + right + ['>']

            # (Possible) Cotensor(s)
            while isinstance(m[0], classes.Tensor):
                cotensor = m.pop(0)
                term = cotensor.get_term().term2list() + ['.'] + term
            
            # Mu / Comu
            mulink = m.pop(0)
            mu = []
            source = None
            target = None
            if mulink.positive():
                mu = ["comu"]
                source = mulink.bottom.get_term(True)
                target = mulink.top.get_term(False)
            else:
                mu = ["mu"]
                source = mulink.top.get_term(False)
                target = mulink.bottom.get_term(True)
                
            term = mu + source.term2list() + ['.'] + term  
            subs.extend(target.term2list())
        return term
        
  
class Node(object):
    
    def __init__(self):
        print "error"
    
    
class Component(Node):

    def __init__(self, g, component, index):
        self.index = index
        self.graph = g
        self.component = component
        self.outgoing_mu_comu = []
    
    def set_command(self, command):
        self.command = command
        
    def add_outgoing_mu_comu(self, m):
        self.outgoing_mu_comu.append(m)
        
    def get_outgoing(self, mu_vis):
        return [x for x in self.outgoing_mu_comu if not x in mu_vis]
    

class Cotensor(Node):

    def __init__(self, g, cotensor, index):
        self.index = index
        self.graph = g
        self.cotensor = cotensor
        self.attached = []
        
    def get_attached(self):
        [t1, t2] = self.cotensor.non_main_connections()
        i1 = t1
        i2 = t2
        for c in self.graph.components:
            if t1 in c:
                i1 = self.graph.component_nodes[self.graph.components.index(c)]
            if t2 in c:
                i2 = self.graph.component_nodes[self.graph.components.index(c)]
        
        attach = [i1, i2]
        
        for x,i in enumerate(attach):
            if isinstance(i, classes.Link):
                if i.is_command():
                    attach[x] = self.graph.command_edges[self.graph.command.index(i)]
                else:
                    attach[x] = self.graph.mu_comu_edges[self.graph.mu_comu.index(i)]
                    
        self.attached = attach
        
    def attachable(self, visited):
        if not [x for x in self.attached if not x in visited]:
            return True
        return False
        

class Edge(object):

    def __init__(self):
        print "error"
        
    def set_origin_and_destination(self, l):
        origin = None
        destination = None
        t = l.top
        b = l.bottom
        if isinstance(t.hypothesis, classes.Tensor):
            for c in self.graph.components:
                if t.hypothesis in c:
                    t = self.graph.components.index(c)
                    break
            else:   # t is a cotensor
                t = t.hypothesis
        if isinstance(b.conclusion, classes.Tensor):
            for c_ in self.graph.components:
                if b.conclusion in c_:
                    b = self.graph.components.index(c_)
                    break
            else:   # b is a cotensor
                b = b.conclusion

        if l.positive():
            origin = b
            destination = t
        else:
            origin = t
            destination = b
        if l.is_command():
            temp = origin
            origin = destination
            destination = temp
                
        self.origin = origin
        self.destination = destination
        if isinstance(origin, classes.Tensor):   
            self.origin = self.graph.cotensor_nodes[self.graph.cotensors.index(origin)]
        if isinstance(destination, classes.Tensor):   
            self.destination = self.graph.cotensor_nodes[self.graph.cotensors.index(destination)]
        if isinstance(origin, int):  # component
            self.origin = self.graph.component_nodes[origin]
        if isinstance(destination, int):  # component
            self.destination = self.graph.component_nodes[destination]
    

class Mu_Comu(Edge):

    def __init__(self, g, mu_comu, index):
        self.index = index
        self.graph = g
        self.mu_comu = mu_comu
        self.set_origin_and_destination(mu_comu)
        
        # Working assumption 1
        if isinstance(self.origin, Component) and isinstance(self.destination, Component):
            self.origin.add_outgoing_mu_comu(self)
    
class Command(Edge):

    def __init__(self, g, command, index):
        self.index = index
        self.graph = g
        self.command = command
        self.set_origin_and_destination(command)
        
        # Working assumption 2
        self.graph.component_nodes[index].set_command(self)
        
        
        
        