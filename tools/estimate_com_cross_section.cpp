// SPDX-License-Identifier: CERN-OHL-P-2.0
// Reproduction of the illustrative CMU-007 cross-section calculation.
// Fixed snapshot: H=.190 mm, T=.035 mm, Er=4.5, mask=.035 mm, mask Er=3.3.
// Usage: estimate_com_cross_section [grid_mm extent_mm width_mm gap_mm]
// This does not read the KiCad design. Review these inputs after stackup changes.
#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
// Independent finite-volume electrostatic cross-section check, not a qualified solver.
// Odd-mode symmetry at x=0; one trace at +1 V, bottom plane at zero.
// All lengths in mm. Relative capacitance per length is dimensionless (C / eps0).
struct Result { double c; int iterations; double residual; };
Result solve(double d, double extent, double er, int coat, double w, double s,
             double h, double t, double mask, double emask) {
    int n = int(std::lround(extent/d))+1;
    int size=n*n;
    std::vector<double> v(size,0), ex(size,0), ey(size,0);
    std::vector<unsigned char> metal(size,0);
    auto idx=[n](int i,int j){return j*n+i;};
    auto eps=[=](double x,double y){
        if(er==1) return 1.0;
        if(y<h-1e-10) return er;
        if(coat==1 && y<h+t+mask) return emask; // planarized upper surface
        if(coat==2) {
            if(y<h+mask) return emask;
            double dx=std::max(std::max(s/2-x,x-(s/2+w)),0.0);
            double dy=std::max(y-(h+t),0.0);
            if(dx*dx+dy*dy<mask*mask) return emask; // conformal coating
        }
        return 1.0;
    };
    for(int j=0;j<n;j++) for(int i=0;i<n;i++) {
        int k=idx(i,j); double x=i*d,y=j*d;
        if(x>=s/2-1e-9 && x<=s/2+w+1e-9 && y>=h-1e-9 && y<=h+t+1e-9)
            metal[k]=1, v[k]=1;
        ex[k]=0.5*(eps(x+d/2,y+d/4)+eps(x+d/2,y-d/4));
        ey[k]=0.5*(eps(x+d/4,y+d/2)+eps(x-d/4,y+d/2));
    }
    double omega=1.96;
    double residual=0;
    int iter=0;
    for(iter=0;iter<14000;iter++) {
        residual=0;
        for(int j=1;j<n-1;j++) for(int i=1;i<n-1;i++) {
            int k=idx(i,j); if(metal[k]) continue;
            double den=ex[k]+ex[k-1]+ey[k]+ey[k-n];
            double vn=(ex[k]*v[k+1]+ex[k-1]*v[k-1]+ey[k]*v[k+n]+ey[k-n]*v[k-n])/den;
            double delta=vn-v[k];
            residual=std::max(residual,std::abs(delta));
            v[k]+=omega*delta;
        }
        if(residual<2e-10) break;
    }
    double charge=0;
    for(int j=1;j<n-1;j++) for(int i=1;i<n-1;i++) {
        int k=idx(i,j); if(!metal[k]) continue;
        if(!metal[k+1]) charge+=ex[k]*(1-v[k+1]);
        if(!metal[k-1]) charge+=ex[k-1]*(1-v[k-1]);
        if(!metal[k+n]) charge+=ey[k]*(1-v[k+n]);
        if(!metal[k-n]) charge+=ey[k-n]*(1-v[k-n]);
    }
    return {charge,iter,residual};
}
int main(int argc,char**argv) {
    double d=argc>1?std::atof(argv[1]):.005;
    double extent=argc>2?std::atof(argv[2]):1.0;
    double w=argc>3?std::atof(argv[3]):.21,s=argc>4?std::atof(argv[4]):.25,h=.19,t=.035,mask=.035,er=4.5,emask=3.3;
    if(argc>5 || !std::isfinite(d) || !std::isfinite(extent) ||
       !std::isfinite(w) || !std::isfinite(s) || d<=0 || w<=0 || s<=0 ||
       extent<=std::max(s/2+w,h+t+mask)+2*d || extent/d>1200) {
        std::fprintf(stderr,"Invalid geometry or grid (maximum 1200 cells per side).\n");
        return 1;
    }
    for(double length : {extent,s/2,w,h,t}) {
        if(std::abs(length/d-std::round(length/d))>1e-7) {
            std::fprintf(stderr,"Domain and conductor boundaries must align with the grid.\n");
            return 1;
        }
    }
    std::printf("H=%.3f T=%.3f W=%.3f S=%.3f mask=%.3f Er=%.2f mask_Er=%.2f\n",
                h,t,w,s,mask,er,emask);
    const double eta0=376.730313668;
    auto air=solve(d,extent,1,0,w,s,h,t,mask,emask);
    if(air.residual>=2e-10) return 2;
    std::printf("mesh_mm=%.6f extent_mm=%.3f air_C_over_eps0=%.9f iter=%d res=%.3g\n",d,extent,air.c,air.iterations,air.residual);
    std::fflush(stdout);
    for(int coat=0;coat<3;coat++) {
        auto result=solve(d,extent,er,coat,w,s,h,t,mask,emask);
        if(result.residual>=2e-10) return 2;
        double zdiff=2*eta0/std::sqrt(result.c*air.c);
        std::printf("coat=%d Zdiff=%.6f Zodd=%.6f C_over_eps0=%.9f iter=%d res=%.3g\n",coat,zdiff,zdiff/2,result.c,result.iterations,result.residual);
        std::fflush(stdout);
    }
}
