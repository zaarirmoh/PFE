# # admin.py
# from django.contrib import admin
# from unfold.admin import ModelAdmin
# from unfold.admin import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget

# from django_celery_beat.models import (
#     ClockedSchedule,
#     PeriodicTask,
# )
# from django_celery_beat.admin import ClockedScheduleAdmin as BaseClockedScheduleAdmin
# from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
# from django_celery_beat.admin import PeriodicTaskForm, TaskSelectWidget

# admin.site.unregister(PeriodicTask)
# admin.site.unregister(ClockedSchedule)


# class UnfoldTaskSelectWidget(UnfoldAdminSelectWidget, TaskSelectWidget):
#     pass


# class UnfoldPeriodicTaskForm(PeriodicTaskForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields["task"].widget = UnfoldAdminTextInputWidget()
#         self.fields["regtask"].widget = UnfoldTaskSelectWidget()


# @admin.register(PeriodicTask)
# class PeriodicTaskAdmin(BasePeriodicTaskAdmin, ModelAdmin):
#     form = UnfoldPeriodicTaskForm


# @admin.register(ClockedSchedule)
# class ClockedScheduleAdmin(BaseClockedScheduleAdmin, ModelAdmin):
#     pass
from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)

# Unregister all django-celery-beat models from admin
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)