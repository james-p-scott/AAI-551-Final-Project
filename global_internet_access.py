# import the file_io namespace
import file_io

def load_global_internet_access_data():
    """
    calls the class method from file_io namespace that loads the ITU global internet access
    data from a .csv file into a Pandas dataframe
    
    :return: Pandas dataframe containing the ITU global internet access data
    """
    # load the ITU Individual Internet Usage data from the .csv file into a Pandas dataframe
    df_loader = file_io.CSV_Load_DF("datasets", "individuals-using-the-internet.csv")
    # if the .csv file loaded successfully, display the head of the Pandas df
    if df_loader.df is not None:
        print(df_loader.df.head())
