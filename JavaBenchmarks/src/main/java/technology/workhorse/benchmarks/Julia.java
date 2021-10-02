package technology.workhorse.benchmarks;

import org.apache.commons.math3.complex.Complex;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.ToIntFunction;

public class Julia {

//    private List<Double> x = new ArrayList<>();
//    private List<Double> y = new ArrayList<>();

    private List<Complex> zs = new ArrayList<>();


    /**
     * This is a close to copy and paste of the naive implementation from the python example
     */
    @Test
    public void testNaive() {
        int desiredWidth = 4000;
        int maxIterations = 300;
        double x1 = -1.8;
        double x2 = 1.8;
        double y1 = -1.8;
        double y2 = 1.8;

        double cReal = -0.62772;
        double cImag = -.42193;

        buildCoords(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zs.size());
        int[] output = new int[zs.size()];

        long start_time = System.currentTimeMillis();
        calculateNaive(maxIterations, zs, new Complex(cReal,cImag), output);

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Calculate took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());

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

    private double[][] buildCoordsPerf(int desiredWidth, double x1, double x2, double y1, double y2) {
        double out[][] = new double[desiredWidth*desiredWidth][2];
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
        int desiredWidth = 4000;
        int maxIterations = 300;
        double x1 = -1.8;
        double x2 = 1.8;
        double y1 = -1.8;
        double y2 = 1.8;

        double cReal = -0.62772;
        double cImag = -.42193;

        double[][] zsPerf = buildCoordsPerf(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zsPerf.length);
        long start_time = System.currentTimeMillis();
        int[] output = Arrays.stream(zsPerf).mapToInt(getIterativeCalcFunction(maxIterations, cReal, cImag)).toArray();

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Calculate took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());
    }


    @Test
    public void testOptCodeParallelStreams() {
        int parallelism = 0;
        int desiredWidth = 4000;
        int maxIterations = 300;
        double x1 = -1.8;
        double x2 = 1.8;
        double y1 = -1.8;
        double y2 = 1.8;

        double cReal = -0.62772;
        double cImag = -.42193;

        double[][] zsPerf = buildCoordsPerf(desiredWidth, x1, x2, y1, y2);

        System.out.println("Length of x:" + desiredWidth);
        System.out.println("Total elements:" + zsPerf.length);
        long start_time = System.currentTimeMillis();

        int[] output = Arrays.stream(zsPerf).parallel().mapToInt(getIterativeCalcFunction(maxIterations, cReal, cImag)).toArray();


        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Calculate took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum());
    }


    private void buildCoords(double desiredWidth, double x1, double x2, double y1, double y2) {
        // Redesigned because the python example exhibits poor floating point error accumulation

        for (double i = 0; i < desiredWidth; i++) {
            double x = (x1 * desiredWidth + (x2 - x1) * i) / desiredWidth;
            for (int j = 0; j < desiredWidth; j++) {
                double y = (y1 * desiredWidth + (y2 - y1) * j) / desiredWidth;
                zs.add(new Complex(x, y));
            }
        }

//        List<Double> x = new ArrayList<>();
//        List<Double> y = new ArrayList<>();
//        double xStep = ((x2 - x1) / (double) (desiredWidth));
//        double yStep = ((y2 - y1) / (double) (desiredWidth));
//
//        for (double ycoord = y1; ycoord < y2; ycoord += yStep) {
//            y.add(ycoord);
//        }
//
//
//        for (double xcoord = x1; xcoord < x2; xcoord += xStep) {
//            x.add(xcoord);
//        }
//
//        for (Double ycoord : y) {
//            for (Double xcoord : x) {
//                zs.add(new Complex(xcoord, ycoord));
//            }
//        }


    }

}
