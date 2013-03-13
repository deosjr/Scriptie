#!/usr/bin/env python

# LIRa refers to:
# http://www.phil.uu.nl/~moortgat/lmnlp/2012/Docs/contributionLIRA.pdf
# Proofs nets and the categorial flow of information
# Michael Moortgat and Richard Moot

# Algorithm:
# 1) Unfolding
# 2) Pruning
# 3) Combinatorics
# 4) Soundness
# 5) Proof Term

from helper_functions import *
import classes_linear as classes
import argparser
from table import Table
import graph as g
import term

import os, sys
import platform
import itertools
              
  
# By default the formula appears in hypothesis position.  
def unfold_formula(formula, raw, hypothesis):
    vertex = classes.Vertex(formula, hypothesis)
    structure = classes.ProofStructure(formula, vertex)
    vertex.is_value = True      
    vertex.term = term.Atomic_Term(raw)
    if simple_formula(formula):
        structure.add_atom(vertex,hypothesis)
    else:
        vertex.unfold(formula, hypothesis, structure)     # Recursively unfold
 
    to_remove = []
    for l in structure.links:
        if l.contract():
            to_remove.append(l)           
    for l in to_remove:
        structure.links.remove(l)
        
    # Toggle whole formula
    p = argparser.Parser()
    args = p.get_arguments()
    if args.main:
        vertex.main ='|texttt{{{0}}}'.format(args.main)
    return structure
    
    
def unfold_all(sequentlist, raw):
    classes.vertices = {}
    classes.removed = 0
    classes.next_alpha = 0
    hypotheses = [unfold_formula(x, y, True) for (x,y) in zip(sequentlist[0], raw[0])]
    conclusions = [unfold_formula(x, y, False) for (x,y) in zip(sequentlist[1], raw[1])]
    modules = hypotheses + conclusions
    return modules
    
    
def create_composition_graph(sequent, raw, possible_binding):
    # Unfolding (again)
    modules = unfold_all(sequent, raw)   
    
    components = []
    for m in modules:
        components.extend(m.get_components())
            
    components = [x for x in components if not x == []]
    
    # Creating the composition graph
    composition_graph = modules[0]
    for m in modules[1:]:
        composition_graph.join(m)
    for b in possible_binding:
        link = classes.Link(b[1],b[0])
        if not link.contract():
            composition_graph.add_link(link)    
    
    command = [l for l in composition_graph.links if l.is_command()]
    mu_comu = [l for l in composition_graph.links if not l.is_command()]
    
    return composition_graph, components, command, mu_comu
    
    
def main():

    p = argparser.Parser()
    args = p.get_arguments()
    if len(args.sequent) != 1:
        p.print_help()
        sys.exit()
    raw_sequent = args.sequent[0]
    
    lexicon = []
    if args.lexicon:
        lexicon, classes.polarity = build_lexicon(args.lexicon)
    
    # Parsing the sequent
    raw_sequent = [map(lambda x : x.strip(), y) for y in
                [z.split(",") for z in raw_sequent.split("=>")]]
                
    if len(raw_sequent) != 2:
        syntax_error()
         
    sequent = raw_sequent     
    if lexicon:
        sequent = [map(lambda y : lookup(y, lexicon), x) for x in raw_sequent]

    # 1) Unfolding
    # Links added as either command or mu/comu
    
    modules = unfold_all(sequent, raw_sequent)
    
    # 2) Pruning
    # Checks: atom bijection
    
    atom_hypotheses = []
    atom_conclusions = []
    for m in modules:
        atom_hypotheses += m.hypotheses
        atom_conclusions += m.conclusions
        
    # Van Benthem count / Count Invariance 
    if sorted([h.main for h in atom_hypotheses]) != sorted([c.main for c in atom_conclusions]):
        no_solutions()
    
    # Chart of possible atom unification
    
    chart = {}
    for h in atom_hypotheses:
        if h.main not in chart:
            chart[h.main] = Table(h)
        else:
            chart[h.main].add_hypothesis(h)
    for c in atom_conclusions:
        chart[c.main].add_conclusion(c)
        
    for t in chart.values():
        t.create_table()
        
    # Checks: (simple) acyclicity
        t.prune_acyclicity()
    
    # TODO: Checks: (simple) connectedness
        #t.prune_connectedness()
        
    # Checks: Co-tensor will never contract
        t.prune_cotensor()
        
    # TODO: Checks: focusing, mu / comu
    
    # 3) Combinatorics    
    # Creating all possible derivation trees
    for t in chart.values():
        t.combine()
        
    tables = [t.atom_bindings for t in chart.values()]
    possible_bindings = []
    table_product = list(itertools.product(*tables))
    for product in table_product:
        binding = []
        for b in product:
            binding += b
        possible_bindings += [binding]
        
    # For each possible binding, create a proof net
    # Shallow / Deep copy problem: unfold every time
    # This is cost-intensive but the easiest way (?)
    # This requires bindings to refer to indices
    # instead of Vertex objects (these are destroyed each unfolding)
    
    no_solution = True
    # Erase file
    if args.tex:
        f = open('formula.tex', 'w')
        f.close()
            
    for i in range(0,len(possible_bindings)):
        # Copy problem
        if i > 0:
            modules = unfold_all(sequent, raw_sequent)
            
        proof_net = modules[0]
        for m in modules[1:]:
            proof_net.join(m)
        for b in possible_bindings[i]:
            link = classes.Link(b[1],b[0])
            if not link.contract():
                proof_net.add_link(link)
                
        # Checks: (mu / comu) -- command bijection
        if not proof_net.bijection():
            continue
        
        # 4) Soundness
        # Collapse all links, not needed anymore
        
        for l in proof_net.links:
            l.collapse_link()
        proof_net.links = []
        
        # Try to contract
        proof_net.contract()
        
        # If there are cotensors left, this is not a solution
        if [x for x in proof_net.tensors if x.is_cotensor()]:
            print "not a solution"
            continue          
        
        # Check: Connectedness of the whole structure
        # Traversal, checking total connectedness and acyclicity
        # NOTE: Can only be checked on contracted net

        if proof_net.tensors:
            if not proof_net.connected_acyclic():
                continue
        
        # Print to TeX
        if args.tex:
            proof_net.toTeX(no_solution)
            
        no_solution = False
        
        # 5) Proof term
        # TODO: Compostion Graph Traversal
        # NOTE: Can only be done on non-contracted net
        
        if args.term:
        
            composition_graph, components, command, mu_comu = create_composition_graph(sequent, raw_sequent, possible_bindings[i])
            
            # Step 1: create matchings
            # TODO: Working assumptions (see graph.py)
            
            # Create traversal graph
            cotensors = [x for x in composition_graph.tensors if x.is_cotensor()]
            graph = g.Graph(components, cotensors, mu_comu, command)              
                
            # Step 2: Calculate term in order of matching
            matching = graph.match()
            
            # Step 3: Write to TeX
            graph.to_TeX(matching, composition_graph)
            
        # For debugging
        # proof_net.print_debug() 
      
    if args.tex and not no_solution:
        # End of document
        f = open('formula.tex', 'a')
        f.write('\end{document}')
        f.close()
        os.system('pdflatex formula.tex')
        if platform.system() == 'Windows':
            os.system('start formula.pdf')
        elif platform.system() == 'Linux':
            os.system('pdfopen --file formula.pdf')
        # Mac OS X ?
        
    if no_solution:
        no_solutions()
         
if __name__ == '__main__':
    main()     
  