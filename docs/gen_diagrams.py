#!/usr/bin/env python3
"""Build the BFD, DFD (context, level 1, level 2) and system architecture diagrams of Hép Bookstore.

Writes docs/SoDo_Hep_Bookstore.html, .md, .pdf and docs/diagrams/*.png, *.mmd.
Needs Playwright + Chrome and Internet (mermaid from jsDelivr). Run: python3 docs/gen_diagrams.py
"""
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parent
OUT = DOCS / 'diagrams'
OUT.mkdir(exist_ok=True)

# ---------- BFD: sơ đồ phân rã chức năng ----------
BFD = [
    ('1', 'Bán hàng trực tuyến', ['Xem, tìm, lọc sách', 'Quản lý giỏ hàng', 'Đặt hàng, đặt trước sách hết',
                                  'Thanh toán QR hoặc COD', 'Tra cứu đơn hàng', 'Đăng ký, tài khoản khách',
                                  'Quét mã xem giá', 'Gửi liên hệ']),
    ('2', 'Quản lý đơn hàng', ['Xem, lọc đơn', 'Cập nhật trạng thái đơn', 'Nhập đơn Facebook/Instagram',
                               'Bán tại quầy (POS, quét mã vạch)', 'Tự hủy đơn giữ chỗ quá hạn',
                               'Hủy đơn, hoàn tiền']),
    ('3', 'Quản lý thanh toán', ['Nhận webhook SePay', 'Tự khớp theo mã đơn và số tiền',
                                 'Xử lý giao dịch chưa khớp', 'Xác nhận thủ công (quản lý)']),
    ('4', 'Quản lý sách và kho', ['Thêm, sửa sách', 'Điều chỉnh tồn kho', 'Cảnh báo tồn thấp',
                                  'Chia sách về cho đơn đặt trước', 'Lịch sử biến động kho']),
    ('5', 'Quản lý nhập hàng', ['Quản lý nhà cung cấp', 'Lập phiếu nhập', 'Nhận hàng, cộng kho']),
    ('6', 'Quản lý khách hàng', ['Thêm, sửa khách hàng', 'Xem lịch sử mua']),
    ('7', 'Quản trị hệ thống', ['Đăng nhập, đăng xuất', 'Quản lý nhân viên',
                                'Phân quyền: quản lý, bán hàng, kho',
                                'Danh mục sách, dữ liệu gốc (trang /admin/)']),
    ('8', 'Báo cáo thống kê', ['Tổng quan (dashboard)', 'Doanh thu theo kênh', 'Đơn theo trạng thái',
                               'Sách bán chạy', 'Xuất đơn ra CSV']),
]


def bfd_html():
    cols = []
    for num, name, leaves in BFD:
        items = ''.join(f'<li><b>{num}.{i}</b> {html.escape(t)}</li>' for i, t in enumerate(leaves, 1))
        cols.append(f'<div class="bfd-col"><div class="bfd-fn">{num}. {html.escape(name)}</div><ul>{items}</ul></div>')
    return ('<div class="bfd" id="bfd"><div class="bfd-root">HỆ THỐNG QUẢN LÝ BÁN SÁCH HÉP BOOKSTORE</div>'
            f'<div class="bfd-row">{"".join(cols)}</div></div>')


def bfd_mermaid():
    lines = ['flowchart TD', '  R["HỆ THỐNG QUẢN LÝ BÁN SÁCH<br/>HÉP BOOKSTORE"]']
    for num, name, leaves in BFD:
        lines.append(f'  F{num}["{num}. {name}"]')
        lines.append(f'  R --> F{num}')
        prev = f'F{num}'
        for i, t in enumerate(leaves, 1):
            lines.append(f'  F{num}_{i}["{num}.{i} {t}"]')
            lines.append(f'  {prev} --- F{num}_{i}' if prev == f'F{num}' else f'  {prev} ~~~ F{num}_{i}')
            prev = f'F{num}_{i}'
    return '\n'.join(lines)


