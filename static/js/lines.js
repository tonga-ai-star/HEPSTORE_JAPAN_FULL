'use strict';
(function(){
const box=document.querySelector('[data-lines]');if(!box)return;
const MAX_LINES=50;
const add=document.querySelector('[data-add-line]');
const notify=(text)=>{if(window.hepToast)window.hepToast(text);};
/* Gắn lại nút xóa cho mọi dòng; luôn giữ ít nhất một dòng. */
const sync=()=>{box.querySelectorAll('[data-remove-line]').forEach(b=>{b.onclick=()=>{if(box.querySelectorAll('[data-line]').length>1){b.closest('[data-line]').remove();}else{notify('Cần ít nhất một dòng sách.');}};});};
add?.addEventListener('click',()=>{if(box.querySelectorAll('[data-line]').length>=MAX_LINES){notify(`Tối đa ${MAX_LINES} dòng sách mỗi phiếu. Tạo phiếu mới cho phần còn lại.`);return;}const row=box.querySelector('[data-line]').cloneNode(true);row.querySelectorAll('input').forEach(el=>{el.value=el.name==='quantity'?'1':'0';});row.querySelectorAll('select').forEach(el=>{el.value='';});box.appendChild(row);row.querySelector('select')?.focus();sync();});
sync();
})();
