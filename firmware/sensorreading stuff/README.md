# sensorreading stuff firmware

This folder contains all the firmware fileas needed to read the BNO-055 sensor and get the values into a usable format. They then get sent to the Qualia board to then get displaed and used there.

## code.py

Reading the BNO-055 sensor data via I2C. After that the raw aceleration data is going to be put though some calculations to get world koordinates with the startpoint as a reference. To try to compensate the drift that comes from integartion of the raw values the script applies a simple kalman filter to the raw values. Additional when there is less movement the values are zeroed out to keep noise and therfore drifta ta a minimum.