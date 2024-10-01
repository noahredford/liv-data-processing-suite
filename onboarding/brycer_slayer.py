import pandas as pd
import re
import os

def clean_and_format_brycer_data(premise_file_path, contact_file_path):
    # Determine the file extension for both files
    premise_ext = os.path.splitext(premise_file_path)[1].lower()
    contact_ext = os.path.splitext(contact_file_path)[1].lower()

    # Load the Premise file based on extension
    if premise_ext in ['.xls', '.xlsx']:
        premise_df = pd.read_excel(premise_file_path, engine='openpyxl')
    elif premise_ext == '.csv':
        premise_df = pd.read_csv(premise_file_path)
    else:
        raise ValueError("Unsupported file format for Premise file. Only .xls, .xlsx, and .csv are supported.")

    # Load the Contact file based on extension
    if contact_ext in ['.xls', '.xlsx']:
        contact_df = pd.read_excel(contact_file_path, engine='openpyxl')
    elif contact_ext == '.csv':
        contact_df = pd.read_csv(contact_file_path)
    else:
        raise ValueError("Unsupported file format for Contact file. Only .xls, .xlsx, and .csv are supported.")

    # Remove unwanted columns in the premise sheet
    df = premise_df.drop(['ID', 'ReferenceNumber'], axis=1)

    # Rename 'Name' to 'Premise Name' in the premise file
    df = df.rename(columns={'Name': 'Premise Name', 'Address Line 1': 'Address Line 1', 'Report Type': 'System Types'})

    # Ensure 'Premise Name' values are strings and remove unwanted characters
    def clean_premise_name(text):
        text = str(text)
        text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation, but keep spaces and alphanumeric characters
        text = re.sub(r"llc\b", "LLC", text, flags=re.IGNORECASE)  # Ensure LLC is always capitalized
        text = re.sub(r"bbq\b", "BBQ", text, flags=re.IGNORECASE)  # Ensure BBQ is always capitalized
        return text.title()  # Convert to title case

    # Apply the cleaning function to Premise Name
    df['Premise Name'] = df['Premise Name'].apply(clean_premise_name)

    # Format the 'Address Line 1' column to title case and clean it
    df['Address Line 1'] = df['Address Line 1'].astype(str).str.title().str.replace(r'[.,-]', '', regex=True)

    # Fix ordinal suffixes (e.g., "17Th" to "17th")
    def fix_ordinal_suffixes(text):
        # Replace common ordinal patterns like "1St", "2Nd", "3Rd", "4Th"
        text = re.sub(r'(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), text)
        return text

    # Fix building descriptors merged with road names (e.g., "17ThBldg" to "17th Bldg")
    def separate_building_descriptors(text):
        # Insert a space before building/descriptor keywords if they are merged with numbers
        return re.sub(r'(\d+\w*)(Bldg|Clubhouse|Suite|Unit|Apt|Flr|Floor)', r'\1 \2', text)

    # Apply these fixes to Premise Name and Address Line 1
    df['Premise Name'] = df['Premise Name'].apply(fix_ordinal_suffixes).apply(separate_building_descriptors)
    df['Address Line 1'] = df['Address Line 1'].apply(fix_ordinal_suffixes).apply(separate_building_descriptors)

    # Fix cardinal directions and street abbreviations
    def format_address(addr):
        addr = str(addr)  # Ensure the value is a string
        addr = re.sub(r'\bN\b', 'North', addr)
        addr = re.sub(r'\bS\b', 'South', addr)
        addr = re.sub(r'\bE\b', 'East', addr)
        addr = re.sub(r'\bW\b', 'West', addr)
        addr = re.sub(r'\bSt\b', 'Street', addr)
        addr = re.sub(r'\bRd\b', 'Road', addr)
        addr = re.sub(r'\bCt\b', 'Court', addr)
        addr = re.sub(r'\bDr\b', 'Drive', addr)
        addr = re.sub(r'\bLn\b', 'Lane', addr)
        addr = re.sub(r'\bBlvd\b', 'Boulevard', addr)
        return addr

    df['Address Line 1'] = df['Address Line 1'].apply(format_address)

    # Proper punctuation for 'City', 'State', and 'Zip'
    df['City'] = df['City'].str.title()
    df['St'] = df['St'].str.upper()
    df['Zip'] = df['Zip'].astype(str)

    # Rename system types as instructed
    system_type_mapping = {
        'Hood Suppression System': 'Commercial Hood Suppression',
        'Sprinkler System': 'Fire Sprinkler System',
        '5 Year Sprinkler': 'Sprinkler 5 Year',
        'Fire Alarm': 'Fire Alarm System',
        'Fire Pump': 'Fire Pump',
        'Paint/Spray Booth Suppression': 'Dry Chemical Suppression',
        'Standpipe': 'Standpipe System',
        'Commercial Kitchen Exhaust Cleaning': 'Commercial Hood Cleaning'
    }
    df['System Types'] = df['System Types'].replace(system_type_mapping)

    # Concatenate System Types for premises with multiple report types, ensuring they are separated by commas with no spaces
    df = df.groupby(['Premise Name', 'Address Line 1', 'City', 'St', 'Zip'], as_index=False).agg({
        'System Types': lambda x: ','.join(sorted(set(map(str, x))))  # No spaces after commas
    })

    # Match the premise name from the contact file to the profile sheet and add the correct email
    contact_df = contact_df[['Premises Name', 'Contact Email']]  # Updated to 'Premises Name'

    # Rename 'Premises Name' to 'Premise Name' to match with the premise DataFrame
    contact_df = contact_df.rename(columns={'Premises Name': 'Premise Name'})

    # Merge the contact information into the premise_df
    df = pd.merge(df, contact_df, on='Premise Name', how='left')

    return df