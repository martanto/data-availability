import matplotlib.pyplot as plt

from data_availability import PlotAvailability


if __name__ == "__main__":
    fig = (
        PlotAvailability("example.xlsx")
        .select(years=["2016", "2017", "2018"])
        .plot(
            title="Data Availability — VG.IJEN.00.EHZ",
            tile_shape="squircle",
            cbar_height=10,
        )
    )
    plt.savefig("output.png", dpi=150, bbox_inches="tight")
    print("Saved to output.png")
