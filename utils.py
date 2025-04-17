import pandas as pd
import argparse
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

def init_driver():
    """
    Initialise a headless Chrome WebDriver
    
    Returns:
        driver (selenium.webdriver): Selenium WebDriver instance.
    """
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        return driver
    
    except Exception as e:
        logging.error(f"Failed to initialise WebDriver: {e}")

def clean_input(name):
    """Sanitise the input name by removing extra characters."""
    name = name.strip()
    name = name.strip('"')
    return name
            
def standardise_phone(number):
    """Standardise Irish phone numbers to the international format (+353)."""
    if not isinstance(number, str):
        return "non-valid number"
    
    #normalise input
    clean_num = re.sub(r'^\s*\d{5}\s*(?=\(0?\d{1,3}\))', '',number) #remove 5 digit internal extension e.g. 22605 (042) 9322605
    clean_num = re.sub(r'(353|00353|\+353)?\s*(\d{1,2})\s*\(0?\2\)', r'\1 \2',clean_num) #remove duplicated area code e.g. 353 71 (071) 9142696
    clean_num = re.sub(r'[^\d+]','',clean_num) #remove non-numeric characters (except +)
    clean_num = re.sub(r'^(00|\+)?353','',clean_num) #remove country code
    clean_num = clean_num.lstrip('0') #remove leading zeros

    #check for mobile numbers
    if clean_num.startswith(('83', '85', '86', '87', '89')) and len(clean_num)==9:
        return f"+353 {clean_num[:2]} {clean_num[2:5]} {clean_num[5:]}"
    
    #check for landline - format as +353 X XXX XXXX or +353 XX XXX XXXX or +353 XX XXXXX
    if clean_num.startswith('1') and len(clean_num)==8: #Dublin 1
        return f"+353 {clean_num[:1]} {clean_num[1:4]} {clean_num[4:]}"
    elif len(clean_num)==7:  #shorter landline numbers
        return f"+353 {clean_num[:2]} {clean_num[2:]}"
    elif len(clean_num)==8:  #shorter landline numbers
        return f"+353 {clean_num[:2]} {clean_num[2:5]} {clean_num[5:]}"
    elif len(clean_num)==9:  #longer landline numbers e.g. Cork 21
        return f"+353 {clean_num[:2]} {clean_num[2:5]} {clean_num[5:]}"
    
    #if not a valid format and length
    return "non-valid number"

def check_filetype(filename,extension,check_exists=False):
    """
    Validates the type and existence of a file.

    Args:
        filename (str): Path to the file to be checked.
        extension (str): Expected file extension (e.g., 'csv', 'xlsx').
        check_exists (bool, optional): If True, also checks whether the file exists. Defaults to False.

    Returns:
        bool: True if checks are passed

    Raises:
        argparse.ArgumentTypeError: If the file extension is incorrect or the file does not exist (when check_exists is True).
    """
    if not filename.lower().endswith(extension):
        raise argparse.ArgumentTypeError(f"File '{filename}' is not {extension} file.")
    if check_exists:
        if not os.path.isfile(filename):
            raise argparse.ArgumentTypeError(f"File '{filename}' does not exist.")
    return True

def load_excel_file(filepath,max_expected_header_rows=3):
    """
    Loads an Excel file and detect the header row by scanning for the first row of numeric data.

    This is useful for files with multiple header rows, where users may have removed
    some rows, or where the true header row varies.

    Args:
        filepath (str): Path to the Excel (.xlsx) file.
        max_expected_header_rows (int, optional): Maximum number of initial rows to scan to detect
                                           the start of numeric data. Defaults to 3.

    Returns:
        pandas.DataFrame: A DataFrame with properly set column headers and cleaned data.

    Raises:
        ValueError: If the file has fewer than 2 rows or no numeric row is detected within
                    the first `max_expected_header_rows` rows.
    """
    df_raw = pd.read_excel(filepath,header=None).head(500)
    total_rows = df_raw.shape[0]

    if total_rows<2:
        raise ValueError("File has too few rows to determine header.")

    header_idx = None

    #scan first few rows to detect where data starts
    for i in range(0,min(max_expected_header_rows,total_rows)):
        first_cell = df_raw.iloc[i, 0]
        try:
            float(first_cell)
            is_numeric = True
        except (ValueError, TypeError):
            is_numeric = False

        if is_numeric:
            header_idx = i - 1
            break

    if header_idx is None:
        #fall back to last row among the first few if nothing is clearly numeric
        header_idx = min(max_expected_header_rows, total_rows) - 1

    new_header = df_raw.iloc[header_idx].tolist()
    df_data = df_raw.iloc[header_idx + 1:].reset_index(drop=True)
    df_data.columns = new_header

    return df_data

def update_change_log(change_log,name,id,change_type,field=''):
    """
    Updates the change log DataFrame with a new change entry.

    Args:
        change_log (pd.DataFrame): The DataFrame tracking all changes.
        name (str): The trading name associated with the record.
        id (str): The registration number of the record.
        change_type (str): The type of change ('added', 'removed', or 'updated').
        field (str, optional): The specific field that was changed (only used if change_type is 'updated'). Default is '' (an empty string)

    Returns:
        pd.DataFrame: The updated change log with the new entry added.
    """
    change_log.append({
            "Trading Name":name,
            "Registration Number":id,
            "change_type":change_type,
            "field_changed":field
        })
    
    return change_log
