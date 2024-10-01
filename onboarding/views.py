from django.shortcuts import render

# Create your views here.

def dashboard(request):
    return render(request, 'onboarding/dashboard.html')

def brycer_processor(request):
    if request.method == 'POST':
        # Handle file uploads
        premise_file = request.FILES.get('premise_file')
        contact_file = request.FILES.get('contact_file')
        
        # Save the files temporarily
        fs = FileSystemStorage()
        premise_file_name = fs.save(premise_file.name, premise_file)
        contact_file_name = fs.save(contact_file.name, contact_file)
        
        # Get user selections
        add_occupancy_types = request.POST.get('add_occupancy_types')
        add_system_types = request.POST.get('add_system_types')

        # Process the files and apply enhancements (this logic will be added)
        
        # Provide feedback to the user
        context = {
            'message': 'Files uploaded successfully. Processing started...',
            'add_occupancy_types': add_occupancy_types,
            'add_system_types': add_system_types,
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