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
# 5) Semantics ?

from helper_functions import *
import classes_linear as classes
import argparser
from table import Table

import os, sys
import platform
import itertools
              
  
# By default the formula appears in hypothesis position.  
def unfold_formula(formula, hypothesis=1):
    vertex = classes.Vertex(formula, hypothesis)
    structure = classes.ProofStructure(formula, vertex)
    vertex.is_value = True      #TODO: check this
    if simple_formula(formula):
        structure.add_atom(vertex,hypothesis)
    else:
        vertex.unfold(formula, hypothesis, structure)     # Recursively unfold
    # Toggle whole formula
    p = argparser.Parser()
    args = p.get_arguments()
    if args.main:
        vertex.main ='|texttt{{{0}}}'.format(args.main)
    return structure
    
    
def unfold_all(sequentlist):
    classes.vertices = {}
    hypotheses = [unfold_formula(x, True) for x in sequentlist[0]]
    conclusions = [unfold_formula(x, False) for x in sequentlist[1]]
    modules = hypotheses + conclusions
    return modules

    
def main():
    p = argparser.Parser()
    args = p.get_arguments()
    if len(args.sequent) != 1:
        p.print_help()
        sys.exit()
    sequent = args.sequent[0]
    
    lexicon = {}
    
    if args.lexicon:
        lexicon = build_lexicon(args.lexicon)
    
    # Parsing the sequent
    sequent = [map(lambda x : x.strip(), y) for y in
                [z.split(",") for z in sequent.split("=>")]]
    if lexicon:
        sequent = [map(lambda y : lookup(y, lexicon), x) for x in sequent]
    
    # 1) Unfolding
    # Links added as either command or mu/comu
    
    modules = unfold_all(sequent)
    
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
        
    # TODO: Checks: acyclicity
        #t.prune_acyclicity()
    
    # TODO: Checks: connectedness
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
    
    first = True
    for i in range(0,len(possible_bindings)):
    
        # Copy problem
        if i > 0:
            modules = unfold_all(sequent)
            
        proof_net = modules[0]
        for m in modules[1:]:
            proof_net.join(m)
        for b in possible_bindings[i]:
            link = classes.Link(b[1],b[0])
            if not link.contract():
                proof_net.add_link(link)    
                
        proof_net.print_debug()
        
        # Checks: mu / comu bijection
        if not proof_net.bijection():
            not_a_solution()
            break
        
        # 4) Soundness
        # TODO: Check whether structure can be reduced to proof net
        # TODO: Check: Connectedness of the whole structure
        if not proof_net.connected():
            not_a_solution()
            break
            
        # TODO: Try to contract
        
        # 5) Semantics ?
        # TODO: Net traversal
        
        # Print to TeX
        if args.tex:
            proof_net.toTeX(first)
            first = False

        # For debugging
        #for x in modules:
        #    x.print_debug()  
      
    if args.tex:
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
         
if __name__ == '__main__':
    main()     
  