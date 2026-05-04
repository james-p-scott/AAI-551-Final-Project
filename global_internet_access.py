"""
global_internet_access.py

contains utilities used to load, clean, and plot .csv datasets

functions that contribute directly to addressing the Final Project problem:
 - load_global_internet_access_data(): load a .csv using file_io and print basic diagnostics
 - clean_global_internet_access_data(): reduce, clean, and normalize the raw dataframe
 - plot_cleaned_internet_bar(): plot a horizontal bar chart with a fixed axis range
 - plot_all_cleaned_internet_bars(): plot the cleaned df using multiple plots with
     consistent axes
 - plot_cleaned_internet_in_n_plots(): split the cleaned df into N plots with uniform
     batch sizes
"""

# Requirements (part 1) compliance:
#   1.3 Use at least 2 advanced Python libraries for data and processing.  here, we are using
#       pandas to load and clean datasets and matplotlib.pyplot for plotting bar plots of the
#       ITU dataset.
#
# import the file_io namespace
import importlib
import matplotlib.pyplot as plt
import pandas as pd
import math
import file_io

# Requirements (part 2) compliance:
#   2.3  at least one built-in library/module (e.g. time, random, math, itertools).
#        the following codeblock uses the reload() lib function from 'importlib' to
#        ensure that local edits are incorporated prior to rebuilding the code.
#
# reload module to pick up local edits during incremental development
importlib.reload(file_io)

# Requirements (Part 1) compliance:
#   1.2 define at least 2 meaningful, well-defined functions that contribute directly to
#       solving the problem.
def load_global_internet_access_data():
    """
    load the ITU global internet access .csv into a Pandas dataframe and print the head.
    returns the CSV_Load_DF loader instance.
    """
    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  string types (e.g. "datasets", string filenames) are immutable
    #        objects.
    #
    # load the raw .csv file using the Logging_CSV_Load_DF subclass
    df_loader = file_io.Logging_CSV_Load_DF("datasets", "individuals-using-the-internet.csv")
    # validate the df, checking for an empty dataframe.  display a small sample of the
    # dataframe on success, otherwise display a 'No data' error message on the console.
    if df_loader.df is not None:
        print(df_loader.df.head())
    else:
        print(f"\nNo data loaded from the specified file\n")

    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  the code below defines a dictionary 'meta' which satisfiles
    #        the 2nd instance of mutable types required by requirement 1.7.
    meta = {
        "source": {
            "filepath": df_loader.filepath,
            "rows_loaded": 0 if df_loader.df is None else len(df_loader.df)
        },
        "loader": {
            "class": type(df_loader).__name__,
            "notes": {"logging": True}
        }
    }

    # Requirements (Part 2) compliance:
    #   2.6 Use of recursion
    # file_io.Logging_CSV_Load_DF.walk_nested_dict() is a recursive helper function
    #
    # walk the metadata using the recursive helper function defined in the
    # file_io.Logging_CSV_Load_DF class
    print("\nMetadata (flattened):")
    for path, value in file_io.Logging_CSV_Load_DF.walk_nested_dict(meta):
        dotted = ".".join(path) if path else "(root)"
        print(f"  {dotted} = {value}")

    # return the loaded dataframe loader
    return df_loader

# Requirements (Part 1) compliance:
#   1.2 define at least 2 meaningful, well-defined functions that contribute directly to
#       solving the problem.
def clean_global_internet_access_data():
    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  user-defined class instances (e.g. 'loader') are mutable objects.
    #
    # load the raw .csv file via the loader instance
    loader = file_io.CSV_Load_DF("datasets", "individuals-using-the-internet.csv")
    print(loader.shape)
    print(loader.columns)
    print(loader.head(3))
    print(f"number of rows in loaded df = ",len(loader))
    # construct the cleaner using composition
    cleaner = file_io.Clean_DF(loader=loader)
    print(f"\n {cleaner}\n")
    # reduce the df to its core columns
    cleaner.reduce_to_core_columns()

    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  Pandas Series (e.g. mask_header_row) are mutable objects.
    #
    # build a boolean mask of rows where any column value equals the column name (case-insensitive)
    mask_header_row = pd.Series(False, index=cleaner.df.index)
    for col in cleaner.df.columns:
        # compare stringified values to the column name; strip whitespace and ignore case
        mask_header_row |= cleaner.df[col].astype(str).str.strip().str.lower().eq(col.lower())

    if mask_header_row.any():
        print(f"Dropping {mask_header_row.sum()} rows that appear to be header rows embedded in the data")
        cleaner.df = cleaner.df[~mask_header_row].copy()

    # reduce the df to include only the most recent valid dataValue for each country (entityIso)
    cleaner.reduce_to_latest_by_iso()

    # validate reduced_latest
    if cleaner.df is None or cleaner.df.empty:
        print("No cleaned data remained after the dataframe reduction")
        return cleaner.df

    # convert dataValue from percentage to a fraction
    if "dataValue" in cleaner.df.columns:
        # coerce to numeric then determine max
        cleaner.df["dataValue"] = pd.to_numeric(cleaner.df["dataValue"], errors="coerce")
        max_val = cleaner.df["dataValue"].max(skipna=True)
        if pd.notna(max_val) and max_val > 1.0:
            cleaner.df["dataValue"] = cleaner.df["dataValue"] / 100.0
        print("dataValues converted from % to fraction")
    else:
        print("warning: no 'dataValue' present.  conversion from % to fraction not performed")

    # Sort by dataValue descending (largest first). Keep NaNs at the end.
    if "dataValue" in cleaner.df.columns:
        cleaner.df = cleaner.df.sort_values(by="dataValue", ascending=False, na_position="last").reset_index(drop=True)

    # display the cleaned results and return the cleaned dataframe
    print(cleaner.df.head())
    return cleaner.df

