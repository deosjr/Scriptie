# np    1   2   3
#  4    T   T   F
#  5    F   T   T   
#  6    T   T   T

# (np2,np6) is table[2][1]
# hypotheses on x-axis
# conclusions on y-axis

import classes_linear as classes

class Table(object):

    def __init__(self, atom):
        self.hypotheses = [atom]
        self.conclusions = []
        self.table = []
        self.atom_bindings = []
        
    def add_hypothesis(self, atom):
        self.hypotheses.append(atom)
        
    def add_conclusion(self, atom):
        self.conclusions.append(atom)
        
    def create_table(self):
        n = len(self.hypotheses)
        self.table = [[True]*n for i in range(n)]
        
    def prune_acyclicity(self):    
        for x in range(0, len(self.hypotheses)):
            for y in range(0, len(self.conclusions)):
                print "TODO" 
        
    def prune_connectedness(self):
        for x in range(0, len(self.hypotheses)):
            for y in range(0, len(self.conclusions)):
                print "TODO"
                
    def prune_cotensor(self):
        for x in range(0, len(self.hypotheses)):
            for y in range(0, len(self.conclusions)):
                h = self.hypotheses[x]
                c = self.conclusions[y]
                cH = c.hypothesis
                hC = h.conclusion
                if h.is_lexical_item() and isinstance(cH, classes.OneHypothesis) and cH.is_cotensor():
                    self.table[x][y] = False
                if c.is_lexical_item() and isinstance(hC, classes.TwoHypotheses) and hC.is_cotensor():
                    self.table[x][y] = False
        
    def combine(self):
        self.atom_bindings = self.dfs(0,[],[])
    
    # Depth-first search, exhaustive      
    def dfs(self, x, explored, combination):
        if x == len(self.hypotheses):
            return [combination]
        answers = []
        for y in range(len(self.conclusions)):
            if y not in explored and self.table[x][y]:
                combo = (self.hypotheses[x].alpha, self.conclusions[y].alpha)
                c = self.dfs(x+1, explored + [y], combination + [combo])
                if c != None:
                    answers += c
        return answers
                
        
        
    