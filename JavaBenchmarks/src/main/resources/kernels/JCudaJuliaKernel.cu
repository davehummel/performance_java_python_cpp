extern "C"
#include <thrust/complex.h>


__global__ void julia(double *complexAdditive,double *complexInputGrid, int *output)
{

    uint32_t i = blockIdx.x * blockDim.x  + threadIdx.x;


    uint16_t maxIterations = complexAdditive[0];
    double cReal = complexAdditive[1];
    double cImag = complexAdditive[2];

    double realPartSqr;
    double imagPartSqr;

    double z0 = complexInputGrid[i*2];
    double z1 = complexInputGrid[i*2+1];

    uint16_t n = 0;

    while (n < maxIterations && ((realPartSqr = z0 * z0) + (imagPartSqr = z1 * z1) < 4)) {
                z1 = 2 * z0 * z1 + cImag;
                z0 = realPartSqr - imagPartSqr + cReal;
                n++;
            }

    output[i] = n;

}
