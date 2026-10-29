from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Plataforma(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    url = models.URLField(blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Canal(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    seguidores = models.PositiveIntegerField(default=0)
    # 1:N -> cada canal tiene una categoría principal
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='canales')
    # N:M -> un canal puede emitir en varias plataformas
    plataformas = models.ManyToManyField(Plataforma, related_name='canales', blank=True)

    class Meta:
        ordering = ['-seguidores', 'nombre']
        verbose_name_plural = 'canales'

    def __str__(self):
        return self.nombre


class Creador(models.Model):
    nombre = models.CharField(max_length=100)
    biografia = models.TextField(blank=True)
    canal = models.OneToOneField(Canal, on_delete=models.CASCADE, related_name='creador')

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'creadores'

    def __str__(self):
        return self.nombre
