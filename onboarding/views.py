from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .brycer_slayer import clean_and_format_brycer_data, enhance_with_occ_types# Import the cleaning function
import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import os
import logging


logger = logging.getLogger(__name__)  # Setting up a logger

# Create your views here.

def dashboard(request):
    return render(request, 'onboarding/dashboard.html')

def brycer_processor(request):
    logger.info("View called: brycer_processor")
    
    if request.method == 'POST':
        logger.info("POST request received")
        
        # Handle file uploads
        premise_file = request.FILES.get('premise_file')
        contact_file = request.FILES.get('contact_file')
        
        if not premise_file or not contact_file:
            logger.error("Missing files: Premise or Contact file")
            return render(request, 'onboarding/brycer_processor.html', {
                'error': 'Please upload both files.'
            })

        logger.info(f"Files received: premise_file={premise_file}, contact_file={contact_file}")
        
        # Save the uploaded files
        fs = FileSystemStorage()
        premise_file_name = fs.save(premise_file.name, premise_file)
        contact_file_name = fs.save(contact_file.name, contact_file)

        logger.info(f"Files saved: premise_file_name={premise_file_name}, contact_file_name={contact_file_name}")

        # Get the file paths
        premise_file_path = fs.path(premise_file_name)
        contact_file_path = fs.path(contact_file_name)

        try:
            # Clean and format the data
            logger.info("Cleaning and formatting data")
            cleaned_df = clean_and_format_brycer_data(premise_file_path, contact_file_path)

            # Check if the user wants to add occupancy types
            add_occupancy_types = request.POST.get('add_occupancy_types')
            logger.info(f"Occupancy Type Enhancement selected: {add_occupancy_types}")

            # Apply Occupancy Type Enhancement if selected
            if add_occupancy_types:
                logger.info("Applying occupancy type enhancement")
                cleaned_df = enhance_with_occ_types(cleaned_df)

            # Save the cleaned and enhanced data to a new Excel file
            cleaned_file_name = 'cleaned_brycer_data.xlsx'
            cleaned_file_path = fs.path(cleaned_file_name)

            logger.info("Saving cleaned data to Excel")
            with pd.ExcelWriter(cleaned_file_path, engine='openpyxl') as writer:
                cleaned_df.to_excel(writer, index=False)

            # Provide feedback and a download link
            logger.info("Process successful, returning download link")
            context = {
                'message': 'Files processed and cleaned successfully.',
                'download_url': fs.url(cleaned_file_name)
            }
        except Exception as e:
            # Handle errors and log them
            logger.error(f"Error during processing: {str(e)}")
            context = {
                'error': str(e)
            }

        return render(request, 'onboarding/brycer_processor.html', context)

    logger.info("Returning to form without POST")
    return render(request, 'onboarding/brycer_processor.html')
def data_scrubber(request):
    if request.method == 'POST':
        # Handle file upload and form data
        excel_file = request.FILES.get('excel_file')
        add_occupancy_types = request.POST.get('add_occupancy_types')
        add_system_types = request.POST.get('add_system_types')
        
        # Process the file and apply options (logic to be added)

    return render(request, 'onboarding/data_scrubber.html')

def kml_to_business(request):
    if request.method == 'POST':
        # Handle file upload and form data
        kml_file = request.FILES.get('kml_file')
        add_occupancy_types = request.POST.get('add_occupancy_types')
        add_system_types = request.POST.get('add_system_types')
        
        # Process the file and apply options (logic to be added)

    return render(request, 'onboarding/kml_to_business.html')