extern "C"



__global__ void add(double *deltas,double *in, double *out)
{
    uint32_t iStep = blockDim.x * gridDim.x*2 ;
    // Assume squares here
//     uint32_t jStep = blockDim.y * gridDim.y ;
       uint32_t i = (blockIdx.x * blockDim.x  + threadIdx.x)*2;
//
       uint32_t __i = (i-2)%iStep;
       uint32_t _i = (i-1)%iStep;
       uint32_t i_ = (i+1)%iStep;
       uint32_t j = (blockIdx.y * blockDim.y  + threadIdx.y)*2;
       uint32_t __j = (j -2)%iStep*iStep;
       uint32_t _j = (j- 1)%iStep*iStep;
       uint32_t j_ = (j + 1)%iStep*iStep;
       j*= iStep;
//        out[_i+_j] = in[ _i+_j];
//         out[_i+j] = in[ _i+j];
//          out[i+_j] = in[ i+_j];
//           out[i+j] = in[i+j];
out[_i+_j] = in[_i+_j] + .2 *( -4 * in[_i+_j] + in[__i+_j] + in[_i+__j] + in[i+_j] + in[_i+j]);
out[i+_j] =  in[i+_j] + .2 *( -4 * in[i+_j] + in[_i+_j] + in[i+__j] + in[i_+_j] + in[i+j]);
out[_i+j] =   in[_i+j] + .2 *( -4 * in[_i+j] +  in[__i+j] + in[_i+_j] + in[i+j] + in[_i+j_]);
out[i+j] = in[i+j] + .2*( -4 * in[i+j] + in[_i+j] + in[i+_j] + in[i_+j] + in[i+j_]);
}
