import numpy as np
import logging

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
        logging.debug("!!! Accelerometer and reference vector are aligned or opposite")
        if dot < 0:  # Opposés
            logging.debug("!!! Accelerometer and reference vector are opposite")
            # Rotation de 180° autour d'un axe orthogonal quelconque
            axis = np.array([1, 0, 0]) if abs(measured[2]) < 0.999 else np.array([0, 1, 0])
            qw = 0
            qx, qy, qz = axis / np.linalg.norm(axis)
        else:  # Alignés
            logging.debug("!!! Accelerometer and reference vector are aligned")
            return (1.0, 0.0, 0.0, 0.0)  # Pas de rotation
    else:
        axis /= axis_norm
        qw = np.cos(angle / 2)
        qx, qy, qz = axis * np.sin(angle / 2)

    return normalize_quaternion(np.array([qw, qx, qy, qz]))

def quaternion_difference(q1, q2):
    """Calcule la différence entre deux quaternions."""
    q2_conj = np.array([q2[0], -q2[1], -q2[2], -q2[3]])  # Conjugué de q2
    return quaternion_multiply(q1, q2_conj)

def kalman_filter_quaternion(P, q_gyro, q_acc, R_gyro, R_acc):
    """
    Filtre de Kalman pour fusionner deux quaternions représentant des positions.

    Args:
        P: Matrice de covariance de l'état (4x4).
        q_gyro: Quaternion provenant du gyroscope (prédiction).
        q_acc: Quaternion provenant de l'accéléromètre (mesure).
        R_gyro: Incertitude associée au gyroscope (bruit de processus).
        R_acc: Incertitude associée à l'accéléromètre (bruit de mesure).

    Returns:
        q_new: Nouveau quaternion de l'état (fusionné).
        P_new: Nouvelle matrice de covariance de l'état.
    """
    # Normalisation des quaternions
    # q_gyro = normalize_quaternion(q_gyro)
    # q_acc = normalize_quaternion(q_acc)

    # Prédiction
    q_pred = q_gyro
    P_pred = P + R_gyro

    # Innovation (erreur entre la mesure et la prédiction)
    delta_q = quaternion_difference(q_acc, q_pred)
    y = delta_q[1:]  # Erreur sur les axes (x, y, z)

    # Calcul du gain de Kalman
    S = P_pred + R_acc
    K = np.dot(P_pred, np.linalg.inv(S))  # Gain de Kalman

    # Mise à jour de l'état
    correction = np.dot(K, y)
    q_correction = np.array([np.sqrt(1 - np.sum(correction**2)), *correction])
    q_new = quaternion_multiply(q_pred, q_correction)
    q_new = normalize_quaternion(q_new)

    # Mise à jour de la covariance
    P_new = np.dot((np.eye(4) - K), P_pred)

    return q_new, P_new