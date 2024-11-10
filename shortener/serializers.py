from rest_framework import serializers
from .models import URL  # Ensure this import is correct

print("Loading serializers.py")


class URLSerializer(serializers.ModelSerializer):
    class Meta:
        model = URL
        fields = ['original_url']  # Make sure these fields exist in your URL model
