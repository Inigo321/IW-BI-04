"""Pruebas de las mejoras de E4a.  Ejecutar con:  python manage.py test streamers"""
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .models import Canal, Categoria, Creador, Plataforma


class DatosMixin:
    fixtures = ['datos_ejemplo']


class RolesMixin(DatosMixin):
    """Crea los roles y sus usuarios de prueba (comando crear_roles)."""

    @classmethod
    def setUpTestData(cls):
        call_command('crear_roles', password='Clave-de-prueba-1', verbosity=0)

    def entrar(self, usuario):
        self.client.force_login(User.objects.get(username=usuario))


class PaginasPublicasTests(DatosMixin, TestCase):
    def test_todas_las_paginas_responden(self):
        canal = Canal.objects.first()
        urls = [
            reverse('portada'),
            reverse('canal_list'),
            reverse('canal_detail', args=[canal.pk]),
            reverse('categoria_list'),
            reverse('categoria_detail', args=[canal.categoria_id]),
            reverse('plataforma_list'),
            reverse('plataforma_detail', args=[Plataforma.objects.first().pk]),
            reverse('login'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_portada_un_destacado_por_categoria(self):
        respuesta = self.client.get(reverse('portada'))
        destacados = respuesta.context['destacados']
        self.assertEqual(len(destacados), Categoria.objects.filter(canales__isnull=False).distinct().count())
        for canal in destacados:
            mejor = canal.categoria.canales.order_by('-seguidores').first()
            self.assertEqual(canal.pk, mejor.pk)


class RendimientoTests(DatosMixin, TestCase):
    """Opción 7: el número de consultas no crece con el número de elementos."""

    def test_consultas_listados(self):
        with self.assertNumQueries(1):
            self.client.get(reverse('portada'))
        with self.assertNumQueries(1):
            self.client.get(reverse('canal_list'))
        with self.assertNumQueries(1):
            self.client.get(reverse('categoria_list'))
        with self.assertNumQueries(1):
            self.client.get(reverse('plataforma_list'))


class FormulariosTests(RolesMixin, TestCase):
    """Opción 3: formularios basados en el modelo (con un administrador de contenido)."""

    def setUp(self):
        self.entrar('admincontenido')

    def test_crear_editar_y_borrar_canal(self):
        categoria = Categoria.objects.first()
        plataforma = Plataforma.objects.first()
        datos = {'nombre': 'Canal de prueba', 'descripcion': 'Hola', 'seguidores': 10,
                 'categoria': categoria.pk, 'plataformas': [plataforma.pk]}
        respuesta = self.client.post(reverse('canal_create'), datos, follow=True)
        canal = Canal.objects.get(nombre='Canal de prueba')
        self.assertRedirects(respuesta, canal.get_absolute_url())
        self.assertContains(respuesta, 'se ha creado correctamente')
        self.assertEqual(list(canal.plataformas.all()), [plataforma])

        datos['seguidores'] = 99
        self.client.post(reverse('canal_update', args=[canal.pk]), datos)
        canal.refresh_from_db()
        self.assertEqual(canal.seguidores, 99)

        self.client.post(reverse('canal_delete', args=[canal.pk]))
        self.assertFalse(Canal.objects.filter(pk=canal.pk).exists())

    def test_errores_de_validacion(self):
        existente = Canal.objects.first()
        datos = {'nombre': existente.nombre.upper(), 'seguidores': -5}
        respuesta = self.client.post(reverse('canal_create'), datos)
        self.assertEqual(respuesta.status_code, 200)
        errores = respuesta.context['form'].errors
        self.assertIn('nombre', errores)       # nombre repetido
        self.assertIn('seguidores', errores)   # negativo
        self.assertIn('categoria', errores)    # obligatorio

    def test_crear_creador_para_canal_sin_creador(self):
        canal = Canal.objects.create(nombre='Sin creador', categoria=Categoria.objects.first())
        self.client.post(reverse('creador_create', args=[canal.pk]), {'nombre': 'Ana', 'biografia': ''})
        self.assertEqual(Creador.objects.get(canal=canal).nombre, 'Ana')
        # Si ya tiene creador, "nuevo" redirige a editar (relación 1:1)
        respuesta = self.client.get(reverse('creador_create', args=[canal.pk]))
        self.assertRedirects(respuesta, reverse('creador_update', args=[canal.creador.pk]))


class PermisosFormulariosTests(RolesMixin, TestCase):
    """Opción 7 (seguridad): los formularios públicos exigen sesión y permisos."""

    def setUp(self):
        # Las URL se generan en español aunque otra prueba haya dejado el inglés activo.
        translation.activate('es')
        self.addCleanup(translation.deactivate)

    def urls_protegidas(self):
        canal = Canal.objects.first()
        return [
            reverse('canal_create'),
            reverse('canal_update', args=[canal.pk]),
            reverse('canal_delete', args=[canal.pk]),
            reverse('creador_create', args=[canal.pk]),
            reverse('creador_update', args=[canal.creador.pk]),
        ]

    def test_sin_sesion_pide_iniciar_sesion(self):
        for url in self.urls_protegidas():
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertRedirects(respuesta, f"{reverse('login')}?next={url}", fetch_redirect_response=False)
        total = Canal.objects.count()
        self.client.post(reverse('canal_delete', args=[Canal.objects.first().pk]))
        self.assertEqual(Canal.objects.count(), total)

    def test_revisor_no_puede_modificar(self):
        self.entrar('revisor')
        for url in self.urls_protegidas():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        detalle = self.client.get(Canal.objects.first().get_absolute_url())
        self.assertNotContains(detalle, 'boton-peligro')

    def test_editor_crea_pero_no_borra_ni_toca_seguidores(self):
        self.entrar('editor')
        canal = Canal.objects.first()
        self.assertEqual(self.client.get(reverse('canal_delete', args=[canal.pk])).status_code, 403)
        formulario = self.client.get(reverse('canal_create'))
        self.assertNotContains(formulario, 'name="seguidores"')
        datos = {'nombre': 'Del editor', 'seguidores': 999999, 'categoria': Categoria.objects.first().pk}
        self.client.post(reverse('canal_create'), datos)
        self.assertEqual(Canal.objects.get(nombre='Del editor').seguidores, 0)

    def test_iniciar_y_cerrar_sesion(self):
        url = reverse('canal_create')
        respuesta = self.client.post(reverse('login'),
                                     {'username': 'editor', 'password': 'Clave-de-prueba-1', 'next': url})
        self.assertRedirects(respuesta, url)
        self.assertContains(self.client.get(reverse('portada')), 'Has iniciado sesión como editor.')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)  # solo por POST
        self.assertRedirects(self.client.post(reverse('logout')), reverse('portada'))
        self.assertEqual(self.client.get(url).status_code, 302)


class AjaxTests(DatosMixin, TestCase):
    """Opción 1: respuestas JSON para el JavaScript."""

    def test_busqueda_json(self):
        canal = Canal.objects.first()
        trozo = canal.nombre[1:4]
        respuesta = self.client.get(reverse('api_canales'), {'q': trozo})
        self.assertEqual(respuesta['Content-Type'], 'application/json')
        nombres = [c['nombre'] for c in respuesta.json()['canales']]
        self.assertIn(canal.nombre, nombres)
        self.assertTrue(all(trozo.lower() in n.lower() for n in nombres))

    def test_busqueda_sin_javascript(self):
        respuesta = self.client.get(reverse('canal_list'), {'q': 'zzzz-no-existe'})
        self.assertContains(respuesta, 'Ningún canal coincide')

    def test_seguir_por_ajax_y_sin_ajax(self):
        canal, otro = Canal.objects.all()[:2]
        url = reverse('canal_seguir', args=[canal.pk])
        respuesta = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(respuesta.json(), {'seguidores': canal.seguidores + 1, 'siguiendo': True})
        respuesta = self.client.post(reverse('canal_seguir', args=[otro.pk]))
        self.assertRedirects(respuesta, otro.get_absolute_url())
        otro_antes = otro.seguidores
        otro.refresh_from_db()
        self.assertEqual(otro.seguidores, otro_antes + 1)

    def test_seguir_solo_una_vez_por_visitante(self):
        canal = Canal.objects.first()
        antes = canal.seguidores
        url = reverse('canal_seguir', args=[canal.pk])
        for _ in range(3):
            self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        canal.refresh_from_db()
        self.assertEqual(canal.seguidores, antes + 1)
        detalle = self.client.get(canal.get_absolute_url())
        self.assertTrue(detalle.context['siguiendo'])
        self.assertContains(detalle, 'disabled')

    def test_seguir_solo_por_post(self):
        canal = Canal.objects.first()
        self.assertEqual(self.client.get(reverse('canal_seguir', args=[canal.pk])).status_code, 405)

    def test_seguir_exige_csrf(self):
        from django.test import Client
        cliente = Client(enforce_csrf_checks=True)
        canal = Canal.objects.first()
        respuesta = cliente.post(reverse('canal_seguir', args=[canal.pk]))
        self.assertEqual(respuesta.status_code, 403)


class AdminRolesTests(RolesMixin, TestCase):
    """Opción 4: cada rol ve y puede hacer cosas distintas en el panel."""

    def test_panel_personalizado(self):
        self.entrar('admincontenido')
        respuesta = self.client.get(reverse('admin:index'))
        self.assertContains(respuesta, 'Streamers United · Administración')
        self.assertContains(respuesta, 'css/admin.css')

    def test_administrador_de_contenido(self):
        self.entrar('admincontenido')
        canal = Canal.objects.first()
        self.assertEqual(self.client.get(reverse('admin:streamers_canal_delete', args=[canal.pk])).status_code, 200)
        respuesta = self.client.get(reverse('admin:streamers_canal_change', args=[canal.pk]))
        self.assertContains(respuesta, 'name="seguidores"')  # editable
        listado = self.client.get(reverse('admin:streamers_canal_changelist'))
        self.assertContains(listado, 'poner_seguidores_a_cero')

    def test_editor(self):
        self.entrar('editor')
        canal = Canal.objects.first()
        self.assertEqual(self.client.get(reverse('admin:streamers_canal_add')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:streamers_canal_delete', args=[canal.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:streamers_categoria_add')).status_code, 403)
        respuesta = self.client.get(reverse('admin:streamers_canal_change', args=[canal.pk]))
        self.assertNotContains(respuesta, 'name="seguidores"')  # solo lectura
        listado = self.client.get(reverse('admin:streamers_canal_changelist'))
        self.assertNotContains(listado, 'poner_seguidores_a_cero')

    def test_revisor(self):
        self.entrar('revisor')
        canal = Canal.objects.first()
        self.assertEqual(self.client.get(reverse('admin:streamers_canal_changelist')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:streamers_canal_add')).status_code, 403)
        respuesta = self.client.post(reverse('admin:streamers_canal_change', args=[canal.pk]), {'nombre': 'X'})
        self.assertEqual(respuesta.status_code, 403)


class IdiomasTests(RolesMixin, TestCase):
    """Opción 6: la web funciona en español y en inglés."""

    def test_raiz_redirige_al_idioma(self):
        respuesta = self.client.get('/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertRedirects(respuesta, '/en/')
        respuesta = self.client.get('/', HTTP_ACCEPT_LANGUAGE='fr')
        self.assertRedirects(respuesta, '/es/')  # idioma por defecto

    def test_textos_traducidos(self):
        espanol = self.client.get('/es/canales/')
        ingles = self.client.get('/en/canales/')
        self.assertContains(espanol, '<html lang="es">')
        self.assertContains(espanol, 'Buscar canal')
        self.assertContains(ingles, '<html lang="en">')
        self.assertContains(ingles, 'Search channel')
        self.assertContains(ingles, 'All channels (10)')
        self.assertNotContains(ingles, 'Buscar canal')

    def test_plurales_y_mensajes(self):
        self.assertContains(self.client.get('/en/categorias/'), '2 channels')
        self.entrar('admincontenido')
        categoria = Categoria.objects.first()
        datos = {'nombre': 'New one', 'seguidores': 1, 'categoria': categoria.pk}
        respuesta = self.client.post('/en/canales/nuevo/', datos, follow=True)
        self.assertContains(respuesta, 'The channel “New one” has been created.')
        respuesta = self.client.post('/en/canales/nuevo/', {'nombre': 'New one'})
        self.assertContains(respuesta, 'A channel with that name already exists.')

    def test_cambiar_idioma_mantiene_la_pagina(self):
        canal = Canal.objects.first()
        respuesta = self.client.post(reverse('set_language'),
                                     {'language': 'en', 'next': f'/es/canales/{canal.pk}/'})
        self.assertRedirects(respuesta, f'/en/canales/{canal.pk}/')

    def test_inicio_de_sesion_traducido(self):
        self.assertContains(self.client.get('/en/'), 'Log in to add or edit channels.')
        self.assertContains(self.client.get('/en/cuentas/entrar/'), 'You need an account with permissions')
