from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import PacienteEndemia


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PacienteEndemiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacienteEndemia
        fields = "__all__"