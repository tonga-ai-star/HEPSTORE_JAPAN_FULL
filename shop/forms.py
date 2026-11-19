from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Book,Category,Supplier,Customer,ContactMessage

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
    class Meta:
        model=Book
        fields=['category','supplier','title_vi','title_ja','slug','author_ja','publisher','isbn','description_vi','price','cost_price','min_stock','cover','featured','active']
        widgets={'description_vi':forms.Textarea(attrs={'rows':4})}
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.style()
    def clean_slug(self):
        return slugify(self.cleaned_data['slug'])

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
