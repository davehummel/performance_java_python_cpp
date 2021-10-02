/*
 * JCuda - Java bindings for NVIDIA CUDA
 *
 * Copyright 2008-2016 Marco Hutter - http://www.jcuda.org
 */
package technology.workhorse.benchmarks;

import jcuda.Pointer;
import jcuda.Sizeof;
import jcuda.driver.*;
import jcuda.samples.utils.ImageProvider;
import jcuda.samples.utils.JCudaSamplesUtils;
import jcuda.samples.utils.JavaFXRenderer;

import java.io.IOException;

import static jcuda.driver.JCudaDriver.*;

/**
 * This is a sample class demonstrating how to use the JCuda driver
 * bindings to load and execute a CUDA vector addition kernel.
 * The sample reads a CUDA file, compiles it to a PTX file
 * using NVCC, loads the PTX file as a module and executes
 * the kernel function.
 */
public class JCudaDiffusion {


    public static void initializeGrid(double[] grid, double setValue, double low, double high, int width) {
        int xStart = (int) (width * low);
        int xEnd = (int) (width * high);

        int yStart = (int) (width * low);
        int yEnd = (int) (width * high);

        for (int x = xStart; x < xEnd; x++) {
            for (int y = yStart; y < yEnd; y++) {
                grid[x + y * width] = setValue;
            }
        }
    }

    /**
     * Entry point of this sample
     *
     * @param args Not used
     * @throws IOException If an IO error occurs
     */
    public static void main(String args[]) throws IOException {


        // Enable exceptions and omit all subsequent error checks
        JCudaDriver.setExceptionsEnabled(true);

        // Create the PTX file by calling the NVCC
         double gridFactor = 1;
        String ptxFileName = JCudaSamplesUtils.preparePtxFile(
                "src/main/resources/kernels/JCudaDiffusionKernel1x1.cu");
//        double gridFactor = .5;
//        String ptxFileName = JCudaSamplesUtils.preparePtxFile(
//                "src/main/resources/kernels/JCudaDiffusionKernel2x2.cu");



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

        int width = 1024*2;
        int[] shape = {width, width};
        int numElements = width * width;
        int iterations = 10000;

        boolean render = false;
        boolean renderEveryFrame = true;

        byte[] image = render ? new byte[shape[0] * shape[1] * 3] : null;
        ImageProvider imageProvider = null;


        if (render) {
            imageProvider = new ImageProvider() {
                @Override
                public int[] getDimensions() {
                    return shape;
                }

                @Override
                public byte[] getImage() {
                    return image;
                }

            };
            final ImageProvider provider = imageProvider;
            new Thread(() -> JavaFXRenderer.launch(provider)).start();
        }

        // Allocate and fill the host input data
        double gridA[] = new double[numElements];
        double gridB[] = new double[numElements];
        initializeGrid(gridA, 1, .4, .5, width);
        double deltas[] = {.2, 1}; // {dt,D}

        // Allocate the device input data, and copy the
        // host input data to the device

        CUdeviceptr deviceGridA = new CUdeviceptr();
        cuMemAlloc(deviceGridA, numElements * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceGridA, Pointer.to(gridA),
                numElements * Sizeof.DOUBLE);
        CUdeviceptr deviceGridB = new CUdeviceptr();
        cuMemAlloc(deviceGridB, numElements * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceGridB, Pointer.to(gridB),
                numElements * Sizeof.DOUBLE);

        CUdeviceptr deviceDelta = new CUdeviceptr();
        cuMemAlloc(deviceDelta, 2 * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceDelta, Pointer.to(deltas),
                2 * Sizeof.DOUBLE);

        int blockSizeX = 32;
        int gridSizeX = (int) Math.ceil(((double) width * gridFactor) / blockSizeX);

        System.out.println("Compute Grid - x:" + gridSizeX + " y:" + gridSizeX);

        Pointer kernelParametersA = Pointer.to(
                Pointer.to(deviceDelta),
                Pointer.to(deviceGridA ), // alternate input and output on each run
                Pointer.to(deviceGridB )
        );

        Pointer kernelParametersB = Pointer.to(
                Pointer.to(deviceDelta),
                Pointer.to(deviceGridB ), // alternate input and output on each run
                Pointer.to(deviceGridA )
        );




        long startTime = System.currentTimeMillis();
        for (int i = 0; i < iterations; i++) {
            // Set up the kernel parameters: A pointer to an array
            // of pointers which point to the actual values.


            // Call the kernel function.

            cuLaunchKernel(function,
                    gridSizeX, gridSizeX, 1,      // Grid dimension
                    blockSizeX, blockSizeX, 1,      // Block dimension
                    0, null,               // Shared memory size and stream
                    (i%2 == 0)?kernelParametersA:kernelParametersB, null // Kernel- and extra parameters
            );
            if (render) {

                if ((renderEveryFrame || imageProvider.isRenderReady()) && !imageProvider.isTerminated()) {

                    cuCtxSynchronize();
                    cuMemcpyDtoH(Pointer.to(gridB), iterations % 2 == 0 ? deviceGridB : deviceGridA,
                            numElements * Sizeof.DOUBLE);

                    int pixel = 0;

                    for (double d : gridB) {
                        image[pixel] = (byte) (d * 255);
                        image[pixel + 1] = (byte) (d * d * 255);
                        image[pixel + 2] = (byte) (d * d * d * 255);
                        pixel += 3;
                    }

                    boolean success = false;
                    do {
                        success = imageProvider.renderNow();
                    }
                    while (!success && renderEveryFrame && !imageProvider.isTerminated());
                }

            }

//          cuCtxSynchronize();
        }
        cuCtxSynchronize();
        cuMemcpyDtoH(Pointer.to(gridB), iterations % 2 == 0 ? deviceGridB : deviceGridA,
                numElements * Sizeof.DOUBLE);
        System.out.println("GPU (external time):" + (System.currentTimeMillis() - startTime) / 1000.0);


        // Allocate host output memory and copy the device output
        // to the host.

        cuMemcpyDtoH(Pointer.to(gridB), iterations % 2 == 0 ? deviceGridA : deviceGridB,
                numElements * Sizeof.DOUBLE);

        System.out.println("Sum check A:" + sumCheck(gridB, width));

        // Clean up.
        cuMemFree(deviceGridA);
        cuMemFree(deviceGridB);

        if (render){
            imageProvider.terminate();
        }

    }

    static public double sumCheck(double[] grid, int width) {
        double out = 0;
        for (int x = 0; x < width; x++)
            for (int y = 0; y < width; y++)
                out += grid[x + y * width] * (x + y);

        return out;
    }


}
