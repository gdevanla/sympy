from sympy.physics.quantum.qexpr import QExpr, QuantumError
from sympy.physics.quantum.tensorproduct import TensorProduct
from sympy.core.mul import Mul
from sympy.core.add import Add
from sympy.core.power import Pow
from sympy.core.expr import Expr
from sympy.printing.str import sstr
from sympy.physics.quantum.hilbert import HilbertSpace
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.operator import Operator, OuterProduct
from sympy.physics.quantum.represent import represent
from sympy.functions.elementary.exponential import log
from sympy.physics.quantum.qexpr import _qsympify_sequence
from sympy.core import sympify
from sympy.core.numbers import Number
from sympy.matrices.matrices import Matrix

class Density(QExpr):
    """
       Generic Density operator object
       The calling convention will be densityOp([state1, prob1],... [staten, probn])
    """

    _label_separator = u' + '
    
    @classmethod
    def _eval_args(cls, args):
        """
            This will check to make sure that all of the pure state hilbert
            spaces contained within it are contained in the same hilbert space?
        """
        for i in xrange(2):
            if isinstance(args[-i-1], list):
                args = args + (1,)
        args = sympify(args)        
        #do check to make sure first comes prob, then state
        for item in args[:-2]:
            assert isinstance(item[1], Number)
                    
        return args
    
    @classmethod
    def _eval_hilbert_space(cls, args):
        """
            The hilbert space is determined by looking at the hilbert space of 
            the internal pure states
            
            for now just return hilbertspace
        """
        return HilbertSpace()
    
    @property    
    def label(self):
        """
            needs to create a tuple of matrix elements in density matrix
            e.g (2*|00><00|, 3*|01><01|)
        
        """
        ret_val = tuple()
        for state in self.state_part:
            ret_val = ret_val + (self.lhs*state[0]*Dagger(state[0])*state[1]*self.rhs,)
        return ret_val

    #Should I move the operators into the density at Mul, or on  
    
    def getstate(self, index):
        #returns the state in place index
        state = self.args[index][0]
        return state
    
    def getprob(self, index):
        #returns the prob in place index
        prob = self.args[index][1]
        return prob
    
    @property
    def state_part(self):
        return self.args[:-2]
    
    @property
    def lhs(self):
        return self.args[-2]
    
    @property
    def rhs(self):
        return self.args[-1]
        
    def operate_on(self, operators):
        args_list = list(self.args)
        args_list[-1] = self.rhs*Dagger(operators)
        args_list[-2] = operators*self.lhs
        return Density(*args_list)
    
    #-------------------------------------------------------------------------
    # Represent
    #-------------------------------------------------------------------------

    def _represent_default_basis(self, **options):
        return self._represent_ZGate(None, **options)

    def _represent_ZGate(self, basis, **options):
        bits = options['nqubits']
        state_m = represent(self.getstate(0), nqubits=bits)
        m = state_m*state_m.H*self.getprob(0)

        for i in xrange(len(self.args)-3):
            state_m = represent(self.getstate(i+1), nqubits=bits)
            m += state_m*state_m.H*self.getprob(i+1)
        m = represent(self.lhs, nqubits=bits)*m*represent(self.rhs, nqubits=bits)
        return m 

    #-------------------------------------------------------------------------
    # Apply
    #-------------------------------------------------------------------------
    def _apply_density(self, **options):
        from sympy.physics.quantum.qapply import qapply
        result = []
        for state in self.state_part:
            result.append([qapply(self.lhs*state[0], **options), state[1]])
        result.append(1)
        result.append(1)
        return Density(*result)
            

    def entropy(self,nqubits):
        """
            Von Neumann entropy is defined to be sum(lambda*ln(lambda)) 
            where lambda is the eigenvalue of a matrix
        """
        rho = represent(self, nqubits=nqubits)
        from scipy.linalg import eigvals
        return -sum([(eigen*log(eigen)).evalf() for eigen in eigvals(rho).tolist() if eigen != 0])
        
def matrix_to_density(mat):
    """
       Works by finding the eigenvectors and eigenvalues of the matrix.
       We know we can decompose rho by doing:
           sum(EigenVal*|Eigenvect><Eigenvect|)
    """
    from sympy.physics.quantum.qubit import matrix_to_qubit
    eigen = mat.eigenvects()
    #pull out all the eigenvectors and values from the 
    #poorly designed eigenvects method
    return Density(*[[matrix_to_qubit(Matrix([vector,])),x[0]] for x in eigen for vector in x[2] if x[0] != 0])
    
def reduced_density(state, unobserved_qubit, **options):
    def find_index_that_is_projected(j, k, unobserved_qubit):
         bit_mask = 2**unobserved_qubit - 1
         return ((j >> unobserved_qubit) << (1 + unobserved_qubit)) + (j & bit_mask) + (k << unobserved_qubit)

    old_density = represent(state, **options)
    old_size = old_density.cols
    new_size = old_size/2
    new_density = Matrix().zeros(new_size)
    for i in xrange(new_size):
        for j in xrange(new_size):
            for k in xrange(2):
                col = find_index_that_is_projected(j,k,unobserved_qubit)
                row = find_index_that_is_projected(i,k,unobserved_qubit)
                new_density[i,j] += old_density[row, col]          
    return Matrix(new_density)
    
