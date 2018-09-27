from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
import os
import pickle
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def execute_code(request):
    if request.method == 'GET':
        data = """pass"""
        return HttpResponse(data)
    else:
        return HttpResponse(' ')
