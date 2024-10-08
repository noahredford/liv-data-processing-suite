from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .brycer_slayer import clean_and_format_brycer_data, enhance_with_occ_types# Import the cleaning function
import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import os
import logging
import pickle
from .data_scrubber_logic import clean_and_format_data_scrubber, enhance_with_occ_types, enhance_with_system_types





logger = logging.getLogger(__name__)  # Setting up a logger

# Create your views here.

def dashboard(request):
    return render(request, 'onboarding/dashboard.html')

def brycer_processor(request):
    if request.method == 'POST':
        # Handle file uploads
        premise_file = request.FILES.get('premise_file')
        contact_file = request.FILES.get('contact_file')

        if not premise_file or not contact_file:
            return render(request, 'onboarding/brycer_processor.html', {
                'error': 'Please upload both files.'
            })

        # Save the uploaded files
        fs = FileSystemStorage()
        premise_file_name = fs.save(premise_file.name, premise_file)
        contact_file_name = fs.save(contact_file.name, contact_file)

        # Get the file paths
        premise_file_path = fs.path(premise_file_name)
        contact_file_path = fs.path(contact_file_name)

        try:
            # Clean and format the data
            cleaned_df = clean_and_format_brycer_data(premise_file_path, contact_file_path)

            # Check if the user wants to add occupancy types
            add_occupancy_types = request.POST.get('add_occupancy_types')

            # Apply Occupancy Type Enhancement if selected
            if add_occupancy_types:
                cleaned_df = enhance_with_occ_types(cleaned_df)

            # Check if the user wants to add system types
            add_system_types = request.POST.get('add_system_types')

            # Apply System Type Enhancement if selected
            if add_system_types:
                logger.info("Applying system type enhancement")

                # Load the trained model and MultiLabelBinarizer
                downloads_folder = os.path.expanduser('~/Downloads/')
                with open(os.path.join(downloads_folder, 'azog_model.pkl'), 'rb') as model_file:
                    model = pickle.load(model_file)
                with open(os.path.join(downloads_folder, 'bolg_mlb.pkl'), 'rb') as mlb_file:
                    mlb = pickle.load(mlb_file)

                # Extract the Premise Name column for prediction
                X_new = cleaned_df['Premise Name'].fillna('')

                # Make predictions using the trained model
                y_pred = model.predict(X_new)

                # Convert the binary predictions back into readable system types
                predicted_system_types = mlb.inverse_transform(y_pred)

                # Hard-coded system types for specific premises
                hardcoded_types = ['Fire Alarm System', 'Sprinkler 5 Year', 'Fire Sprinkler System', 
                                   'Commercial Hood Cleaning', 'Commercial Hood Suppression']

                # Update predictions with hardcoded values for specific premise types
                final_predictions = []
                for premise_name, predicted_types in zip(X_new, predicted_system_types):
                    predicted_types = list(predicted_types)
                    
                    # Check if the premise name contains keywords for hospitals, schools, or hotels
                    if any(keyword in premise_name.lower() for keyword in ['hospital', 'elementary', 'high school', 'junior high', 'hotel']):
                        final_predictions.append(hardcoded_types)
                    elif any(keyword in premise_name.lower() for keyword in ['auto repair', 'auto detailing', 'car repair', 'auto center']):
                        predicted_types.append('Dry Chemical Suppression')
                        final_predictions.append(predicted_types)
                    else:
                        final_predictions.append(predicted_types)

                # Add the predictions to the cleaned DataFrame
                cleaned_df['Predicted System Types'] = [','.join(types) for types in final_predictions]

            # Save the cleaned and enhanced data to a new Excel file
            cleaned_file_name = 'cleaned_brycer_data.xlsx'
            cleaned_file_path = fs.path(cleaned_file_name)

            with pd.ExcelWriter(cleaned_file_path, engine='openpyxl') as writer:
                cleaned_df.to_excel(writer, index=False)

            # Provide feedback and a download link
            context = {
                'message': 'Files processed and cleaned successfully.',
                'download_url': fs.url(cleaned_file_name)
            }
        except Exception as e:
            # Handle any errors during processing
            logger.error(f"Error during processing: {str(e)}")
            context = {
                'error': str(e)
            }

        return render(request, 'onboarding/brycer_processor.html', context)

    return render(request, 'onboarding/brycer_processor.html')

