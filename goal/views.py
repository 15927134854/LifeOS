from django.http import JsonResponse
from rest_framework.views import APIView

from LifeOS.common.utils import GetTokenUser
from LifeOS.conf.error_conf import STATUES_CODES


class Simulate(APIView):
    def get(self, request, *args, **kwargs):

        result = {}
        result['message'] = '操作成功！'
        result['errorCode'] = STATUES_CODES['OK']
        return JsonResponse(result)

    def post(self, request, *args, **kwargs):

        result = {}
        result['message'] = '操作成功！'
        result['errorCode'] = STATUES_CODES['OK']
        return JsonResponse(result)

    def put(self, request, *args, **kwargs):

        result = {}
        result['message'] = '操作成功！'
        result['errorCode'] = STATUES_CODES['OK']
        return JsonResponse(result)

    def delete(self, request, *args, **kwargs):

        result = {}
        result['message'] = '操作成功！'
        result['errorCode'] = STATUES_CODES['OK']
        return JsonResponse(result)