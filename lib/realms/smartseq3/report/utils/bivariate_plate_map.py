import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from io import BytesIO
from pathlib import Path
from matplotlib.collections import PatchCollection

class BivariatePlateMap:
    def __init__(self, data, color_values=None, size_values=None, well_values=None,
                 color_map="RdYlBu", title="", color_title = "", size_title="",
                 x_label="", y_label="", figsize=(10, 7), output_dir=None, fig_name=None,
                 radius_min=10, radius_max=200, log_size=False, log_color=False):
        """
        Create a bivariate plate map plot with customizable parameters.

        Args:
            data (pd.DataFrame): DataFrame containing the data to be plotted.
            color_values (str, optional): Column name for values that determine color. Default is None.
            size_values (str, optional): Column name for values that determine size. Default is None.
            color_map (str, optional): Color map for the plot. Default is "RdYlBu".
            title (str, optional): Title of the plot. Default is an empty string.
            x_label (str, optional): Label for the x-axis. Default is an empty string.
            y_label (str, optional): Label for the y-axis. Default is an empty string.
            figsize (tuple, optional): Size of the figure. Default is (10, 6).
            radius_min (int, optional): Minimum radius for the plot points. Default is 10.
            radius_max (int, optional): Maximum radius for the plot points. Default is 200.
            log_scale (bool, optional): Whether to apply logarithmic scale. Default is True.
        """
        self.data = data
        self.color_values = color_values
        self.size_values = size_values
        self.well_values = well_values
        self.color_map = color_map
        self.title = title
        self.color_title = color_title
        self.size_title = size_title
        self.x_label = x_label
        self.y_label = y_label
        self.figsize = figsize
        self.radius_min = radius_min
        self.radius_max = radius_max
        self.log_size = log_size
        self.log_color = log_color
        self.rows = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
        self.columns = [str(i+1) for i in range(24)]
        self.fig_name = fig_name
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()

    def generate_plot(self):
        """
        Generates the bivariate plate map plot using the class attributes.
        """
        # Create the layout matrix
        layout, value_scale = self._create_layout_matrix()

        print(f"Initial: {value_scale.min()}")

        # Apply logarithmic scaling if specified
        if self.log_color:
            layout = np.log2(layout)
            color_title = f"{self.color_title} (log2)"
        else:
            color_title = self.color_title

        if self.log_size:
            value_scale = np.log2(value_scale)
            size_title = f"{self.size_title} (log2)"
        else:
            size_title = self.size_title

        layout = np.nan_to_num(layout)

        # Generate grid for plotting
        x, y = np.meshgrid(np.arange(len(self.columns)), np.arange(len(self.rows)))

        # Create figure and axes
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # # Apply min-max scaling for dot sizes
        R = (value_scale - value_scale.min()) / (value_scale.max() - value_scale.min())
        R = R * (self.radius_max - self.radius_min) + self.radius_min

        # Reverse the scaling operation
        threshold_value = (0 / (self.radius_max - self.radius_min)) * (value_scale.max() - value_scale.min()) + value_scale.min()

        print(threshold_value)

        min_above_threshold = np.min(value_scale[value_scale > threshold_value])

        print(min_above_threshold)

        print(value_scale.min())

        # Scatter plot with variable dot sizes and colors
        sc = self.ax.scatter(x.flat, y.flat, s=R.flat, c=layout.flat, cmap=self.color_map)

        # Configure plot aesthetics
        self._configure_plot_aesthetics()

        # Add colorbar and legends
        self._add_colorbar(sc, label=color_title)
        self._add_size_legend(value_scale, label=size_title)

        # Set plot title and axis labels
        # plt.title(self.title)
        # plt.xlabel(self.x_label)
        # plt.ylabel(self.y_label)

        # # Save plot if filename is provided
        # if self.fig_name:
        #     plt.savefig(self.output_dir / self.fig_name)

        # Adjust layout for optimal display
        plt.tight_layout()
        # Adjust the top margin
        plt.subplots_adjust(top=0.85)  # Adjust the value as needed

        return plt.gcf()


    def _create_layout_matrix(self):
        """
        Creates a layout matrix representing the well plate based on the input data.

        Returns:
            tuple: A tuple containing the layout matrix and the value scale for dot sizes.
        """
        # Initialize the layout matrix with zeros
        layout = np.zeros((len(self.rows), len(self.columns)))
        value_scale = np.zeros_like(layout)

        # Iterate over the DataFrame and populate the layout and value_scale matrices
        for _, row in self.data.iterrows():
            well_id = row[self.well_values]
            row_label, col_label = well_id[0], int(well_id[1:])
            row_index = self.rows.index(row_label)
            col_index = col_label - 1  # Adjust for 0-based indexing

            if self.color_values in row:
                layout[row_index, col_index] = row[self.color_values]
            if self.size_values in row:
                value_scale[row_index, col_index] = row[self.size_values]

        return layout, value_scale
    

    def _configure_plot_aesthetics(self):
        """
        Configures the aesthetics of the plate map plot, including tick labels, grid lines, and axis limits.
        """
        # Set Major ticks
        self.ax.set(xticks=np.arange(len(self.columns)), yticks=np.arange(len(self.rows)),
                    xticklabels=self.columns, yticklabels=self.rows)

        # Set Minor ticks for grid lines
        self.ax.set_xticks(np.arange(len(self.columns) + 1) - 0.5, minor=True)
        self.ax.set_yticks(np.arange(len(self.rows) + 1) - 0.5, minor=True)

        # Hide Minor ticks and show grid lines on Minor Grid
        self.ax.tick_params(axis='both', which='minor', length=0)
        self.ax.grid(which='minor')

        # Set the plot limits
        self.ax.set_xlim(-0.5, len(self.columns) - 0.5)
        self.ax.set_ylim(-0.5, len(self.rows) - 0.5)

        # Invert Y axis and place X axis ticks at the top to resemble a plate layout
        self.ax.invert_yaxis()
        self.ax.xaxis.tick_top()

        # Set plot title and axis labels if provided
        # if self.title:
        #     self.ax.set_title(self.title)
        # if self.x_label:
        #     self.ax.set_xlabel(self.x_label)
        # if self.y_label:
        #     self.ax.set_ylabel(self.y_label)


    def _add_colorbar(self, scatter_plot, label):
        """
        Adds a colorbar to the plot.

        Args:
            label (str): Label for the colorbar, describing what the colors represent.
        """
        # Create colorbar based on the scatter plot
        cbar = self.fig.colorbar(scatter_plot, ax=self.ax)

        # Set the label for the colorbar
        cbar.ax.set_ylabel(label)

        # Optionally, additional customization can be added here, like colorbar position, orientation, etc.


    def _add_size_legend(self, value_scale, label):
        """
        Adds a legend for dot sizes to the plot, based on the value scale.

        Args:
            value_scale (np.ndarray): Array containing the values used to scale the dot sizes.
        """
        # Define the range of dot sizes based on the value scale
        min_size = int(value_scale.min())
        max_size = int(value_scale.max())
        mid_size = int(np.max(value_scale) / 2)

        # min_threshold = round(self.radius_min / self.radius_max * (max_size - min_size) + min_size)
        # Calculate the minimum threshold for the smallest dot size
        # min_threshold = (self.radius_min / self.radius_max) * (max_size - min_size) + min_size

        # Calculate the point size for the median value
        Rmid = (mid_size - min_size) / (max_size - min_size) * (self.radius_max - self.radius_min) + self.radius_min

        # Create dummy scatter plots for legend
        legend_dots = [plt.scatter([], [], s=self.radius_min, edgecolors='none', color='black'),
                    plt.scatter([], [], s=Rmid, edgecolors='none', color='black'),
                    plt.scatter([], [], s=self.radius_max, edgecolors='none', color='black')]

        # Define labels for each size
        # TODO: Not correct - even if the dot size is scaled, the value should be the same as the original value
        min_value_label = f"0 - {min_size}"
        labels = [str(min_size), str(mid_size), str(max_size)]

        # Create the legend with these dummy scatter plots
        self.ax.legend(legend_dots, labels, title=label, ncol=3, loc=8, frameon=False,
                    labelspacing=1.0, title_fontsize='medium', fontsize=12, handletextpad=1,
                    borderpad=1.0, bbox_to_anchor=(0.5, -0.20))

        # Adjust layout to accommodate the legend
        plt.tight_layout()


    # def _add_size_legend(self, value_scale, label=""):
    #     """
    #     Adds a legend for dot sizes to the plot, based on the value scale.

    #     Args:
    #         value_scale (np.ndarray): Array containing the values used to scale the dot sizes.
    #         legend_title (str): Title for the size legend.
    #     """
    #     # Calculate the half of the max value to be used as mid-point
    #     mid_value = np.max(value_scale) / 2

    #     # Calculate dot sizes for min, mid, and max values
    #     min_dot_size = self._scale_to_radius(np.min(value_scale), value_scale)
    #     mid_dot_size = self._scale_to_radius(mid_value, value_scale)
    #     max_dot_size = self._scale_to_radius(np.max(value_scale), value_scale)

    #     # Calculate the min and max values represented by the dots
    #     min_threshold = round(min_dot_size / max_dot_size * (np.max(value_scale) - np.min(value_scale)) + np.min(value_scale))
    #     min_value_label = f"0 - {min_threshold}"
    #     max_value_label = str(int(np.max(value_scale)))

    #     # Create dummy scatter plots for legend
    #     legend_dots = [plt.scatter([], [], s=size, edgecolors='none', color='black') 
    #                 for size in [min_dot_size, mid_dot_size, max_dot_size]]

    #     # Define labels for each size
    #     labels = [min_value_label, str(round(mid_value)), max_value_label]

    #     # Create the legend with these dummy scatter plots
    #     self.ax.legend(legend_dots, labels, title=label, loc='lower center', 
    #                 bbox_to_anchor=(0.5, -0.1), frameon=False, labelspacing=1.5, 
    #                 title_fontsize='medium', fontsize='small', scatterpoints=1, ncol=3)

    #     # Adjust layout to accommodate the legend
    #     plt.tight_layout()


    # def _scale_to_radius(self, value, value_scale):
    #     """
    #     Scales a given value to a radius within the specified min and max radius range.

    #     Args:
    #         value (float): The value to be scaled.
    #         value_scale (np.ndarray): The array of values used for scaling.

    #     Returns:
    #         float: The scaled radius.
    #     """
    #     # Scale the value to a proportion of the range
    #     proportion = (value - np.min(value_scale)) / (np.max(value_scale) - np.min(value_scale))
    #     return proportion * (self.radius_max - self.radius_min) + self.radius_min




    # def generate_plot(self, log_transform=True, dot_size_range=(10, 200), legend_title='Value'):
    #     """
    #     Generates the bivariate plate map plot.

    #     Parameters:
    #     - log_transform (bool): Whether to log-transform the color values.
    #     - dot_size_range (tuple): A tuple defining the minimum and maximum dot sizes.
    #     - legend_title (str): The title to use for the legend of dot sizes.
    #     """
    #     if log_transform:
    #         self.layout = np.log2(self.layout)

    #     self.layout = np.nan_to_num(self.layout)

    #     x, y = np.meshgrid(np.arange(len(self.cols)), np.arange(len(self.rows)))

    #     self.fig, self.ax = plt.subplots(figsize=(10, 6))

    #     # Apply min-max scaling for dot sizes
    #     R = (self.value_scale - self.value_scale.min()) / (self.value_scale.max() - self.value_scale.min())
    #     R = R * (dot_size_range[1] - dot_size_range[0]) + dot_size_range[0]

    #     # Scatter plot with variable dot sizes and colors
    #     sc = self.ax.scatter(x.flat, y.flat, s=R.flat, c=self.layout.flat, cmap=self.color_map)

    #     # Set tick labels and grid
    #     self.ax.set(xticks=np.arange(len(self.cols)), yticks=np.arange(len(self.rows)),
    #                 xticklabels=self.cols, yticklabels=self.rows)
    #     self.ax.set_xticks(np.arange(len(self.cols)+1)-0.5, minor=True)
    #     self.ax.set_yticks(np.arange(len(self.rows)+1)-0.5, minor=True)
    #     self.ax.tick_params(axis='both', which='minor', length=0)
    #     self.ax.grid(which='minor')
    #     self.ax.set_xlim(-0.5, len(self.cols)-0.5)
    #     self.ax.set_ylim(-0.5, len(self.rows)-0.5)
    #     self.ax.invert_yaxis()
    #     self.ax.xaxis.tick_top()

    #     # Colorbar and its label
    #     cbar = self.fig.colorbar(sc)
    #     cbar.ax.set_ylabel('Values (log2)' if log_transform else 'Values')

    #     # Legend for dot sizes
    #     self._add_dot_size_legend(dot_size_range, legend_title)

    #     # Adjust layout
    #     plt.tight_layout()

    # def _add_dot_size_legend(self, dot_size_range, title):
    #     """
    #     Adds a legend for dot sizes to the plot with three representative sizes:
    #     minimum, median, and maximum values from the data.

    #     Parameters:
    #     - dot_size_range (tuple): A tuple defining the minimum and maximum dot sizes.
    #     - title (str): The title to use for the legend.
    #     """
    #     # Representative points for the legend
    #     min_point = plt.scatter([], [], s=dot_size_range[0], color='black')
    #     mid_point = plt.scatter([], [], s=np.mean(dot_size_range), color='black')
    #     max_point = plt.scatter([], [], s=dot_size_range[1], color='black')

    #     # Labels for each representative point
    #     labels = [f"Min: {self.value_scale.min()}",
    #               f"Median: {self.value_scale.median()}",
    #               f"Max: {self.value_scale.max()}"]

    #     # Create the legend and add it to the plot
    #     legend = self.ax.legend([min_point, mid_point, max_point], labels, loc=8, 
    #                             bbox_to_anchor=(0.5, -0.2), title=title, ncol=3,
    #                             handletextpad=1, borderpad = 1.8, frameon=False,
    #                             fontsize=12)
    #     self.ax.add_artist(legend)

    def save_plot(self):
        """
        Saves the generated plate map plot to a file.

        Parameters:
        - filename (str): The path to the file where the plot should be saved.
        """
        plt.savefig(self.output_dir / self.fig_name)
        plt.close()

    def show_plot(self):
        """
        Displays the generated plate map plot.
        """
        plt.show()
