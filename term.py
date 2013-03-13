# Proof terms as objects

next_alpha = 1


class Term(object):

    def __init__(self):
        print "error"

class Atomic_Term(Term):

    def __init__(self, atom=None):
        global next_alpha
        self.text = False
        if atom:
            self.atom = atom
            self.text = True
        else:
            self.atom = None 

    def term2list(self):
        global next_alpha
        if self.text:
            return ['\\textrm{' + self.atom + '}']
        if not self.atom:
            self.atom = chr(96 + next_alpha)
            next_alpha += 1
        return [self.atom]


class Complex_Term(Term):

    def __init__(self, left, functor, right):
        self.functor = functor
        self.left = left
        self.right = right

    def term2list(self):

        left = self.left.term2list()
        right = self.right.term2list()

        if isinstance(left, Complex_Term):
            left = ['('] + left + [')']

        if isinstance(right, Complex_Term):
            right = ['('] + right + [')']

        return left + [self.functor] + right


class Cotensor_Term(Complex_Term):

    def __init__(self, left, right, bottom):
        self.left = left
        self.right = right
        self.bottom = bottom

    def term2list(self):

        t1 = self.left.term2list()
        t2 = self.right.term2list()
        bottom = self.bottom.term2list()

        return ['\\frac{'] + t1 + t2 + ['}{'] + bottom + ['}']

