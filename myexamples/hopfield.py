#!/usr/bin/python

from sympy.physics.quantum.qubit import Qubit, matrix_to_qubit
from sympy.physics.quantum.gate import HadamardGate, XGate
from sympy.physics.quantum.qapply import qapply
from sympy import pprint
from sympy.physics.quantum.represent import represent
from sympy import sqrt
from sympy import simplify




def add_states(arg1, arg2):
    #print 'adding 2 values=', represent(arg1) , represent(arg2)
    return represent(arg1) + represent(arg2)

def qapply_H(arg):
    #print 'apply H to ', arg
    return qapply(HadamardGate(0)*arg)

def qapply_I(arg):
    return arg

def qapply_X(arg):
    return qapply(XGate(0)*arg)

U=qapply_H

if __name__ == '__main__':
    n=10
    iterations = 20

    nodes = list()
    for i in range(0,n):
        nodes.append(Qubit('1'))

    #initialize
    H=HadamardGate(0)
    for i in range(0,n):
        nodes[i] =  qapply(H*nodes[i])

    print "Initial state"
    pprint(nodes)

    for i in range(0,iterations):
        for j in range(0,4):
            y = map(U, nodes)
            state = reduce(add_states, y)
            state = state - represent(y[j])

            norm = (sqrt(state[0]**2 + state[1]**2)).evalf()
            state[0] =  simplify(state[0])/norm
            state[1] =  simplify(state[1])/norm
            nodes[j] = matrix_to_qubit(state)

        pprint([(represent(i)).evalf() for i in nodes])
