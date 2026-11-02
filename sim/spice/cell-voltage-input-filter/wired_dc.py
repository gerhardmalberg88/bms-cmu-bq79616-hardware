"""Independent DC MNA for verification and exact incremental coordinates.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from wired_study import configured, number

def independent_dc(base,case, return_currents=False):
    d=configured(base,case)
    names=sorted({x for f in d.values() for x in f[1:3]}-{'0'})
    ni={n:i for i,n in enumerate(names)}
    branches=[name for name in d if name[0] in 'VL']
    bi={n:len(ni)+i for i,n in enumerate(branches)}
    a=lil_matrix((len(ni)+len(bi),)*2);b=np.zeros(a.shape[0])
    def put(i,j,x):
        if i is not None and j is not None:a[i,j]+=x
    def adm(f,g):
        p,n=ni.get(f[1]),ni.get(f[2])
        put(p,p,g);put(n,n,g);put(p,n,-g);put(n,p,-g)
    for name,f in d.items():
        kind=name[0];p,n=ni.get(f[1]),ni.get(f[2])
        if kind=='R':adm(f,1/number(f[3]))
        elif kind=='S':
            control=d['V_enable'+name[6:]][3].split()
            active=float(control[1])
            adm(f,1e-10+(1/case.get('ron',2.5)-1e-10)*active)
        elif kind=='I':
            value=number(' '.join(f[3:]).split()[1])
            if p is not None:b[p]-=value
            if n is not None:b[n]+=value
        elif kind in 'VL':
            k=bi[name];put(p,k,1);put(n,k,-1);put(k,p,1);put(k,n,-1)
            if kind=='V':b[k]=number(' '.join(f[3:]).split()[1])
        elif kind!='C':raise ValueError('Unstamped '+name)
    a=a.tocsr();x=spsolve(a,b)
    if not np.isfinite(x).all():raise ValueError('Independent DC solve failed')
    voltages={n:float(x[i]) for n,i in ni.items()}|{'0':0.}
    residual=float(np.max(abs(a@x-b)))
    if return_currents:
        return voltages,residual,{name:float(x[i]) for name,i in bi.items()}
    return voltages,residual
