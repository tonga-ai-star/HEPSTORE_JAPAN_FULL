"""Add 11 real books from Hép Bookstore's Facebook page, with their real ISBN-13 so the barcode scanner finds them.

ISBNs were checked against openBD / the National Diet Library (bản bìa cứng, tankōbon). Prices are
placeholders: the posts do not list prices, so Nga must set the real price in the back office.
Idempotent: run again and existing books (same ISBN) are left untouched.
Run: python3 manage.py nhap_sach_hep
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Book, Category, StockMovement

PRICE = 380000  # placeholder, see module docstring
BOOKS = [
    # isbn, title_vi, title_ja, author, publisher, category slug, cover, description
    ('9784046854735', 'Dù vậy vẫn vươn tay tới ánh sáng', 'それでも光に手を伸ばす', 'Payao', 'KADOKAWA',
     'van-hoc-nhat', 'covers/hep/9784046854735.jpg',
     'Dù chỉ đang cố tỏ ra dịu dàng, thì người ấy vẫn là một người dịu dàng. Tản văn đã vượt mốc 150.000 bản, '
     'tác giả Payao viết tặng những ai đang mang cảm giác ngột ngạt, khó thở.'),
    ('9784046807540', 'Tiệm ngọt cho những đêm muốn khóc', '泣きたい夜の甘味処', '中山有香里 (Nakayama Yukari)',
     'KADOKAWA', 'van-hoa-doi-song', 'covers/hep/9784046807540.jpg',
     'Ở một thị trấn nọ có tiệm bánh ngọt chỉ mở về đêm, chủ quán là một chú gấu và một chú cá hồi. '
     'Những người mệt mỏi, có những đêm chỉ muốn khóc, lần lượt tìm đến đây. Sách đoạt giải Comic tại '
     '第9回料理レシピ本大賞.'),
    ('9784344030039', 'Ong mật và sấm xa', '蜜蜂と遠雷', '恩田陸 (Onda Riku)', '幻冬舎', 'van-hoc-nhat', '',
     'Tiểu thuyết về những thí sinh tại một cuộc thi piano quốc tế. Giải Naoki và giải Honya Taishō 2017.'),
    ('9784065222690', 'Những thế giới nhỏ', 'スモールワールズ', '一穂ミチ (Ichiho Michi)', '講談社',
     'van-hoc-nhat', '', 'Tập truyện ngắn về những thế giới nhỏ bé, gần gũi của từng gia đình, từng con người.'),
    ('9784862551825', 'Cô ấy và chú mèo của cô ấy', '彼女と彼女の猫', '新海誠, 永川成基 (Shinkai Makoto, Nagakawa Naruki)',
     'カンゼン', 'van-hoc-nhat', '', 'Tiểu thuyết từ phim ngắn đầu tay của Shinkai Makoto, kể qua góc nhìn một chú mèo.'),
    ('9784120052989', 'Những chú cá voi 52 hertz', '52ヘルツのクジラたち', '町田そのこ (Machida Sonoko)', '中央公論新社',
     'van-hoc-nhat', '', 'Câu chuyện về những người cô đơn mà tiếng gọi không ai nghe thấy. Giải Honya Taishō 2021.'),
    ('9784488028022', 'Vầng trăng lưu lạc', '流浪の月', '凪良ゆう (Nagira Yuu)', '東京創元社', 'van-hoc-nhat', '',
     'Tiểu thuyết về một mối quan hệ bị xã hội hiểu lầm. Giải Honya Taishō 2020.'),
    ('9784163910031', 'Trăm hoa', '百花', '川村元気 (Kawamura Genki)', '文藝春秋', 'van-hoc-nhat', '',
     'Câu chuyện về người mẹ dần mất trí nhớ và người con trai đi tìm lại những ký ức giữa hai mẹ con.'),
    ('9784087716535', 'Tiệm cắt tóc nhìn ra biển', '海の見える理髪店', '荻原浩 (Ogiwara Hiroshi)', '集英社',
     'van-hoc-nhat', '', 'Tập truyện ngắn về gia đình và những điều chưa kịp nói. Giải Naoki 2016.'),
    ('9784041110508', 'Hiệu sách Muguet', 'ミュゲ書房', '伊藤調 (Ito Shirabe)', 'KADOKAWA', 'van-hoc-nhat', '',
     'Câu chuyện về một biên tập viên trẻ tiếp quản hiệu sách nhỏ của ông ngoại ở vùng quê.'),
    # Nga sent a photo of the front cover only. The barcode number is not verified yet, so this book uses a
    # temporary SKU: replace it with the 13 digits under the barcode on the back cover to make it scannable.
    ('HEP-MINNA-SC1-VI', 'Tiếng Nhật cho mọi người - Sơ cấp 1 - Bản dịch và giải thích ngữ pháp (Bản mới)',
     'みんなの日本語 初級I 翻訳・文法解説 ベトナム語版', '3A Network', '3A Network', 'nhat-ngu', '',
     'Sách đi kèm giáo trình Minna no Nihongo Sơ cấp 1: dịch từ vựng, hội thoại và giải thích ngữ pháp '
     'từng bài bằng tiếng Việt.'),
]
SLUGS = {'HEP-MINNA-SC1-VI': 'tieng-nhat-cho-moi-nguoi-so-cap-1-ban-dich'}


class Command(BaseCommand):
    help = 'Thêm 11 cuốn sách thật của Hép (có ISBN thật để quét mã)'

    @transaction.atomic
    def handle(self, *args, **options):
        cats = {c.slug: c for c in Category.objects.all()}
        added = 0
        for isbn, vi, ja, author, publisher, cat, cover, desc in BOOKS:
            slug = SLUGS.get(isbn, f'hep-{isbn}')
            if Book.objects.filter(isbn=isbn).exists() or Book.objects.filter(slug=slug).exists():
                continue
            book = Book.objects.create(
                isbn=isbn, title_vi=vi, title_ja=ja, slug=slug, author_ja=author, publisher=publisher,
                category=cats[cat], cover=cover or 'cover-default.svg', description_vi=desc, price=PRICE,
                stock=1, min_stock=1, allow_preorder=True, restock_days=14, featured=bool(cover))
            StockMovement.objects.create(book=book, delta=1, reason='Nhập sách thật của Hép', reference='NHAP-HEP')
            added += 1
        self.stdout.write(self.style.SUCCESS(f'Đã thêm {added} cuốn (bỏ qua {len(BOOKS) - added} cuốn đã có).'))
