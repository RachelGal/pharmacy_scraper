import pandas as pd
import argparse
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from tqdm import tqdm
from utils import init_driver,check_filetype,load_excel_file,clean_input,standardise_phone,update_change_log

#constants
url = "https://www.psi.ie/search-registers"
log_file = "scraper.log"
change_log_file = "change_log.csv"

#logging configuration
logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format="%(asctime)s %(levelname)s:%(message)s")

def search_register(name,driver):
    """
    Search the online pharmacy register for a given trading name.

    Args:
        name (str): The trading name to search for.
        driver (webdriver.Chrome): A Selenium Chrome driver instance.

    Returns:
        dict: A dictionary of results keyed by PSI Registration Number. Each value contains:
              - 'Trading Name'
              - 'Phone Number'
              - 'Website'
              - 'Superintendent Pharmacist'
              - 'Supervising Pharmacist'
              Returns an empty dict if no results are found or an error occurs.
    """
    try:
        driver.get(url)
        clean_name = clean_input(name)

        #search name
        try:
            search_box = WebDriverWait(driver,10).until(
                EC.presence_of_element_located((By.ID,"search-input"))
            )
            search_box.clear()
            search_box.send_keys(clean_name)
            search_box.send_keys(Keys.RETURN)
        except TimeoutException:
            logging.warning("Search input not found.")
            return {}
        
        #initialise results dict
        all_results = {}

        #wait for search results to load
        time.sleep(3)

        while True:
            WebDriverWait(driver,10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR,"ul.results-list > li")
                )
            )

            #collect all search results on page
            result_elements = driver.find_elements(By.CSS_SELECTOR,"ul.results-list > li > div.results-item")
            
            for element in result_elements:
                try:
                    #get name
                    name_element = element.find_element(By.CSS_SELECTOR,"div.results-item__header__text > h2")
                    result_name = name_element.text.strip()

                    #get id - psi registration number
                    id_element = element.find_element(By.XPATH,".//p[span[text()='PSI Registration Number:']]")
                    result_id = driver.execute_script("return arguments[0].textContent;",id_element)
                    result_id = result_id.split(":")[-1].strip() #use this method due to hidden characters
                    
                    try:
                        #phone number
                        phone_element = element.find_element(By.XPATH,".//p[span[text()='Tel:']]")
                        if phone_element:
                            phone_number = phone_element.text.replace("Tel:","").strip()
                            
                            #standardise phone number to desired format
                            standardised_phone = standardise_phone(phone_number)

                        else:
                            phone_number = "not available"
                        
                        #website
                        website_element = element.find_element(By.XPATH,".//p[span[text()='Web:']]")
                        if website_element:
                            website = website_element.text.replace("Web:","").strip()
                        else:
                            website = "not available"

                        #superintendent pharmacist
                        super_pharm_element = element.find_element(By.XPATH,".//p[span[text()='Superintendent Pharmacist:']]")
                        if super_pharm_element:
                            super_pharm = driver.execute_script("return arguments[0].textContent;",super_pharm_element)
                            super_pharm = super_pharm.split(":")[-1].strip()
                        else:
                            super_pharm = "not available"

                        #supervising pharmacist
                        superv_pharm_element = element.find_element(By.XPATH,".//p[span[text()='Supervising Pharmacist:']]")
                        if superv_pharm_element:
                            superv_pharm = driver.execute_script("return arguments[0].textContent;",superv_pharm_element)
                            superv_pharm = superv_pharm.split(":")[-1].strip()
                        else:
                            superv_pharm = "not available"

                    except Exception as e:
                        logging.error(f"Error extracting information: {e}")

                    #results dict
                    all_results[result_id] = {
                        "Trading Name":result_name,
                        "Phone Number":standardised_phone,
                        "Website":website,
                        "Superintendent Pharmacist":super_pharm,
                        "Supervising Pharmacist":superv_pharm
                    }

                except Exception as e:
                    logging.warning(f"Error processing item: {e}")

            try:
                next_button = driver.find_element(By.XPATH,".//button[@class='btn btn-link' and contains(text(), '›')]")
                driver.execute_script("arguments[0].scrollIntoView();", next_button) #scroll down if not in view
                time.sleep(1) #wait for scroll
                if "disabled" in next_button.get_attribute("class"): #if no more pages then search next result
                    break
                next_button.click() #click 'next' button (>) to go to next page
                time.sleep(3) #allow time for page to load

            except: #no more pages
                break

        return all_results

    except Exception as e:
        logging.error(f"Error in search for {name}: {e}")
        return {}

