import pytest
from utils import init_driver,standardise_phone,check_filetype
from main import compare_csv,url
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import argparse
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_init_driver():
    driver = init_driver()
    assert driver is not None
    assert "chrome" in driver.capabilities["browserName"].lower()
    driver.quit()

def test_load_url():
    driver = init_driver()
    driver.get(url)
    assert "Search the Registers | PSI" in driver.title  # Adjust based on real page title
    driver.quit()

def test_search_box_exists():
    driver = init_driver()
    driver.get(url)
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-input"))
        )
        assert element is not None
    finally:
        driver.quit()

def test_standardise_phone():
    assert standardise_phone("01 234 5678") == "+353 1 234 5678"
    assert standardise_phone("353 86 1234567") == "+353 86 123 4567"
    assert standardise_phone("(071) 9142696") == "+353 71 914 2696"
    assert standardise_phone("22605 (042) 9322605") == "+353 42 932 2605"
    assert standardise_phone("052 12345") == "+353 52 12345"
    assert standardise_phone("foo") == "non-valid number"

def test_invalid_filetype(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("just some text")
    with pytest.raises(argparse.ArgumentTypeError, match="is not csv"):
        check_filetype(str(file),'csv')

def test_file_not_found():
    with pytest.raises(argparse.ArgumentTypeError):
        check_filetype("non_existent.csv","csv", check_exists=True)

def test_compare_csv_no_change():
    df1 = pd.DataFrame({
        "Registration Number": [1],
        "Trading Name": ["Pharma A"],
        "Phone": ["123"]
    })
    df2 = df1.copy()

    changes = compare_csv(df1, df2)
    assert changes.empty

def test_compare_csv_addition():
    df1 = pd.DataFrame(columns=["Registration Number", "Trading Name", "Phone"])
    df2 = pd.DataFrame({
        "Registration Number": [1],
        "Trading Name": ["Pharma A"],
        "Phone": ["123"]
    })

    changes = compare_csv(df1, df2)
    assert len(changes) == 1
    assert changes.iloc[0]["change_type"] == "added"

def test_compare_csv_removal():
    df1 = pd.DataFrame({
        "Registration Number": [1],
        "Trading Name": ["Pharma A"],
        "Phone": ["123"]
    })
    df2 = pd.DataFrame(columns=["Registration Number", "Trading Name", "Phone"])

    changes = compare_csv(df1, df2)
    assert len(changes) == 1
    assert changes.iloc[0]["change_type"] == "removed"

def test_compare_csv_multiple_field_update():
    df1 = pd.DataFrame({
        "Registration Number": [1],
        "Trading Name": ["Pharma A"],
        "Phone": ["123"],
        "Website": ["http://a.com"]
    })
    df2 = pd.DataFrame({
        "Registration Number": [1],
        "Trading Name": ["Pharma A"],
        "Phone": ["456"],
        "Website": ["http://b.com"]
    })

    changes = compare_csv(df1, df2)
    assert len(changes) == 2
    assert set(changes["field_changed"]) == {"Phone", "Website"}
