from django.contrib import admin
from rango.models import Category, Page


class PageAdmin(admin.ModelAdmin):
    list_display = ('title','category','url','views')

class CatAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name','views','likes','slug')
    

admin.site.register(Category,CatAdmin)
admin.site.register(Page,PageAdmin)

