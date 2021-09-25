extern "C"
__global__ void add(int n, double *a, double *b, double *sum)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;

        sum[i,j] = j;

}