# Requirements (Part 1) compliance:
#   1.2 define at least 2 meaningful, well-defined functions that contribute directly to
#       solving the problem.
#
# also
#
# Requirements (part 1) compliance:
#   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
#        string, tuple).  integers (e.g. figsize=(14,7)) are immutable objects.
def plot_cleaned_internet_bar(df, value_col="dataValue", name_col="entityName", top_n=50,
                              figsize=(14, 7), title="Internet usage by country", y_limits=None):
    """
    Plot a bar chart of the cleaned DataFrame or of a provided subset.

    - df: pandas.DataFrame (the cleaned DataFrame produced by clean_global_internet_access_data)
    - value_col: column with numeric values (should be fractional 0..1 after conversion)
    - name_col: column with country/entity names
    - top_n: number of top entries to plot (by value); if df already is a subset, set top_n=None to plot all
    - y_limits: tuple (ymin, ymax) to enforce a consistent y-axis range across multiple plots
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None. Nothing to plot.")

    if value_col not in df.columns:
        raise KeyError(f"Value column '{value_col}' not found in DataFrame.")
    if name_col not in df.columns:
        # fallback to entityIso if names missing
        if "entityIso" in df.columns:
            name_col = "entityIso"
        else:
            raise KeyError(f"Name column '{name_col}' not found and no 'entityIso' fallback available.")

    # Work on a copy to avoid mutating caller's DF
    plot_df = df.copy()

    # Ensure numeric
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")

    # If values are percentages (max > 1), convert to fraction
    if plot_df[value_col].max(skipna=True) > 1.0:
        plot_df[value_col] = plot_df[value_col] / 100.0

    # Drop rows without valid values
    plot_df = plot_df.dropna(subset=[value_col, name_col]).copy()
    if plot_df.empty:
        raise ValueError("No valid rows to plot after dropping NaNs.")

    # Select top_n by value (descending) if requested
    if top_n is not None:
        plot_df = plot_df.sort_values(by=value_col, ascending=False).head(top_n)
    else:
        plot_df = plot_df.sort_values(by=value_col, ascending=False)

    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  matplotlib container objects are mutable objects.
    #
    # Use horizontal bar chart for readability of many labels
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    bars = ax.barh(plot_df[name_col].astype(str), plot_df[value_col], color="#4C72B0")

    # Format axes and title
    ax.set_xlabel("Internet usage (fraction of population)")
    ax.set_title(title)

    # Reverse y-axis so largest value on top (since horizontal bars)
    ax.invert_yaxis()

    # Set consistent y-axis limits if provided
    if y_limits is not None:
        ax.set_xlim(y_limits)

    # Format x-axis as percentages (0-100%)
    from matplotlib.ticker import FuncFormatter
    # Requirements (part 2) compliance:
    #   2.1  at least one of the special functions: enumerate, map, zip, filter, lambda, reduce
    #   the following code block employs the lambda special function
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{100 * x:.0f}%"))

    # Tight layout and show
    plt.tight_layout()
    plt.show()

# Requirements (Part 1) compliance:
#   1.2 define at least 2 meaningful, well-defined functions that contribute directly to
#       solving the problem.
def plot_all_cleaned_internet_bars(df, batch_size=40, value_col="dataValue", name_col="entityName",
                                   figsize=(14, 7), title="Internet usage by country"):
    """
    Display the entire cleaned dataframe in multiple bar plots, showing up to `batch_size`
    rows per plot. Loop through the cleaned dataframe in descending order of `value_col`.
    The y-axis (value axis) range is computed once from the whole dataframe and applied
    to every plot to keep visuals consistent across batches.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None. Nothing to plot.")

    # Work on a copy and ensure numeric/fractional values for consistent range calculation
    full_df = df.copy()
    full_df[value_col] = pd.to_numeric(full_df[value_col], errors="coerce")
    if full_df[value_col].max(skipna=True) > 1.0:
        full_df[value_col] = full_df[value_col] / 100.0

    # Drop rows missing value or name (they won't be plotted)
    full_df = full_df.dropna(subset=[value_col]).copy()
    if full_df.empty:
        raise ValueError("No valid rows in the full DataFrame to determine y-axis limits.")

    # Determine global y-axis limits. Typically internet usage is in [0, 1],
    # but we compute min/max from data and clamp to [0, 1] to avoid weird ranges.
    global_min = float(full_df[value_col].min(skipna=True))
    global_max = float(full_df[value_col].max(skipna=True))
    # Clamp to sensible bounds
    global_min = max(0.0, global_min)
    global_max = min(1.0, global_max) if pd.notna(global_max) else 1.0
    # Requirements (part 2) compliance:
    #   2.3  at least one built-in library/module (e.g. time, random, math, itertools).
    #        the following codeblock uses the isclose function from the built-in math lib
    #
    # If max equals min (rare), expand a bit for visibility
    if math.isclose(global_max, global_min):
        global_max = min(1.0, global_min + 0.05)

    y_limits = (global_min, global_max)

    # Sort and paginate
    plot_df = full_df.sort_values(by=value_col, ascending=False).reset_index(drop=True)
    total = len(plot_df)
    # Requirements (part 2) compliance:
    #   2.3  at least one built-in library/module (e.g. time, random, math, itertools).
    #        the following codeblock uses the ceiling function from the built-in math lib
    n_plots = math.ceil(total / batch_size)

    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  generator objects (e.g. 'starts') are mutable objects.
    #
    # and
    #
    #   2.4  one generator function or generator expression.  the following statement employs
    #        a generator expression: starts = (i * batch_size for i in range(n_plots))
    #
    # generator expression for batch starting indices
    starts = (i * batch_size for i in range(n_plots))

    # Requirements (part 2) compliance:
    #   2.1  at least one of the special functions: enumerate, map, zip, filter, lambda, reduce
    #   the following code block employs the enumerate special function
    for i, start in enumerate(starts, start=1):
        end = start + batch_size
        subset = plot_df.iloc[start:end].copy()
        sub_title = f"{title} — rows {start + 1} to {min(end, total)} of {total}"
        # call the plotting helper with top_n=None so it plots all rows in `subset`, and pass y_limits
        plot_cleaned_internet_bar(subset, value_col=value_col, name_col=name_col, top_n=None,
                                  figsize=figsize, title=sub_title, y_limits=y_limits)

