# ETL-python-from-log-data-to-SQL-database

## 🧰 Project Overview

This project implements an **ETL (Extract-Transform-Load)** pipeline in **Python** to process machine or tester log data and load it into a SQL database.  
It automates parsing, cleaning, and transforming large sets of raw logs into structured database records for analytics and reporting.

---

## ⚙️ Key Features

- **Extract**: Read raw `.log` or `.txt` files from multiple folders.
- **Regex-based Parsing**: Extract key information using powerful regular expressions.
- **Transform**: Clean, standardize, and enrich the data before loading.
- **Load**: Store results into a relational SQL database (SQL Server, MySQL, or PostgreSQL).
- **Duplicate Prevention**: Avoid reloading the same test data.
- **Configurable**: Adjust folder paths, regex patterns, and SQL table mapping easily.

---

## 🧩 Role of Regex (Regular Expressions)

Regex plays a central role in this ETL pipeline — it defines how data is **identified and extracted** from unstructured log text.

### 🧠 How It Works
Each log file line is matched against one or more regex patterns that capture specific values, such as test start time, insertion count, or pass/fail results.

For example:

```python
special_patterns = {
    'Test_Start_Date': r'Test Start Time:\s*(\d{4}-\d{2}-\d{2})',
    'Test_Start_Time': r'Test Start Time:\s*\d{4}-\d{2}-\d{2}\s*(\d{2}:\d{2}:\d{2})',
    'Insertion_Count': r'<00000140>.*?Insertion count:\s*(\d+)',
    'Result': r'Result:\s*(PASS|FAIL)'
}
