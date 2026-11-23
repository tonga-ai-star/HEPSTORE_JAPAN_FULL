# Sơ đồ phân tích hệ thống Hép Bookstore

BFD, DFD và kiến trúc hệ thống, dựng theo mã nguồn hiện tại. Ảnh PNG nằm trong `docs/diagrams/`.

## Sơ đồ phân rã chức năng (BFD)

8 nhóm chức năng chính, mỗi nhóm tách thành các chức năng con. Nhóm 1 dành cho khách; nhóm 2 đến 8 nằm ở trang quản trị và chỉ mở theo vai trò: bán hàng (2, 3, 6), kho (4, 5), quản lý (tất cả, riêng 3.4, 2.6 hoàn tiền, 7 và 8 chỉ quản lý).

![Sơ đồ phân rã chức năng (BFD)](diagrams/BFD.png)

## DFD mức ngữ cảnh (mức 0)

Toàn bộ hệ thống là một tiến trình. 5 tác nhân ngoài trao đổi dữ liệu với hệ thống. Khách chuyển khoản trực tiếp cho ngân hàng (nét đứt), hệ thống chỉ biết tiền vào qua webhook của SePay.

![DFD mức ngữ cảnh (mức 0)](diagrams/DFD_muc_ngu_canh.png)

```mermaid
flowchart LR
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
  NK -- "Sách, danh mục, điều chỉnh kho,<br/>nhà cung cấp, phiếu nhập" --> P0
  P0 -- "Tồn kho, cảnh báo tồn thấp,<br/>lịch sử kho" --> NK
  QL -- "Tài khoản nhân viên, vai trò,<br/>xác nhận tiền thủ công, hoàn tiền" --> P0
  P0 -- "Báo cáo doanh thu, sách bán chạy,<br/>file CSV đơn hàng" --> QL
  classDef ent fill:#2c3a7e,stroke:#1f2547,color:#ffffff,font-weight:bold
  classDef proc fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  classDef store fill:#f4ece0,stroke:#2c3a7e,stroke-dasharray:0,color:#1f2547
```

## DFD mức đỉnh (mức 1)

8 tiến trình ứng với 8 chức năng BFD, 8 kho dữ liệu ứng với các bảng trong ERD: D1 Book, Category; D2 Order, OrderItem; D3 Customer; D4 PaymentTransaction; D5 StockMovement; D6 Supplier, PurchaseOrder, PurchaseItem; D7 User, StaffProfile; D8 ContactMessage.

![DFD mức đỉnh (mức 1)](diagrams/DFD_muc_1.png)

```mermaid
flowchart TB
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
  D1 -- "Giá, tồn kho, ngày về" --> P1
  P1 -- "Đơn mới" --> D2
  P1 -- "Lời nhắn" --> D8
  NV -- "Đơn FB/IG, POS, trạng thái" --> P2
  D2 <-- "Đọc, cập nhật đơn" --> P2
  P2 -- "Trừ, hoàn tồn" --> D1
  P2 -- "Ghi xuất, nhập lại" --> D5
  D3 -- "Thông tin khách" --> P2
  SP -- "Webhook tiền vào" --> P3
  P3 -- "Lưu giao dịch" --> D4
  P3 -- "Đánh dấu đã thanh toán" --> D2
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
  QL -- "Nhân viên, vai trò" --> P7
  P7 <--> D7
  D2 -- "Đơn, doanh thu" --> P8
  P8 -- "Báo cáo, CSV" --> QL
  classDef ent fill:#2c3a7e,stroke:#1f2547,color:#ffffff,font-weight:bold
  classDef proc fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  classDef store fill:#f4ece0,stroke:#2c3a7e,stroke-dasharray:0,color:#1f2547
```

## DFD mức dưới đỉnh (mức 2): đặt hàng và thanh toán QR

Phân rã luồng quan trọng nhất: khách đặt hàng, trả tiền bằng QR, đơn tự chuyển sang đã thanh toán. Đơn chuyển khoản không trả tiền sau 3 ngày bị hủy và trả sách về kho.

![DFD mức dưới đỉnh (mức 2): đặt hàng và thanh toán QR](diagrams/DFD_muc_2_dat_hang_thanh_toan.png)

```mermaid
flowchart LR
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
  P31 -- "Khớp: đã thanh toán" --> D2
  P31 -- "Không khớp: chờ xử lý" --> NV
  D2 -- "Trạng thái đơn (hỏi mỗi vài giây)" --> P14
  P14 -- "Thanh toán thành công<br/>hoặc đơn đã hủy" --> KH
  D2 -- "Đơn chưa trả tiền quá 3 ngày" --> P21
  P21 -- "Hủy đơn" --> D2
  P21 -- "Trả sách về kho" --> D1
  classDef ent fill:#2c3a7e,stroke:#1f2547,color:#ffffff,font-weight:bold
  classDef proc fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  classDef store fill:#f4ece0,stroke:#2c3a7e,stroke-dasharray:0,color:#1f2547
```

## Kiến trúc hệ thống (System Architecture)

Ứng dụng Django một khối chạy trên máy cửa hàng, không thuê hosting. Hai tên miền trên cùng một server được tách bằng middleware. Chỉ đường dẫn webhook được mở ra Internet qua ngrok để SePay gọi vào. Luồng nghiệp vụ dồn vào services.py; views chỉ nhận yêu cầu và hiển thị.

![Kiến trúc hệ thống (System Architecture)](diagrams/Kien_truc_he_thong.png)

```mermaid
flowchart TB
  subgraph U["Người dùng"]
    B1["Trình duyệt khách<br/>(máy tính, điện thoại)"]
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
      M1["HostSplitMiddleware<br/>tách 2 link, chặn tunnel"]
      M2["CSRF, Session, Auth"]
      M3["RoleAccessMiddleware<br/>quản lý / bán hàng / kho"]
    end
    subgraph V["Views (shop/)"]
      V1["views.py<br/>cửa hàng + quản trị"]
      V2["payment_views.py<br/>webhook, trạng thái thanh toán"]
      V3["scan_views.py<br/>quét mã xem giá"]
      V4["staff_views.py<br/>nhân viên"]
    end
    SVC["services.py<br/>tạo đơn, đặt trước, kho,<br/>đánh dấu đã trả, hoàn tiền"]
    ORM["Django ORM<br/>models.py (13 bảng)"]
    TPL["Templates + static<br/>CSS wa, JS, three.js r170"]
    CMD["Lệnh nền: huy_don_qua_han,<br/>seed_demo, sepay_thu"]
    DB[("SQLite<br/>db.sqlite3")]
    ENV[/".env<br/>tài khoản NH, khoá SePay"/]
  end
  B1 --> H1
  B2 --> H2
  H1 --> M1
  H2 --> M1
  M1 --> M2 --> M3 --> V
  V --> SVC --> ORM --> DB
  V --> TPL
  CMD --> SVC
  ENV -.-> V2
  B1 -. "tải ảnh QR" .-> VQR
  B1 -. "chuyển khoản" .-> BANK
  BANK --> SEPAY
  SEPAY -- "POST webhook" --> NG --> M1
  B1 -. "font, icon" .-> CDN
  B2 -. "font, icon" .-> CDN
  classDef default fill:#f4ece0,stroke:#2c3a7e,color:#1f2547
  classDef hot fill:#fdf1e4,stroke:#d9772b,stroke-width:2px,color:#1f2547
  class SVC,M1,M3,V2 hot
```
