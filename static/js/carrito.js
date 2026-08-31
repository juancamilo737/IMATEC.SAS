/* Carrito de solicitud de cotización — se guarda en el navegador del cliente */
const CARRITO_KEY = 'imatec_carrito_v1';

function leerCarrito(){
  try { return JSON.parse(localStorage.getItem(CARRITO_KEY) || '[]'); }
  catch(e){ return []; }
}
function guardarCarrito(items){
  try { localStorage.setItem(CARRITO_KEY, JSON.stringify(items)); } catch(e){}
  pintarContador();
}
function pintarContador(){
  const n = leerCarrito().reduce((s,i)=> s + Number(i.cantidad||0), 0);
  document.querySelectorAll('#carrito-num').forEach(el=>{
    el.textContent = n;
    el.style.display = n ? 'inline-flex' : 'none';
  });
}
function agregarAlCarrito(producto, cantidad, observacion){
  const items = leerCarrito();
  const i = items.findIndex(x => x.id === producto.id);
  if (i >= 0){
    items[i].cantidad = Number(items[i].cantidad) + Number(cantidad || 1);
    if (observacion) items[i].observacion = observacion;
  } else {
    items.push({...producto, cantidad: Number(cantidad || 1), observacion: observacion || ''});
  }
  guardarCarrito(items);
  avisar(`"${producto.nombre}" agregado a su solicitud`);
}
function quitarDelCarrito(id){
  guardarCarrito(leerCarrito().filter(x => x.id !== id));
  if (window.pintarCarrito) window.pintarCarrito();
}
function actualizarCantidad(id, cantidad){
  const items = leerCarrito();
  const it = items.find(x => x.id === id);
  if (it){ it.cantidad = Math.max(1, Number(cantidad) || 1); guardarCarrito(items); }
  if (window.pintarCarrito) window.pintarCarrito();
}
function vaciarCarrito(){ guardarCarrito([]); if (window.pintarCarrito) window.pintarCarrito(); }

function avisar(texto){
  const t = document.createElement('div');
  t.textContent = texto;
  t.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:999;background:#1B1B1A;' +
    'color:#FCEA0B;padding:14px 20px;border-radius:6px;font-family:Montserrat,sans-serif;' +
    'font-weight:700;font-size:.85rem;box-shadow:0 8px 32px rgba(0,0,0,.3);max-width:320px';
  document.body.appendChild(t);
  setTimeout(()=>{ t.style.transition='.3s'; t.style.opacity='0'; t.style.transform='translateY(10px)'; }, 2200);
  setTimeout(()=> t.remove(), 2600);
}
document.addEventListener('DOMContentLoaded', pintarContador);
