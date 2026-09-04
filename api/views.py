from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count
from .models import PacienteEndemia
from .serializers import PacienteEndemiaSerializer

class PacienteEndemiaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PacienteEndemia.objects.all()
    serializer_class = PacienteEndemiaSerializer

@api_view(['GET'])
def casos_por_bairro(request): # funcao para agrupar o campo bairro e contar os numeros de registros
    dados = PacienteEndemia.objects.values('bairro').annotate(casos=Count('id'))
    # dados formatados
    dados_formatados = {item['bairro']: item['casos'] for item in dados if item['bairro']}

    return Response(dados_formatados)