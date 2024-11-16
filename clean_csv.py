import csv
import re

# Load the CSV file
input_file = r".\data\tech_skills.csv"  # Replace with your CSV file path
output_file = r".\data\tech_skills_clean.csv"  # Output file path

# Read and clean the single row
with open(input_file, "r") as infile:
    reader = csv.reader(infile)
    for row in reader:
        # Clean each cell in the row
        cleaned_row = [re.sub(r'[^a-z0-9]', '', cell.lower()) for cell in row]

# Save the cleaned row to a new CSV file
with open(output_file, "w", newline="") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(cleaned_row)

print("File cleaned and saved as", output_file)
