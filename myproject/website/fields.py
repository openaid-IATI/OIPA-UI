from django.forms.fields import MultipleChoiceField, ChoiceField
from django.core.exceptions import ValidationError

class DynamicMultipleChoiceField(MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])


class DynamicChoiceField(ChoiceField):
    def validate(self, value):
        pass