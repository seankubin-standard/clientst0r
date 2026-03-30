from django.contrib import admin
from .models import ScheduledTask, TaskAssignment, TaskComment

admin.site.register(ScheduledTask)
admin.site.register(TaskAssignment)
admin.site.register(TaskComment)
