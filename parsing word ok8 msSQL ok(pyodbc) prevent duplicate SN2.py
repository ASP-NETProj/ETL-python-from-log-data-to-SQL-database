import os
import re
import csv
import pyodbc

# ======================================
# CONFIGURATION
# ======================================
root_directory = 'C:/Users/budis/source/repos/ok/ETL parsing word python OK (from log to SQL )/!log from FTP/'
csv_directory = 'C:/Users/budis/source/repos/ok/ETL parsing word python OK (from log to SQL )/'
csv_output_path = os.path.join(csv_directory, 'word_values_results.csv')

# SQL Server info
DB_SERVER = 'DESKTOP-MR2VJ1G'   # or 'localhost'
DB_NAME = 'TestStandDB'

# ======================================
# REGEX PATTERNS
# ======================================
special_patterns = {
    'Test_Start_Date': r'<00000050>.*?Info:\s*Test Start Time:\s*(\d{4}-\d{2}-\d{2})',
    'Test_Start_Time': r'<00000050>.*?Info:\s*Test Start Time:\s*\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2})',
    '00000140_Insertion_count': r'<00000140>.*?Insertion count:\s*(.+)',
    '00008000_Status_Test': r'<00008000>.*?Info:\s*(.+)',
    '00000130_Tot_Test_time': r'<00000130>.*?Total Test Time:\s*(.+)',
    '00003080_': r'<00003080>.*?Serial:\s*(.+)',
    '00003080_Serial_Block': r'<00003080>.*?Serial:\s*(.*?)(?=<\d{8}>)',
}

# ======================================
# READ LOG FILES
# ======================================
results = []

for subdir, _, files in os.walk(root_directory):
    for filename in files:
        if filename.endswith('.log'):
            file_path = os.path.join(subdir, filename)
            relative_path = os.path.relpath(subdir, root_directory)

            row = {
                'Subfolder': relative_path,
                'Filename': filename,
                'File_Location': file_path
            }

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

                for label, pattern in special_patterns.items():
                    match = re.search(pattern, content, re.IGNORECASE)
                    row[label] = match.group(1).strip() if match else ''

            results.append(row)

# ======================================
# INSERT INTO SQL SERVER
# ======================================
try:
    connection_string = (
        f"Driver={{ODBC Driver 17 for SQL Server}};"
        f"Server={DB_SERVER};"
        f"Database={DB_NAME};"
        f"Trusted_Connection=yes;"
    )

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ Connected to SQL Server successfully.")

    # Create table if not exists
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LogResults' AND xtype='U')
    CREATE TABLE LogResults (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Subfolder NVARCHAR(255),
        Filename NVARCHAR(255),
        File_Location NVARCHAR(500),
        Test_Start_Date NVARCHAR(50),
        Test_Start_Time NVARCHAR(50),
        [00000140_Insertion_count] NVARCHAR(100),
        [00008000_Status_Test] NVARCHAR(200),
        [00000130_Tot_Test_time] NVARCHAR(100),
        [00003080_] NVARCHAR(200),
        [00003080_Serial_Block] NVARCHAR(200)
    )
    """
    cursor.execute(create_table_sql)
    conn.commit()

    # Ensure unique index on (Serial, Date, Time)
    cursor.execute("""
    IF NOT EXISTS (
        SELECT * FROM sys.indexes WHERE name = 'IX_LogResults_Unique'
    )
    CREATE UNIQUE INDEX IX_LogResults_Unique
    ON LogResults ([00003080_], Test_Start_Date, Test_Start_Time)
    """)
    conn.commit()

    # Insert data only if not exists
    insert_sql = """
    IF NOT EXISTS (
        SELECT 1 FROM LogResults
        WHERE [00003080_] = ? AND Test_Start_Date = ? AND Test_Start_Time = ?
    )
    INSERT INTO LogResults (
        Subfolder, Filename, File_Location,
        Test_Start_Date, Test_Start_Time,
        [00000140_Insertion_count], [00008000_Status_Test],
        [00000130_Tot_Test_time], [00003080_], [00003080_Serial_Block]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    inserted_count = 0
    for row in results:
        cursor.execute(insert_sql, (
            row.get('00003080_', ''),
            row.get('Test_Start_Date', ''),
            row.get('Test_Start_Time', ''),
            row['Subfolder'],
            row['Filename'],
            row['File_Location'],
            row.get('Test_Start_Date', ''),
            row.get('Test_Start_Time', ''),
            row.get('00000140_Insertion_count', ''),
            row.get('00008000_Status_Test', ''),
            row.get('00000130_Tot_Test_time', ''),
            row.get('00003080_', ''),
            row.get('00003080_Serial_Block', '')
        ))
        inserted_count += cursor.rowcount

    conn.commit()
    print(f"✅ Insert complete. {inserted_count} new rows added (duplicates skipped).")

    # ======================================
    # EXPORT DATA FROM SQL SERVER TO CSV
    # ======================================
    print("📤 Exporting all data from SQL Server to CSV...")

    select_sql = "SELECT * FROM LogResults ORDER BY ID"
    cursor.execute(select_sql)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    export_path = os.path.join(csv_directory, 'LogResults_from_SQL.csv')

    with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"✅ Export complete. Data saved to: {export_path}")

except Exception as e:
    print(f"❌ SQL Server operation error: {e}")

finally:
    if 'conn' in locals():
        conn.close()
