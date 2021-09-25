package technology.workhorse.benchmarks;

//import org.ejml.data.DMatrixIterator;
//import org.ejml.data.DMatrixRMaj;
//import org.ejml.dense.row.CommonOps_DDRM;

import org.junit.jupiter.api.Test;
import org.nd4j.linalg.api.buffer.DataType;
import org.nd4j.linalg.api.ndarray.INDArray;
import org.nd4j.linalg.api.ops.custom.Roll;
import org.nd4j.linalg.factory.Nd4j;
import org.nd4j.linalg.indexing.NDArrayIndex;
import org.nd4j.linalg.indexing.NDArrayIndexAll;

import java.util.Arrays;

public class Diffusion {
    static private int[] shape = {1024, 1024};
    static private int iterations = 5000;
    static private int concurrency = 16;

    static int threadCompleteCounter = 0;
    static volatile boolean[] threadCompleteArray = new boolean[concurrency];
    static Object threadSyncLock = new Object();


    public static void initializeGrid(double[][] grid, double setValue, double low, double high) {
        int xStart = (int) (grid.length * low);
        int xEnd = (int) (grid.length * high);

        int yStart = (int) (grid[0].length * low);
        int yEnd = (int) (grid[0].length * high);

        for (int x = xStart; x < xEnd; x++) {
            for (int y = yStart; y < yEnd; y++) {
                grid[x][y] = setValue;
            }
        }
    }

    public static void initializeGrid(INDArray grid, double setValue, double low, double high) {
        int xStart = (int) (grid.shape()[0] * low);
        int xEnd = (int) (grid.shape()[0] * high);

        int yStart = (int) (grid.shape()[1] * low);
        int yEnd = (int) (grid.shape()[1] * high);

        for (int x = xStart; x < xEnd; x++) {
            for (int y = yStart; y < yEnd; y++) {
                grid.put(x, y, setValue);
            }
        }

    }

    public static void evolve(double[][] current, double[][] target, double dt, double D, int startX, int endX) {
        int xSize = current.length;
        int ySize = current[0].length;

        int shiftXDown, shiftXUp, shiftYDown, shiftYUp;

        for (int i = startX; i < endX; i++) {
            if (i == 0)
                shiftXDown = xSize - 1;
            else
                shiftXDown = i - 1;
            if (i == xSize - 1)
                shiftXUp = 0;
            else
                shiftXUp = i + 1;

            for (int j = 0; j < ySize; j++) {

                if (j == 0)
                    shiftYDown = ySize - 1;
                else
                    shiftYDown = j - 1;
                if (j == ySize - 1)
                    shiftYUp = 0;
                else
                    shiftYUp = j + 1;


                target[i][j] = (current[i][j] * -4.0 +
                        current[shiftXDown][j] +
                        current[shiftXUp][j] +
                        current[i][shiftYDown] +
                        current[i][shiftYUp]) * D * dt + current[i][j];

            }
        }
    }



