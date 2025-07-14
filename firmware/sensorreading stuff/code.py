import time
import board
import busio
import adafruit_bno055
import math
import digitalio

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
local_position = [0.0, 0.0, 0.0]
global_position = [0.0, 0.0, 0.0]

prev_time = time.monotonic()

movement_threshold = 0.5
still_time_required = 1.0
still_start = None
is_still = False

# === Pulse output pin setup ===
pulse_pin = digitalio.DigitalInOut(board.TX)  # use TX or another pin
pulse_pin.direction = digitalio.Direction.OUTPUT
pulse_pin.value = False

# Pulse sending state machine variables
pulse_state = 0   # 0=idle, 1=sending x pulse, 2=x gap, 3=y pulse, 4=y gap, 5=z pulse, 6=z gap
pulse_start = 0
pulse_duration = 0
gap_duration = 0.05  # 50ms gap between pulses
send_interval = 1.0  # send position every 1 second
last_send_time = 0

# Coordinates to send (normalized)
coords_to_send = [0.0, 0.0, 0.0]

# Pulse length range
MIN_PULSE = 0.01  # 10 ms minimum pulse
MAX_PULSE = 0.5   # 500 ms maximum pulse
MAX_COORD_VALUE = 10.0  # expected max abs value of position for scaling


def coord_to_pulse_length(value):
    # Clamp to [-1,1]
    v = max(-1.0, min(1.0, value))
    # Map from [-1,1] to [MIN_PULSE, MAX_PULSE]
    return MIN_PULSE + (v + 1) / 2 * (MAX_PULSE - MIN_PULSE)

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
                velocity = [0.0, 0.0, 0.0]
                local_position = [0.0, 0.0, 0.0]
                is_still = True
                print("Device is still: local position reset")
        else:
            still_start = None
            is_still = False

            for i, a in enumerate((ax_f, ay_f, az_f)):
                velocity[i] += a * dt
                local_position[i] += velocity[i] * dt

            for i in range(3):
                global_position[i] += local_position[i]
                local_position[i] = 0

        final_position = [global_position[i] + local_position[i] for i in range(3)]

        print(f"Position -> X: {final_position[0]:.2f}  Y: {final_position[1]:.2f}  Z: {final_position[2]:.2f}")

        # Prepare coordinates to send once per second
        if (now - last_send_time) >= send_interval and pulse_state == 0:
            # Normalize coords to [-1,1] for pulse encoding
            coords_to_send = [max(-1.0, min(1.0, c / MAX_COORD_VALUE)) for c in final_position]
            pulse_state = 1  # start pulse sending
            last_send_time = now

    else:
        print("Waiting for sensor data...")

    # ===== Non-blocking pulse sending state machine =====
    if pulse_state != 0:
        if pulse_state in [1, 3, 5]:  # sending a pulse HIGH
            if pulse_start == 0:
                # start pulse
                pulse_start = now
                idx = (pulse_state - 1) // 2  # 0 for x, 1 for y, 2 for z
                pulse_duration = coord_to_pulse_length(coords_to_send[idx])
                pulse_pin.value = True
            elif (now - pulse_start) >= pulse_duration:
                # pulse done, go LOW and next gap state
                pulse_pin.value = False
                pulse_start = now
                pulse_state += 1  # advance to gap state

        elif pulse_state in [2, 4, 6]:  # sending LOW gap
            if (now - pulse_start) >= gap_duration:
                pulse_start = 0
                pulse_state += 1
                if pulse_state > 6:
                    pulse_state = 0  # done all pulses

    time.sleep(0.01)  # small sleep to yield CPU, maintain ~100Hz loop
