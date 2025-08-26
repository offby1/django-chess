from django import forms


class ImportPGNForm(forms.Form):
    imported_pgn = forms.FileField()
