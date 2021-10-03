package technology.workhorse.benchmarks;

import jcuda.samples.utils.ImageProvider;
import jcuda.samples.utils.JavaFXRenderer;
import org.apache.commons.math3.complex.Complex;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.ToIntFunction;

public class Julia extends ImageProvider {

    private final int desiredWidth = 6000;
    private final int maxIterations = 400;
    private final int parrallelism = 16; // Ignored, auto set to CPU thread count, need to setup customer threadpool ...
    private final int[] dimensions = new int[]{desiredWidth, desiredWidth};


    private double cReal = -0.62772, cImag = -.42193;

    private double x1 = -1.8, x2 = 1.8, y1 = -1.8, y2 = 1.8;

    private final boolean render = false;

    private byte[] image = render ? new byte[dimensions[0] * dimensions[1] * 3] : null;


    /**
     * This is a close to copy and paste of the naive implementation from the python example
     */
    @Test
    public void testNaive() {

        List<Complex> zs = buildCoords(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zs.size());
        int[] output = new int[zs.size()];


        tryRender(output);

        long start_time = System.currentTimeMillis();
        calculateNaive(maxIterations, zs, new Complex(cReal, cImag), output);

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Julia naive single threaded took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());
        if (render) {
            new Thread(() -> JavaFXRenderer.launch(this)).start();
        }

        while (render && !isTerminated()){
            tryRender(output);
            try {
                Thread.sleep(1);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

    }

    private void calculateNaive(int maxIterations, List<Complex> zs, Complex cs, int[] output) {
        for (int i = 0; i < output.length; i++) {
            int n = 0;
            Complex z = zs.get(i);

            while (n < maxIterations && z.abs() < 2) {
                z = z.multiply(z).add(cs);
                n++;
            }
            output[i] = n;
        }
    }

    /**
     * Returns a list of complex numbers smoothly filling the range with x1 to x2 for real and y1 to y2 for imag components
     *
     * @param desiredWidth Number of cells in both real and complex direction.  Output size will be this value squared
     * @param x1 Real min
     * @param x2 Real max
     * @param y1 Complex min
     * @param y2 Complex max
     * @return An 1d array of double[2] complex numbers (real at index 0)
     */
    public static double[][] buildCoordsPerf(int desiredWidth, double x1, double x2, double y1, double y2) {
        double out[][] = new double[desiredWidth * desiredWidth][2];
        // Redesigned because the python book example exhibits poor floating point error accumulation

        int n = 0;
        for (double i = 0; i < desiredWidth; i++) {
            double x = (x1 * desiredWidth + (x2 - x1) * i) / desiredWidth;
            for (int j = 0; j < desiredWidth; j++) {
                double y = (y1 * desiredWidth + (y2 - y1) * j) / desiredWidth;
                out[n][0] = x;
                out[n][1] = y;
                n++;
            }
        }
        return out;

    }

    ToIntFunction<double[]> getIterativeCalcFunction(int maxIterations, double cReal, double cImag) {
        ToIntFunction<double[]> calculation = (z) -> {
            int n = 0;

            double realPartSqr;
            double imagPartSqr;

            while (n < maxIterations && ((realPartSqr = z[0] * z[0]) + (imagPartSqr = z[1] * z[1]) < 4)) {
                z[1] = 2 * z[0] * z[1] + cImag;
                z[0] = realPartSqr - imagPartSqr + cReal;
                n++;
            }
            return n;
        };
        return calculation;
    }

    @Test
    public void testOptCodeSingle() {

        double[][] zsPerf = buildCoordsPerf(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zsPerf.length);
        long start_time = System.currentTimeMillis();
        int[] output = Arrays.stream(zsPerf).mapToInt(getIterativeCalcFunction(maxIterations, cReal, cImag)).toArray();

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Julia optimized single threaded took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());
        if (render) {
            new Thread(() -> JavaFXRenderer.launch(this)).start();
        }

        while (render && !isTerminated()){
            tryRender(output);
            try {
                Thread.sleep(1);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }


    @Test
    public void testOptCodeParallelStreams() {


        double[][] zsPerf = buildCoordsPerf(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zsPerf.length);
        long start_time = System.currentTimeMillis();

        int[] output = Arrays.stream(zsPerf).parallel().mapToInt(getIterativeCalcFunction(maxIterations, cReal, cImag)).toArray();


        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Julia optimized parallel took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());
        if (render) {
            new Thread(() -> JavaFXRenderer.launch(this)).start();
        }

        while (render && !isTerminated()){
            tryRender(output);
            try {
                Thread.sleep(1);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    /**
     * Returns a list of complex numbers smoothly filling the range with x1 to x2 for real and y1 to y2 for imag components
     *
     * @param desiredWidth Number of cells in both real and complex direction.  Output size will be this value squared
     * @param x1 Real min
     * @param x2 Real max
     * @param y1 Complex min
     * @param y2 Complex max
     * @return A List of complex numbers
     */
    static public List<Complex> buildCoords(int desiredWidth, double x1, double x2, double y1, double y2) {
        // Redesigned because the python example exhibits poor floating point error accumulation
        List<Complex> zs = new ArrayList<Complex>(desiredWidth*2);
        for (double i = 0; i < desiredWidth; i++) {
            double x = (x1 * desiredWidth + (x2 - x1) * i) / desiredWidth;
            for (int j = 0; j < desiredWidth; j++) {
                double y = (y1 * desiredWidth + (y2 - y1) * j) / desiredWidth;
                zs.add(new Complex(x, y));
            }
        }
        return zs;
    }

    private void tryRender(int output[]) {

        if (isRenderReady()) {

            int pixel = 0;

            for (int v : output) {
                image[pixel] = (byte) ((Math.sqrt(v)*Math.sqrt(maxIterations))*(255.0/maxIterations));
                image[pixel + 1] = image[pixel];
                image[pixel + 2] = image[pixel];
                pixel += 3;
            }


            renderNow();

        }
    }

    @Override
    public int[] getDimensions() {
        return dimensions;
    }

    @Override
    public byte[] getImage() {
        return image;
    }
}
