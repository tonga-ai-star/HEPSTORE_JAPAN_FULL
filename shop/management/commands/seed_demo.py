"""Idempotent fictional demo catalog. Does not create fake payments."""
from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category, Supplier, Book, StockMovement

CATEGORIES=[
 ('van-hoc-nhat','Văn học & câu chuyện','日本文学','Tản văn, truyện và câu chuyện lấy cảm hứng từ Nhật Bản.'),
 ('nhat-ngu','Học tiếng Nhật','日本語','Tủ sách đồng hành trên hành trình học ngôn ngữ.'),
 ('van-hoa-doi-song','Văn hóa & đời sống','日本の暮らし','Những lát cắt về tinh thần và nhịp sống Nhật.'),
 ('nghe-thuat','Nghệ thuật & sáng tạo','芸術','Thẩm mỹ, kiến trúc, thủ công và sáng tạo.'),
]
BOOKS=[
 ('Bốn mùa ở Kyoto','京都の四季','bon-mua-o-kyoto','van-hoc-nhat',125000,14,'Chuyến dạo qua những mùa thay lá, lễ hội và con ngõ cổ ở Kyoto.'),
 ('Một ngày dưới tán sakura','桜の下の一日','mot-ngay-duoi-tan-sakura','van-hoc-nhat',98000,23,'Những tản văn về mùa xuân, khởi đầu và ký ức.'),
 ('Những lá thư từ Tokyo','東京からの手紙','nhung-la-thu-tu-tokyo','van-hoc-nhat',132000,17,'Hành trình khám phá nhịp sống thành thị bằng các câu chuyện nhỏ.'),
 ('Một tiệm sách ở Kamakura','鎌倉の本屋','tiem-sach-kamakura','van-hoc-nhat',155000,12,'Tản văn giả tưởng về người đọc sách và một thị trấn ven biển.'),
 ('Hiragana từ trang đầu','ひらがなの初歩','hiragana-tu-trang-dau','nhat-ngu',65000,35,'Bộ bài học nhập môn chữ Hiragana với phương pháp ghi nhớ.'),
 ('Katakana mỗi ngày','毎日のカタカナ','katakana-moi-ngay','nhat-ngu',72000,30,'Sổ luyện chữ Katakana và từ vựng quen thuộc.'),
 ('Nhật ngữ trong quán cà phê','カフェの日本語','nhat-ngu-quan-ca-phe','nhat-ngu',89000,20,'Mẫu hội thoại ngắn theo các tình huống thường ngày.'),
 ('300 câu giao tiếp Nhật','日本語会話','300-cau-giao-tiep-nhat','nhat-ngu',110000,16,'Luyện phản xạ ngôn ngữ qua hội thoại mẫu đơn giản.'),
 ('Wabi Sabi – đẹp từ bình dị','侘び寂びの心','wabi-sabi-dep-tu-binh-di','van-hoa-doi-song',165000,11,'Giới thiệu cảm hứng thẩm mỹ của sự giản dị, tự nhiên.'),
 ('Bento và những bữa cơm nhỏ','小さな弁当','bento-nhung-bua-com-nho','van-hoa-doi-song',145000,9,'Gợi ý bố trí bữa ăn cân bằng lấy cảm hứng từ hộp cơm Nhật.'),
 ('Chuyện trà đạo','茶の湯の物語','chuyen-tra-dao','van-hoa-doi-song',175000,8,'Tìm hiểu khái niệm hiếu khách, tĩnh tại và nghi lễ thưởng trà.'),
 ('Những khu vườn bình yên','静かな庭','nhung-khu-vuon-binh-yen','van-hoa-doi-song',139000,19,'Khám phá cách quan sát cây cỏ, khoảng lặng và bố cục khu vườn.'),
 ('Origami cho người bắt đầu','折り紙入門','origami-cho-nguoi-bat-dau','nghe-thuat',79000,27,'Những bài gấp giấy hình học đơn giản.'),
 ('Màu sắc trong tranh Nhật','日本画の色','mau-sac-tranh-nhat','nghe-thuat',189000,7,'Những câu chuyện màu sắc lấy cảm hứng từ hội họa Nhật.'),
 ('Ghi chép bằng tranh','絵で描く日記','ghi-chep-bang-tranh','nghe-thuat',128000,22,'Thực hành ghi chép bằng nét vẽ và một cuốn sổ nhỏ.'),
 ('Kiến trúc gỗ Nhật Bản','日本の木造建築','kien-truc-go-nhat','nghe-thuat',199000,5,'Giới thiệu cảm hứng từ kiến trúc gỗ và khoảng trống.'),
]

class Command(BaseCommand):
    help='Tạo dữ liệu DEMO giả lập cho Hép Store. Không tạo đơn hàng hoặc giao dịch giả.'
    @transaction.atomic
    def handle(self,*args,**opts):
        categories={}
        for slug,name,name_ja,description in CATEGORIES:
            c,_=Category.objects.get_or_create(slug=slug,defaults={'name_vi':name,'name_ja':name_ja,'description':description})
            categories[slug]=c
        suppliers=[]
        for name in ['Nguồn cung minh họa · Sách Nhật A','Nguồn cung minh họa · Văn hóa B','Nguồn cung minh họa · Nhật ngữ C']:
            supplier,_=Supplier.objects.get_or_create(name=name,defaults={'note':'CHỈ LÀ DỮ LIỆU MẪU. Thay bằng nhà cung cấp thật và hồ sơ chứng minh nguồn gốc khi vận hành.'})
            suppliers.append(supplier)
        created=0
        for idx,(title,ja,slug,cat,price,stock,desc) in enumerate(BOOKS):
            sku=f'HEP-DEMO-{idx+1:03d}'
            book,new=Book.objects.get_or_create(isbn=sku,defaults={'category':categories[cat],
              'supplier':suppliers[idx%3],'title_vi':title,'title_ja':ja,'slug':slug,'author_ja':'Hép Studio · DEMO',
              'publisher':'Dữ liệu mô phỏng – không phải sách phát hành thực',
              'description_vi':desc+' Đây là sách và mô tả minh họa, không đại diện cho ấn phẩm hay nhà xuất bản có thật.',
              'price':price,'cost_price':round(price*.6),'stock':stock,'min_stock':6,'featured':idx<8,'cover':f'covers/cover-{idx+1:02d}.svg'})
            if new:
                StockMovement.objects.create(book=book,delta=stock,reason='Tồn đầu kỳ DỮ LIỆU MẪU',reference='DEMO-SEED')
                created+=1
        self.stdout.write(self.style.SUCCESS(f'Đã tạo {created} sách demo mới; danh mục và nguồn cung được tái sử dụng nếu có.'))