# Requirements (Part 1) compliance:
#   1.2 define at least 2 meaningful, well-defined functions that contribute directly to
#       solving the problem.
def plot_cleaned_internet_in_n_plots(df, num_plots=6, value_col="dataValue",
                                     name_col="entityName", figsize=(14,7),
                                     title="Internet usage by country"):
    """
    Split `df` into `num_plots` batches and plot each batch in a separate bar chart.
    For total rows T and num_plots P:
      base = T // P
      remainder = T % P
    This implementation puts `base` rows in the first P-1 plots and
    `base + remainder` rows in the final plot (matching your 38,38,38,38,38,39 example).
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None. Nothing to plot.")

    # make working copy and ensure numeric fractional values
    work = df.copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    if work[value_col].max(skipna=True) > 1.0:
        work[value_col] = work[value_col] / 100.0
    work = work.dropna(subset=[value_col]).reset_index(drop=True)

    total = len(work)
    if total == 0:
        raise ValueError("No valid rows to plot after dropping NaNs.")

    # Compute batch sizes: base for first (P-1) plots, last plot gets the remainder
    base = total // num_plots
    remainder = total % num_plots
    if base == 0:
        # fewer rows than plots: make some plots empty (or reduce num_plots)
        raise ValueError("num_plots is larger than number of rows; reduce num_plots")

    # Requirements (part 1) compliance:
    #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
    #        string, tuple).  the code below defines a list 'batch_sizes' that satisfies 1
    #        mutable instance from requirement 1.7.
    batch_sizes = [base] * (num_plots - 1)
    batch_sizes.append(base + remainder)

    # Determine a consistent x-axis (value axis) range across all plots
    global_min = float(max(0.0, work[value_col].min(skipna=True)))
    global_max = float(min(1.0, work[value_col].max(skipna=True))) if pd.notna(work[value_col].max(skipna=True)) else 1.0
    if global_max <= global_min:
        global_max = min(1.0, global_min + 0.05)
    y_limits = (global_min, global_max)

    # sort by value descending and iterate through batches
    sorted_df = work.sort_values(by=value_col, ascending=False).reset_index(drop=True)
    start = 0
    # Requirements (part 2) compliance:
    #   2.1  at least one of the special functions: enumerate, map, zip, filter, lambda, reduce
    #   the following code block employs the enumerate special function
    for i, sz in enumerate(batch_sizes, start=1):
        end = start + sz
        subset = sorted_df.iloc[start:end].copy()
        sub_title = f"{title} — batch {i} rows {start+1}–{min(end, total)} of {total}"
        # call existing plotting helper; pass y_limits and top_n=None so it plots whole subset
        plot_cleaned_internet_bar(subset, value_col=value_col, name_col=name_col,
                                  top_n=None, figsize=figsize, title=sub_title,
                                  y_limits=y_limits)
        start = end