def compare_csv(old_df,new_df):
    """
    Compares two data frames representing different iterations of the same dataset and
    returns a changelog of differences

    Args:
        file1 (pandas.DataFrame): data frame to be updated
        file2 (pandas.DataFrame): data frame with updates
        
    Returns:
        changes_df(pandas.DataFrame): A changelog DataFrame containing the following columns:
                    Trading Name: The name of the entity (from name_column)
                    Registration Number: The unique ID for the row
                    change_type: One of "added", "removed", or "updated"
                    field_changed: The column name if the row was updated, otherwise blank

    Notes:
        Only columns common to both files are compared.
        If a row is updated in multiple fields, each field change is recorded as a separate row in the changelog.
    """
    key_columns = ["Registration Number","Trading Name"]

    #align to shared columns
    common_cols = list(set(old_df.columns) & set(new_df.columns))
    old_df = old_df[common_cols]
    new_df = new_df[common_cols]

    #clean values
    for col in key_columns:
        old_df[col] = old_df[col].astype(str).str.strip()
        new_df[col] = new_df[col].astype(str).str.strip()

    old_df.set_index(key_columns,inplace=True)
    new_df.set_index(key_columns,inplace=True)

    #find removed rows
    removed = old_df[~old_df.index.isin(new_df.index)]
    #find added rows
    added = new_df[~new_df.index.isin(old_df.index)]
    #find updated rows
    common_old = old_df[old_df.index.isin(new_df.index)]
    common_new = new_df[new_df.index.isin(old_df.index)]
    diffs = common_old.compare(common_new,keep_shape=True,keep_equal=False)

    #create the changelog
    changes = []

    #update the changelog
    for idx,row in removed.iterrows():
        changes = update_change_log(changes,idx[1],idx[0],"removed")

    for idx,row in added.iterrows():
        changes = update_change_log(changes,idx[1],idx[0],"added")

    for idx in diffs.index.unique():
        changed_fields = diffs.loc[idx].dropna().index.get_level_values(0).unique()
        for field in changed_fields:
            changes = update_change_log(changes,idx[1],idx if not isinstance(idx, tuple) else idx[0],"updated",field)

    #convert to data frame
    changes_df = pd.DataFrame(changes)

    return changes_df

def get_data(in_df,driver):
    """
    Enhances a DataFrame with additional information from an online register.

    Groups the input DataFrame by 'Trading Name', queries an online register
    for each group using the provided Selenium driver, and updates each row
    with contact and pharmacist details based on matching registration numbers.

    Args:
        in_df (pd.DataFrame): Input DataFrame containing at least 'Trading Name' and 'Registration Number' columns.
        driver (selenium.webdriver): Selenium WebDriver instance used to perform web scraping.

    Returns:
        pd.DataFrame: The updated DataFrame with additional columns 
                      'Phone Number', 'Website', 'Superintendent Pharmacist', and 
                      'Supervising Pharmacist'.
    """
    grouped = in_df.groupby("Trading Name") #for more efficient searching
    total_rows = len(in_df)
    print(f"Processing {total_rows} rows...\n")

    #name = unique trading names
    #group = rows with the same trading name
    for name,group in tqdm(grouped):
        logging.info(f"Searching for {name}")
        results = search_register(name,driver) #get all fields
        
        for index,row in group.iterrows(): #for each row with that name
            name = row["Trading Name"]
            id = row["Registration Number"]

            #search for matching result
            try:
                result = results[str(id)]
                #get location in output file
                i = in_df[in_df["Registration Number"]==id].index[0]
                #update
                in_df.at[i,"Phone Number"] = result.get("Phone Number")
                in_df.at[i,"Website"] = result.get("Website")
                in_df.at[i,"Superintendent Pharmacist"] = result.get("Superintendent Pharmacist")
                in_df.at[i,"Supervising Pharmacist"] = result.get("Supervising Pharmacist")
                
            except KeyError:
                logging.warning(f"No match found for {row['Trading Name']} with ID {row['Registration Number']}")
    
    return in_df

def main(input_file,input_type,output_file,current_data=None):
    driver = init_driver()

    #check for correct file type
    check_filetype(input_file,input_type,check_exists=True)
    check_filetype(output_file,'csv')

    try:
        if input_type=="xlsx":
            in_df = load_excel_file(input_file)
        else:
            in_df = pd.read_csv(input_file)
        
        df = get_data(in_df,driver)
        
        #if file provided for comparison
        if current_data:
            check_filetype(current_data,'csv',check_exists=True)
            old_df = pd.read_csv(current_data) #previous version of data

            change_df = compare_csv(old_df,df)

            print(f"Updated file at {output_file}. Changes detailed at {change_log_file}")

            df.to_csv(output_file,index=False)
            change_df.to_csv(change_log_file,index=False)

        else:
            print(f"Updated file at {output_file}")
            
            df.to_csv(output_file,index=False)

    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file',type=str,help="Path to file with data to search",required=True)
    parser.add_argument('--filetype',choices=['csv', 'xlsx'],help="Input filetype",required=True)
    parser.add_argument('--output-file',type=str,help="Path to output file",default="output.csv")
    parser.add_argument('--current-data',type=str,help="Path to current dataset in csv format")
    args = parser.parse_args()

    main(args.input_file,args.filetype,args.output_file,args.current_data)

