'use strict';
(async()=>{
const select=document.querySelector('#book-select'),isbnInput=document.querySelector('#isbn-input');
if(!select||!isbnInput)return;
const data=[...select.options].filter(x=>x.value).map(x=>({id:x.value,isbn:x.dataset.isbn,stock:+x.dataset.stock,price:+x.dataset.price,title:x.textContent.split(' · ')[0]}));
const cart=new Map();const cartBox=document.querySelector('#pos-cart');const totalBox=document.querySelector('#pos-total');
const money=v=>Math.round(v).toLocaleString('vi-VN')+' ₫';
const msgBox=document.querySelector('#pos-msg');
/* Thông báo nội tuyến ngay trên nút tạo hóa đơn, thay cho hộp thoại trình duyệt. */
function showMsg(text){if(!msgBox){window.hepToast?.(text);return;}msgBox.textContent=text;msgBox.hidden=false;}
function clearMsg(){if(msgBox){msgBox.hidden=true;msgBox.textContent='';}}
function render(){cartBox.replaceChildren();let total=0;
for(const [id,qty] of cart){const book=data.find(x=>x.id===id);if(!book)continue;total+=book.price*qty;
const row=document.createElement('div');row.className='pos-line';const name=document.createElement('span');name.textContent=book.title;
const input=document.createElement('input');input.type='number';input.min='1';input.max=String(book.stock);input.name='quantity';input.value=String(qty);input.required=true;input.addEventListener('change',()=>{const v=+input.value;if(!Number.isInteger(v)||v<1||v>book.stock){showMsg(`Số lượng phải từ 1 đến ${book.stock}. Còn ${book.stock} cuốn trong kho.`);input.value=qty;return;}clearMsg();cart.set(id,v);render();});
const hidden=document.createElement('input');hidden.type='hidden';hidden.name='book';hidden.value=book.id;
const price=document.createElement('strong');price.textContent=money(book.price*qty);const remove=document.createElement('button');remove.type='button';remove.className='btn btn-ghost btn-sm btn-icon';remove.setAttribute('aria-label','Bỏ '+book.title+' khỏi giỏ');remove.innerHTML='<i class="ph ph-x" aria-hidden="true"></i>';remove.addEventListener('click',()=>{cart.delete(id);render();});row.append(name,input,price,remove,hidden);cartBox.append(row);
}totalBox.textContent=money(total);}
function addBook(book){if(!book)return showMsg('Chưa chọn sách hoặc ISBN chưa có trong kho. Chọn sách trong danh sách rồi bấm thêm.');if(book.stock<=0)return showMsg(`${book.title} đã hết hàng. Chọn sách khác.`);const next=(cart.get(book.id)||0)+1;if(next>book.stock)return showMsg(`Số lượng vượt tồn kho. Còn ${book.stock} cuốn.`);clearMsg();cart.set(book.id,next);render();}
document.querySelector('#pos-add')?.addEventListener('click',()=>addBook(data.find(x=>x.id===select.value)));
document.querySelectorAll('[data-choose-book]').forEach(btn=>btn.addEventListener('click',()=>addBook(data.find(x=>x.id===btn.dataset.chooseBook))));
/* Thiếu tick tiền mặt: lần gửi 1 cảnh báo nội tuyến và đổi nút, lần gửi 2 mới tạo đơn. Thay cho hộp xác nhận trình duyệt. */
const payment=document.querySelector('#pos-payment'),tick=document.querySelector('#cash-confirm'),submitBtn=document.querySelector('[data-pos-submit]');
const submitLabel=submitBtn?submitBtn.textContent:'';let unpaidArmed=false;
function disarmUnpaid(){unpaidArmed=false;if(submitBtn)submitBtn.textContent=submitLabel;}
payment?.addEventListener('change',()=>{disarmUnpaid();clearMsg();});tick?.addEventListener('change',()=>{disarmUnpaid();clearMsg();});
document.querySelector('#pos-form').addEventListener('submit',e=>{if(!cart.size){e.preventDefault();showMsg('Giỏ POS đang trống. Thêm ít nhất một cuốn sách trước khi tạo hóa đơn.');return;}if(payment.value==='cash'&&!tick.checked&&!unpaidArmed){e.preventDefault();unpaidArmed=true;showMsg('Chưa tích ô đã nhận đủ tiền mặt. Đơn sẽ ở trạng thái chưa thanh toán. Tích ô nếu đã thu, hoặc bấm lại để vẫn tạo.');if(submitBtn)submitBtn.textContent='Vẫn tạo đơn chưa thu';}});
let stream=null,timer=null,detector=null,tmModel=null,running=false,recognizing=false;
const video=document.querySelector('#scan-video'),status=document.querySelector('#camera-status');
async function stop(){running=false;recognizing=false;if(timer){clearTimeout(timer);timer=null;}if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}video.srcObject=null;status.textContent='Camera đã tắt';}
async function startCam(){if(!navigator.mediaDevices?.getUserMedia){status.textContent='Trình duyệt không cho phép camera. Sử dụng localhost/HTTPS.';return false;}await stop();stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});video.srcObject=stream;await video.play();running=true;return true;}
const onISBN=(isbn,mode)=>{const found=data.find(x=>x.isbn===isbn);isbnInput.value=isbn;status.textContent=`${mode}: ${isbn}${found?' · '+found.title:' · chưa có trong kho'}`;if(found){select.value=found.id;} };
document.querySelector('#start-scan')?.addEventListener('click',async()=>{try{if(!(await startCam()))return;if(!('BarcodeDetector' in window)){status.textContent='Trình duyệt không hỗ trợ quét camera BarcodeDetector. Dùng máy quét USB hoặc nhập ISBN.';return;}detector=new BarcodeDetector({formats:['ean_13','ean_8','code_128','upc_a']});status.textContent='Đưa mã vạch ISBN vào camera';async function loop(){if(!running)return;try{const codes=await detector.detect(video);if(codes.length){const isbn=(codes[0].rawValue||'').trim();if(isbn){onISBN(isbn,'Mã vạch');await stop();status.textContent='Đã nhận '+isbn+' · bấm Tra cứu hoặc chọn nhanh sách';return;}}}catch(err){/* video frame might not be ready */}timer=setTimeout(loop,250);}loop();}catch(err){status.textContent='Không mở được camera: '+err.message;await stop();}});
document.querySelector('#stop-scan')?.addEventListener('click',()=>stop());
// Optional Teachable Machine: model class labels MUST be ISBN/SKU, never product name guess.
const aiBtn=document.querySelector('#start-ai');aiBtn?.addEventListener('click',async()=>{try{if(!(await startCam()))return;const url=document.querySelector('.ai-box')?.dataset.tmUrl||'';if(!url||!window.tmImage){status.textContent='Thiếu mô hình AI hoặc thư viện Teachable Machine.';return;}tmModel=await tmImage.load(url.replace(/\/?$/,'/')+'model.json',url.replace(/\/?$/,'/')+'metadata.json');recognizing=true;status.textContent='Nhìn bìa sách và giữ ổn định...';let last='',streak=0;async function predict(){if(!running||!recognizing)return;const pred=await tmModel.predict(video);const top=[...pred].sort((a,b)=>b.probability-a.probability)[0];if(top&&top.probability>=.88&&top.className.toLowerCase()!=='background'){if(top.className===last)streak++;else{last=top.className;streak=1;}if(streak>=3){onISBN(top.className,'AI');recognizing=false;return;}}else streak=0;timer=setTimeout(predict,350);}predict();}catch(err){status.textContent='Mô hình AI chưa sẵn sàng: '+err.message;await stop();}});
window.addEventListener('pagehide',()=>stop());
})();
