<br>

<div align="center">

![Static Badge](https://img.shields.io/badge/Hack_Club_UNDERCITY-Hack_Club?style=flat&logo=hackclub&color=white)

![Adafruit](https://img.shields.io/badge/adafruit-000000?style=for-the-badge&logo=adafruit&logoColor=white) ![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)

</div>

<br>

# undercity_gps_thingy
a nextgen GPS handheld that uses an IMU for better accuracy

be aware that this was a single person project made during UNDERCITY a hardware hackathon. Therefore some things are not quite as polished due to time constarins.

## Case

I know scrrenshots of CAd software isn't our best friend but just so you know where everything goes and how it was designed to look like :)

<img src="./images/cad_screenshot.png" width="600" />

<br>

Now a real world image of the parts half assembled.

<img src="./images/half_assembled.jpg" width="600" />

<img src="./images/some_things_inside_the_case.jpg" width="600" />

## Firmware

There will are two separate firmware files one for the ESP32 S3 on the [Qualia board](/firmware/qualia%20ESP32%20S3%20(display%20controling)/) to drive the display and recieve the sensor data and [one for](/firmware/sensorreading%20stuff/) the seperate microcontroller who is collecting the data from the BNO-055.

## rough schematics (only so you know what to solder)

<img src="./schematics/schematics.png" width="600" />

## BOM (at Undercity dev boards and breakout boards are used later a PCB might be a good idea)

sensors
- BNO055 (https://www.adafruit.com/product/2472)
- GPS module (https://www.adafruit.com/product/4279)
display/ display driver
- Adafruit Qualia (https://www.adafruit.com/product/5800)
- 4" Square Touchscreen (https://www.adafruit.com/product/5794)
computing
- Raspberry Pi Zero

## Credits
- Raspberry Pi Zero 2W Symbol and Footprint by Raspberry Pi
  https://www.snapeda.com/parts/RASPBERRY%20PI%20ZERO%202%20W/Raspberry%20Pi/view-part/
- ultimate GPS module 3D model by Jason Febbraro
  https://grabcad.com/library/adafruit-ultimate-gps-gnss-with-usb-4279-1
- BNO-055 IMU module 3D model by Brey Caraway
  https://grabcad.com/library/adafruit-bno055-9-dof-imu-stemma-qt-1