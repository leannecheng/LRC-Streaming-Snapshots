import pandas as pd
import json
import re

def clean_language_name(name):
    """Remove stray punctuation, correct typos, and normalize casing on language names."""
    name = re.sub(r'^[^A-Za-z]+|[^A-Za-z]+$', '', name.strip())
    if not name:
        return "Unknown"
    corrected = name.lower()
    typo_map = {
        "frecnh": "french"
    }
    corrected_fixed = typo_map.get(corrected, corrected)
    return corrected_fixed.capitalize()

# File and sheet
excel_file = "S Streaming Statistics Sp_Su 2023 - Winter 2024.xlsx"
sheet_name = "Winter 2024"
output_filename = "cleaned_data_winter2024.json"

print(f"🔎 Processing sheet: {sheet_name}")
df = pd.read_excel(excel_file, sheet_name=sheet_name)

json_data = {
    "terms": {
        sheet_name: {
            "total_students": 0,
            "total_reservations": 0,
            "departments": {}
        }
    }
}
term = json_data["terms"][sheet_name]

for idx, row in df.iterrows():
    # --- Extract and normalize course ---
    course_code = str(row["Course"]).strip()
    if not course_code or "practice" in course_code.lower():
        continue  # Skip rows with missing course or containing "Practice"

    # --- Extract and normalize department ---
    raw_department = course_code.split()[0].strip()
    department = raw_department.lower().capitalize() if raw_department else "Unknown"

    # --- Correct typo: "Asain" → "Asian"
    if department.lower() == "asain":
        department = "Asian"

    # --- Extract and normalize level ---
    match = re.search(r'\d+', course_code)
    if match:
        course_num = int(match.group())
        level_bucket = (course_num // 100) * 100
        level = str(level_bucket)
    else:
        level = "Unknown"

    # --- Extract, correct, and normalize language ---
    raw_language = str(row["Language"]).strip()
    if raw_language and raw_language.lower() != "nan":
        primary_language = clean_language_name(raw_language.split()[0])
        if primary_language.lower() == "french":
            print(f"✅ Corrected typo in row {idx}: detected Frecnh → French")
    else:
        primary_language = None  # We'll handle this below

    # --- Department overrides for Asianlan/Slavic/Asian ---
    if department.lower() in ["asianlan", "slavic", "asian"]:
        if primary_language:
            department = f"{department}: {primary_language}"
        else:
            department = f"{department}: Other"

    # --- Enrollment data ---
    students = int(row["Students Enrolled"])
    reservations = int(row["Reservations"])

    # --- Build JSON hierarchy (dept -> levels) ---
    if department not in term["departments"]:
        term["departments"][department] = {
            "levels": {},
            "total_students": 0,
            "total_reservations": 0
        }
    dept = term["departments"][department]

    if level not in dept["levels"]:
        dept["levels"][level] = {
            "students": 0,
            "reservations": 0
        }

    # --- Aggregate counts ---
    dept["levels"][level]["students"] += students
    dept["levels"][level]["reservations"] += reservations

    dept["total_students"] += students
    dept["total_reservations"] += reservations

    term["total_students"] += students
    term["total_reservations"] += reservations

# --- Write JSON ---
with open(output_filename, "w") as f:
    json.dump(json_data, f, indent=2)

print(f"✅ JSON for {sheet_name} saved as {output_filename}")
