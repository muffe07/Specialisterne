import operator
import re
import math

def calculate(a,b,function):
    try:
        return(function(a,b))
    except:
        pass
    try:
        return(function(b))
    except:
        pass
    try:
        return(function(a))
    except:
        pass
    
    print("error")
    print(a)
    print(b)
    print(function)

function_dict = {"+":operator.add,"-":operator.sub,"/":operator.truediv,"*":operator.mul,"sqrt":math.sqrt,"^":operator.pow}



def construct_tree_from_string(s):
    order_of_operations = ['([-+])','([*/])','(sqrt|\^)']
    for i in order_of_operations:
        a = re.split(i,s)
        if(len(a)==1): 
            try:
                return(float(a[0]))
            except ValueError:
                pass
        if(len(a)>1):
            number = construct_tree_from_string(a[0])
            for i in range(int(len(a)/2)):
                i*=2
                number2 = float(construct_tree_from_string(a[i+2]))
                number = calculate(number,number2,function_dict[a[i+1]])
            return number

def pattern_replacement(match):
    expression = match.group(0)[1:-1]
    return str(construct_tree_from_string(expression))

def construct_tree_with_parethsesis(s):
    while(True):
        pattern = '(\([^\(\)]*\))'
        matches = re.findall(pattern,s)
        if(matches):
            s = re.sub(pattern,pattern_replacement ,s)
        else:
            break
    return(construct_tree_from_string(s))

def is_input_valid(s):
    if re.match('^(sqrt|[-+*\/\d\(\)])*$',s):
        return True
    else:
        return False


def get_function_from_user():
    while(True):
        expression = input("input expression: ")
        if(expression == "q"): break
        if(not is_input_valid(expression)): 
            print("expression not valid")
            continue
        result = (construct_tree_with_parethsesis(expression))
        print("the result is {0}".format(result))

get_function_from_user()