STYLE = '''
  classDef ent fill:#2c3a7e,stroke:#1f2547,color:#ffffff,font-weight:bold
  classDef proc fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  classDef store fill:#f4ece0,stroke:#2c3a7e,stroke-dasharray:0,color:#1f2547'''

DFD0 = '''flowchart LR
  KH["Khách hàng"]:::ent
  BH["Nhân viên bán hàng"]:::ent
  NK["Nhân viên kho"]:::ent
  QL["Quản lý"]:::ent
  SP["SePay / Ngân hàng MB"]:::ent
  P0(("0<br/>Hệ thống<br/>Hép Bookstore")):::proc
  KH -- "Tìm sách, giỏ hàng, thông tin đặt hàng,<br/>mã tra cứu, lời nhắn liên hệ" --> P0
  P0 -- "Danh mục, giá, tồn kho, mã QR chuyển khoản,<br/>trạng thái đơn, ngày dự kiến có hàng" --> KH
  KH -. "Chuyển khoản theo mã QR" .-> SP
  SP -- "Webhook giao dịch tiền vào<br/>(số tiền, nội dung, mã tham chiếu)" --> P0
  BH -- "Đơn FB/Instagram, đơn POS, mã vạch,<br/>cập nhật trạng thái, khách hàng" --> P0
  P0 -- "Danh sách đơn, giao dịch chưa khớp,<br/>thông tin thanh toán" --> BH
  NK -- "Sách, điều chỉnh kho,<br/>nhà cung cấp, phiếu nhập" --> P0
  P0 -- "Tồn kho, cảnh báo tồn thấp,<br/>lịch sử kho" --> NK
  QL -- "Tài khoản nhân viên, vai trò, danh mục sách,<br/>xác nhận tiền thủ công, hoàn tiền" --> P0
  P0 -- "Báo cáo doanh thu, sách bán chạy,<br/>file CSV đơn hàng, lời nhắn liên hệ" --> QL''' + STYLE

DFD1 = '''flowchart TB
  KH["Khách hàng"]:::ent
  NV["Nhân viên<br/>(bán hàng, kho)"]:::ent
  QL["Quản lý"]:::ent
  SP["SePay"]:::ent
  P1(("1.0<br/>Bán hàng<br/>trực tuyến")):::proc
  P2(("2.0<br/>Quản lý<br/>đơn hàng")):::proc
  P3(("3.0<br/>Quản lý<br/>thanh toán")):::proc
  P4(("4.0<br/>Quản lý<br/>sách và kho")):::proc
  P5(("5.0<br/>Quản lý<br/>nhập hàng")):::proc
  P6(("6.0<br/>Quản lý<br/>khách hàng")):::proc
  P7(("7.0<br/>Quản trị<br/>hệ thống")):::proc
  P8(("8.0<br/>Báo cáo<br/>thống kê")):::proc
  D1[("D1 Sách, danh mục")]:::store
  D2[("D2 Đơn hàng, chi tiết đơn")]:::store
  D3[("D3 Khách hàng")]:::store
  D4[("D4 Giao dịch thanh toán")]:::store
  D5[("D5 Biến động kho")]:::store
  D6[("D6 Nhà cung cấp, phiếu nhập")]:::store
  D7[("D7 Tài khoản, nhân viên")]:::store
  D8[("D8 Lời nhắn liên hệ")]:::store
  KH -- "Yêu cầu tìm sách, đơn đặt" --> P1
  P1 -- "Sách, mã QR, trạng thái đơn" --> KH
  D1 <-- "Đọc giá, tồn, ngày về;<br/>trừ tồn khi đặt" --> P1
  P1 <-- "Đơn mới; đọc trạng thái<br/>khi tra cứu" --> D2
  P1 -- "Ghi xuất bán" --> D5
  P1 -- "Hồ sơ khách từ đơn" --> D3
  P1 -- "Tài khoản khách đăng ký" --> D7
  P1 -- "Lời nhắn" --> D8
  NV -- "Đơn FB/IG, POS, trạng thái" --> P2
  D2 <-- "Đọc, cập nhật đơn" --> P2
  P2 -- "Trừ, hoàn tồn" --> D1
  P2 -- "Ghi xuất, nhập lại" --> D5
  D3 <-- "Tìm, tạo hồ sơ khách<br/>theo SĐT" --> P2
  SP -- "Webhook tiền vào" --> P3
  P3 -- "Lưu giao dịch" --> D4
  P3 <-- "Tìm đơn theo mã;<br/>đánh dấu đã thanh toán" --> D2
  QL -- "Xác nhận thủ công, hoàn tiền" --> P3
  P3 -- "Giao dịch chưa khớp" --> NV
  NV -- "Sách, điều chỉnh kho" --> P4
  P4 -- "Cập nhật sách, tồn" --> D1
  P4 -- "Ghi biến động" --> D5
  P4 -- "Chia sách cho đơn đặt trước" --> D2
  NV -- "Phiếu nhập" --> P5
  P5 <--> D6
  P5 -- "Cộng tồn khi nhận hàng" --> P4
  NV -- "Thông tin khách" --> P6
  P6 <--> D3
  QL -- "Nhân viên, vai trò, danh mục" --> P7
  P7 -- "Danh mục sách" --> D1
  P7 <--> D7
  D8 -- "Lời nhắn khách" --> P7
  P7 -- "Lời nhắn (trang /admin/)" --> QL
  D2 -- "Đơn, doanh thu" --> P8
  P8 -- "Báo cáo, CSV" --> QL''' + STYLE

