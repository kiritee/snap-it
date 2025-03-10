import csv

def is_valid_csv(file_path):
    try:
        with open(file_path, newline='', encoding='utf-8') as file:
            sniffer = csv.Sniffer()
            sample = file.read(1024)  # Read a small portion to detect delimiter
            file.seek(0)  # Reset file pointer
            
            # Check if it's a CSV based on structure
            if not sniffer.has_header(sample):
                return False  # No header found, possibly not a CSV

            reader = csv.reader(file)
            row_length = None

            for row in reader:
                if row_length is None:
                    row_length = len(row)
                elif len(row) != row_length:
                    return False  # Inconsistent row lengths

            return True  # If no issues, it's a valid CSV
    except Exception as e:
        return False  # Any error in reading means it's not a valid CSV

# Usage:
file_path = "your_file.csv"
print(is_valid_csv(file_path))  # True if valid CSV, False otherwise
