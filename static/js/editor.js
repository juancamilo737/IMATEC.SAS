/* Editor de ítems compartido por cotizaciones, remisiones y facturas */
let ITEMS = [];
let CON_IMPUESTOS = true;
let IVA_DEFECTO = 19;

function fmtCOP(v){
  const n = Math.round(Number(v) || 0);
  return '$ ' + n.toLocaleString('es-CO').replace(/,/g, '.');
}

function agregarFila(base){
  ITEMS.push(Object.assign({
    producto_id: null, descripcion: '', especificaciones: '', cantidad: 1,
    unidad: 'UND', precio: 0, descuento_pct: 0, iva_pct: IVA_DEFECTO, observacion: ''
  }, base || {}));
  pintarItems();
}

function quitarFila(i){ ITEMS.splice(i, 1); pintarItems(); }

function cambiar(i, campo, valor){
  ITEMS[i][campo] = ['cantidad','precio','descuento_pct','iva_pct'].includes(campo)
    ? (parseFloat(valor) || 0) : valor;
  pintarItems();
}

function elegirProducto(i, id){
  const p = PRODUCTOS.find(x => String(x.id) === String(id));
  if (p){
    ITEMS[i].producto_id = p.id;
    ITEMS[i].descripcion = p.nombre;
    ITEMS[i].especificaciones = p.especificaciones || '';
    ITEMS[i].unidad = p.unidad || 'UND';
    ITEMS[i].precio = Number(p.precio) || 0;
    ITEMS[i].iva_pct = Number(p.iva_pct) || IVA_DEFECTO;
  } else {
    ITEMS[i].producto_id = null;
  }
  pintarItems();
}

function totalesDoc(){
  let subtotal = 0, iva = 0;
  ITEMS.forEach(it => {
    const base = (Number(it.cantidad)||0) * (Number(it.precio)||0) *
                 (1 - (Number(it.descuento_pct)||0)/100);
    subtotal += base;
    if (CON_IMPUESTOS) iva += base * (Number(it.iva_pct)||0)/100;
  });
  const dg = Number(document.getElementById('descuento')?.value) || 0;
  const baseFinal = subtotal - dg;
  if (CON_IMPUESTOS && subtotal > 0 && dg) iva = iva * (baseFinal / subtotal);
  return { subtotal, descuento: dg, iva, total: baseFinal + iva };
}

function pintarItems(){
  const cuerpo = document.getElementById('items-cuerpo');
  const opciones = PRODUCTOS.map(p =>
    `<option value="${p.id}">${p.categoria} — ${p.nombre}</option>`).join('');

  cuerpo.innerHTML = ITEMS.map((it, i) => `
    <tr>
      <td style="width:34px" class="silencio">${i+1}</td>
      <td>
        <select onchange="elegirProducto(${i}, this.value)" style="margin-bottom:.35rem">
          <option value="">— Escribir libre —</option>${opciones}
        </select>
        <input type="text" value="${(it.descripcion||'').replace(/"/g,'&quot;')}"
          placeholder="Descripción del ítem" onchange="cambiar(${i},'descripcion',this.value)">
        ${CON_IMPUESTOS ? `<textarea placeholder="Especificaciones / medidas (opcional)"
          onchange="cambiar(${i},'especificaciones',this.value)"
          style="margin-top:.35rem">${it.especificaciones||''}</textarea>`
        : `<input type="text" placeholder="Observación" style="margin-top:.35rem"
          value="${(it.observacion||'').replace(/"/g,'&quot;')}"
          onchange="cambiar(${i},'observacion',this.value)">`}
      </td>
      <td style="width:88px"><input type="number" step="0.01" value="${it.cantidad}"
        onchange="cambiar(${i},'cantidad',this.value)"></td>
      <td style="width:80px"><input type="text" value="${it.unidad}"
        onchange="cambiar(${i},'unidad',this.value)"></td>
      <td style="width:120px"><input type="number" step="1" value="${it.precio}"
        onchange="cambiar(${i},'precio',this.value)"></td>
      ${CON_IMPUESTOS ? `
      <td style="width:70px"><input type="number" step="0.01" value="${it.descuento_pct}"
        onchange="cambiar(${i},'descuento_pct',this.value)"></td>
      <td style="width:70px"><input type="number" step="0.01" value="${it.iva_pct}"
        onchange="cambiar(${i},'iva_pct',this.value)"></td>` : ''}
      <td class="num" style="width:120px;padding-top:.85rem;white-space:nowrap">
        <strong>${fmtCOP((it.cantidad||0)*(it.precio||0)*(1-(it.descuento_pct||0)/100))}</strong></td>
      <td style="width:44px"><button type="button" class="btn btn-sm btn-claro"
        onclick="quitarFila(${i})" title="Quitar">✕</button></td>
    </tr>`).join('');

  if (!ITEMS.length){
    cuerpo.innerHTML = `<tr><td colspan="9" class="vacio" style="padding:2rem">
      <b>Sin ítems</b><p>Agregue el primero con el botón de abajo.</p></td></tr>`;
  }

  const t = totalesDoc();
  const caja = document.getElementById('totales');
  if (caja){
    caja.innerHTML = `
      <div><span>Subtotal</span><span>${fmtCOP(t.subtotal)}</span></div>
      ${t.descuento ? `<div><span>Descuento</span><span>-${fmtCOP(t.descuento)}</span></div>` : ''}
      ${CON_IMPUESTOS ? `<div><span>IVA</span><span>${fmtCOP(t.iva)}</span></div>` : ''}
      <div class="grande"><span>Total</span><span>${fmtCOP(t.total)}</span></div>`;
  }
  const campo = document.getElementById('items_json');
  if (campo) campo.value = JSON.stringify(ITEMS);
}

function prepararEnvio(e){
  ITEMS = ITEMS.filter(i => (i.descripcion || '').trim() !== '');
  if (!ITEMS.length){
    e.preventDefault();
    alert('Agregue al menos un ítem con descripción.');
    return false;
  }
  document.getElementById('items_json').value = JSON.stringify(ITEMS);
  return true;
}
