import pandas as pd
import re
import os
import pickle


def clean_and_format_data_scrubber(file_path):
    # Determine file type for the file and load it appropriately
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.xlsx':
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_ext == '.xls':
        df = pd.read_excel(file_path, engine='xlrd')
    elif file_ext == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext} for data scrubber file")

    # Remove unwanted columns in the data scrubber sheet, assuming the columns are the same as in Brycer
    df = df.drop(['ID', 'ReferenceNumber'], axis=1, errors='ignore')  # Ignore errors in case columns don't exist

    # Rename columns in the data file
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

    # Check for the 'City', 'St', and 'Zip' columns before processing
    if 'City' in df.columns:
        df['City'] = df['City'].str.title()

    if 'St' in df.columns:
        df['St'] = df['St'].str.upper()

    if 'Zip' in df.columns:
        df['Zip'] = df['Zip'].astype(str)

    return df


def enhance_with_occ_types(df):
    # Load the Occupancy Type Master Key Words file
    keywords_file = '/Users/noahredford/liv-onboarding/Occupancy Type Master Key Words.xlsx'  # Corrected path
    keywords_data = pd.read_excel(keywords_file)

    # Create a dictionary from the keywords file
    keywords_dict = {}

    # Assuming the first column has the occupancy types and the second column has the keywords
    for i, row in keywords_data.iterrows():
        occupancy_type = row.iloc[0]  # Access first column with .iloc
        keyword_list = str(row.iloc[1]).split(",")  # Access second column with .iloc and split by commas
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


def enhance_with_system_types(df):
    # Load the trained model and MultiLabelBinarizer
    model_path = '/Users/noahredford/liv-onboarding/azog_model.pkl'  # Correct the model path
    mlb_path = '/Users/noahredford/liv-onboarding/bolg_mlb.pkl'  # Correct the MultiLabelBinarizer path

    # Load the trained model and the MultiLabelBinarizer
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    
    with open(mlb_path, 'rb') as mlb_file:
        mlb = pickle.load(mlb_file)

    # Fill NaN values in 'Premise Name'
    df['Premise Name'] = df['Premise Name'].fillna('')

    # Make predictions using the trained model
    X_new = df['Premise Name']
    y_pred = model.predict(X_new)

    # Convert binary predictions to readable system types using the MultiLabelBinarizer
    predicted_system_types = mlb.inverse_transform(y_pred)

    # Hardcoded logic for specific premises
    hardcoded_types = ['Fire Alarm System', 'Sprinkler 5 Year', 'Fire Sprinkler System', 'Commercial Hood Cleaning', 'Commercial Hood Suppression']

    final_predictions = []
    for premise_name, predicted_types in zip(X_new, predicted_system_types):
        predicted_types = list(predicted_types)
        
        # Hardcoded overrides for hospitals, schools, and hotels
        if any(keyword in premise_name.lower() for keyword in ['hospital', 'elementary', 'high school', 'hotel']):
            final_predictions.append(hardcoded_types)
        # Auto repair places get Dry Chemical Suppression
        elif any(keyword in premise_name.lower() for keyword in ['auto repair', 'auto center']):
            predicted_types.append('Dry Chemical Suppression')
            final_predictions.append(predicted_types)
        else:
            final_predictions.append(predicted_types)

    # Add predictions to DataFrame as a string with no spaces after commas
    df['Predicted System Types'] = [','.join(types) for types in final_predictions]

    return df