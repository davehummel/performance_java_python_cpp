package jcuda.samples.utils;

import javafx.animation.AnimationTimer;
import javafx.application.Application;
import javafx.scene.Group;
import javafx.scene.Scene;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.image.PixelFormat;
import javafx.scene.image.PixelWriter;
import javafx.stage.Stage;

import java.util.Arrays;

public class JavaFXRenderer extends Application {


    static private ImageProvider provider;

    @Override
    public void start(Stage primaryStage) throws Exception {
        int[] dimensions = provider.getDimensions();
        primaryStage.setTitle("JavaFx Image Source Renderer");
        Group root = new Group();
        Canvas canvas  = new Canvas(dimensions[0],dimensions[1]);
        root.getChildren().add(canvas);
        Scene primaryScene = new Scene(root);
        primaryStage.setScene(primaryScene);
        primaryStage.setOnCloseRequest(event -> {
            provider.terminate();
        });
        primaryStage.show();
        AnimationTimer timer = new AnimationTimer() {
            @Override
            public void handle(long now) {
                GraphicsContext gc = canvas.getGraphicsContext2D();
                PixelWriter pw = gc.getPixelWriter();
                if (!provider.holdRenderer()){
                    return;
                }
                pw.setPixels(0,0,dimensions[0],dimensions[1], PixelFormat.getByteRgbInstance(),provider.getImage(),0,dimensions[1]*3);
                provider.completeRenderer();

            }
        };
        timer.start();
    }


    static public void launch(ImageProvider newProvider) {
        provider = newProvider;
        launch();
    }

    public static void main(String[] args) {
        launch(new NullProvider(1024,1024));
    }

    private static class NullProvider extends ImageProvider {
        private final int[] dimensions;
        private byte[] buffer;

        public NullProvider(int width, int height) {
            dimensions = new int[] {width,height};
            buffer = new byte[width*height*3];
            (new Thread(()->{
                while(true) {
                    try {
                        System.out.println("+");
                        Thread.sleep(1);
                        renderNow();
                        Arrays.fill(buffer, (byte) (System.currentTimeMillis() % 255));
                        if (isTerminated())
                            return;
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }

            })).start();
        }



        @Override
        public int[] getDimensions() {
            return dimensions;
        }

        @Override
        public byte[] getImage() {
            return buffer;
        }
    }
}