DFD2 = '''flowchart LR
  KH["Khách hàng"]:::ent
  SP["SePay"]:::ent
  NV["Nhân viên bán hàng"]:::ent
  P11(("1.1<br/>Kiểm tra giỏ<br/>và tồn kho")):::proc
  P12(("1.2<br/>Tạo đơn,<br/>tách phần đặt trước")):::proc
  P13(("1.3<br/>Hiện mã QR<br/>VietQR")):::proc
  P31(("3.1<br/>Nhận và<br/>khớp giao dịch")):::proc
  P14(("1.4<br/>Báo kết quả<br/>cho khách")):::proc
  P21(("2.1<br/>Tự hủy đơn<br/>quá hạn giữ chỗ")):::proc
  D1[("D1 Sách")]:::store
  D2[("D2 Đơn hàng")]:::store
  D4[("D4 Giao dịch thanh toán")]:::store
  D5[("D5 Biến động kho")]:::store
  D3[("D3 Khách hàng")]:::store
  P12 -- "Hồ sơ khách" --> D3
  KH -- "Giỏ hàng, họ tên, SĐT, địa chỉ" --> P11
  D1 -- "Tồn kho, cho phép đặt trước,<br/>số ngày về hàng" --> P11
  P11 -- "Sách thiếu: hỏi khách đồng ý<br/>chờ khoảng N ngày" --> KH
  P11 -- "Dòng hợp lệ" --> P12
  P12 -- "Trừ phần có sẵn" --> D1
  P12 -- "Ghi xuất kho" --> D5
  P12 -- "Đơn, mã đơn, ngày dự kiến" --> D2
  P12 -- "Mã đơn, tổng tiền" --> P13
  P13 -- "QR chứa số tiền và mã đơn" --> KH
  KH -. "Chuyển khoản" .-> SP
  SP -- "Webhook (Authorization: Apikey)" --> P31
  P31 -- "Lưu giao dịch" --> D4
  D2 -- "Đơn chờ theo mã, số tiền" --> P31
  P31 -- "Đúng mã đơn và đủ số tiền:<br/>đã thanh toán, xác nhận đơn" --> D2
  P31 -- "Sai số tiền, không thấy mã,<br/>trùng đơn: chờ nhân viên xử lý" --> NV
  D2 -- "Trạng thái đơn (trang QR hỏi lại mỗi 4 giây)" --> P14
  P14 -- "Thanh toán thành công<br/>hoặc đơn đã hủy" --> KH
  D2 -- "Đơn web chưa xác nhận, chưa trả tiền<br/>quá 3 ngày, không có giao dịch kèm" --> P21
  P21 -- "Hủy đơn" --> D2
  P21 -- "Trả sách về kho" --> D1''' + STYLE

