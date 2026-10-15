
#include <Accelerate/Accelerate.h>
extern "C" int solve_spd(int n, long *ptr, int *idx, double *val, int nrhs, double *rhs) {
    SparseMatrix_Double A = {};
    A.structure.rowCount=n; A.structure.columnCount=n;
    A.structure.columnStarts=ptr; A.structure.rowIndices=idx;
    A.structure.attributes.kind=SparseSymmetric;
    A.structure.attributes.triangle=SparseLowerTriangle;
    A.structure.blockSize=1; A.data=val;
    SparseSymbolicFactorOptions sf = _SparseDefaultSymbolicFactorOptions; sf.orderMethod=SparseOrderMetis;
    SparseNumericFactorOptions nf = _SparseDefaultNumericFactorOptions_Double;
    auto fact = SparseFactor(SparseFactorizationCholesky,A,sf,nf);
    if(fact.status!=SparseStatusOK) return fact.status;
    DenseMatrix_Double B = {};
    B.rowCount=n; B.columnCount=nrhs; B.columnStride=n; B.data=rhs;
    SparseSolve(fact,B);
    SparseCleanup(fact);
    return 0;
}
