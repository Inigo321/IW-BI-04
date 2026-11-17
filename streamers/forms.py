from django import forms
from django.utils.translation import gettext_lazy as _

from .admin import es_administrador_de_contenido
from .models import Canal, Creador


class CanalForm(forms.ModelForm):
    """Formulario público para crear y editar canales (basado en el modelo Canal)."""

    class Meta:
        model = Canal
        fields = ['nombre', 'descripcion', 'seguidores', 'categoria', 'plataformas']
        labels = {
            'nombre': _('Nombre del canal'),
            'descripcion': _('Descripción'),
            'seguidores': _('Seguidores'),
            'categoria': _('Categoría principal'),
            'plataformas': _('Plataformas en las que emite'),
        }
        help_texts = {
            'seguidores': _('Número aproximado de seguidores.'),
            'plataformas': _('Marca todas las que correspondan.'),
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'plataformas': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = _('Elige una categoría')
        # Igual que en el admin: solo los administradores de contenido cambian
        # los seguidores a mano. El resto los consigue con el botón "Seguir".
        if user is None or not es_administrador_de_contenido(user):
            del self.fields['seguidores']

    def clean_nombre(self):
        """No permite dos canales con el mismo nombre (sin distinguir mayúsculas)."""
        nombre = self.cleaned_data['nombre'].strip()
        repetidos = Canal.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(_('Ya existe un canal con ese nombre.'))
        return nombre


class CreadorForm(forms.ModelForm):
    """Formulario público para el creador de un canal (basado en el modelo Creador).

    El canal no se elige en el formulario: lo fija la vista a partir de la URL.
    """

    class Meta:
        model = Creador
        fields = ['nombre', 'biografia']
        labels = {
            'nombre': _('Nombre del creador'),
            'biografia': _('Biografía'),
        }
        widgets = {
            'biografia': forms.Textarea(attrs={'rows': 4}),
        }
