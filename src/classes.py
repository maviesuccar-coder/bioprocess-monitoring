import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        """
        Utility class used to monitor bioprocesses by
        generating dashboards and summaries.

        Parameters
        ----------
        filepath : str
            Input CSV dataset path.
        ph_lims : tuple[float, float]
            Lower and upper acceptable pH limits.
        temperature_lims : tuple[float, float]
            Lower and upper acceptable temperature limits.
        """

        # Read the fermentation dataset.
        self.df = pd.read_csv(filepath)

        # Save the acceptable operating limits.
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims

    def extract_batch(self, batch_id):
        """
        Extracts data corresponding to a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing only rows associated with
            the requested batch.
        """

        df_batch = self.df[self.df["batch_id"] == batch_id].copy()

        return df_batch

    def optimal_ph_mask(self, df_batch):
        """
        Determines whether each pH measurement falls within
        the acceptable operating range.
        """

        ph_min = self.ph_lims[0]
        ph_max = self.ph_lims[1]

        mask = df_batch["pH"].between(ph_min, ph_max, inclusive="both")

        return mask

    def optimal_temperature_mask(self, df_batch):
        """
        Determines whether each temperature measurement falls
        within the acceptable operating range.
        """

        temperature_min = self.temperature_lims[0]
        temperature_max = self.temperature_lims[1]

        mask = df_batch["temperature_C"].between(
            temperature_min,
            temperature_max,
            inclusive="both"
        )

        return mask

    def get_n_batches(self):
        """
        Determines the number of unique batches present
        in the dataset.
        """

        n_batches = self.df["batch_id"].nunique()

        return n_batches

    def export_dashboard(self, batch_id, filepath):
        """
        Creates and saves a dashboard figure for a single batch.
        """

        # Extract the requested batch.
        df_batch = self.extract_batch(batch_id)

        # Determine which pH and temperature measurements
        # are inside the acceptable ranges.
        ph_mask = self.optimal_ph_mask(df_batch)
        temperature_mask = self.optimal_temperature_mask(df_batch)

        # Create a figure with four subplots.
        fig, axes = plt.subplots(
            nrows=2,
            ncols=2,
            figsize=(12, 8),
            constrained_layout=True
        )

        # Give convenient names to the four subplots.
        ax_concentrations = axes[0, 0]
        ax_temperature = axes[0, 1]
        ax_ph = axes[1, 0]
        ax_oxygen = axes[1, 1]

        # -----------------------------------------------------
        # Top-left: concentrations versus time
        # -----------------------------------------------------

        ax_concentrations.scatter(
            df_batch["time_h"],
            df_batch["C_glucose_g_L^-1"],
            color="blue",
            marker="o",
            label="Glucose"
        )

        ax_concentrations.scatter(
            df_batch["time_h"],
            df_batch["C_biomass_g_L^-1"],
            color="orange",
            marker="s",
            label="Biomass"
        )

        ax_concentrations.scatter(
            df_batch["time_h"],
            df_batch["C_product_g_L^-1"],
            color="purple",
            marker="^",
            label="Product"
        )

        ax_concentrations.set_title("Concentrations")
        ax_concentrations.set_xlabel("Time (h)")
        ax_concentrations.set_ylabel("Concentration (g/L)")
        ax_concentrations.legend()

        # -----------------------------------------------------
        # Top-right: temperature versus time
        # -----------------------------------------------------

        ax_temperature.scatter(
            df_batch.loc[temperature_mask, "time_h"],
            df_batch.loc[temperature_mask, "temperature_C"],
            color="green",
            marker="o",
            label="Within range"
        )

        ax_temperature.scatter(
            df_batch.loc[~temperature_mask, "time_h"],
            df_batch.loc[~temperature_mask, "temperature_C"],
            color="red",
            marker="x",
            label="Outside range"
        )

        ax_temperature.set_title("Temperature")
        ax_temperature.set_xlabel("Time (h)")
        ax_temperature.set_ylabel("Temperature (°C)")
        ax_temperature.legend()

        # -----------------------------------------------------
        # Bottom-left: pH versus time
        # -----------------------------------------------------

        ax_ph.scatter(
            df_batch.loc[ph_mask, "time_h"],
            df_batch.loc[ph_mask, "pH"],
            color="green",
            marker="o",
            label="Within range"
        )

        ax_ph.scatter(
            df_batch.loc[~ph_mask, "time_h"],
            df_batch.loc[~ph_mask, "pH"],
            color="red",
            marker="x",
            label="Outside range"
        )

        ax_ph.set_title("pH")
        ax_ph.set_xlabel("Time (h)")
        ax_ph.set_ylabel("pH")
        ax_ph.legend()

        # -----------------------------------------------------
        # Bottom-right: dissolved oxygen versus time
        # -----------------------------------------------------

        ax_oxygen.scatter(
            df_batch["time_h"],
            df_batch["DO_percent"],
            color="teal",
            marker="o"
        )

        ax_oxygen.set_title("Dissolved Oxygen")
        ax_oxygen.set_xlabel("Time (h)")
        ax_oxygen.set_ylabel("Dissolved Oxygen (%)")

        # Format all four graphs consistently.
        for ax in axes.flat:
            ax.xaxis.set_major_locator(MultipleLocator(6))
            ax.grid(True, alpha=0.3)

        # Add a title for the entire dashboard.
        fig.suptitle(f"Fermentation Batch {batch_id}", fontsize=16)

        # Save and close the dashboard.
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def export_summary(self, filepath):
        """
        Generates a batch summary table and exports it to a CSV file.
        """

        summary_rows = []

        # Process each unique batch in numerical order.
        batch_ids = sorted(self.df["batch_id"].unique())

        for batch_id in batch_ids:
            df_batch = self.extract_batch(batch_id)

            # Calculate the percentage of acceptable measurements.
            ph_optimal_percent = round(
                self.optimal_ph_mask(df_batch).mean() * 100,
                2
            )

            temperature_optimal_percent = round(
                self.optimal_temperature_mask(df_batch).mean() * 100,
                2
            )

            # Sort by time before selecting the final measurement.
            df_batch = df_batch.sort_values("time_h")

            final_product_concentration = df_batch[
                "C_product_g_L^-1"
            ].iloc[-1]

            # Add this batch's results to the summary.
            summary_rows.append(
                {
                    "batch_id": batch_id,
                    "ph_optimal_percent": ph_optimal_percent,
                    "temperature_optimal_percent":
                        temperature_optimal_percent,
                    "C_product_g_L^-1_final":
                        final_product_concentration
                }
            )

        # Convert all results into a DataFrame.
        df_summary = pd.DataFrame(summary_rows)

        # Export the summary without an extra index column.
        df_summary.to_csv(filepath, index=False)