    public static Thread evolveThread(int threadCount, int threadID, double[][] a, double[][] b, double dt, double D, Object onComplete) {

        Thread thread = new Thread(() -> {

            double[][] current = a;
            double[][] target = b;

            int startX = (shape[0] * threadID) / threadCount;
            int endX = (shape[0] * (threadID + 1)) / threadCount;

            System.out.println("Thread " + threadID + " startX = " + startX + " endX = " + endX);

            synchronized (threadSyncLock) {
                try {
                    synchronized (onComplete) {
                        onComplete.notify();
                    }
                    threadSyncLock.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            long threadStartTime = System.currentTimeMillis();
            double[][] swap;
            for (int i = 0; i < iterations; i++) {
                evolve(current, target, dt, D, startX, endX);
                swap = current;
                current = target;
                target = swap;

                // *** Hot wait
                int completeCount = 0;
                synchronized (threadSyncLock) {
                    threadCompleteArray[threadID] = true;
                    for (boolean threadComplete : threadCompleteArray) {
                        if (threadComplete)
                            completeCount++;
                    }
                }
                if (completeCount == concurrency) { // All threads have finished this pass, notify via map and continue
                    Arrays.fill(threadCompleteArray, false);
                } else { // Some threads are still working, wait in a hot loop until someone flips the map back to false
                    while (threadCompleteArray[threadID]) ;
                }
                // *** Sleep Wait
//                synchronized (threadSyncLock) {
//                    threadCompleteCounter++;
//                    if (threadCompleteCounter == concurrency) {
//                        threadCompleteCounter = 0;
//                        threadSyncLock.notifyAll();
//                    } else {
//                        try {
//                            threadSyncLock.wait();
//                        } catch (InterruptedException e) {
//                            e.printStackTrace();
//                        }
//
//                    }
//                }
            }
            System.out.println("Thread " + threadID + " Finished after " + (System.currentTimeMillis() - threadStartTime) / 1000.0);
            synchronized (onComplete) {
                onComplete.notify();
            }
        }, "evolve" + threadID);
        thread.setPriority(Thread.MAX_PRIORITY);
        return thread;
    }


    @Test
    public void threadedSimple() {


        double[][] a = new double[shape[0]][shape[1]];
        double[][] b = new double[shape[0]][shape[1]];

        initializeGrid(a, 1, .4, .5);

        Thread[] threadPool = new Thread[concurrency];

        Object onComplete = new Object();
        synchronized (onComplete) {
            for (int i = 0; i < concurrency; i++) {
                threadPool[i] = evolveThread(concurrency, i, a, b, .2, 1, onComplete);
                threadPool[i].start();
                try {
                    onComplete.wait(); // wait for thread to complete setup - waiting on threadSyncLock
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }

            long startTime = System.currentTimeMillis();

            synchronized (threadSyncLock) {
                threadSyncLock.notifyAll(); // Get all threads running
            }

            try {
                System.out.println("Main Thread Waiting...");
                onComplete.wait();
                System.out.println("Simple Threaded (external time):" + (System.currentTimeMillis() - startTime) / 1000.0);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

        System.out.println("Sum check A:" + sumCheck(a));
        System.out.println("Sum check B:" + sumCheck(b));


    }

    static public double sumCheck(double[][] grid) {
        double out = 0;
        for (int x = 0; x < shape[0]; x++)
            for (int y = 0; y < shape[1]; y++)
                out += grid[x][y] * (x + y);

        return out;
    }

    static public double sumCheck(INDArray grid) {
        double out = 0;
        for (int x = 0; x < shape[0]; x++)
            for (int y = 0; y < shape[1]; y++)
                out += grid.getDouble(x, y) * (x + y);

        return out;
    }

    public INDArray createRollMatrix(int shift, int size) {
        INDArray out = Nd4j.eye(size);
        shift = shift % size;
        if (shift < 0) shift = size + shift;
        out = Nd4j.vstack(out.get(NDArrayIndex.interval(shift, size), NDArrayIndex.all()), out.get(NDArrayIndex.interval(0, shift), NDArrayIndex.all()));
        return out;
    }


    public static void evolveMatrixMath(INDArray current, INDArray target, INDArray scratch, double dt, double D, int startX, int endX, INDArray rollLeftMultiplier, INDArray rollRightMultiplier) {
        current.mul(-4, target);

        current.mmul(rollLeftMultiplier, scratch);
        target.add(scratch, target);
        current.mmul(rollRightMultiplier, scratch);
        target.add(scratch, target);
        rollLeftMultiplier.mmul(current, scratch);
        target.add(scratch, target);
        rollRightMultiplier.mmul(current, scratch);
        target.add(scratch, target);

        target.mul(dt * D, target);
        target.add(current, target);

    }

    public static void evolveMatrixRCOps(INDArray current, INDArray target, double dt, double D, int startX, int endX) {

        int xSize = shape[0];
        int ySize = shape[1];

        int shiftXDown, shiftXUp, shiftYDown, shiftYUp;

        for (int i = startX; i < endX; i++) {
            if (i == 0)
                shiftXDown = xSize - 1;
            else
                shiftXDown = i - 1;
            if (i == xSize - 1)
                shiftXUp = 0;
            else
                shiftXUp = i + 1;

            for (int j = 0; j < ySize; j++) {

                if (j == 0)
                    shiftYDown = ySize - 1;
                else
                    shiftYDown = j - 1;
                if (j == ySize - 1)
                    shiftYUp = 0;
                else
                    shiftYUp = j + 1;

                target.put(i, j, (current.getDouble(i, j) * -4.0 +
                        current.getDouble(shiftXDown, j) +
                        current.getDouble(shiftXUp, j) +
                        current.getDouble(i, shiftYDown) +
                        current.getDouble(i, shiftYUp)) * D * dt + current.getDouble(i, j));

            }
        }
    }


    @Test
    public void nd4JMatrixOps() {
        Nd4j.setDefaultDataTypes(DataType.DOUBLE, DataType.DOUBLE);

        INDArray a = Nd4j.zeros(DataType.DOUBLE, shape[0], shape[1]);
        INDArray b = Nd4j.zeros(DataType.DOUBLE, shape[0], shape[1]);

        INDArray scratch = Nd4j.zeros(DataType.DOUBLE, shape[0], shape[1]);

        INDArray rollLeftMultiplier = createRollMatrix(-1, shape[0]);
        INDArray rollRightMultiplier = createRollMatrix(1, shape[0]);

        initializeGrid(a, 1, .4, .5);

        INDArray current = a;
        INDArray next = b;
        INDArray swap;

        long startTime = System.currentTimeMillis();
        for (int i = 0; i < iterations; i++) {
            evolveMatrixRCOps(current, next, .2, 1, 0, shape[0]);
            swap = current;
            current = next;
            next = swap;
        }
        System.out.println("Simple:" + (System.currentTimeMillis() - startTime) / 1000.0);
        System.out.println("Sum check:" + sumCheck(current));
        synchronized (Thread.currentThread()) {
            Thread.currentThread().notify();
        }

    }


    @Test
    public void simple() {

        double[][] a = new double[shape[0]][shape[1]];
        double[][] b = new double[shape[0]][shape[1]];

        initializeGrid(a, 1, .4, .5);

        double[][] current = a;
        double[][] next = b;
        double[][] swap;
        long startTime = System.currentTimeMillis();
        for (int i = 0; i < iterations; i++) {
            evolve(current, next, .2, 1, 0, shape[0]);
            swap = current;
            current = next;
            next = swap;

        }
        System.out.println("Simple:" + (System.currentTimeMillis() - startTime) / 1000.0);
        System.out.println("Sum check:" + sumCheck(current));
        synchronized (Thread.currentThread()) {
            Thread.currentThread().notify();
        }
    }


//    public static void initializeMatrix(DMatrixRMaj grid, double setValue, double low, double high) {
//        int xStart = (int) (shape[0] * low);
//        int xEnd = (int) (shape[0] * high);
//
//        int yStart = (int) (shape[1] * low);
//        int yEnd = (int) (shape[1] * high);
//
//        DMatrixIterator iter = grid.iterator(true, yStart, xStart, yEnd, xEnd);
//        iter.set(setValue);
//        do {
//            iter.next();
//            iter.set(setValue);
//        } while (iter.hasNext());
//
//    }
//
//    public static void addIter(DMatrixIterator iterSource, DMatrixIterator iterTarget) {
//        while (iterSource.hasNext()) {
//            iterTarget.set(iterSource.next() + iterTarget.next());
//        }
//    }
//
//    static DMatrixRMaj shiftBuffer;
//
//    public static void evolve(DMatrixRMaj current, DMatrixRMaj target, double dt, double D) {
//        int xSize = shape[0];
//        int ySize = shape[1];
//        int shiftXDown, shiftXUp;
//        int shiftYDown, shiftYUp;
//
//        CommonOps_DDRM.scale(-4, current, target);
//
//        for (int i = 0; i < xSize; i++) {
//            if (i == 0)
//                shiftXDown = xSize - 1;
//            else
//                shiftXDown = i - 1;
//            if (i == xSize - 1)
//                shiftXUp = 0;
//            else
//                shiftXUp = i + 1;
//
//            for (int j = 0; j < ySize; j++) {
//
//                if (j == 0)
//                    shiftYDown = ySize - 1;
//                else
//                    shiftYDown = j - 1;
//
//                if (j == ySize - 1)
//                    shiftYUp = 0;
//                else
//                    shiftYUp = j + 1;
//
//                target.add(i, j, current.unsafe_get(shiftXDown, j)
//                        + current.unsafe_get(shiftXUp, j)
//                        + current.unsafe_get(i, shiftYDown)
//                        + current.unsafe_get(i, shiftYUp));
//
//            }
//        }
//
//        CommonOps_DDRM.addEquals(current, D * dt, target);
//
//    }
//
//
//    @Test
//    public void optimizedEMJL() {
//        DMatrixRMaj current = new DMatrixRMaj(shape[0], shape[1]);
//        DMatrixRMaj next = new DMatrixRMaj(shape[0], shape[1]);
//        shiftBuffer = new DMatrixRMaj(shape[0], shape[1]);
//
//        initializeMatrix(current, 1, .4, .5);
//
//        long startTime = System.currentTimeMillis();
//
//        for (int i = 0; i < iterations; i++) {
//            evolve(current, next, .2, 1);
//
//        }
//        System.out.println("Simple EMJL:" + (System.currentTimeMillis() - startTime) / 1000.0);
//
//    }
}