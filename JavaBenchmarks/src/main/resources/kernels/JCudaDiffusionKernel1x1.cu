extern "C"



__global__ void add(double *deltas,double *in, double *out)
{
    uint32_t iStep = blockDim.x * gridDim.x ;
    // Assume squares here
//     uint32_t jStep = blockDim.y * gridDim.y ;
    uint32_t i = blockIdx.x * blockDim.x  + threadIdx.x;

    uint32_t j = (blockIdx.y * blockDim.y  + threadIdx.y)*iStep;

out[i+j] = in[i+j] + deltas[0]*deltas[1] *( -4 * in[i+j] + in[((blockIdx.x * blockDim.x  + threadIdx.x) -1)%iStep+j] + in[((blockIdx.x * blockDim.x  + threadIdx.x) +1)%iStep +j] + in[i+((blockIdx.y * blockDim.y  + threadIdx.y) -1)%iStep *iStep] + in[i+((blockIdx.y * blockDim.y  + threadIdx.y) +1)%iStep *iStep]) ;

}
