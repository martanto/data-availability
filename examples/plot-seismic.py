import matplotlib.pyplot as plt

from data_availability import PlotSeismicAvailability


def main():
    fig = PlotSeismicAvailability(
        start_date="2020-01-01",
        end_date="2021-12-31",
        sds_dir=r"D:\Data\LEKR",
        station="LEKR",
        network="VG",
        location="00",
        channel="EHZ",
        n_jobs=10,
        verbose=True,
    ).plot()

    plt.savefig("output.png", dpi=150, bbox_inches="tight")
    print("Saved to output.png")


if __name__ == "__main__":
    main()
