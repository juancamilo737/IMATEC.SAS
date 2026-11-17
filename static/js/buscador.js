/* Buscador con sugerencias para listas largas (clientes, sobre todo).
 *
 * Por qué existe: con 174 clientes, una lista desplegable obliga a saltar por
 * la primera letra y a bajar a ciegas. Aquí se escribe y van saliendo los que
 * coinciden, como en Excel.
 *
 * Es una MEJORA del <select> de siempre, no un reemplazo: el <select> sigue
 * en la página y es el que se envía. Si este archivo no carga, la pantalla
 * funciona como antes.
 *
 * Uso:  <select name="cliente_id" data-buscable required> … </select>
 */
(function () {
  "use strict";

  // «BOGOTÁ» y «bogota» deben encontrarse mutuamente.
  function normalizar(t) {
    return (t || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function escaparHTML(t) {
    return t.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // Resalta cada palabra buscada dentro del texto original, respetando
  // tildes y mayúsculas de la pantalla.
  function resaltar(texto, palabras) {
    const plano = normalizar(texto);
    const marcas = [];
    palabras.forEach(function (p) {
      let desde = 0, i;
      while ((i = plano.indexOf(p, desde)) !== -1) {
        marcas.push([i, i + p.length]);
        desde = i + p.length;
      }
    });
    if (!marcas.length) return escaparHTML(texto);
    marcas.sort(function (a, b) { return a[0] - b[0]; });
    const unidas = [];
    marcas.forEach(function (m) {
      const u = unidas[unidas.length - 1];
      if (u && m[0] <= u[1]) u[1] = Math.max(u[1], m[1]);
      else unidas.push(m.slice());
    });
    // normalizar() sólo quita tildes y colapsa espacios, así que la longitud
    // suele conservarse. Si no, se devuelve sin resaltar antes que cortar el
    // nombre por donde no es.
    if (plano.length !== texto.length) return escaparHTML(texto);
    let salida = "", fin = 0;
    unidas.forEach(function (m) {
      salida += escaparHTML(texto.slice(fin, m[0]));
      salida += "<mark>" + escaparHTML(texto.slice(m[0], m[1])) + "</mark>";
      fin = m[1];
    });
    return salida + escaparHTML(texto.slice(fin));
  }

  const TOPE = 60;           // cuántas sugerencias se pintan como máximo
  let contador = 0;

  function montar(select) {
    if (select.dataset.buscableListo) return;
    select.dataset.buscableListo = "1";

    const id = "bus" + ++contador;
    const opciones = Array.prototype.slice
      .call(select.options)
      .filter(function (o) { return o.value !== ""; })
      .map(function (o) {
        const texto = o.textContent.replace(/\s+/g, " ").trim();
        // data-busca lleva lo que se puede buscar pero no vale la pena pintar
        // en cada renglón; hoy, la ciudad.
        const extra = o.dataset.busca || "";
        return {
          valor: o.value,
          texto: texto,
          // lo que se busca: incluye la ciudad, que no se pinta
          plano: normalizar(texto + " " + extra),
        };
      });

    const caja = document.createElement("div");
    caja.className = "buscador";

    const entrada = document.createElement("input");
    entrada.type = "text";
    entrada.className = "buscador-entrada";
    entrada.setAttribute("role", "combobox");
    entrada.setAttribute("aria-expanded", "false");
    entrada.setAttribute("aria-autocomplete", "list");
    entrada.setAttribute("aria-controls", id + "-lista");
    entrada.autocomplete = "off";
    entrada.placeholder = select.dataset.placeholder || "Escriba para buscar…";
    const etiqueta = select.closest(".campo") &&
                     select.closest(".campo").querySelector("label");
    if (etiqueta) {
      if (!etiqueta.id) etiqueta.id = id + "-et";
      entrada.setAttribute("aria-labelledby", etiqueta.id);
    }

    const lista = document.createElement("ul");
    lista.className = "buscador-lista";
    lista.id = id + "-lista";
    lista.setAttribute("role", "listbox");
    lista.hidden = true;

    const estado = document.createElement("div");
    estado.className = "buscador-estado";
    estado.setAttribute("aria-live", "polite");

    select.parentNode.insertBefore(caja, select);
    caja.appendChild(entrada);
    caja.appendChild(lista);
    caja.appendChild(estado);
    caja.appendChild(select);
    select.classList.add("buscador-oculto");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");

    let visibles = [];
    let activo = -1;
    let acabaDeElegir = false;   // evita reabrir la lista tras escoger

    function elegido() {
      return opciones.find(function (o) { return o.valor === select.value; });
    }

    function pintarElegido() {
      const e = elegido();
      entrada.value = e ? e.texto : "";
      caja.classList.toggle("tiene-eleccion", !!e);
      estado.textContent = "";
    }

    function cerrar() {
      lista.hidden = true;
      entrada.setAttribute("aria-expanded", "false");
      entrada.removeAttribute("aria-activedescendant");
      activo = -1;
    }

    function filtrar(texto) {
      const palabras = normalizar(texto).split(" ").filter(Boolean);
      if (!palabras.length) return opciones.slice();
      // Todas las palabras deben aparecer, en cualquier orden y en cualquier
      // parte: así «agua tecno» encuentra «ALMACENAMIENTO DE AGUA … TECNOLOGIA».
      return opciones.filter(function (o) {
        return palabras.every(function (p) { return o.plano.indexOf(p) !== -1; });
      });
    }

    function abrir(texto) {
      const todos = filtrar(texto);
      visibles = todos.slice(0, TOPE);
      lista.innerHTML = "";
      const palabras = normalizar(texto).split(" ").filter(Boolean);

      if (!todos.length) {
        const vacio = document.createElement("li");
        vacio.className = "buscador-vacio";
        vacio.textContent = "Ningún cliente coincide con «" + texto.trim() + "».";
        lista.appendChild(vacio);
        estado.textContent = "Sin coincidencias.";
      } else {
        visibles.forEach(function (o, i) {
          const li = document.createElement("li");
          li.id = id + "-op" + i;
          li.setAttribute("role", "option");
          li.setAttribute("aria-selected", "false");
          li.className = "buscador-opcion";
          li.innerHTML = resaltar(o.texto, palabras);
          li.addEventListener("mousedown", function (ev) {
            ev.preventDefault();            // no pierde el foco antes de elegir
            escoger(i);
          });
          lista.appendChild(li);
        });
        if (todos.length > visibles.length) {
          const mas = document.createElement("li");
          mas.className = "buscador-mas";
          mas.textContent = "y " + (todos.length - visibles.length) +
                            " más — siga escribiendo para afinar";
          lista.appendChild(mas);
        }
        estado.textContent = todos.length === 1
          ? "1 cliente encontrado."
          : todos.length + " clientes encontrados.";
      }
      lista.hidden = false;
      entrada.setAttribute("aria-expanded", "true");
      marcar(-1);
    }

    function marcar(i) {
      const previo = lista.querySelector(".activa");
      if (previo) {
        previo.classList.remove("activa");
        previo.setAttribute("aria-selected", "false");
      }
      activo = i;
      if (i < 0 || i >= visibles.length) {
        entrada.removeAttribute("aria-activedescendant");
        return;
      }
      const li = document.getElementById(id + "-op" + i);
      if (!li) return;
      li.classList.add("activa");
      li.setAttribute("aria-selected", "true");
      entrada.setAttribute("aria-activedescendant", li.id);
      // Mantiene la opción marcada a la vista sin arrastrar toda la página.
      const arriba = li.offsetTop, abajo = arriba + li.offsetHeight;
      if (arriba < lista.scrollTop) lista.scrollTop = arriba;
      else if (abajo > lista.scrollTop + lista.clientHeight)
        lista.scrollTop = abajo - lista.clientHeight;
    }

    function escoger(i) {
      const o = visibles[i];
      if (!o) return;
      select.value = o.valor;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      pintarElegido();
      cerrar();
      acabaDeElegir = true;
      entrada.focus();
      // El cursor al principio: si no, la casilla queda desplazada al final
      // del nombre y parece que dice otra cosa.
      try { entrada.setSelectionRange(0, 0); } catch (e) {}
      entrada.scrollLeft = 0;
    }

    entrada.addEventListener("click", function () {
      if (lista.hidden) abrir(elegido() ? "" : entrada.value);
    });

    entrada.addEventListener("input", function () {
      select.value = "";                    // lo escrito manda hasta que elija
      caja.classList.remove("tiene-eleccion");
      abrir(entrada.value);
    });

    entrada.addEventListener("focus", function () {
      if (acabaDeElegir) { acabaDeElegir = false; return; }
      // Al entrar en la casilla se selecciona todo: así escribir de nuevo
      // reemplaza al cliente anterior sin tener que borrar a mano.
      entrada.select();
      abrir(elegido() ? "" : entrada.value);
    });

    entrada.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        if (lista.hidden) { abrir(entrada.value); return; }
        if (!visibles.length) return;
        const paso = ev.key === "ArrowDown" ? 1 : -1;
        let i = activo + paso;
        if (i < 0) i = visibles.length - 1;
        if (i >= visibles.length) i = 0;
        marcar(i);
      } else if (ev.key === "Enter") {
        if (!lista.hidden && activo >= 0) {
          ev.preventDefault();              // elegir, no enviar el formulario
          escoger(activo);
        } else if (!lista.hidden && visibles.length === 1) {
          ev.preventDefault();
          escoger(0);
        }
      } else if (ev.key === "Escape") {
        if (!lista.hidden) { ev.stopPropagation(); cerrar(); pintarElegido(); }
      } else if (ev.key === "Tab") {
        // Si sólo queda uno, tabular lo da por elegido: es lo que se espera.
        if (!lista.hidden && visibles.length === 1 && !select.value) escoger(0);
        cerrar();
      }
    });

    entrada.addEventListener("blur", function () {
      window.setTimeout(function () {
        if (caja.contains(document.activeElement)) return;
        cerrar();
        pintarElegido();                    // texto a medias no se queda
      }, 120);
    });

    // El <select> sigue siendo obligatorio, pero está oculto: el navegador no
    // puede mostrarle el aviso encima. Se lleva el foco a la casilla visible.
    select.addEventListener("invalid", function (ev) {
      ev.preventDefault();
      caja.classList.add("falta");
      estado.textContent = "Elija un cliente de la lista.";
      entrada.focus();
    });
    select.addEventListener("change", function () {
      if (select.value) caja.classList.remove("falta");
    });

    pintarElegido();
  }

  function iniciar() {
    document.querySelectorAll("select[data-buscable]").forEach(montar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }

  window.BuscadorSelect = { montar: montar, iniciar: iniciar };
})();
