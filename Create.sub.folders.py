import os
import csv
import sys

if len(sys.argv) < 2:
    print("Usage: python create.sub.folders.with.test.files.Revised.py <csv_file_path>")
    sys.exit(1)

csv_file_path = sys.argv[1]

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    for row in reader:
        test_location = row.get('test_location', '').strip()
        if test_location:
            test_dir = os.path.dirname(test_location)
            if test_dir:
                os.makedirs(test_dir, exist_ok=True)
                print(f"Created directory for test_location: {test_dir}")

        output_location = row.get('output_location', '').strip()
        if output_location:
            output_dir = os.path.dirname(output_location)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                print(f"Created directory for output_location: {output_dir}")
