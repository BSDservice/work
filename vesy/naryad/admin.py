from django.contrib import admin
from .models import *


class RecordAdmin(admin.ModelAdmin):
    list_filter = ('task',)


admin.site.register(Record, RecordAdmin)
admin.site.register(Task)
admin.site.register(Contractor)
admin.site.register(Consignee)
admin.site.register(Employer)
admin.site.register(Consignor)
admin.site.register(Carrier)
admin.site.register(Rubble)
admin.site.register(RubbleQuality)
admin.site.register(RubbleRoot)
admin.site.register(Place)
admin.site.register(AllocatedVolume)

# Register your models here.
