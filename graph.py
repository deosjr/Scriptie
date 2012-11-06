# Working assumptions : 
# 1 - All components are connected by mu/comu-links
# 2 - All components have a single command link attached
# 3 - We only compute one term (so 1 starting point, one outgoing mu, deterministic)

import classes_linear as classes


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

    def get_starting_point(self):
        starting_points = [x for x in self.component_nodes if x.outgoing_mu_comu]
        if starting_points:
            # Working Assumption 3
            return starting_points[0]
        return []
        
    def match(self):
        match = []
        
        comp = self.get_starting_point()
        
        while [x for x in self.mu_comu_edges if not x.visited]:
        
            comp.visited = True
            match.append(comp.command.command)
            comp.command.visited = True
            
            for c in [x for x in self.cotensor_nodes if not x.visited]:
                if c.attachable():
                    match.append(c.cotensor)
                    c.visited = True
               
            if comp.outgoing_mu_comu:
                # Working Assumption 3
                m = comp.outgoing_mu_comu[0]
            else:
                leftover_mu = [x for x in self.mu_comu_edges if not x.visited]
                # Working Assumption 3
                m = leftover_mu[0]
               
            match.append(m.mu_comu)
            m.visited = True
            
            if isinstance(m.destination, Component):
                comp = m.destination
            else:
                leftover_comp = [x for x in self.component_nodes if not x.visited]
                if leftover_comp:
                    # Working Assumption 3
                    comp = leftover_comp[0]
            
        return match
        
  
class Node(object):
    
    def __init__(self):
        print "error"
    
    
class Component(Node):

    def __init__(self, g, component, index):
        self.index = index
        self.graph = g
        self.component = component
        self.outgoing_mu_comu = []
        self.visited = False
    
    def set_command(self, command):
        self.command = command
        
    def add_outgoing_mu_comu(self, m):
        self.outgoing_mu_comu.append(m)
    

class Cotensor(Node):

    def __init__(self, g, cotensor, index):
        self.index = index
        self.graph = g
        self.cotensor = cotensor
        self.attached = []
        self.visited = False
        
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
        
    def attachable(self):
        if not [x for x in self.attached if not x.visited]:
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
        self.visited = False
        
        # Working assumption 1
        if isinstance(self.origin, Component):
            self.origin.add_outgoing_mu_comu(self)
    
class Command(Edge):

    def __init__(self, g, command, index):
        self.index = index
        self.graph = g
        self.command = command
        self.set_origin_and_destination(command)
        self.visited = False
        
        # Working assumption 2
        self.graph.component_nodes[index].set_command(self)
        
        
        
        