ARCH = '''flowchart TB
  subgraph U["Người dùng"]
    B1["Trình duyệt khách<br/>(máy tính, điện thoại, camera quét mã)"]
    B2["Trình duyệt nhân viên<br/>+ camera / máy quét mã vạch"]
  end
  subgraph EXT["Dịch vụ ngoài"]
    BANK["Ngân hàng MB"]
    SEPAY["SePay<br/>(gói miễn phí)"]
    VQR["img.vietqr.io<br/>(ảnh mã QR)"]
    CDN["Google Fonts, Phosphor icons,<br/>ZXing (CDN)"]
  end
  NG["ngrok tunnel<br/>chỉ mở /api/sepay/webhook/"]
  subgraph SRV["Máy chạy Django 5.2 (không thuê hosting)"]
    direction TB
    H1["shop.localhost:8000<br/>Trang khách"]
    H2["quantri.localhost:8000<br/>Trang quản trị"]
    subgraph MW["Middleware"]
      M0["Security, Session"]
      M1["HostSplitMiddleware<br/>tách 2 link, chặn tunnel"]
      M2["CSRF, Auth"]
      M3["RoleAccessMiddleware<br/>quản lý / bán hàng / kho"]
    end
    subgraph V["Views (shop/)"]
      V1["views.py<br/>cửa hàng + quản trị"]
      V2["payment_views.py<br/>webhook, trạng thái thanh toán"]
      V3["scan_views.py<br/>quét mã xem giá"]
      V4["staff_views.py<br/>nhân viên"]
    end
    PAY["payments.py<br/>kiểm khoá, khớp mã đơn và số tiền"]
    ADM["Django admin /admin/<br/>dữ liệu gốc, lời nhắn liên hệ"]
    SVC["services.py<br/>tạo đơn, đặt trước, kho,<br/>đánh dấu đã trả, hoàn tiền"]
    ORM["Django ORM<br/>models.py (13 bảng)"]
    TPL["Templates + static<br/>CSS wa, JS, three.js r170"]
    CMD["Lệnh nền: huy_don_qua_han,<br/>seed_demo, sepay_thu"]
    DB[("SQLite<br/>db.sqlite3")]
    ENV[/".env<br/>tài khoản NH, khoá SePay"/]
  end
  B1 --> H1
  B2 --> H2
  H1 --> M0
  H2 --> M0
  M0 --> M1 --> M2 --> M3 --> V
  V --> SVC --> ORM --> DB
  V2 --> PAY --> SVC
  ADM --> ORM
  V --> TPL
  CMD --> SVC
  ENV -.-> V2
  B1 -. "tải ảnh QR" .-> VQR
  B1 -. "chuyển khoản" .-> BANK
  BANK --> SEPAY
  SEPAY -- "POST webhook" --> NG --> M0
  B1 -. "font, icon" .-> CDN
  B2 -. "font, icon" .-> CDN
  classDef default fill:#f4ece0,stroke:#2c3a7e,color:#1f2547
  classDef hot fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  class SVC,M1,M3,V2,PAY hot'''

