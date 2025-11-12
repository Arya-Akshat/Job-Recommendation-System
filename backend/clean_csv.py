import csv
import re
import os

# --- Constants ---
INPUT_FILE = os.path.join('data', 'tech_skills.csv')
OUTPUT_FILE = os.path.join('data', 'tech_skills_clean.csv')

def clean_skills_csv(input_path: str, output_path: str):
    """
    Reads a single row of skills from a CSV, cleans each skill,
    and saves the cleaned skills to a new CSV file.
    """
    try:
        with open(input_path, "r", encoding='utf-8') as infile:
            reader = csv.reader(infile)
            # Read only the first row, if it exists
            first_row = next(reader, None)
            
            if first_row is None:
                print(f"Warning: Input file '{input_path}' is empty.")
                return

            # Clean each cell in the row: convert to lowercase and remove non-alphanumeric chars.
            cleaned_row = [re.sub(r'[^a-z0-9]', '', cell.lower()) for cell in first_row]

        # Save the cleaned row to a new CSV file
        with open(output_path, "w", newline="", encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(cleaned_row)

        print(f"File cleaned and saved as '{output_path}'")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clean_skills_csv(INPUT_FILE, OUTPUT_FILE)
