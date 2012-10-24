import re
import sys
import pyparsing as p


def parse(formula):
    atom = p.Word(p.alphas + "'|{}$")
    operator = p.oneOf("\\ / * (\\) (/) (*)")
    bracket = p.oneOf("( )")
    f = p.OneOrMore(atom | operator | bracket)
    formula = f.parseString(formula)
    check = [len(formula) for i in range(0, len(formula))]
    operators = ["\\", "/", "*", "(\\)", "(/)", "(*)"]
    symmetry = 0
    for i,c in enumerate(formula):
        if c is "(":
            symmetry += 1
        elif c is ")":
            symmetry -= 1
        if symmetry < 0:
            syntax_error()
        if c in operators:
            check[i] = symmetry
    main = check.index(min(check))
    return ["".join(formula[:main]),formula[main],"".join(formula[main+1:])]
    
# This returns True if the formula contains no connectives.   
def simple_formula(formula):
    connectives = re.compile(r"(\*|\\|/|\(\*\)|\(/\)|\(\\\))")
    search = connectives.search(formula)
    return search is None     


def operators_to_TeX(string):
    string = string.replace("\\", "\\backslash ")
    string = string.replace("(*)", "\oplus ")
    string = string.replace("*", "\otimes ")
    string = string.replace("(/)", "\oslash ")
    string = string.replace("(\\backslash )", "\obslash ")
    string = string.replace("|", "\\")
    return string   
    

def no_solutions():
    print "\nThere are no solutions"
    sys.exit()
    
    
def syntax_error():
    print "\nSyntax error in formula"
    sys.exit()


def lookup(label, lexicon):
    if label in lexicon:   
        # Returns first value found for label in lexicon
        # Multiple entries are not supported
        return lexicon[label][0]
    else:
        return label
    

def build_lexicon(pathfile):
    lex = {}
    f = open(pathfile)
    for line in f:
        if line[0] != '#' and line[0] != '\n':
            
            entry = line.split("::")
            label = entry[0].strip()
            atomic_value = entry[1]
            match = re.search(r'[^\ ]\n$', line)
            if match:
               atomic_value = atomic_value[:-1]                    
            if label in lex:
                lex[label] += atomic_value.strip()
            else:
                lex[label] = [atomic_value.strip()]
    f.close()
    return lex

    
def type(connective, hypo):
    types = {
        # LIRa figure 14
        # (con,hypo):(#premises,geometry)
        # geometry: (f)ormula,(l)eft,(r)ight, (<)arrow to previous, 
        # (v)alue, (e)context
       
        # Fusion connectives - hypothesis
        ("/",1):(2,"frleve"),
        ("*",1):(1,"f<lrvvv"),
        ("\\",1):(2,"lfrvee"),
        # Fusion connectives - conclusion
        ("/",0):(1,"lf<reev"),
        ("*",0):(2,"lrfvvv"),
        ("\\",0):(1,"rlf<eve"),
        # Fission connectives - hypothesis
        ("(/)",1):(2,"f<rlvev"),
        ("(*)",1):(1,"flreee"),
        ("(\\)",1):(2,"lf<revv"),
        # Fission connectives - conclusion
        ("(/)",0):(1,"lfrvve"),
        ("(*)",0):(2,"lrf<eee"),
        ("(\\)",0):(1,"rlfvev")        
    }
    return types[(connective, hypo)] 
    
    
