"""
file_io.py

This file contains methods used to access external datasets, such as data from the ITU-T DataHub
"""
# import the external libs
import pandas as pd
import os

class CSV_Load_DF:
    """
    Load a .csv file into a pandas ddtaframe and expose basic load status.

    This helper class constructs the file path from a `subdirectory` and `filename`,
    attempts to read the .csv file using `pandas.read_csv`, and stores the resulting
    dataframe of the instance in the `df` attribute. If loading fails, `df` will
    remain `None` and an exception will be thrown.

    Parameters
    ----------
    subdirectory : str
        Directory or path segment containing the .csv file. It will be joined with
        `filename` using `os.path.join`
    filename : str
        The name of the .csv file to load

    Attributes
    ----------
    filepath : str
        Full path (joined `subdirectory` and `filename`) to the target .csv file.
    df : pandas.DataFrame | None
        The loaded dataframe on success, or `None` if the .csv didn't load successfully

    Behavior
    --------
    - Attempts to load the .csv file during object initialization by calling `load_df()`.
    - Prints an informational message on success or a descriptive error on failure.
    - Catches common pandas/file-related exceptions such as `FileNotFoundError`,
      `pandas.errors.EmptyDataError`, and `pandas.errors.ParserError`, as well as
      other unexpected exceptions.

    Example
    -------
    ```
    loader = CSV_Load_DF("subdirectory_name", "filename.csv")
    if loader.df is not None:
        print(loader.df.head())
    ```
    """
    def __init__(self, subdirectory, filename):
        """
        class constructor that builds the filename from the subdir/filename args,
        initializes the instance df to 'None', and attempts to load the df during
        object instantiation by calling `load_df()`.

        :param subdirectory:
        :param filename:
        """
        self.filepath = os.path.join(subdirectory, filename)
        self.df = None
        self.load_df()

    def load_df(self):
        """
        attempt to load the dataframe from the .csv file referenced by the args

        :return: a string that conveys either success or failure of the .csv file load operation
        """
        # use try to handle exceptions
        try:
            self.df = pd.read_csv(self.filepath)
            print(f"Successfully loaded file: {self.filepath}")

        # exception = file not found
        except FileNotFoundError:
            print(f"Error: The file '{self.filepath}' was not found")

        # exception = .csv file contains no data
        except pd.errors.EmptyDataError:
            print(f"Error: The file '{self.filepath}' is empty")

        # exception = file parsing error
        except pd.errors.ParserError:
            print(f"Error: There was a parsing error in the file '{self.filepath}'")

        # exception = unexpected error of type e
        except Exceptions as e:
            print(f"An unexpected error occurred: {e}")


