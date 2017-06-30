from django import forms
from .models import Intent, Strategy, Validation, Chatbot


class UploadUtterancesForm(forms.Form):
    intent = forms.ModelChoiceField(queryset=Intent.objects.all())
    utterances = forms.CharField(widget=forms.Textarea)


class CreateMutantsForm(forms.Form):
    strategy = forms.ModelChoiceField(queryset=Strategy.objects.all())
    validation = forms.ModelChoiceField(queryset=Validation.objects.all())
    chatbot = forms.ModelChoiceField(queryset=Chatbot.objects.all())
    nb_per_mutant = forms.IntegerField(max_value=100, min_value=1)
    compute_ans = forms.BooleanField(required=False)