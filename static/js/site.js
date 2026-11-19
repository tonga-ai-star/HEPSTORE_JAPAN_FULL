// Progressive enhancement only. No client-side prices are authoritative.
'use strict';
document.querySelectorAll('[data-confirm]').forEach(el=>el.addEventListener('click',e=>{if(!confirm(el.dataset.confirm)){e.preventDefault()}}));
