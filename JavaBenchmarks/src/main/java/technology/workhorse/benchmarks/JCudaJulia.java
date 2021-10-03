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
import java.util.Arrays;
import java.util.stream.DoubleStream;

import static jcuda.driver.JCudaDriver.*;

/**
 * This is a sample class demonstrating how to use the JCuda driver
 * bindings to load and execute a CUDA vector addition kernel.
 * The sample reads a CUDA file, compiles it to a PTX file
 * using NVCC, loads the PTX file as a module and executes
 * the kernel function.
 */
public class JCudaJulia {


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
                "src/main/resources/kernels/JCudaJuliaKernel.cu");
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
        cuModuleGetFunction(function, module, "julia");

        final int desiredWidth = 6000;
        final int maxIterations = 400;

        final int[] dimensions = new int[]{desiredWidth, desiredWidth};

        boolean render = false;


        byte[] image = render ? new byte[dimensions[0] * dimensions[1] * 3] : null;
        ImageProvider imageProvider = null;


        if (render) {
            imageProvider = new ImageProvider() {
                @Override
                public int[] getDimensions() {
                    return dimensions;
                }

                @Override
                public byte[] getImage() {
                    return image;
                }

            };
        }

        // Allocate and fill the host input data
        double cReal = -0.62772, cImag = -.42193;
        double x1 = -1.8, x2 = 1.8, y1 = -1.8, y2 = 1.8;


        double[] inputGrid = Julia.buildCoords(desiredWidth, x1, x2, y1, y2).stream().flatMapToDouble(
                complex -> DoubleStream.builder().add(complex.getReal()).add(complex.getImaginary()).build()).toArray();

        double[] additive = {maxIterations,cReal, cImag};

        int[] output = new int[dimensions[0] * dimensions[1]];

        // Allocate the device input data, and copy the
        // host input data to the device

        CUdeviceptr deviceInput = new CUdeviceptr();
        cuMemAlloc(deviceInput, inputGrid.length * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceInput, Pointer.to(inputGrid),
                inputGrid.length * Sizeof.DOUBLE);

        CUdeviceptr deviceOutput = new CUdeviceptr();
        cuMemAlloc(deviceOutput, output.length * Sizeof.INT);


        CUdeviceptr deviceAdditive = new CUdeviceptr();
        cuMemAlloc(deviceAdditive, 3 * Sizeof.DOUBLE);
        cuMemcpyHtoD(deviceAdditive, Pointer.to(additive),
                3 * Sizeof.DOUBLE);


        int blockSize = 256;
        int gridSize = (int) Math.ceil((double) desiredWidth * desiredWidth / blockSize);

        System.out.println("Compute Grid - " + gridSize);

        Pointer kernelParameters = Pointer.to(
                Pointer.to(deviceAdditive),
                Pointer.to(deviceInput),
                Pointer.to(deviceOutput)
        );


        long startTime = System.currentTimeMillis();


        // Call the kernel function.

        cuLaunchKernel(function,
                gridSize, 1, 1,      // Grid dimension
                blockSize, 1, 1,      // Block dimension
                0, null,               // Shared memory size and stream
                kernelParameters, null // Kernel- and extra parameters
        );

        cuCtxSynchronize();


        cuMemcpyDtoH(Pointer.to(output), deviceOutput,
                output.length * Sizeof.INT);

        double secs = (System.currentTimeMillis() - startTime) / 1000.0;
        System.out.println("Julia optimized GPU took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());

        // Clean up.
        cuMemFree(deviceInput);
        cuMemFree(deviceOutput);
        cuMemFree(deviceAdditive);

        if (render) {
            final ImageProvider provider = imageProvider;
            new Thread(() -> JavaFXRenderer.launch(provider)).start();
        }

        while (render && !imageProvider.isTerminated()){
            if (imageProvider.isRenderReady()) {

                int pixel = 0;

                for (int v : output) {
                    image[pixel] = (byte) ((Math.sqrt(v)*Math.sqrt(maxIterations))*(255.0/maxIterations));
                    image[pixel + 1] = image[pixel];
                    image[pixel + 2] = image[pixel];
                    pixel += 3;
                }


                imageProvider.renderNow();

            }
            try {
                Thread.sleep(1);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
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
