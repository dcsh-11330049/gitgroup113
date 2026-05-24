from django.shortcuts import render
from django.http import JsonResponse
from .models import User, Club, TransferApplication, ApprovalLog

# Create your views here.

def index(request):
    return render(request, 'index/index.html', {'clubs': Club.objects.all()})

def clubs_api(request):
    clubs = Club.objects.select_related('president').all()
    clubs_data = []
    for club in clubs:
        clubs_data.append({
            'id': club.id,
            'name': club.club_name,
            'president_name': club.president.name if club.president else '',
            'description': club.description,
            'description_url': club.description_url,
            'current_members': club.current_members,
            'max_capacity': club.max_capacity,
            'is_full': club.current_members >= club.max_capacity,
        })
    return JsonResponse(clubs_data, safe=False)