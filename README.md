# Irish Pharmacy Online Register Scraper

This is a Python script that uses Selenium to enhance a published register of pharmacies from [Pharmaceutical Society of Ireland (PSI)](https://www.psi.ie) by scraping the online [Pharmaceutical Society of Ireland (PSI)](https://www.psi.ie) register. It takes a list of names published in an excel file or csv file and returns corresponding search results from the register.

---

## Features

- Scrapes contact details from the official pharmacy register
- Standardises phone numbers to a clean, consistent format
- Handles input from CSV or XLSX files
- Outputs enriched data to a CSV file
- Includes CLI for easy use

---

## Requirements

- Python 3.8+
- Google Chrome (installed)
- ChromeDriver (must be in your system PATH)

---

## Installation

1. **Clone the repository**
   
   ```bash
   git clone https://github.com/RachelGal/pharmacy-scraper.git
   cd pharmacy-scraper
   ```
   
3. Install required packages:

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py --input-file path/to/input.csv --filetype csv --output-file path/to/output.csv

```

### Required Arguments

| Argument        | Type   | Description                                                              |
|-----------------|--------|--------------------------------------------------------------------------|
| `--input-file`  | `str`  | **(Required)** Path to the input file containing data to search.         |
| `--filetype`    | `str`  | **(Required)** Format of the input file. Must be either `csv` or `xlsx`. |

### Optional Arguments

| Argument         | Type   | Description                                                                 |
|------------------|--------|-----------------------------------------------------------------------------|
| `--output-file`  | `str`  | Path to the output file. Defaults to `output.csv` if not specified.         |
| `--current-data` | `str`  | Optional path to an existing dataset of pharmacies (in CSV format) for comparison.        |

---

## Testing

This project includes unit tests for core functions like phone number standardisation and file type checks.

### Run tests:

```bash
pytest
```

> Make sure you have `pytest` installed. It's included in `requirements.txt`.

---

## Project Structure

```
pharmacy-scraper/
├── main.py               # Main script
├── utils.py              # Helper functions (e.g. phone formatting)
├── tests/
│   └── test_utils.py     # Unit tests
├── requirements.txt
└── README.md
```

---

## Disclaimer

This tool scrapes publicly available information from the PSI Register. Use responsibly and ensure compliance with the website's terms of service.
