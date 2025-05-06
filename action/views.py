from django.http import JsonResponse
from rest_framework.views import APIView

from LifeOS.common.utils import GetTokenUser
from LifeOS.conf.error_conf import STATUES_CODES


# Create your views here.

class Vialization(APIView):
    def get(self, request, *args, **kwargs):

        result = {}
        token_user = GetTokenUser(request)
        if token_user:
            pass
            result['message'] = '操作成功！'
            result['errorCode'] = STATUES_CODES['OK']

        return JsonResponse(result)

    def post(self, request, *args, **kwargs):

        result = {}
        token_user = GetTokenUser(request)
        if token_user:
            pass
            result['message'] = '操作成功！'
            result['errorCode'] = STATUES_CODES['OK']

        return JsonResponse(result)

    def put(self, request, *args, **kwargs):

        result = {}
        token_user = GetTokenUser(request)
        if token_user:
            pass
            result['message'] = '操作成功！'
            result['errorCode'] = STATUES_CODES['OK']

        return JsonResponse(result)

    def delete(self, request, *args, **kwargs):

        result = {}
        token_user = GetTokenUser(request)
        if token_user:
            pass
            result['message'] = '操作成功！'
            result['errorCode'] = STATUES_CODES['OK']

        return JsonResponse(result)