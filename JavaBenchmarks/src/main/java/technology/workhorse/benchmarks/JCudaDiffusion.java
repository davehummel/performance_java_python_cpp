/*
 * JCuda - Java bindings for NVIDIA CUDA
 *
 * Copyright 2008-2016 Marco Hutter - http://www.jcuda.org
 */
package technology.workhorse.benchmarks;

import jcuda.Pointer;
import jcuda.Sizeof;
import jcuda.driver.*;
import jcuda.samples.utils.JCudaSamplesUtils;

import java.io.IOException;

import static jcuda.driver.JCudaDriver.*;

/**
 * This is a sample class demonstrating how to use the JCuda driver
 * bindings to load and execute a CUDA vector addition kernel.
 * The sample reads a CUDA file, compiles it to a PTX file
 * using NVCC, loads the PTX file as a module and executes
 * the kernel function.
 */
public class JCudaDiffusion
{
    /**
     * Entry point of this sample
     *
     * @param args Not used
     * @throws IOException If an IO error occurs
     */
    public static void main(String args[]) throws IOException
    {
        // Enable exceptions and omit all subsequent error checks
        JCudaDriver.setExceptionsEnabled(true);

        // Create the PTX file by calling the NVCC
        String ptxFileName = JCudaSamplesUtils.preparePtxFile(
            "src/main/resources/kernels/JCudaVectorAddKernel.cu");

        // Initialize the driver and create a context for the first device.
        cuInit(0);
        CUdevice device = new CUdevice();
        cuDeviceGet(device, 0);
        CUcontext context = new CUcontext();
        cuCtxCreate(context, 0, device);

        // Load the ptx file.
        CUmodule module = new CUmodule();
        cuModuleLoad(module, ptxFileName);

        // Obtain a function pointer to the "add" function.
        CUfunction function = new CUfunction();
        cuModuleGetFunction(function, module, "add");

        int width = 512;
        int numElements = width*width;

        // Allocate and fill the host input data
        double hostInputA[] = new double[numElements];
        double hostInputB[] = new double[numElements];
        for(int i = 0; i < width; i++) {
            for(int j = 0; j < width; j++) {
                hostInputA[i+j*width] = (double) i+j*width;
                hostInputB[j+i*width] = (double) i+j*width;
            }
        }

        // Allocate the device input data, and copy the
        // host input data to the device
        CUdeviceptr deviceInputA = new CUdeviceptr();
        cuMemAlloc(deviceInputA, numElements * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceInputA, Pointer.to(hostInputA),
            numElements * Sizeof.DOUBLE);
        CUdeviceptr deviceInputB = new CUdeviceptr();
        cuMemAlloc(deviceInputB, numElements * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceInputB, Pointer.to(hostInputB),
            numElements * Sizeof.DOUBLE);

        // Allocate device output memory
        CUdeviceptr deviceOutput = new CUdeviceptr();
        cuMemAlloc(deviceOutput, numElements * Sizeof.DOUBLE);

        // Set up the kernel parameters: A pointer to an array
        // of pointers which point to the actual values.
        Pointer kernelParameters = Pointer.to(
            Pointer.to(new int[]{width,width}),
            Pointer.to(deviceInputA),
            Pointer.to(deviceInputB),
            Pointer.to(deviceOutput)
        );

        // Call the kernel function.
        int blockSizeX = 32;
        int gridSizeX = (int)Math.ceil((double)width / blockSizeX);
        cuLaunchKernel(function,
            gridSizeX,  gridSizeX, 1,      // Grid dimension
            blockSizeX, blockSizeX, 1,      // Block dimension
            0, null,               // Shared memory size and stream
            kernelParameters, null // Kernel- and extra parameters
        );
        cuCtxSynchronize();

        // Allocate host output memory and copy the device output
        // to the host.
        double hostOutput[] = new double[numElements];
        cuMemcpyDtoH(Pointer.to(hostOutput), deviceOutput,
            numElements * Sizeof.DOUBLE);

        // Verify the result
        boolean passed = true;
        for(int i = 0; i < numElements; i++)
        {
            System.out.print(hostOutput[i]);
            if ((i+1)%128==0) {
                System.out.println();
            }else {
                System.out.print(",");
            }
        }
        System.out.println("Test "+(passed?"PASSED":"FAILED"));

        // Clean up.
        cuMemFree(deviceInputA);
        cuMemFree(deviceInputB);
        cuMemFree(deviceOutput);
    }


}
