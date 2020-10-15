from django.contrib import admin

# Register your models here.
from map.models import Customer, Location, Tag, Form

admin.site.register(Customer)
admin.site.register(Location)
admin.site.register(Tag)
admin.site.register(Form)
