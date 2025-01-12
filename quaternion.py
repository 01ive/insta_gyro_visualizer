import numpy as np

# Fonction pour normaliser un quaternion
def normalize_quaternion(q):
    return q / np.linalg.norm(q)

# Fonction pour mettre à jour le quaternion avec le gyroscope
def update_quaternion_with_gyro(q, gyro, dt):
    wx, wy, wz = gyro
    dq = np.array([1, wx*dt/2, wy*dt/2, wz*dt/2])
    dq = normalize_quaternion(dq)
    # Mise à jour du quaternion : q_new = q * dq
    q_new = quaternion_multiply(q, dq)
    return normalize_quaternion(q_new)

# Multiplication de quaternions
def quaternion_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])

def quaternion_to_euler(q):
    w, x, y, z = q

    # Calcul du roulis (roll)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x**2 + y**2)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Calcul du tangage (pitch)
    sinp = np.sqrt(1 + 2 * (w * y - x * z))
    cosp = np.sqrt(1 - 2 * (w * y - x * z))
    pitch = 2 * np.arctan2(sinp, cosp) - np.pi / 2

    # Calcul du lacet (yaw)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y**2 + z**2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw
