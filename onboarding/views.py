from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .brycer_slayer import clean_and_format_brycer_data  # Import the cleaning function
import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import os


# Create your views here.

def dashboard(request):
    return render(request, 'onboarding/dashboard.html')

def brycer_processor(request):
    if request.method == 'POST':
        # Handle file uploads
        premise_file = request.FILES.get('premise_file')
        contact_file = request.FILES.get('contact_file')

        # Save the uploaded files
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        premise_file_name = fs.save(premise_file.name, premise_file)
        contact_file_name = fs.save(contact_file.name, contact_file)

        # Get the file paths
        premise_file_path = fs.path(premise_file_name)
        contact_file_path = fs.path(contact_file_name)

        try:
            # Clean, format, and merge data from both files
            cleaned_df = clean_and_format_brycer_data(premise_file_path, contact_file_path)

            # Save the cleaned data to a new Excel file in the media directory
            cleaned_file_name = 'cleaned_brycer_data.xlsx'
            cleaned_file_path = os.path.join(settings.MEDIA_ROOT, cleaned_file_name)
            
            # Create an Excel writer object and save the DataFrame to an Excel file
            with pd.ExcelWriter(cleaned_file_path, engine='openpyxl') as writer:
                cleaned_df.to_excel(writer, index=False)

            # Provide feedback and a download link
            context = {
                'message': 'Files processed and cleaned successfully.',
                'download_url': os.path.join(settings.MEDIA_URL, cleaned_file_name)
            }
        except ValueError as e:
            # Handle file format errors
            context = {
                'error': str(e)
            }

        return render(request, 'onboarding/brycer_processor.html', context)

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