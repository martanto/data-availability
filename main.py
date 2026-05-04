import matplotlib.pyplot as plt

from data_availability import plot_availability


if __name__ == "__main__":
    fig = plot_availability("example.xlsx", title="Data Availability — VG.IJEN.00.EHZ")
    plt.savefig("output.png", dpi=150, bbox_inches="tight")
    print("Saved to output.png")
