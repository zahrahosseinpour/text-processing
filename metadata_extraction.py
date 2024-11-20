import os
import re
import pandas as pd

# Define the DICOM tag pattern for the primary extraction
primary_pattern = r"\b(LO:|DS:|UT:|UI:)\s*'([\w\s\.\-]{1,60})'"

# Define the additional DICOM tag patterns
additional_dicom_patterns = {
    'UI': r'UI:\s*([\w\.\-]+)',
    'FL': r'\bFL:\s*\[([\d\.\,\s]+)\]'
}

def extract_tags_in_sequence(value):
    extracted_tags = []
    current_tag_sequence = []
    
    found_matches = re.findall(primary_pattern, value)
    for match in found_matches:
        tag = match[0]
        value = match[1].strip()
        current_tag_sequence.append({'Tag': tag, 'Value': value})
    
    if current_tag_sequence:
        extracted_tags.extend(current_tag_sequence)
    
    return extracted_tags

def extract_additional_tags(value):
    additional_tags = []
    
    for tag_type, pattern in additional_dicom_patterns.items():
        found_matches = re.findall(pattern, value)
        for match in found_matches:
            tag = tag_type
            if tag_type == 'FL':
                values = match.replace(',', '').split()
                values = [float(v) for v in values]
            elif tag_type == 'UI':
                values = match
            additional_tags.append({'Tag': tag, 'Value': values})
    
    return additional_tags

def process_metadata_file(file_path):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Extract required columns directly from the DataFrame
    patient_id = df['PatientID'].iloc[0] if 'PatientID' in df.columns else None
    content_date = df['ContentDate'].iloc[0] if 'ContentDate' in df.columns else None
    patient_age = df['PatientAge'].iloc[0] if 'PatientAge' in df.columns else None
    patient_sex = df['PatientSex'].iloc[0] if 'PatientSex' in df.columns else None
    accession_number = df['AccessionNumber'].iloc[0] if 'AccessionNumber' in df.columns else None
    series_instance_uid = df['SeriesInstanceUID'].iloc[0] if 'SeriesInstanceUID' in df.columns else None
    sop_instance_uid = df['SOPInstanceUID'].iloc[0] if 'SOPInstanceUID' in df.columns else None
    sr_file_name = df['SRFileName'].iloc[0] if 'SRFileName' in df.columns else None

    if not patient_id or not content_date or not patient_age or not patient_sex:
        print(f"PatientID, ContentDate, PatientAge, or PatientSex not found in {file_path}")
        return

    # Initialize a list to store the matches
    matches = []

    # Iterate over the DataFrame to find matches in the 'ContentSequence' column
    for index, row in df.iterrows():
        content_sequence_value = row.get('ContentSequence', '')
        if pd.isna(content_sequence_value):
            continue
        extracted_tags = extract_tags_in_sequence(content_sequence_value)
        additional_tags = extract_additional_tags(content_sequence_value)
        for tag in extracted_tags:
            matches.append({'Tag': tag['Tag'], 'Value': tag['Value']})
        for tag in additional_tags:
            matches.append({'Tag': tag['Tag'], 'Value': tag['Value']})

    # Include the extracted column values in the matches
    matches.extend([
        {'Tag': 'PatientID', 'Value': patient_id},
        {'Tag': 'ContentDate', 'Value': content_date},
        {'Tag': 'PatientAge', 'Value': patient_age},
        {'Tag': 'PatientSex', 'Value': patient_sex},
        {'Tag': 'AccessionNumber', 'Value': accession_number},
        {'Tag': 'SeriesInstanceUID', 'Value': series_instance_uid},
        {'Tag': 'SOPInstanceUID', 'Value': sop_instance_uid},
        {'Tag': 'SRFileName', 'Value': sr_file_name}
    ])

    # Create a DataFrame from the matches
    output_df = pd.DataFrame(matches, columns=['Tag', 'Value'])

    # Define the output directory
    output_dir = '/Users/zahrahosseinpour/Documents/Veolity/Veo_analysis/step2_tags'
    os.makedirs(output_dir, exist_ok=True)

    # Create filenames with PatientID
    output_filename = f'extracted_tags_{patient_id}.csv'
    output_file_path = os.path.join(output_dir, output_filename)

    # Save the matches to the specified folder as a CSV file
    output_df.to_csv(output_file_path, index=False)
    print(f"Matches have been saved to {output_file_path}")

# Root directory where SR folders are located
root_dir = '/Users/zahrahosseinpour/Documents/Veolity/Veo_analysis/metadatas_Oct15'

# Walk through the directory and find all CSV files that include "metadata" in their name
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if 'metadata' in file.lower() and file.endswith('.csv'):
            file_path = os.path.join(subdir, file)
            process_metadata_file(file_path)
