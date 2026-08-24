from timdr_radar import TIMDRRadar
from rcs_sphere import rcs_sphere, classify_regime, SPEED_OF_LIGHT_M_S

radar = TIMDRRadar()

traj = [
    [0, 0, 0],
    [1, 0.2, 1],
    [2, 0.5, 2],
    [3, 1.2, 3],
    [4, 2.5, 4],
]

flow = radar.timdr_flow(traj)
twist = radar.twist(traj)
stable = radar.trm_reduce(traj)
pred = radar.predict(traj)

print("TIMDR-flow:", flow)
print("Twist points:", twist)
print("Stabilized:", stable)
print("Prediction:", pred)

# --- RCS w reżimie rezonansowym (Mie) - patrz rcs_sphere.py ---
print("\nRCS idealnie przewodzacej kuli o promieniu 0.5m w funkcji czestotliwosci:")
radius = 0.5
for freq_ghz in [0.1, 0.3, 0.5, 1.0, 3.0, 10.0]:
    freq_hz = freq_ghz * 1e9
    wavelength = SPEED_OF_LIGHT_M_S / freq_hz
    ka = 2 * 3.141592653589793 * radius / wavelength
    sigma = rcs_sphere(freq_hz, radius)
    print(f"  f={freq_ghz:5.2f} GHz  ka={ka:6.2f}  rezim={classify_regime(ka):11s}  RCS={sigma:.4f} m^2")
