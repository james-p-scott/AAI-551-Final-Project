# AAI-551-Final-Project
# Evaluating the Digital Divide - Characterizing the Key Underlying Aspects that Drive Disparities in Access

## Team Members
|---------------|--------------------------|------------|---------------|
|      NAME     |       EMAIL ADDRESS      | STEVENS ID |    GitHub ID  |
|---------------|--------------------------|------------|---------------|
| Jeff Busold   | jbusold@stevens.edu      |  20006079  |  OverkillLC   |
| James Scott   | james.p.scott@boeing.com |  10311319  | james-p-scott |
| Dominick Vovk | dvovk1015@gmail.com      |  20002381  |               |
|---------------|--------------------------|------------|---------------|

## Problem Description
### Project Overview
The Digital Divide refers to the gap between those individuals, households, and populations that have access to modern information and communications technology (ICT) and those that do not.  In this context, ICT refers to broadband Internet access, modern computing devices, and the digital literacy required to access and use these capabilities.  According to statistics collected by the International Telecommunication Union (ITU), approximately 2.2 billion of the earth’s 8.3 billion human population remain unconnected, primarily residing in developing countries.  The key drivers behind the Digital Divide are economic disparity (e.g. the cost of modern computers and Internet subscriptions), geographic limitations (e.g. urban vs rural), digital literacy (e.g. lack of technology training) and education (e.g. budget shortfalls in lower income school districts), and demographic factors (e.g. age, disabilities, barriers to access based on social or cultural attributes).
This project proposes to analyze at least three (3) key aspects that drive the Digital Divide, selected from the following list and based on team member interests:
a)	Extend past research to predict the size and growth rate of the Digital Divide, circa 2026
b)	Evaluate the impact of economic disparities on the size and growth rate of the Digital Divide, based on the available dataset
c)	Evaluate the impact of digital literacy and skills on the size and growth rate of the Digital Divide, based on the available dataset
d)	Evaluate the impact of educational gaps on the size and growth rate of the Digital Divide, based on the available dataset
e)	Evaluate the impact of age and demographic factors on the size and growth rate of the Digital Divide, based on the available dataset

### Project Dependencies
- Determining which of te above key aspects a team member chooses to address depends on first gaining familiarity with the publicly available datasets listed below
- Prior to beginning code development, each team member must document their class definitions, functions, and key algorithms and data structures to be used by their Python code
- Before checking project artifacts into the GitHub repo, each team member must understand how to use GitHub
- Data from the datasets must be loaded from the public dataset into a suitable dataframe for processing
- Each team member must update the project README.md file when they commit new or modified (properly documented) code into the GitHub repo

### External Libraries
 - NumPy - an open-source used for scientific computing and performing high-performance mathematical operations on large, multi-dimensional data structures
 - Pandas - an open-source library used for data manipulation, analysis, and cleaning
 - GeoPandas - open-source extensions to Pandas that allows spatial operations to be performed on geometric types
 - TensorFlow - an open-source library developed by Google Brain to simplify the development and deployment of Machine Learning and Deep Learning models (c.f. PyTorch or Keras)

### File/Module Structure
The main function resides in AAI-551-Final-Project.ipynb with all other classes and functions contained in .py files that are imported into the proper namespace.

```
AAI-551_Final-Project.ipynb         — main program (entry point)
file_io.py                          — CSV data loading utility (CSV_Load_DF class)
global_internet_access.py           — global internet access analysis module
load_ict_data.py                    — ICT data loading helpers
digital_skills/                     — digital literacy & ICT skills analysis package
    __init__.py                     — package exports
    ict_skills_dataset.py           — ICTSkillsDataset class (loads one ITU skill-category CSV)
    digital_skills_analyzer.py      — DigitalSkillsAnalyzer class (cross-category analysis & visualization)
    digital_skills_analysis.py      — top-level entry-point functions called from the notebook
    digital_literacy_predictor.py   — DigitalLiteracyPredictor class (linear regression forecasting)  
    tests/
        test_ict_skills.py          — pytest test suite for the digital_skills package
datasets/                           — ITU CSV data files
```

### Python Version Used
Python 3.14.3

## Publicly Available Datasets
1. The International Telecommunications Union (ITU) provides a public dataset (1975-2025) of annual Digital Divide related statistics. https://datahub.itu.int 
2. The United Nations provides a large collection of public datasets (2010-2025), one of which reflects the global population, per country. https://data.un.org 
3. The World Bank provides a dataset (1960-2025) that relate to economic indicators for each country in the world https://datacatalog.worldbank.org/home  

## How to Run the Program
1. Clone the repository and open `AAI-551_Final-Project.ipynb` in Jupyter or VS Code.
2. Ensure the `datasets/` directory is present at the project root with all ITU CSV files.
3. Install required libraries: `pip install pandas numpy matplotlib torch pytest`
4. Run all notebook cells in order.

To run the pytest test suite:
```
python -m pytest digital_skills/tests/ -v
```
*(to be updated with additional test cases as development progresses)*

## Main Contributions of Each Team Member

### Jeff Busold — Digital Literacy & ICT Skills Analysis
Analyzed the impact of digital literacy and ICT skills on the Digital Divide using ITU skill-category datasets. Contributions include:
- `digital_skills/ict_skills_dataset.py` — `ICTSkillsDataset` class: loads a single ITU ICT skill-category CSV and provides filtered views by country, year, gender, age group, and urban/rural geography.
- `digital_skills/digital_skills_analyzer.py` — `DigitalSkillsAnalyzer` class: composes multiple `ICTSkillsDataset` instances to enable cross-category ranking, skill gap identification, trend analysis, gender gap analysis, age-group distribution analysis, and matplotlib visualizations.
- `digital_skills/digital_skills_analysis.py` — top-level entry-point functions (`load_all_ict_skill_datasets`, `load_skill_level_summary`, `iter_country_data`, `run_digital_literacy_analysis`) called directly from the project notebook.
- `digital_skills/digital_literacy_predictor.py` — `DigitalLiteracyPredictor` class: uses historical ITU skill-category data to train a simple linear regression model for predicting future digital literacy levels and plotting growth forecasts.
- `digital_skills/__init__.py` — package exports for the above classes and functions.
- `digital_skills/tests/` — pytest test suite

### James Scott
*(to be updated)*

### Dominick Vovk
*(to be updated)*
