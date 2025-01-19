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

def accelerometer_to_quaternion(ax, ay, az):
    """
    Convert accelerometer data to a quaternion representing orientation.

    Args:
        ax: Acceleration along X-axis.
        ay: Acceleration along Y-axis.
        az: Acceleration along Z-axis.

    Returns:
        A tuple (qw, qx, qy, qz) representing the quaternion.
    """
    # Vecteur gravité mesuré
    measured = np.array([ax, ay, az])
    norm = np.linalg.norm(measured)
    if norm == 0:
        raise ValueError("L'accélération ne peut pas être un vecteur nul.")
    measured /= norm

    # Vecteur gravité de référence
    reference = np.array([1, 0, 0])

    # Calcul de l'axe de rotation
    axis = np.cross(measured, reference)
    axis_norm = np.linalg.norm(axis)

    # Calcul de l'angle
    dot = np.dot(measured, reference)
    angle = np.acos(np.clip(dot, -1.0, 1.0))

    # Cas particulier : vecteurs parallèles ou antiparallèles
    if axis_norm < 1e-6:  # Les vecteurs sont alignés ou opposés
        if dot < 0:  # Opposés
            # Rotation de 180° autour d'un axe orthogonal quelconque
            axis = np.array([1, 0, 0]) if abs(measured[2]) < 0.999 else np.array([0, 1, 0])
            qw = 0
            qx, qy, qz = axis / np.linalg.norm(axis)
        else:  # Alignés
            return (1.0, 0.0, 0.0, 0.0)  # Pas de rotation
    else:
        axis /= axis_norm
        qw = np.cos(angle / 2)
        qx, qy, qz = axis * np.sin(angle / 2)

    return np.array([qw, qx, qy, qz])