DIAGRAMS = [
    ('BFD', 'Sơ đồ phân rã chức năng (BFD)', None,
     '8 nhóm chức năng chính, mỗi nhóm tách thành các chức năng con. Nhóm 1 dành cho khách; nhóm 2 đến 8 '
     'nằm ở trang quản trị và chỉ mở theo vai trò: bán hàng (2, 3, 6), kho (4, 5), quản lý (tất cả). '
     'Danh mục sách chỉ sửa được ở trang /admin/ của Django (7.4). '
     'Riêng 2.6 hoàn tiền, 3.4 xác nhận tiền thủ công, nhóm 7 và 8.2 đến 8.5 chỉ quản lý; 8.1 tổng quan ai cũng xem.'),
    ('DFD_muc_ngu_canh', 'DFD mức ngữ cảnh (mức 0)', DFD0,
     'Toàn bộ hệ thống là một tiến trình. 5 tác nhân ngoài trao đổi dữ liệu với hệ thống. Khách chuyển '
     'khoản trực tiếp cho ngân hàng (nét đứt), hệ thống chỉ biết tiền vào qua webhook của SePay.'),
    ('DFD_muc_1', 'DFD mức đỉnh (mức 1)', DFD1,
     '8 tiến trình ứng với 8 chức năng BFD, 8 kho dữ liệu ứng với các bảng trong ERD: D1 Book, Category; '
     'D2 Order, OrderItem; D3 Customer; D4 PaymentTransaction; D5 StockMovement; D6 Supplier, '
     'PurchaseOrder, PurchaseItem; D7 User, StaffProfile; D8 ContactMessage.'),
    ('DFD_muc_2_dat_hang_thanh_toan', 'DFD mức dưới đỉnh (mức 2): đặt hàng và thanh toán QR', DFD2,
     'Phân rã luồng quan trọng nhất: khách đặt hàng, trả tiền bằng QR, đơn tự chuyển sang đã thanh toán. '
     'Đơn web còn ở trạng thái mới, chưa trả tiền quá 3 ngày (đơn đặt trước: 3 ngày sau ngày dự kiến có hàng) '
     'thì tự hủy và trả sách về kho; đơn đã có giao dịch chuyển khoản liên quan thì để nhân viên xử lý, không tự hủy.'),
    ('Kien_truc_he_thong', 'Kiến trúc hệ thống (System Architecture)', ARCH,
     'Ứng dụng Django một khối chạy trên máy cửa hàng, không thuê hosting. Hai tên miền trên cùng một '
     'server được tách bằng middleware. Chỉ đường dẫn webhook được mở ra Internet qua ngrok để SePay gọi vào. '
     'Luồng nghiệp vụ dồn vào services.py; views chỉ nhận yêu cầu và hiển thị.'),
]

CSS = '''@page{size:A3 landscape;margin:12mm}
body{font-family:Arial,"DejaVu Sans",sans-serif;color:#1f2547;margin:24px;background:#fff}
h1{color:#2c3a7e;margin:0 0 4px}h2{color:#2c3a7e;margin:0 0 4px}p.note{color:#4f5679;margin:0 0 12px;max-width:1500px}
section{page-break-after:always;margin-bottom:48px}section:last-child{page-break-after:auto}
.fig{display:inline-block;padding:8px}.fig img{max-width:100%;max-height:235mm}
.legend{font-size:12px;color:#4f5679;margin-top:6px}
.bfd{display:inline-block;padding:12px;font-size:14px}
.bfd-root{margin:0 auto;width:fit-content;padding:12px 28px;background:#2c3a7e;color:#fff;font-weight:700;border-radius:8px;position:relative}
.bfd-root::after{content:'';position:absolute;left:50%;top:100%;height:18px;border-left:2px solid #2c3a7e}
.bfd-row{display:flex;gap:14px;margin-top:36px;position:relative;padding-top:18px}
.bfd-row::before{content:'';position:absolute;top:0;left:calc(100%/16);right:calc(100%/16);border-top:2px solid #2c3a7e}
.bfd-col{width:190px;position:relative}
.bfd-col::before{content:'';position:absolute;left:50%;top:-18px;height:18px;border-left:2px solid #2c3a7e}
.bfd-fn{background:#fdf1e4;border:2px solid #d9772b;border-radius:8px;padding:8px;font-weight:700;text-align:center;min-height:38px;display:flex;align-items:center;justify-content:center}
.bfd-col ul{list-style:none;margin:0;padding:0 0 0 16px;border-left:2px solid #2c3a7e;margin-left:12px}
.bfd-col li{position:relative;margin-top:10px;background:#f4ece0;border:1.5px solid #2c3a7e;border-radius:6px;padding:6px 8px;font-size:13px}
.bfd-col li::before{content:'';position:absolute;left:-18px;top:50%;width:16px;border-top:2px solid #2c3a7e}
.bfd-col li:last-child::after{content:'';position:absolute;left:-20px;top:calc(50% + 2px);bottom:-200px;width:4px;background:#fff}
.bfd-col ul{overflow:hidden;padding-bottom:2px}'''

