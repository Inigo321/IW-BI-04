/* =========================================================
   Streamers United - interacción en el cliente (sin librerías)
   1. Búsqueda de canales en vivo con AJAX (fetch + JSON)
   2. Botón "Seguir canal" por AJAX (POST con token CSRF), una vez por visitante
   3. Mensajes que se pueden cerrar y desaparecen solos
   Los textos visibles llegan traducidos desde las plantillas
   (atributos data-txt-*), así el JavaScript también es multilingüe.
   Si JavaScript está desactivado, todo sigue funcionando con
   formularios normales (mejora progresiva).
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    iniciarBuscador();
    iniciarBotonSeguir();
    iniciarMensajes();
});


/* 1. Búsqueda en vivo ------------------------------------ */
function iniciarBuscador() {
    var formulario = document.querySelector('.buscador');
    if (!formulario) {
        return;
    }
    var campo = formulario.querySelector('input[name="q"]');
    var resultados = document.getElementById('resultados');
    var resumen = document.getElementById('resumen-busqueda');
    var urlApi = formulario.dataset.api;
    var temporizador = null;
    var ultimaPeticion = 0;
    // Los textos vienen traducidos desde la plantilla (atributos data-txt-*)
    var txt = formulario.dataset;

    function buscar() {
        var texto = campo.value.trim();
        var numeroPeticion = ++ultimaPeticion;
        resultados.classList.add('cargando');

        fetch(urlApi + '?q=' + encodeURIComponent(texto), {
            headers: { 'Accept': 'application/json' }
        })
            .then(function (respuesta) {
                if (!respuesta.ok) {
                    throw new Error('Error ' + respuesta.status);
                }
                return respuesta.json();
            })
            .then(function (datos) {
                // Si el usuario ha seguido escribiendo, se ignora la respuesta vieja.
                if (numeroPeticion !== ultimaPeticion) {
                    return;
                }
                pintarResultados(resultados, datos.canales, texto, txt);
                resumen.textContent = formatear(
                    texto ? txt.txtResultados : txt.txtTodos,
                    { q: texto, total: datos.total }
                );
                // La URL refleja la búsqueda, para poder recargar o compartirla.
                var url = texto ? '?q=' + encodeURIComponent(texto) : window.location.pathname;
                window.history.replaceState(null, '', url);
            })
            .catch(function () {
                // Si falla el AJAX, se usa la búsqueda normal del servidor.
                formulario.submit();
            })
            .finally(function () {
                resultados.classList.remove('cargando');
            });
    }

    // Se espera a que el usuario deje de escribir 300 ms antes de preguntar al servidor.
    campo.addEventListener('input', function () {
        clearTimeout(temporizador);
        temporizador = setTimeout(buscar, 300);
    });

    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        clearTimeout(temporizador);
        buscar();
    });
}

function pintarResultados(contenedor, canales, texto, txt) {
    contenedor.textContent = '';

    if (canales.length === 0) {
        var vacio = crear('p', 'vacio', texto ? txt.txtSinCoincidencias : txt.txtVacio);
        contenedor.appendChild(vacio);
        return;
    }

    var lista = crear('ul', 'tarjetas');
    canales.forEach(function (canal, indice) {
        // Misma estructura que includes/tarjeta_canal.html
        var tarjeta = crear('li', 'tarjeta-canal aparecer');
        tarjeta.style.animationDelay = (indice * 40) + 'ms';

        var avatar = crear('span', 'avatar', canal.nombre.charAt(0).toUpperCase());
        avatar.setAttribute('aria-hidden', 'true');

        var titulo = crear('h3');
        titulo.appendChild(enlace(canal.url, canal.nombre));

        var categoria = crear('p');
        var etiqueta = enlace(canal.categoria_url, canal.categoria);
        etiqueta.className = 'etiqueta';
        categoria.appendChild(etiqueta);

        var seguidores = crear('p', 'seguidores');
        seguidores.appendChild(crear('strong', null, String(canal.seguidores)));
        seguidores.appendChild(document.createTextNode(' ' + txt.txtSeguidores));

        tarjeta.append(avatar, titulo, categoria, seguidores);
        lista.appendChild(tarjeta);
    });
    contenedor.appendChild(lista);
}


/* 2. Seguir canal ---------------------------------------- */
function iniciarBotonSeguir() {
    var formulario = document.querySelector('.form-seguir');
    if (!formulario) {
        return;
    }
    var boton = formulario.querySelector('button');
    var contador = document.getElementById('contador-seguidores');

    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        boton.disabled = true;

        fetch(formulario.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': formulario.querySelector('[name="csrfmiddlewaretoken"]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(function (respuesta) {
                if (!respuesta.ok) {
                    throw new Error('Error ' + respuesta.status);
                }
                return respuesta.json();
            })
            .then(function (datos) {
                contador.textContent = datos.seguidores;
                // Efecto: el número "late" y el botón confirma la acción.
                contador.classList.remove('latido');
                void contador.offsetWidth; // reinicia la animación
                contador.classList.add('latido');
                // Solo se puede seguir una vez: el botón se queda en "Siguiendo".
                boton.textContent = formulario.dataset.txtGracias;
                setTimeout(function () {
                    boton.textContent = formulario.dataset.txtSiguiendo;
                }, 1500);
            })
            .catch(function () {
                boton.textContent = formulario.dataset.txtError;
                boton.disabled = false;
            });
    });
}


/* 3. Mensajes -------------------------------------------- */
function iniciarMensajes() {
    var contenedor = document.querySelector('.mensajes');
    if (!contenedor) {
        return;
    }
    contenedor.querySelectorAll('.mensaje').forEach(function (mensaje) {
        var cerrar = crear('button', 'cerrar-mensaje', '×');
        cerrar.type = 'button';
        cerrar.setAttribute('aria-label', contenedor.dataset.txtCerrar);
        cerrar.addEventListener('click', function () {
            ocultar(mensaje);
        });
        mensaje.appendChild(cerrar);
        setTimeout(function () {
            ocultar(mensaje);
        }, 6000);
    });
}

function ocultar(elemento) {
    elemento.classList.add('desvanecer');
    elemento.addEventListener('animationend', function () {
        elemento.remove();
    });
}


/* Utilidades --------------------------------------------- */
// Sustituye {nombre} por su valor (los textos traducidos traen {q} y {total}).
function formatear(plantilla, valores) {
    return plantilla.replace(/\{(\w+)\}/g, function (todo, clave) {
        return String(valores[clave]);
    });
}

// Se usa textContent (nunca innerHTML) para que los datos no puedan inyectar HTML.
function crear(etiqueta, clase, texto) {
    var elemento = document.createElement(etiqueta);
    if (clase) {
        elemento.className = clase;
    }
    if (texto !== undefined) {
        elemento.textContent = texto;
    }
    return elemento;
}

function enlace(url, texto) {
    var a = document.createElement('a');
    a.href = url;
    a.textContent = texto;
    return a;
}
