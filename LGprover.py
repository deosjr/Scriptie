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

import os, sys
import platform
import itertools
              
  
# By default the formula appears in hypothesis position.  
def unfold_formula(formula, raw, hypothesis):
    vertex = classes.Vertex(formula, hypothesis)
    structure = classes.ProofStructure(formula, vertex)
    vertex.is_value = True      #TODO: check this
    vertex.term = raw
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
    
    # Determining the components (maximal subgraphs)
    # TODO: multiple components in a module?!
    components = []
    for m in modules:
        if m.tensors:
            components.append([x for x in m.tensors if not x.is_cotensor()])
    
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
    
    # Arranging commands to index of components
    shuffled = [0 for x in command]
    for l in command:
        if isinstance(l.top.hypothesis, classes.Tensor):
            for c in components:
                if l.top.hypothesis in c:
                    shuffled[components.index(c)] = l
        if isinstance(l.bottom.conclusion, classes.Tensor):
            for c in components:
                if l.bottom.conclusion in c:
                    shuffled[components.index(c)] = l
    command = shuffled
    
    return composition_graph, components, command, mu_comu

    
def main():

    p = argparser.Parser()
    args = p.get_arguments()
    if len(args.sequent) != 1:
        p.print_help()
        sys.exit()
    raw_sequent = args.sequent[0]
    
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
        cotensor_left = False
        for t in proof_net.tensors:
            if t.is_cotensor():
                cotensor_left = True
                break
        if cotensor_left:
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
        
        composition_graph, components, command, mu_comu = create_composition_graph(sequent, raw_sequent, possible_bindings[i])
        
        # A simple version using as an example 
        # subj, tv, det, noun => s
        
        # Step 1: create matchings
        # TODO: Working assumptions: 
        # For every component there is a command and a mu/comu link
        # and there are n-1 mu/comu links between components
        # where n is the number of components.
        # Also, every command is connected to a different component
        # and nothing else.

        # Find all mu/comu links between 2 components
        mu_binders = []
        odd_mu_out = None
        for l in mu_comu:
            t = None
            b = None
            if isinstance(l.top.hypothesis, classes.Tensor):
                for c in components:
                    if l.top.hypothesis in c:
                        t = components.index(c)
            if isinstance(l.bottom.conclusion, classes.Tensor):
                for c_ in components:
                    if l.bottom.conclusion in c_:
                        b = components.index(c_)
            if t is not None and b is not None:
                mu_binders.append((mu_comu.index(l),t,b))
            if t is None:
                odd_mu_out = (mu_comu.index(l),b)
            if b is None:
                odd_mu_out = (mu_comu.index(l),t)

        matchings = []
        
        for p in list(itertools.permutations(mu_binders)):
            matching = []
            substitution = {}
            for m in p:
                origin = None
                replacement = None
                if mu_comu[m[0]].positive():
                    origin = m[2]
                    replacement = m[1]
                else:
                    origin = m[1]
                    replacement = m[2]
                if origin in substitution:
                    origin = substitution[origin]
                if replacement in substitution:
                    replacement = substitution[replacement]
                substitution[origin] = replacement
                for k,v in substitution.items():
                    if v == origin:
                        substitution[k] = replacement 
                matching.append(origin)
                matching.append(m[0])
            odd = odd_mu_out[1]
            if odd in substitution:
                odd = substitution[odd]
            matching.append(odd)
            matching.append(odd_mu_out[0])
            
            matchings.append(matching)
            
        # Step 2: Calculate term in order of matching
        # This is done separately for each matching
        # on a new version of the composition graph
        
        f = open('formula.tex', 'a')
        f.write("{\\scalefont{0.7}\n")
        f.write("\\begin{tikzpicture}\n")
        f.write("\\node [mybox] (box){\n")
        f.write("\\begin{minipage}{0.50\\textwidth}\n")
        
        for m in matchings:
            
            term = []
            subs = []
            
            while m:
                # Command
                comlink = command[m.pop(0)]
                left = comlink.top.get_term(False)
                right = comlink.bottom.get_term(True)
                for x in subs:
                    if x in right:
                        insertion = ['('] + term + [')']
                        index = right.index(x)
                        right = right[:index] + insertion + right[index+1:]
                        break   # Because more than one substitution is not possible, right?
                term = ['<'] + left + ['|'] + right + ['>']
                
                # (Possible) Cotensor(s)
                
                
                # Mu / Comu
                mulink = mu_comu[m.pop(0)]
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
                    
                term = mu + source + ['.'] + term   
                subs.append(target[0])  

            f.write("$")
            for x in term:
                translation = {
                "mu":"\\mu",
                "comu":"\\tilde{\\mu}",
                "|":"\\upharpoonleft",
                "<":"\\langle",
                ">":"\\rangle",
                '\\':"\\backslash",
                "(*)":"\oplus",
                "*":"\otimes",
                "(/)":"\oslash",
                "(\\)":"\obslash"
                }
                if x in translation:
                    f.write(translation[x])
                else:
                    f.write(x)
                f.write(" ")
            f.write("$\n\n")  
        
        f.write("\end{minipage}\n\n};\n")
        f.write("\end{tikzpicture}}\n")
        f.close()
            
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
  