package technology.workhorse.benchmarks;

import org.apache.commons.math3.complex.Complex;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.ToIntFunction;

public class Julia {

    private List<Double> x = new ArrayList<>();
    private List<Double> y = new ArrayList<>();

    private List<Complex> zs = new ArrayList<>();
    private Complex cs;

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

        buildCoords(desiredWidth, x1, x2, y1, y2, cReal, cImag);

        System.out.println("Length of x:" + x.size());
        System.out.println("Total elements:" + zs.size());
        long start_time = System.currentTimeMillis();
        int output[] = calculate(maxIterations, zs, cs);

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Calculate took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum() );
        assert (Arrays.stream(output).sum() == 531748552);
    }

    @Test
    public void testParallel() {
        int parallelism = 0;
        int desiredWidth = 4000;
        int maxIterations = 300;
        double x1 = -1.8;
        double x2 = 1.8;
        double y1 = -1.8;
        double y2 = 1.8;

        double cReal = -0.62772;
        double cImag = -.42193;

        buildCoords(desiredWidth, x1, x2, y1, y2, cReal, cImag);

        System.out.println("Length of x:" + x.size());
        System.out.println("Total elements:" + zs.size());
        long start_time = System.currentTimeMillis();
        int output[] = calculateParallel(maxIterations, zs, cs,parallelism);

        double secs = (System.currentTimeMillis() - start_time) / 1000.0;
        System.out.println("Calculate took " + secs + " seconds");

        // this sum is expected for 4000^2 grid with 300 iterations
        System.out.println(Arrays.stream(output).sum() );
        assert (Arrays.stream(output).sum() == 531748552);
    }

    private int[] calculateParallel(int maxIterations, List<Complex> zs, Complex cs, int parallelism) {
        ToIntFunction<Complex> calculation = (z) -> {
            int n = 0;
            while (n < maxIterations && z.abs() < 2) {
                z = z.multiply(z).add(cs);
                n++;
            }
            return n;
        };

//        if (parallelism < 1) {
            return zs.parallelStream().mapToInt(calculation).toArray();
//        } else {
//
//            ForkJoinPool customThreadPool = new ForkJoinPool(parallelism);
//            return customThreadPool.submit(zs.parallelStream().mapToInt(calculation).toArray());
//        }
    }

    private int[] calculate(int maxIterations, List<Complex> zs, Complex cs) {

        int[] output = new int[zs.size()];

        for (int i = 0; i < output.length; i++) {
            int n = 0;
            Complex z = zs.get(i);

            while (n < maxIterations && z.abs() < 2) {
                z = z.multiply(z).add(cs);
                n++;
            }
            output[i] = n;
        }
        return output;
    }

    private void buildCoords(int desiredWidth, double x1, double x2, double y1, double y2, double cReal, double cImag) {
        double xStep = ((x2 - x1) / (double) (desiredWidth));
        double yStep = ((y2 - y1) / (double) (desiredWidth));

        for (double ycoord = y1; ycoord < y2; ycoord += yStep) {
            y.add(ycoord);
        }


        for (double xcoord = x1; xcoord < x2; xcoord += xStep) {
            x.add(xcoord);
        }

        for (Double ycoord : y) {
            for (Double xcoord : x) {
                zs.add(new Complex(xcoord, ycoord));
            }
        }

        cs = new Complex(cReal,cImag);

    }

}
