from rest_framework import viewsets
from .models import PacienteEndemia
from .serializers import PacienteEndemiaSerializer

class PacienteEndemiaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PacienteEndemia.objects.all()
    serializer_class = PacienteEndemiaSerializer