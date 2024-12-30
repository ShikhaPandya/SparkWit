from django.shortcuts import render, redirect
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from django.http import HttpResponseRedirect
from .models import Event, Venue
from django.contrib.auth.models import User
from .forms import VenueForm, EventForm, EventFormAdmin
from django.http import HttpResponse
import csv
from django.contrib import messages
#import PDF Stuff
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
#import Pagination stuff
from django.core.paginator import Paginator

def admin_approval(request):
    event_count = Event.objects.all().count()
    venue_count = Venue.objects.all().count()
    user_count = User.objects.all().count()
    event_list = Event.objects.all().order_by('-event_date')
    if request.user.is_superuser:
        if request.method=="POST":
            id_list = request.POST.getlist('boxes')
            event_list.update(approved=False)
            for x in id_list:
                Event.objects.filter(pk=int(x)).update(approved=True)
            messages.success(request, ("Event List Approval Has been Updated"))
            return redirect('list-events')
        else: 
            return render(request, 'blog/admin_approval.html', {"event_list":event_list, "event_count":event_count, "venue_count":venue_count, "user_count":user_count,})
    else:
        messages.success(request, ("You aren't authorized to view this page!"))
        return redirect('home')

def my_events(request):
	if request.user.is_authenticated:
		me = request.user.id
		events = Event.objects.filter(attendees=me)
		return render(request, 'blog/my_events.html', {"events":events})
	else:
		messages.success(request, ("You Aren't Authorized To View This Page"))
		return redirect('home')

# Generate PDF File Venue List 
def venue_pdf(request):
    #create a Byte Stream Buffer
    buf=io.BytesIO()
    #create a Canvas
    c=canvas.Canvas(buf, pagesize=letter, bottomup=0)
    #create a Text Object
    textob=c.beginText()
    textob.setTextOrigin(inch, inch)
    textob.setFont("Helvetica", 14)
    # Designate The Model
    venues=Venue.objects.all()
    # Create Blank List
    lines=[]
    for venue in venues:
        lines.append(venue.name)
        lines.append(venue.address)
        lines.append(venue.zip_code)
        lines.append(venue.phone)
        lines.append(venue.web)
        lines.append(venue.email_address)
        lines.append("=======================================")
    # Loop
    for line in lines:
        textob.textLine(line)
    # Finish Up
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    # Return Something
    return FileResponse(buf, as_attachment=True, filename='Venue.pdf')

# Generate CSV File Venue List 
def venue_csv(request):
    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=venues.csv'
    # Create a CSV Writer
    writer=csv.writer(response)
    # Designate The Model
    venues=Venue.objects.all()
    # Add Cloumn Headings to the csv file
    writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web Address', 'Email'])
    # Loop Through and Output
    for venue in venues:
        writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])
    return response

# Generate Text File Venue List 
def venue_text(request):
    response=HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=venues.txt'
    # Designate The Model
    venues=Venue.objects.all()
    # Create Blank List
    lines=[]
    # Loop Through and Output
    for venue in venues:
        lines.append(f'{venue.name}\n{venue.address}\n{venue.zip_code}\n{venue.phone}\n{venue.web}\n{venue.email_address}\n\n\n')
    # Write to TextFile
    response.writelines(lines)
    return response

# Delete a Venue
def delete_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue.delete()
    return redirect('list-venues')

# Delete a Event
def delete_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user == event.manager:
        event.delete()
        messages.success(request, "Event Deleted!!!")
        return redirect('list-events')
    else:
        messages.success(request, "You aren't Authorized to Delete This Event!")
        return redirect('list-events')

def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user.is_superuser:
        form=EventFormAdmin(request.POST or None, instance=event)
    else:
        form=EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        return redirect('list-events')
    
    return render(request, 'blog/update_event.html', {'event': event, 'form':form})

def add_event(request):
    submitted=False
    if request.method == "POST":
        if request.user.is_superuser:
            form=EventFormAdmin(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/add_event?submitted=True')
        else:
            form=EventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.manager = request.user #logged in user
                event.save()
                #form.save()
                return HttpResponseRedirect('/add_event?submitted=True')
    else:
        #just going to the page, not submitting
        if request.user.is_superuser:
            form=EventFormAdmin
        else:
            form=EventForm
        if 'submitted' in request.GET:
            submitted=True

    return render(request, 'blog/add_event.html', {'form':form, 'submitted': submitted})

def update_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    form=VenueForm(request.POST or None, request.FILES or None, instance=venue)
    if form.is_valid():
        form.save()
        return redirect('list-venues')
    
    return render(request, 'blog/update_venue.html', {'venue': venue, 'form':form})

def search_venues(request):
    if request.method == "POST":
        searched = request.POST ['searched']    
        venues=Venue.objects.filter(name__contains=searched)
        return render(request, 'blog/search_venues.html', {'searched':searched, 'venues':venues})
    else:
        return render(request, 'blog/search_venues.html', {})
    
def search_events(request):
    if request.method == "POST":
        searched = request.POST ['searched']    
        events=Event.objects.filter(description__contains=searched)
        return render(request, 'blog/search_events.html', {'searched':searched, 'events':events})
    else:
        return render(request, 'blog/search_events.html', {})

def show_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue_owner = User.objects.get(pk=venue.owner)
    return render(request, 'blog/show_venue.html', {'venue': venue, 'venue_owner': venue_owner })

def list_venues(request):
    #venue_list=Venue.objects.all().order_by('?')
    venue_list=Venue.objects.all()
    # Set up Pagination
    p = Paginator(Venue.objects.all(), 9)
    page = request.GET.get('page')
    venues = p.get_page(page)
    nums = "a" * venues.paginator.num_pages
    return render(request, 'blog/venue.html', {'venue_list':venue_list, 'venues':venues, 'nums':nums})

def add_venue(request):
    submitted=False
    if request.method == "POST":
        form=VenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user.id #logged in user
            venue.save()
            #form.save()
            return HttpResponseRedirect('/add_venue?submitted=True')
    else:
        form=VenueForm
        if 'submitted' in request.GET:
            submitted=True

    return render(request, 'blog/add_venue.html', {'form':form, 'submitted': submitted})


def all_events(request):
    event_list=Event.objects.all().order_by('name')
    return render(request, 'blog/event_list.html', {'event_list':event_list})

def home(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    name="Shikha"
    month=month.capitalize()

    #convert month from name to number
    month_number=list(calendar.month_name).index(month)
    month_number=int (month_number)

    #create a calander
    cal=HTMLCalendar().formatmonth(year, month_number)

    #get current year
    now = datetime.now()
    current_year=now.year

    #query the events Model for Dates
    event_list = Event.objects.filter(event_date__year = year, event_date__month = month_number)

    #get current time
    time=now.strftime('%I:%M %p')

    return render(request, 'blog/home.html', { "name": name, "year": year, "month":month,
     "month_number": month_number, "cal":cal, "current_year":current_year, "time":time, 
     "event_list":event_list, })


