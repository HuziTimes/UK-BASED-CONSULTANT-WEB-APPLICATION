# middleware.py
from django.shortcuts import render

class Custom500Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 500:
            return render(request, '500.html', status=500)
        return response