LEGEND = ('<p class="legend">Ký hiệu: khối xanh đậm là tác nhân ngoài; hình tròn cam là tiến trình; '
          'hình trụ là kho dữ liệu; mũi tên là luồng dữ liệu, nét đứt là luồng ngoài hệ thống.</p>')


def page_html(for_pdf=False):
    parts = [f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Sơ đồ Hép Bookstore</title>'
             f'<style>{CSS}</style></head><body><h1>Sơ đồ phân tích hệ thống Hép Bookstore</h1>'
             '<p class="note">BFD, DFD và kiến trúc hệ thống, dựng theo mã nguồn hiện tại (shop/). '
             'Đi kèm ERD trong ERD_Hep_Bookstore.</p>']
    for key, title, src, note in DIAGRAMS:
        if for_pdf:
            body = f'<div class="fig"><img src="diagrams/{key}.png" alt="{html.escape(title)}"></div>'
        elif src is None:
            body = bfd_html()
        else:
            body = f'<div class="fig"><pre class="mermaid" id="{key}">{html.escape(src)}</pre></div>'
        legend = LEGEND if key.startswith('DFD') else ''
        parts.append(f'<section><h2>{html.escape(title)}</h2><p class="note">{html.escape(note)}</p>{body}{legend}</section>')
    if not for_pdf:
        parts.append('<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>'
                     '<script>mermaid.initialize({startOnLoad:true,theme:"base",flowchart:{useMaxWidth:false,'
                     'htmlLabels:true,curve:"basis"},themeVariables:{fontFamily:"Arial",fontSize:"15px",'
                     'lineColor:"#2c3a7e",primaryTextColor:"#1f2547",edgeLabelBackground:"#ffffff"}});</script>')
    parts.append('</body></html>')
    return ''.join(parts)


def write_md():
    md = ['# Sơ đồ phân tích hệ thống Hép Bookstore', '',
          'BFD, DFD và kiến trúc hệ thống, dựng theo mã nguồn hiện tại. Ảnh PNG nằm trong `docs/diagrams/`.', '']
    for key, title, src, note in DIAGRAMS:
        md += [f'## {title}', '', note, '', f'![{title}](diagrams/{key}.png)', '']
        if src:
            md += ['```mermaid', src, '```', '']
    (DOCS / 'SoDo_Hep_Bookstore.md').write_text('\n'.join(md), encoding='utf-8')


def main():
    for key, _, src, _ in DIAGRAMS:
        (OUT / f'{key}.mmd').write_text(src or bfd_mermaid(), encoding='utf-8')
    live = DOCS / 'SoDo_Hep_Bookstore.html'
    live.write_text(page_html(), encoding='utf-8')
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel='chrome')
        except Exception:
            browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 2200, 'height': 1400}, device_scale_factor=2)
        page.goto(live.as_uri())
        page.wait_for_function("document.querySelectorAll('.mermaid svg').length === %d"
                               % sum(1 for d in DIAGRAMS if d[2]), timeout=60000)
        page.locator('#bfd').screenshot(path=str(OUT / 'BFD.png'))
        for key, _, src, _ in DIAGRAMS:
            if src:
                page.locator(f'#{key} svg').screenshot(path=str(OUT / f'{key}.png'))
        pdf_src = DOCS / '_sodo_pdf.html'
        pdf_src.write_text(page_html(for_pdf=True), encoding='utf-8')
        page.goto(pdf_src.as_uri())
        page.wait_for_function("[...document.images].every(i => i.complete)")
        page.pdf(path=str(DOCS / 'SoDo_Hep_Bookstore.pdf'), prefer_css_page_size=True, print_background=True)
        pdf_src.unlink()
        browser.close()
    write_md()
    print('docs/SoDo_Hep_Bookstore.{html,md,pdf}, docs/diagrams/*.png, *.mmd')


if __name__ == '__main__':
    main()
