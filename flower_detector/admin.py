from django.contrib import admin
from .models import FlowerPrediction
from .models import FlowerInfo

@admin.register(FlowerPrediction)
class FlowerPredictionAdmin(admin.ModelAdmin):
    list_display = ('predicted_class', 'confidence', 'created_at')
    list_filter = ('predicted_class', 'created_at')
    search_fields = ('predicted_class',)



@admin.register(FlowerInfo)
class FlowerInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'family', 'origin')
    search_fields = ('name', 'scientific_name', 'common_names')
    list_filter = ('family', 'sunlight', 'water_needs')