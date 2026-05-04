"""
file_io.py

This file contains methods used to access external datasets, such as data from the ITU-T DataHub
"""
# import the external libs
import pandas as pd
import os
import warnings

# Requirements (part 2) compliance:
#   2.3  at least one built-in library/module (e.g. time, random, math, itertools).
#        the following codeblock uses the filterwarnings function from the built-in warnings lib
#
# ignore warnings
warnings.filterwarnings('ignore')

# Requirements (Part 1) compliance:
#   1.1 have at least 2 meaningful, well-defined classes that have constructores,
#       attributes, methods, and instance objects.  the class 'CSV_Load_DF' serves as
#       the base class for the subclass 'Logging_CSV_Load_DF' that inherits from it.
#       'CSV_Load_DF' also serves as the parent class in a composition structure that
#       'has_a' 'Clean_DF' child class.
#
# and
#
#   1.9 include a proper docstring and meaningful comments for each class and each function.
#       docstrings must be placed immediately below the class definition.
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
    """
    def __init__(self, subdirectory, filename):
        """
        class constructor that builds the filename from the subdir/filename args,
        initializes the instance df to 'None', and attempts to load the df during
        object instantiation by calling `load_df()`.

        :param subdirectory:
        :param filename:
        """
        # Requirements (part 1) compliance:
        #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
        #        string, tuple).  None is an immutable object.
        #
        # and
        #
        # Requirements (part 2) compliance:
        #   2.3  at least one built-in library/module (e.g. time, random, math, itertools).
        #        the following codeblock uses the path.join function from the built-in os lib
        self.filepath = os.path.join(subdirectory, filename)
        self.df = None
        self.load_df()

    # Requirements (part 1) compliance:
    #   1.8  Implement __str__() and at least one additional operator overload.
    #   the class 'CSV_Load_DF' implements __str__() below.
    def __str__(self):
        """
        string method that prints the shape of the df (if data is present) or indicates
        no dataframe (if no data is present)

        :return: string
        """
        if self.df is None:
            return f"CSV_Load_DF(filepath={self.filepath!r}, df=None)"
        else:
            return f"CSV_Load_DF(filepath={self.filepath!r}, df_shape={self.df.shape})"

    # Requirements (part 1) compliance:
    #   1.8  Implement __str__() and at least one additional operator overload.
    #   the class 'CSV_Load_DF' overloads the len operator below.  when called, the
    #   overloaded 'len' operator returns the number of rows in the dataframe.
    def __len__(self):
        """
        overload the len operator to return the number of rows in the loaded dataframe
        (0 if none).
        """
        return 0 if self.df is None else len(self.df)

    # Requirements (part 2) compliance:
    #   2.8 __getattr__.  the CSV_Load_DF class implements the __getattr__ special (dunder)
    #                     function to accommodate attribute lookups that aren't accessed
    #                     via the normal api.
    def __getattr__(self, name):
        """
        Proxy attribute access to the underlying DataFrame (`self.df`) when possible.

        Called only if the normal attribute lookup on the instance fails.
        Example: loader.shape -> delegated to loader.df.shape
        """
        # only attempt to access attributes if df is present
        if self.df is not None and hasattr(self.df, name):
            return getattr(self.df, name)
        # otherwise, raise AttributeError so Python falls back to normal behavior
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def load_df(self):
        """
        attempt to load the dataframe from the .csv file referenced by the args

        :return: a string that conveys either success or failure of the .csv file load operation
        """
        # Requirements (part 1) compliance:
        #   1.4 include at least 2 distinct exception-handling scenarios (e.g. invalid input,
        #       file/data loading errors, runtime/math errors).  in this scenario, we are
        #       using try/except to validate that the .csv file was successfully read, raising
        #       one of the following exceptions on failure:
        #         - FileNotFoundError
        #         - EmptyDataError
        #         - ParserError
        #         - General exception (e)
        #
        # also
        #
        # Requirements (part 1) compliance:
        #   1.5 perform some meaningful data I/O, such as reading from a file or from a database
        #
        # and
        #
        # Requirements (part 1) compliance:
        #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
        #        string, tuple).  Pandas DataFrame is a mutable type.
        #
        # read from a .csv file using Pandas and use try/except to handle exceptions
        try:
            self.df = pd.read_csv(self.filepath)
            print(f"Successfully loaded file: {self.filepath}\n")

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
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Requirements (Part 1) compliance:
#   1.1 have at least 2 meaningful, well-defined classes that have constructors,
#       attributes, methods, and instance objects.  'Logging_CSV_Load_DF' inherits from
#       the base class 'CSV_LOAD_DF'
#
# and
#
#   1.9 include a proper docstring and meaningful comments for each class and each function.
#       docstrings must be placed immediately below the class definition.
class Logging_CSV_Load_DF(CSV_Load_DF):
    """
    subclass that extends CSV_Load_DF to log a message on load.
    inherits behavior and overrides `load_df` from base class
    """
    def load_df(self):
        print(f"[LOG] Attempting to load CSV at: {self.filepath}")
        # call the parent implementation to keep existing behavior
        super().load_df()
        if self.df is not None:
            print(f"[LOG] Loaded dataframe shape: {self.df.shape}")

    # Requirements (part 2):
    #   recursion: the walk_nested_dict() helper function recursively walks a nested
    #              dictionary
    @staticmethod
    def walk_nested_dict(d, prefix=()):
        """
        recursively walk a (future) nested dictionary to yield (path_tuple, value)
        pairs for each leaf in a nested dict.

        - d: dict (possibly containing nested dicts)
        - prefix: tuple of ancestor keys (used internally for recursion)

        example usage:
          meta = {"a": {"b": 1}, "c": 2}
          list(Logging_CSV_Load_DF.walk_nested_dict(meta))
          # returns: [(('a','b'), 1), (('c',), 2)]
        """
        # if not a dict, treat d as a leaf value
        if not isinstance(d, dict):
            yield prefix, d
            return

        # Requirements (part 1) compliance:
        #  1.6  use at least 2 loop statements (for or while) and 2 if statements
        #       demonstrating logical control flow.  the following loop satisfies the
        #       first instance of requirement 1.6.
        for k, v in d.items():
            path = prefix + (k,)
            if isinstance(v, dict):
                # delegate to the same helper for nested dicts
                yield from Logging_CSV_Load_DF.walk_nested_dict(v, path)
            else:
                yield path, v

# Requirements (Part 1) compliance:
#   1.1 have at least 2 meaningful, well-defined classes that have constructores,
#       attributes, methods, and instance objects.  'Clean_DF' is composed from
#       the 'CSV_Load_DF' parent class.
#
# and
#
#   1.9 include a proper docstring and meaningful comments for each class and each function.
#       docstrings must be placed immediately below the class definition.
class Clean_DF:
    """
    Composition-based cleaner that 'has-a' CSV_Load_DF loader.

    Behavior:
      - If constructed with loader (CSV_Load_DF) or subdir+filename, it loads the CSV.
      - The `reduce_to_core_columns()` method keeps only the specified core columns.
      - The set of core columns is:
          ['seriesName','seriesUnits','entityID','entityIso','dataValue','dataYear']
    """

    CORE_COLUMNS = ["seriesName", "seriesUnits", "entityID", "entityIso", "dataValue", "dataYear"]

    def __init__(self, loader=None, subdir=None, filename=None):
        # Requirement (part 1) compliance:
        #   1.6  use at least 2 loop statements and 2 if statements, demonstrating logical
        #        control flow.  the following 3 'if' statements satisfy the requirement
        #        1.6 for 2 'if' statements (this logic block contains 3 'if' statements).
        #
        # Accept either an existing CSV_Load_DF or build one from subdir+filename
        if loader is not None:
            if not isinstance(loader, CSV_Load_DF):
                raise TypeError("loader must be an instance of CSV_Load_DF")
            self.loader = loader
        else:
            if subdir is None or filename is None:
                raise ValueError("Provide either loader or (subdir and filename)")
            self.loader = CSV_Load_DF(subdir, filename)

        # Requirements (part 1) compliance:
        #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
        #        string, tuple).  None is an immutable object.
        #
        # working DataFrame (copy of loader.df) or None
        self.df = None if self.loader.df is None else self.loader.df.copy()

    # Requirements (part 1) compliance:
    #   1.8  Implement __str__() and at least one additional operator overload.
    #   the class 'Clean_DF' implements __str__() below.
    def __str__(self):
        """
        string method that prints the shape of the df (if data is present) or indicates
        no dataframe (if no data is present)

        :return: string
        """
        loader_info = f"{type(self.loader).__name__}({getattr(self.loader, 'filepath', '')})"
        if self.df is None:
            df_info = "df=None"
        else:
            cols = list(self.df.columns)
            df_info = f"df_shape={self.df.shape}, columns={cols!r}"
        return f"Clean_DF(loader={loader_info}, {df_info})"

    # Requirements (part 2) compliance:
    #   2.8 __getattr__.  the Clean_DF class implements the __getattr__ special (dunder)
    #                     function to accommodate attribute lookups that aren't accessed
    #                     via the normal api.
    def __getattr__(self, name):
        """
        try to retrieve attribute from self.df (the working DataFrame), then from self.loader.
        this makes cleaner.columns or cleaner.shape convenient shortcuts.
        """
        # first try the working dataframe (if present)
        if self.df is not None and hasattr(self.df, name):
            return getattr(self.df, name)
        # then try delegating to the loader object (which may expose filepath, etc.)
        if hasattr(self, "loader") and self.loader is not None and hasattr(self.loader, name):
            return getattr(self.loader, name)
        # not found: raise AttributeError (standard behavior)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def reduce_to_core_columns(self):
        """
        Keep only CORE_COLUMNS present in self.df; drop all other columns.
        Updates self.df in place and returns the updated DataFrame.
        """
        if self.df is None:
            raise RuntimeError("No DataFrame loaded to clean (loader.df is None)")

        # Requirements (part 1) compliance:
        #   1.7  use at least 2 mutable types (list, dict, set) and 2 immutable types (number,
        #        string, tuple).  the code below defines a set 'core_set' which provides a
        #        3rd instance of mutable types required by requirement 1.7 (only 2 are
        #        required)
        #
        # and
        #
        #   2.5  one generator function or generator expression.  the following code block employs
        #        set operations
        #
        # create sets for fast membership tests and set algebra
        core_set = set(self.CORE_COLUMNS)
        cols_set = set(self.df.columns)

        # intersection gives core columns that actually exist in the dataframe
        present_set = core_set & cols_set

        # difference gives core columns that are missing from the dataframe
        missing_set = core_set - cols_set

        # Requirements (part 1) compliance:
        #  1.6  use at least 2 loop statements (for or while) and 2 if statements
        #       demonstrating logical control flow.
        #
        #  2.2  comprehension for at least one data type, for example, list comprehension
        #
        #  the following statement satisfies the 2nd instance of requirement 1.6 (for loop)
        #  and also requirement 2.2 (list comprehension)
        #
        # Find intersection of available columns and the core list
        available = [c for c in self.CORE_COLUMNS if c in present_set]

        # If none of the core columns exist, clear to empty dataframe or raise — here we keep empty DF
        if not available:
            # set df to empty dataframe with core columns as columns (all NaN)
            self.df = pd.DataFrame(columns=self.CORE_COLUMNS)
            print("No core columns found in source; created empty DataFrame with core column names.")
            return self.df

        # print diagnostic info about present/missing core columns
        print(f"Reduced DataFrame to core columns: {available}")
        if missing_set:
            print(f"Note: missing core columns: {sorted(list(missing_set))}")

        # Reduce DF to only the available core columns
        self.df = self.df[available].copy()

        # ensure data types: coerce dataValue and dataYear to numeric
        if "dataValue" in self.df.columns:
            self.df["dataValue"] = pd.to_numeric(self.df["dataValue"], errors="coerce")

        # Requirements (part 1) compliance:
        #   include at least 2 distinct exception-handling scenarios (e.g. invalid input,
        #   file/data loading errors, runtime/math errors).  in this scenario, we are
        #   using try/except to determine whether coercing a dataYear from string to a
        #   numeric is successful or not.
        if "dataYear" in self.df.columns:
            # use pandas nullable integer dtype for year if conversion succeeds
            try:
                self.df["dataYear"] = pd.to_numeric(self.df["dataYear"], errors="coerce").astype(pd.Int64Dtype())
            except Exception:
                # leave as-is if conversion fails
                pass

        print(f"Reduced DataFrame to core columns: {available}")
        return self.df

    def reduce_to_latest_by_iso(self, iso_col="entityIso", year_col="dataYear", value_col="dataValue"):
        """
        For each ISO (iso_col) that has multiple rows, keep only the most recently reported
        row with a valid dataValue.

        Strategy:
        - Coerce year_col and value_col to numeric (year -> Int64, value -> float).
        - Drop rows where value_col is missing (NaN) after coercion.
        - Sort by iso_col ascending and year_col descending (most recent first).
        - Drop duplicates keeping the first (most recent) row per iso_col.
        - Reset index and return the reduced DataFrame stored in self.df.

        Parameters:
        - iso_col: str, column name for ISO code (default "entityIso")
        - year_col: str, column name for year (default "dataYear")
        - value_col: str, column name for the measured value (default "dataValue")

        Returns:
        - pandas.DataFrame: the reduced DataFrame assigned to self.df
        """
        if self.df is None:
            raise RuntimeError(
                "No DataFrame loaded to operate on. Run reduce_to_core_columns() first or ensure loader.df exists.")

        # Ensure columns exist; if iso missing we cannot group
        if iso_col not in self.df.columns:
            raise KeyError(f"ISO column '{iso_col}' not found in DataFrame")
        if value_col not in self.df.columns:
            raise KeyError(f"Value column '{value_col}' not found in DataFrame")

        # Work on a copy
        df = self.df.copy()

        # Coerce types
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        # Coerce year to numeric nullable integer dtype if present
        if year_col in df.columns:
            df[year_col] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
        else:
            # If no year column, create one with NA so sorting will treat them as oldest
            df[year_col] = pd.Series([pd.NA] * len(df), dtype="Int64")

        # Drop rows with invalid/missing value_col (we only consider valid reported data)
        before_count = len(df)
        df = df[df[value_col].notna()].copy()
        after_drop_count = len(df)
        dropped_invalid_values = before_count - after_drop_count

        # Normalize iso codes (string, uppercase, stripped)
        df[iso_col] = df[iso_col].astype(str).str.upper().str.strip()

        # Sort by iso then by year descending (most recent first). NaN years will be last.
        df = df.sort_values(by=[iso_col, year_col], ascending=[True, False], na_position="last")

        # Keep the first row per ISO (most recent valid value)
        df_reduced = df.drop_duplicates(subset=[iso_col], keep="first").reset_index(drop=True)

        # Assign back to self.df
        self.df = df_reduced

        kept = len(self.df)
        print(f"Reduced by ISO: kept {kept} rows. Dropped {dropped_invalid_values} rows with invalid values; "
              f"dropped duplicates per ISO down to one row each.")

        return self.df

