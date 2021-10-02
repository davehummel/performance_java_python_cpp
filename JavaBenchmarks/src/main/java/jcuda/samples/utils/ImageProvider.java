package jcuda.samples.utils;

public abstract class ImageProvider {
    public abstract int[] getDimensions();
    public abstract byte[] getImage();

    private boolean renderReady = false;
    private boolean terminated = false;

    public boolean isTerminated(){
        return terminated;
    }

    public void terminate(){
        terminated = true;
        renderNow();
    }

    boolean holdRenderer(){
        if (terminated)
            return false;
        synchronized (this){
            renderReady = true;
            try {
                this.wait();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        return true;
    }
    void completeRenderer(){
        synchronized (this){
            renderReady = false;
            this.notify();
        }
    }

    public boolean isRenderReady(){
        return renderReady;
    }

    public boolean renderNow(){
        synchronized (this){
            if (renderReady) {
                this.notify();
                try {
                    this.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                return true;
            } else {
                return false;
            }
        }
    }
}
