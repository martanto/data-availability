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

    fig = (
        PlotAvailability("example.xlsx")
        .select(years=["2016", "2017", "2018"])
        .plot(
            title="Data Availability — VG.IJEN.00.EHZ",
            kind="bar",
            hspace=2,
            fig_width=10,
            figsize_per_year=0.8,
            cbar_height=5,
        )
    )
    fig.savefig("output-bar.png", dpi=150, bbox_inches="tight")
    print("Saved to output-bar.png")
