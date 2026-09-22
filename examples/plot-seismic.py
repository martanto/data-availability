import matplotlib.pyplot as plt

from data_availability import SeismicAvailability, configure_logging


def main():
    fig = SeismicAvailability(
        start_date="2020-01-01",
        end_date="2022-12-31",
        sds_dir=r"D:\Data\LEKR",
        station="LEKR",
        network="VG",
        location="00",
        channel="EHZ",
        n_jobs=10,
        verbose=True,
    ).plot(tile_shape="squircle")

    plt.savefig("LEKR.png", dpi=150, bbox_inches="tight")
    print("Saved to LEKR.png")


if __name__ == "__main__":
    configure_logging()
    main()