def data_scrubber(request):
    if request.method == 'POST':
        # Handle file uploads
        uploaded_file = request.FILES.get('data_file')

        if not uploaded_file:
            return render(request, 'onboarding/data_scrubber.html', {
                'error': 'Please upload a file.'
            })

        # Save the uploaded file
        fs = FileSystemStorage()
        file_name = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(file_name)

        try:
            print("Start cleaning and formatting data")
            # Clean and format the data
            cleaned_df = clean_and_format_data_scrubber(file_path)
            print("Data cleaning and formatting completed")

            # Check if the user wants to add occupancy types
            add_occupancy_types = request.POST.get('add_occupancy_types')
            if add_occupancy_types:
                print("Enhancing with occupancy types")
                cleaned_df = enhance_with_occ_types(cleaned_df)

            # Check if the user wants to add system types
            add_system_types = request.POST.get('add_system_types')
            if add_system_types:
                print("Enhancing with system types")
                cleaned_df = enhance_with_system_types(cleaned_df)

            # Check if the user wants to assign reference numbers
            assign_reference_number = request.POST.get('assign_reference_number')
            if assign_reference_number:
                print("Assigning reference numbers")
                state_abbreviation = request.POST.get('state_abbreviation')
                ahj_abbreviation = request.POST.get('ahj_abbreviation')
                start_number = int(request.POST.get('start_number'))

                # Assign reference numbers
                cleaned_df = assign_reference_numbers(cleaned_df, state_abbreviation, ahj_abbreviation, start_number)

            # Rename the variable to avoid conflict with the function name
            assign_city_state_zip_check = request.POST.get('assign_city_state_zip')
            if assign_city_state_zip_check:
                print("Assigning city, state, and zip")
                city_value = request.POST.get('city')
                state_value = request.POST.get('state')
                zip_value = request.POST.get('zip')

                # Debug prints to check input values
                print(f"City: {city_value}, State: {state_value}, Zip: {zip_value}")

                # Assign city, state, and zip to each premise
                cleaned_df = assign_city_state_zip(cleaned_df, city_value, state_value, zip_value)

            print("Saving the cleaned data to a new Excel file")
            # Save the cleaned data to a new Excel file
            cleaned_file_name = 'cleaned_data_scrubber.xlsx'
            cleaned_file_path = fs.path(cleaned_file_name)
            cleaned_df.to_excel(cleaned_file_path, index=False, engine='openpyxl')

            print("File processing completed, returning the cleaned data")
            # Provide the download link on the same page
            context = {
                'message': 'File processed and cleaned successfully.',
                'download_url': fs.url(cleaned_file_name)
            }

        except Exception as e:
            # Handle any errors during processing
            print(f"Error during processing: {e}")
            context = {
                'error': str(e)
            }

        return render(request, 'onboarding/data_scrubber.html', context)

    # Initial GET request: Render the form
    return render(request, 'onboarding/data_scrubber.html')

def assign_city_state_zip(df, city_value, state_value, zip_value):
    # Ensure we're not overwriting any built-in names
    df['City'] = city_value
    df['St'] = state_value
    df['Zip'] = zip_value
    return df

def assign_reference_numbers(df, state_abbreviation, ahj_abbreviation, start_number):
    # Generate reference numbers
    reference_numbers = []
    for i in range(len(df)):
        reference_number = f"{state_abbreviation}-{ahj_abbreviation}-{str(start_number + i).zfill(4)}"
        reference_numbers.append(reference_number)
    
    # Assign the generated reference numbers to a new column in the dataframe
    df['Reference Number'] = reference_numbers
    
    return df



    # Initial GET request: Render the form
    return render(request, 'onboarding/data_scrubber.html')

def kml_to_business(request):
    if request.method == 'POST':
        # Handle file upload and form data
        kml_file = request.FILES.get('kml_file')
        add_occupancy_types = request.POST.get('add_occupancy_types')
        add_system_types = request.POST.get('add_system_types')
        
        # Process the file and apply options (logic to be added)

    return render(request, 'onboarding/kml_to_business.html')