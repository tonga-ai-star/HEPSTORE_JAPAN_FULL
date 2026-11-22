from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Book,Category,Supplier,Customer,ContactMessage
from .roles import role_of

class StyledMixin:
    def style(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault('class','form-input')
            if isinstance(field.widget,forms.Textarea):field.widget.attrs.setdefault('rows',3)

class SignUpForm(StyledMixin,UserCreationForm):
    email=forms.EmailField(required=True,label='Email')
    first_name=forms.CharField(max_length=150,label='Họ và tên')
    class Meta:
        model=User
        fields=('username','first_name','email','password1','password2')
        labels={'username':'Tên đăng nhập'}
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.style()
    def clean_email(self):
        email=self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():raise forms.ValidationError('Email này đã được dùng.')
        return email
    def save(self,commit=True):
        u=super().save(commit=False);u.email=self.cleaned_data['email'];u.first_name=self.cleaned_data['first_name'];
        if commit:u.save()
        return u

class BookForm(StyledMixin,forms.ModelForm):
    # Plain text field so Vietnamese titles ("Sách Mới") reach clean_slug and become "sach-moi"
    # instead of failing SlugField validation first.
    slug=forms.CharField(label='Đường dẫn',max_length=220)
    class Meta:
        model=Book
        fields=['category','supplier','title_vi','title_ja','slug','author_ja','publisher','isbn','description_vi','price','cost_price','min_stock','allow_preorder','restock_days','cover','featured','active']
        widgets={'description_vi':forms.Textarea(attrs={'rows':4})}
    PRICE_FIELDS=('price','cost_price')
    def __init__(self,*args,actor=None,**kwargs):
        super().__init__(*args,**kwargs);self.style()
        # Only the manager changes prices of existing books; warehouse staff may still price a brand-new title.
        if self.instance.pk and actor is not None and role_of(actor)!='manager':
            for name in self.PRICE_FIELDS:
                self.fields[name].disabled=True
                self.fields[name].help_text='Chỉ quản lý được đổi giá.'
    def clean_slug(self):
        slug=slugify(self.cleaned_data['slug'].replace('đ','d').replace('Đ','D'))
        if not slug:raise forms.ValidationError('Đường dẫn cần có chữ hoặc số.')
        return slug

class SupplierForm(StyledMixin,forms.ModelForm):
    class Meta:
        model=Supplier
        fields=['name','contact_name','phone','email','address','note','active']
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.style()

class CustomerForm(StyledMixin,forms.ModelForm):
    class Meta:
        model=Customer
        fields=['full_name','email','phone','address','note']
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.style()

class ContactForm(StyledMixin,forms.ModelForm):
    class Meta:
        model=ContactMessage
        fields=['full_name','email','subject','message']
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.style()


class StaffCreateForm(StyledMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, label='Họ và tên')
    role = forms.ChoiceField(label='Vai trò', choices=[('sales', 'Bán hàng'), ('warehouse', 'Kho'), ('manager', 'Quản lý')])
    phone = forms.CharField(max_length=30, required=False, label='Số điện thoại')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'password1', 'password2')
        labels = {'username': 'Tên đăng nhập'}

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs); self.style()
        if actor is not None and not actor.is_superuser:
            self.fields['role'].choices = [('sales', 'Bán hàng'), ('warehouse', 'Kho')]

    def save(self, commit=True):
        from .models import StaffProfile
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.is_staff = True
        user.save()
        StaffProfile.objects.create(user=user, role=self.cleaned_data['role'], phone=self.cleaned_data['phone'])
        return user


class StaffEditForm(StyledMixin, forms.Form):
    role = forms.ChoiceField(label='Vai trò', choices=[('sales', 'Bán hàng'), ('warehouse', 'Kho'), ('manager', 'Quản lý')])
    is_active = forms.BooleanField(label='Cho phép đăng nhập', required=False)
    new_password = forms.CharField(label='Mật khẩu mới (bỏ trống nếu giữ nguyên)', required=False, widget=forms.PasswordInput)

    def __init__(self, *args, user, actor=None, **kwargs):
        from .models import StaffProfile
        self.user = user
        self.profile, _ = StaffProfile.objects.get_or_create(user=user)
        kwargs.setdefault('initial', {'role': self.profile.role, 'is_active': user.is_active})
        super().__init__(*args, **kwargs); self.style()
        if actor is not None and not actor.is_superuser:
            self.fields['role'].choices = [('sales', 'Bán hàng'), ('warehouse', 'Kho')]

    def clean_new_password(self):
        from django.contrib.auth.password_validation import validate_password
        pw = self.cleaned_data.get('new_password')
        if pw:
            validate_password(pw, self.user)
        return pw

    def save(self):
        self.profile.role = self.cleaned_data['role']; self.profile.save(update_fields=['role'])
        self.user.is_active = self.cleaned_data['is_active']
        if self.cleaned_data.get('new_password'):
            self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user
