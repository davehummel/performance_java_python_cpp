module jcuda.samples.utils {
    requires javafx.controls;
    requires javafx.fxml;
    requires jcuda;
    requires java.logging;
    requires org.junit.jupiter.api;
    requires commons.math3;


    opens jcuda.samples.utils to javafx.fxml;
    exports jcuda.samples.utils;
}