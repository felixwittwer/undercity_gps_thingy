import time
import board
import busio
import adafruit_bno055
import math


class SimpleKalman:
    def __init__(self, process_noise=0.01, sensor_noise=0.5, estimated_error=1.0):
        self.q = process_noise
        self.r = sensor_noise
        self.p = estimated_error
        self.x = 0.0

    def update(self, measurement):
        self.p += self.q
        k = self.p / (self.p + self.r)
        self.x += k * (measurement - self.x)
        self.p *= (1 - k)
        return self.x

def rotate_vector(q, v):
    w, x, y, z = q
    vx, vy, vz = v
    ww, xx, yy, zz = w*w, x*x, y*y, z*z
    wx, wy, wz = w*x, w*y, w*z
    xy, xz, yz = x*y, x*z, y*z

    rx = (ww + xx - yy - zz) * vx + 2 * ((xy - wz) * vy + (xz + wy) * vz)
    ry = 2 * ((xy + wz) * vx + (ww - xx + yy - zz) * vy + (yz - wx) * vz)
    rz = 2 * ((xz - wy) * vx + (yz + wx) * vy + (ww - xx - yy + zz) * vz)

    return (rx, ry, rz)

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bno055.BNO055_I2C(i2c)

print("Calibrating bias... Keep sensor still!")
bias_samples = []
for _ in range(100):
    accel = sensor.linear_acceleration
    if accel is not None:
        bias_samples.append(accel)
    time.sleep(0.01)

bias_x = sum([a[0] for a in bias_samples]) / len(bias_samples)
bias_y = sum([a[1] for a in bias_samples]) / len(bias_samples)
bias_z = sum([a[2] for a in bias_samples]) / len(bias_samples)

print(f"Bias X={bias_x:.3f}, Y={bias_y:.3f}, Z={bias_z:.3f}")
print("Starting position tracking...")

kf_x = SimpleKalman()
kf_y = SimpleKalman()
kf_z = SimpleKalman()

velocity = [0.0, 0.0, 0.0]

local_position = [0.0, 0.0, 0.0]   # resets when device is still
global_position = [0.0, 0.0, 0.0]  # never resets

prev_time = time.monotonic()

movement_threshold = 0.5  # adjust as needed
still_time_required = 1.0
still_start = None
is_still = False

while True:
    now = time.monotonic()
    dt = now - prev_time
    prev_time = now

    accel = sensor.linear_acceleration
    quat = sensor.quaternion

    if accel is not None and quat is not None:
        ax_raw = accel[0] - bias_x
        ay_raw = accel[1] - bias_y
        az_raw = accel[2] - bias_z

        ax, ay, az = rotate_vector(quat, (ax_raw, ay_raw, az_raw))

        ax_f = kf_x.update(ax)
        ay_f = kf_y.update(ay)
        az_f = kf_z.update(az)

        accel_magnitude = math.sqrt(ax_f*ax_f + ay_f*ay_f + az_f*az_f)

        if accel_magnitude < movement_threshold:
            if still_start is None:
                still_start = now
            elif (now - still_start) >= still_time_required and not is_still:
                # Device is still, reset local reference frame and velocity
                velocity = [0.0, 0.0, 0.0]
                local_position = [0.0, 0.0, 0.0]
                is_still = True
                print("Device is still: local position reset")
        else:
            still_start = None
            is_still = False

            # Integrate acceleration to velocity and velocity to local_position
            for i, a in enumerate((ax_f, ay_f, az_f)):
                velocity[i] += a * dt
                local_position[i] += velocity[i] * dt

            # Add local_position changes to global_position
            for i in range(3):
                global_position[i] += local_position[i]
                local_position[i] = 0  # reset local after adding to global

        # Final coordinates = global + local (local is mostly zero except when moving)
        final_position = [global_position[i] + local_position[i] for i in range(3)]

        # print(f"Position -> X: {final_position[0]:.2f}  Y: {final_position[1]:.2f}  Z: {final_position[2]:.2f}")
        print(f"{final_position[0]:.2f},{final_position[1]:.2f},{final_position[2]:.2f}")

    else:
        print("Waiting for sensor data...")

    time.sleep(0.05)