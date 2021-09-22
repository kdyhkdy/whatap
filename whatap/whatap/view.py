from django.http.response import HttpResponse ,JsonResponse
from rest_framework.response import Response
import time


def testAPI(request):

    return JsonResponse({"data":"test","mes": "res"},json_dumps_params={'ensure_ascii': True})


