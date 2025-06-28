import pandas as pd
import re

def clean_fall24_streaming(input_path: str, output_path: str):
    """
    Reads the 'RAW' sheet from the given Excel file, cleans and aggregates:
      - Drops rows with missing/blank 'Course'
      - Trims whitespace on 'Course'
      - Drops rows where 'Course' contains 'testcourse' (case-insensitive)
      - Groups by (Uniquename, Course, Section)
      - Aggregates:
          * Reservations = count of rows in group
          * Students Enrolled = first non-null Enrollment parsed as int (default 0)
          * Language = unique CIR_COL::Language values joined by comma
      - Treats missing Section as placeholder "Unknown Section"
    Writes out a new Excel file with one sheet named 'Fall 2024'.
    """
    # 1. Load RAW sheet
    df = pd.read_excel(input_path, sheet_name="RAW")

    # 2. Drop rows with missing/blank Course
    df = df[df["Course"].notna() & df["Course"].str.strip().ne("")]

    # 3. Trim whitespace in Course
    df["Course"] = df["Course"].str.strip()

    # 4. Drop rows where Course contains "testcourse" (case-insensitive)
    df = df[~df["Course"].str.lower().str.contains("testcourse")]

    records = []
    grouped = df.groupby(["Uniquename", "Course", "Section"], dropna=False)
    for (instr, course, section), group in grouped:
        # a) Build comma-joined unique languages
        langs = group["CIR_COL::Language"].dropna().astype(str).str.strip().tolist()
        seen = []
        for lang in langs:
            if lang not in seen:
                seen.append(lang)
        language = ", ".join(seen)

        # b) Count reservations
        reservations = len(group)

        # c) First non-null Enrollment or 0, stripping non-digits
        non_null = group["Enrollment"].dropna()
        if len(non_null) > 0:
            raw_val = str(non_null.iloc[0])
            digits = re.findall(r'\d+', raw_val)
            students = int(digits[0]) if digits else 0
        else:
            students = 0

        # d) Section fallback: placeholder if missing
        sec = section if pd.notna(section) and str(section).strip() != "" else "Unknown Section"

        records.append({
            "Instructor": instr,
            "Course": course,
            "Section": sec,
            "Language": language,
            "Reservations": reservations,
            "Students Enrolled": students
        })

    # 6. Build cleaned DataFrame
    clean_df = pd.DataFrame.from_records(records)

    # 7. Write to new Excel file with sheet named "Fall 2024"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        clean_df.to_excel(writer, sheet_name="Fall 2024", index=False)

    print(f"✅ Cleaned data written to '{output_path}' (sheet='Fall 2024')")


if __name__ == "__main__":
    input_file = "Copy of Fall24Streaming.xlsx"
    output_file = "Fall 2024.xlsx"
    clean_fall24_streaming(input_file, output_file)
    print("All done!")
