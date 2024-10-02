import pandas as pd  # Add this import statement at the top of the file
import re
import os



def clean_and_format_brycer_data(premise_file_path, contact_file_path):
    # Determine file type for premise file and load it appropriately
    premise_file_ext = os.path.splitext(premise_file_path)[1].lower()

    if premise_file_ext == '.xlsx':
        premise_df = pd.read_excel(premise_file_path, engine='openpyxl')
    elif premise_file_ext == '.xls':
        premise_df = pd.read_excel(premise_file_path, engine='xlrd')
    elif premise_file_ext == '.csv':
        premise_df = pd.read_csv(premise_file_path)
    else:
        raise ValueError(f"Unsupported file format: {premise_file_ext} for premise file")

    # Determine file type for contact file and load it appropriately
    contact_file_ext = os.path.splitext(contact_file_path)[1].lower()

    if contact_file_ext == '.xlsx':
        contact_df = pd.read_excel(contact_file_path, engine='openpyxl')
    elif contact_file_ext == '.xls':
        contact_df = pd.read_excel(contact_file_path, engine='xlrd')
    elif contact_file_ext == '.csv':
        contact_df = pd.read_csv(contact_file_path)
    else:
        raise ValueError(f"Unsupported file format: {contact_file_ext} for contact file")

    # Remove unwanted columns in the premise sheet
    df = premise_df.drop(['ID', 'ReferenceNumber'], axis=1)

    # Rename columns in the premise file
    df = df.rename(columns={
        'Name': 'Premise Name',
        'Address Line 1': 'Address Line 1',
        'Report Type': 'System Types'
    })

    # Clean the 'Premise Name' values: remove unwanted characters and fix capitalization
    def clean_premise_name(text):
        text = str(text)
        text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation, but keep spaces and alphanumeric characters
        text = re.sub(r"llc\b", "LLC", text, flags=re.IGNORECASE)  # Ensure LLC is always capitalized
        text = re.sub(r"bbq\b", "BBQ", text, flags=re.IGNORECASE)  # Ensure BBQ is always capitalized
        return text.title()  # Convert to title case

    # Apply the cleaning function to 'Premise Name'
    df['Premise Name'] = df['Premise Name'].apply(clean_premise_name)

    # Clean 'Address Line 1': title case, remove unwanted characters, fix suffixes and building descriptors
    df['Address Line 1'] = df['Address Line 1'].astype(str).str.title().str.replace(r'[.,-]', '', regex=True)

    # Fix ordinal suffixes and building descriptors
    def fix_ordinal_suffixes(text):
        text = re.sub(r'(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), text)
        return text

    def separate_building_descriptors(text):
        return re.sub(r'(\d+\w*)(Bldg|Clubhouse|Suite|Unit|Apt|Flr|Floor)', r'\1 \2', text)

    # Apply these fixes to 'Premise Name' and 'Address Line 1'
    df['Premise Name'] = df['Premise Name'].apply(fix_ordinal_suffixes).apply(separate_building_descriptors)
    df['Address Line 1'] = df['Address Line 1'].apply(fix_ordinal_suffixes).apply(separate_building_descriptors)

    # Format address columns to fix street abbreviations and cardinal directions
    def format_address(addr):
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

    # Ensure proper capitalization for 'City', 'St', and 'Zip'
    df['City'] = df['City'].str.title()
    df['St'] = df['St'].str.upper()
    df['Zip'] = df['Zip'].astype(str)

    # Map system types to their correct names
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

    # Concatenate system types for premises with multiple report types, ensuring no spaces after commas
    df = df.groupby(['Premise Name', 'Address Line 1', 'City', 'St', 'Zip'], as_index=False).agg({
        'System Types': lambda x: ','.join(sorted(set(map(str, x))))
    })

    # Match the premise name from the contact file to the profile sheet and add the correct email
    contact_df = contact_df[['Premises Name', 'Contact Email']]  # Selecting relevant columns
    contact_df = contact_df.rename(columns={'Premises Name': 'Premise Name'})  # Renaming for merging

    # Merge the contact information into the premise DataFrame
    df = pd.merge(df, contact_df, on='Premise Name', how='left')

    return df


import pandas as pd
import re

def enhance_with_occ_types(df):
    # Load the Occupancy Type Master Key Words file
    keywords_file = '/Users/noahredford/liv-onboarding/Occupancy Type Master Key Words.xlsx'  # Replace with the actual path
    keywords_data = pd.read_excel(keywords_file)

    # Create a dictionary from the keywords file
    keywords_dict = {}

    # Assuming the first column has the occupancy types and the second column has the keywords
    for i, row in keywords_data.iterrows():
        occupancy_type = row[0]  # First column is the Occupancy Type
        keyword_list = str(row[1]).split(",")  # Second column contains the keywords, split by commas
        for keyword in keyword_list:
            keyword = keyword.strip().lower()  # Clean up spaces and convert to lowercase
            if keyword:
                keywords_dict[keyword] = occupancy_type

    # Function to assign occupancy types based on keywords in Premise Name
    def assign_occupancy_type(premise_name):
        premise_name = str(premise_name).lower()  # Convert to lowercase for matching
        for keyword, occupancy_type in keywords_dict.items():
            if re.search(rf'\b{keyword}\b', premise_name):  # Match whole words
                return occupancy_type
        return ''  # Return blank if no keyword is found

    # Apply the function to the 'Premise Name' column in the DataFrame
    df['Occupancy Type'] = df['Premise Name'].apply(assign_occupancy_type)

    return df