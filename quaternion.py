import numpy as np
import plotly.express as px
import pandas as pd

pd.options.plotting.backend = "plotly"

# Fonction pour normaliser un quaternion
def normalize_quaternion(q):
    return q / np.linalg.norm(q)

# Fonction pour mettre à jour le quaternion avec le gyroscope
def update_quaternion_with_gyro(q, gyro, dt):
    wx, wy, wz = gyro
    #if
    # theta = np.linalg.norm(gyro) * dt  # Angle de rotation
    # if theta == 0:
    #     return q
    # axis = gyro / np.linalg.norm(gyro)  # Axe de rotation
    # dq = np.array([
    #     np.cos(theta / 2),
    #     np.sin(theta / 2) * axis[0],
    #     np.sin(theta / 2) * axis[1],
    #     np.sin(theta / 2) * axis[2],
    # ])
    #endif
    dq = np.array([1, wx*dt/2, wy*dt/2, wz*dt/2])
    # dq = normalize_quaternion(dq)
    # Mise à jour du quaternion : q_new = q * dq
    q_new = quaternion_multiply(q, dq)
    return normalize_quaternion(q_new)

# Fonction pour corriger le quaternion avec l'accéléromètre
def correct_quaternion_with_accel(q, accel):
    # Calcul du vecteur gravité attendu
    gravity = np.array([1, 0, 0])
    accel_norm = accel / np.linalg.norm(accel)  # Normalisation
    correction_axis = np.cross(accel_norm, gravity)  # Axe de correction
    correction_angle = np.arcsin(np.linalg.norm(correction_axis))  # Angle
    correction_axis = correction_axis / np.linalg.norm(correction_axis)
    dq = np.array([
        np.cos(correction_angle / 2),
        np.sin(correction_angle / 2) * correction_axis[0],
        np.sin(correction_angle / 2) * correction_axis[1],
        np.sin(correction_angle / 2) * correction_axis[2],
    ])
    # Appliquer la correction
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

import numpy as np

def quaternion_to_euler(q):
    """
    Convertit un quaternion en angles d'Euler (roll, pitch, yaw).

    Paramètres :
    q : array-like, [w, x, y, z]
        Le quaternion sous la forme [w, x, y, z].

    Retourne :
    tuple (roll, pitch, yaw) en radians.
    """
    w, x, y, z = q

    # Calcul du roulis (roll)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x**2 + y**2)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Calcul du tangage (pitch)
    # sinp = 2 * (w * y - z * x)
    # if abs(sinp) >= 1:
    #     pitch = np.sign(sinp) * np.pi / 2  # Gérer la singularité
    # else:
    #     pitch = np.arcsin(sinp)
    sinp = np.sqrt(1 + 2 * (w * y - x * z))
    cosp = np.sqrt(1 - 2 * (w * y - x * z))
    pitch = 2 * np.arctan2(sinp, cosp) - np.pi / 2

    # Calcul du lacet (yaw)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y**2 + z**2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw



if __name__ == '__main__':
    # Initialisation
    q = np.array([1, 0, 0, 0])  # Quaternion initial

    csv_file_name = "tests/VID_20240530_173115_003.csv"
    accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)

    # Calculate time starting to 0
    accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0])
    accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift(fill_value=0)

    accelerometer_table['ACC rotation X angle 3D'] = np.arctan2(accelerometer_table['Acc X'], np.sqrt(
                                        np.power(accelerometer_table['Acc Y'], 2) + 
                                        np.power(accelerometer_table['Acc Z'], 2) )  )
    accelerometer_table['ACC rotation Y angle 3D'] = np.arctan2(accelerometer_table['Acc Z'], np.sqrt(
                                        np.power(accelerometer_table['Acc Y'], 2) + 
                                        np.power(accelerometer_table['Acc X'], 2) )  )
    accelerometer_table['ACC rotation Z angle 3D'] = np.arctan2(-accelerometer_table['Acc Y'], np.sqrt(
                                        np.power(accelerometer_table['Acc X'], 2) + 
                                        np.power(accelerometer_table['Acc Z'], 2) )  )

    accelerometer_table['Rotation X'] = 0.0
    accelerometer_table['Rotation Y'] = 0.0
    accelerometer_table['Rotation Z'] = 0.0

    for index in accelerometer_table.index:
        # Mise à jour avec le gyroscope
        gyro_data = np.array([accelerometer_table['Rot X'][index], accelerometer_table['Rot Y'][index], accelerometer_table['Rot Z'][index]])
        q = update_quaternion_with_gyro(q, gyro_data, accelerometer_table['Time delta'][index])

        # Correction avec l'accéléromètre
        # accel_data = np.array([accelerometer_table['Acc X'][index], accelerometer_table['Acc Y'][index], accelerometer_table['Acc Z'][index]])
        # q = correct_quaternion_with_accel(q, accel_data)

        # roll, pitch, yaw = quaternion_to_euler(q)
        # accelerometer_table.loc[index, 'Rotation X'] = roll
        # accelerometer_table.loc[index, 'Rotation Y'] = pitch   
        # accelerometer_table.loc[index, 'Rotation Z'] = yaw

        accelerometer_table.loc[index, 'w'] = q[0]
        accelerometer_table.loc[index, 'x'] = q[1]
        accelerometer_table.loc[index, 'y'] = q[2]
        accelerometer_table.loc[index, 'z'] = q[3]

    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')
    # Display graph
    graph = accelerometer_table.plot()
    graph.show()

    html_file_name = csv_file_name.split('.')[0] + '_q.html'
    graph.write_html(html_file_name)

    # Generate json file
    json_file_name = csv_file_name.split('.')[0] + '.json'
    accelerometer_table.filter(['w', 'x', 'y', 'z'], axis=1).reset_index().to_json(json_file_name, orient='records', indent=2)
