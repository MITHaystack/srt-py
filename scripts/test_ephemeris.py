from utilities.object_tracker import EphemerisTracker
import matplotlib.pyplot as plt

if __name__ == "__main__":
    eph = EphemerisTracker(42.5, -71.5)

    daz = []
    dalt = []
    dnames = []
    for val in eph.get_all_azimuth_elevation():
        print(val + str(eph.get_all_azimuth_elevation()[val]))
        if eph.get_all_azimuth_elevation()[val][1] > 0:
            daz.append(eph.get_all_azimuth_elevation()[val][0])
            dalt.append(eph.get_all_azimuth_elevation()[val][1])
            dnames.append(val)

    fig, ax = plt.subplots()
    ax.scatter(daz, dalt)
    plt.xlabel("azimuth (degs)")
    plt.ylabel("altitude (degs)")
    for i, txt in enumerate(dnames):
        ax.annotate(txt, (daz[i], dalt[i]))
    plt.show()
