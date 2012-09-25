import argparse
import textwrap


class Parser(object):

    def __init__(self):
        self.p = argparse.ArgumentParser(  
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent('''\
        Theorem prover for LG
        Formula language:
                A,B ::= p |             atoms (use alphanum)
                A*B | B\A | A/B |       product
                A(*)B | A(/)B | A(\)B   coproduct
                =>                      inference
                
        To use LaTeX commands as atoms, use |.
        For example: |phi will be translated to \phi
        Example call: LGprover.py "np/n , n => np"'''),
                                    usage = 'LGprover.py [options] sequent')
        self.p.add_argument('sequent', metavar='F', type=str, nargs='+',
                       help='a formula in LG to unfold')
        self.p.add_argument('--lexicon', '-l', action = 'store',
                       help='filepath to lexicon')
        self.p.add_argument('--tex', '-t', action = 'store_true', 
                    help = 'print result to LaTeX')
        self.p.add_argument('--abstract', '-a', action = 'store_true', 
                    help = 'hide internal node decoration')
        self.p.add_argument('--main', '-m', 
                    help = 'hide main formula as argument given')
        self.p.add_argument('--rotate', '-r', action = 'store_true', 
                    help = 'rotate structure 90 degrees counterclockwise')
        self.arguments = self.p.parse_args()
        
    def get_arguments(self):
        return self.arguments
        