'use strict';
(function(){const box=document.querySelector('[data-lines]');if(!box)return;
const add=document.querySelector('[data-add-line]');const sync=()=>{box.querySelectorAll('[data-remove-line]').forEach(b=>{b.onclick=()=>{if(box.querySelectorAll('[data-line]').length>1)b.closest('[data-line]').remove();};});};
add?.addEventListener('click',()=>{if(box.querySelectorAll('[data-line]').length>=50)return alert('Tối đa 50 dòng');const row=box.querySelector('[data-line]').cloneNode(true);row.querySelectorAll('input').forEach(el=>el.value=el.name==='quantity'?'1':'0');row.querySelectorAll('select').forEach(el=>el.value='');box.appendChild(row);sync();});sync();})();
