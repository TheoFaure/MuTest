from django.contrib import admin
from .models import *


admin.site.register(Utterance)
admin.site.register(Answer)
admin.site.register(Intent)
admin.site.register(Entity)
admin.site.register(Mutant)
admin.site.register(Strategy)
admin.site.register(Validation)