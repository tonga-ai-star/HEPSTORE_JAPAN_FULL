#!/usr/bin/env python3
"""One-command local launcher: create venv, install Django, migrate, seed sample books, start site.
Requires Python >=3.10 and Internet on the FIRST install (for pip). Never deploy via runserver.
"""
import argparse
import os
import secrets
import subprocess
import sys
import venv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)

def run(args,**kwargs):
    print('▶',' '.join(map(str,args)),flush=True)
    subprocess.run(list(map(str,args)),check=True,**kwargs)

def main():
    parser=argparse.ArgumentParser(description='Khởi động Hép Store Django')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-run',action='store_true',help='Cài, khởi tạo dữ liệu, nhưng không chạy máy chủ')
    parser.add_argument('--no-seed',action='store_true',help='Không tạo sách mẫu')
    args=parser.parse_args()
    if sys.version_info < (3,10):raise RuntimeError('Cần Python 3.10 trở lên (khuyến nghị Python 3.12).')
    envdir=ROOT/'.venv'
    executable=envdir/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        print('Tạo môi trường Python riêng ...')
        venv.create(envdir,with_pip=True)
    try:
        subprocess.run([str(executable),'-c','import django; assert django.VERSION[:2] == (5,2)'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print('Lần đầu cần Internet để cài Django từ PyPI.')
        run([executable,'-m','pip','install','--disable-pip-version-check','-r',ROOT/'requirements.txt'])
    run([executable,'manage.py','makemigrations','shop','--noinput'])
    run([executable,'manage.py','migrate','--noinput'])
    if not args.no_seed:run([executable,'manage.py','seed_demo'])
    # For local demos only: random credentials generated exactly once; never embedded in downloads.
    from tempfile import NamedTemporaryFile
    env=os.environ.copy()
    code=('import os,django,secrets;os.environ.setdefault("DJANGO_SETTINGS_MODULE","hepstore.settings");'
          'django.setup();from django.contrib.auth import get_user_model;'
          'U=get_user_model();'
          'exists=U.objects.filter(is_superuser=True).exists();'
          'password=secrets.token_urlsafe(14) if not exists else "";'
          'U.objects.create_superuser(os.environ.get("HEPSTORE_ADMIN_USER","admin"),'
          'os.environ.get("HEPSTORE_ADMIN_EMAIL",""),password) if not exists else None;'
          'print("ADMIN_CREATED:"+password if not exists else "ADMIN_EXISTS")')
    result=subprocess.run([str(executable),'-c',code],capture_output=True,text=True,check=True,env=env)
    out=result.stdout.strip()
    if out.startswith('ADMIN_CREATED:'):
        print('\n'+'='*65+'\nTÀI KHOẢN QUẢN TRỊ DEMO (HÃY ĐỔI MẬT KHẨU SAU KHI ĐĂNG NHẬP)')
        print('Tài khoản:',os.environ.get('HEPSTORE_ADMIN_USER','admin'))
        print('Mật khẩu một lần:',out.split('ADMIN_CREATED:',1)[1])
        print('LƯU NGAY MẬT KHẨU NÀY; sau lần đầu sẽ không hiển thị lại.\n'+'='*65+'\n')
    if args.no_run:return
    print('\nHÉP STORE đang chạy trên http://127.0.0.1:'+str(args.port))
    print('Quản trị: http://127.0.0.1:'+str(args.port)+'/management/')
    print('Nhấn CTRL+C để dừng. Không dùng chế độ này để vận hành website công khai.\n',flush=True)
    try:run([executable,'manage.py','runserver',f'127.0.0.1:{args.port}'])
    except KeyboardInterrupt:pass

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('\nLỖI KHỞI ĐỘNG:',exc,file=sys.stderr)
        print('Kiểm tra Python, kết nối Internet, hoặc xem README_HUONG_DAN.md.',file=sys.stderr)
        if os.name=='nt' and sys.stdin.isatty():input('Nhấn Enter để đóng...')
        sys.exit(1)
