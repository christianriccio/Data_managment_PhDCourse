from datetime import datetime
import pandas
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

class Utils: 
    
    FACTOR_COL = "vehicle_make"
    
    def __init__(self, df):
        self.df = df
        
    
    def sql_data(cursor,sql_statement, col_names=True):
        if col_names: 
            cursor.execute(sql_statement)
            col_names = [el[0] for el in cursor.description]
            df = pandas.DataFrame(cursor.fetchall(), columns = col_names)
        else: 
            df = pandas.DataFrame(cursor.execute(sql_statement)) 
        return df
    
        
        
     # Date conversion function
    def date_columns(query):
        """If a date column is included in the query, parse it as a date in the
        dataframe."""
        dates = []
        fields = ["collision_date", "process_date"]
        if '*' in query:
            dates = fields
        else:
            for date in fields:
                if date in query:
                    dates.append(date)

            if not dates:
                dates = None

        return dates
    

    def annotate_year(self, df, ax, month, day, text, xytext, adjust=(0, 0), arrowstyle="->"):
        
        CRASH_COL = "Crashes"
        """ Draw an annotation on the Day of Year plot. """
        # Use 2016 because it is a leapyear, and we plot Feb 29
        doy = datetime(year=2016, month=month, day=day).timetuple().tm_yday
        y_pos = df[CRASH_COL][month][day]

        ax.annotate(
            text,
            (doy+adjust[0], y_pos+adjust[1]),
            xytext=xytext,
            textcoords='offset points',
            arrowprops=dict(
                arrowstyle=arrowstyle,
                connectionstyle="arc3",
            ),
            size=16,
        )
        
        

    # Get the start locations of each month
    def month_starts(self, df):
        """ Get the start and midpoints of each month. """
        # Month starts
        majors = []
        for x, (month, day) in enumerate(df.index):
            if day == 1:
                majors.append(x)
            if month == 12 and day == 31:
                majors.append(x)

        # Midpoints
        minors = []
        for i in range(len(majors)-1):
            end = majors[i+1]
            start = majors[i]
            x = start + (end-start)/2.
            minors.append(x)

        return (majors, minors)
    
    
    def setup_plot(title=None, xlabel=None, ylabel=None):
        """Set up a simple, single pane plot with custom configuration.

        Args:
            title (str, optional): The title of the plot.
            xlabel (str, optional): The xlabel of the plot.
            ylabel (str, optional): The ylabel of the plot.

        Returns:
            (fig, ax): A Matplotlib figure and axis object.

        """
        # Plot Size
        plt.rcParams["figure.figsize"] = (12, 7)  # (Width, height)

        # Text Size
        SMALL = 12
        MEDIUM = 16
        LARGE = 20
        HUGE = 28
        plt.rcParams["axes.titlesize"] = HUGE
        plt.rcParams["figure.titlesize"] = HUGE
        plt.rcParams["axes.labelsize"] = LARGE
        plt.rcParams["legend.fontsize"] = LARGE
        plt.rcParams["xtick.labelsize"] = MEDIUM
        plt.rcParams["ytick.labelsize"] = MEDIUM
        plt.rcParams["font.size"] = SMALL

        # Legend
        plt.rcParams["legend.frameon"] = True
        plt.rcParams["legend.framealpha"] = 1
        plt.rcParams["legend.facecolor"] = "white"
        plt.rcParams["legend.edgecolor"] = "black"

        # Figure output
        plt.rcParams["savefig.dpi"] = 300

        # Make the plol
        fig, ax = plt.subplots()
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Make the title and label area opaque instead of transparent
        fig.patch.set_facecolor(ax.get_facecolor())

        return fig, ax
    
    
    def draw_colored_text_legend_instead_of_real_legend(ax, texts, positions):
        legend = ax.get_legend()
        for patch, text, (x, y) in zip(legend.get_patches(), texts, positions):
            color = patch.get_edgecolor()
            ax.text(x, y, text, color=color, verticalalignment='center', transform=ax.transAxes, fontsize=24)

        legend.remove()
        

    def normalize_dataframe(self, df, factor_col=FACTOR_COL, end_date='2019-07-01'):
        """Normalize the dataframe by setting the mean to 1 over the first few months."""
        ford_mean = df[(df[FACTOR_COL]=='ford') & (df.index < end_date)].mean()
        toyota_mean = df[(df[FACTOR_COL]=='toyota') & (df.index < end_date)].mean()

        df_normed = df.copy(deep=True)
        df_normed.loc[df[factor_col]=='ford', "total"] /= ford_mean[0]
        df_normed.loc[df[FACTOR_COL]=='toyota', "total"] /= toyota_mean[0]

        return df_normed
    
    
    def make_ford_vs_toyota_plot(self, df, fig, ax, toyota_label_xy, ford_label_xy, y,stay_at_home_y,               norm_label_y=None, y_lim=None, factor_col=FACTOR_COL,):

        sns.lineplot(data=df, x="collision_date", y="total", hue=factor_col, drawstyle="steps-post", linewidth=2)

        # Add labels instead of legend
        ax.get_legend().remove()
        ax.text(x=pd.Timestamp(toyota_label_xy[0]), y=toyota_label_xy[1], s="Toyota", color=orange_line_color, fontsize=30)
        ax.text(x=pd.Timestamp(ford_label_xy[0]), y=ford_label_xy[1], s="Ford", color=blue_line_color, fontsize=30)

        # Add Stay at home order
        ax.axvline(x=pd.Timestamp("2020-03-19"), color="red", linewidth=2, zorder=1, label="Stay at home order")
        ax.text(x=pd.Timestamp("2020-03-27"), y=stay_at_home_y, s="Stay-at-home Order", color="red", fontsize=24)


        # Add mean line
        if norm_label_y is not None:
            ax.hlines(y=1, xmin=pd.Timestamp("2019-01-01"), xmax=pd.Timestamp("2019-06-30"), linewidth=3, color=green_line_color, zorder=2)
            ax.text(x=pd.Timestamp("2018-12-14"), y=norm_label_y, s="Mean normalized from\nJanuary through June", color=green_line_color, fontsize=24)

        # Remove date label
        ax.xaxis.label.set_visible(False)

        if y_lim is not None:
            ax.set_ylim(*y_lim)

        return fig, ax