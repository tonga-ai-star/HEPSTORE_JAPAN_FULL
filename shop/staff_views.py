"""Manager-only page to create back-office accounts and assign roles."""
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StaffCreateForm, StaffEditForm
from .models import StaffProfile
from .roles import role_of

log = logging.getLogger('hepstore.staff')
staff = lambda fn: staff_member_required(fn, login_url='/tai-khoan/login/')  # noqa: E731


@staff
def manage_staff(request):
    users = get_user_model().objects.filter(is_staff=True).select_related('staff_profile').order_by('-is_active', 'username')
    rows = [{'user': u, 'role': dict(StaffProfile.ROLES).get(role_of(u) or '', 'Đã khoá')} for u in users]
    return render(request, 'management/staff.html', {'rows': rows})


@staff
def staff_add(request):
    form = StaffCreateForm(request.POST or None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'Đã tạo tài khoản {user.get_username()}.')
        return redirect('manage_staff')
    return render(request, 'management/form.html', {'form': form, 'heading': 'Thêm nhân viên', 'back': 'manage_staff'})


@staff
def staff_edit(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk, is_staff=True)
    if user.is_superuser:
        messages.error(request, 'Tài khoản chủ cửa hàng chỉ sửa trong Django Admin.')
        return redirect('manage_staff')
    if user.pk == request.user.pk:
        messages.error(request, 'Không tự sửa quyền hoặc mật khẩu của chính mình ở đây. Đổi mật khẩu ở trang tài khoản.')
        return redirect('manage_staff')
    if role_of(user) == 'manager' and not request.user.is_superuser:
        messages.error(request, 'Chỉ chủ cửa hàng được sửa tài khoản Quản lý khác.')
        return redirect('manage_staff')
    form = StaffEditForm(request.POST or None, user=user, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log.info('%s cập nhật nhân viên %s: role=%s active=%s đổi_mk=%s', request.user.get_username(), user.get_username(),
                 form.cleaned_data['role'], form.cleaned_data['is_active'], bool(form.cleaned_data.get('new_password')))
        messages.success(request, 'Đã cập nhật nhân viên.')
        return redirect('manage_staff')
    return render(request, 'management/form.html', {'form': form, 'heading': f'Nhân viên {user.get_username()}', 'back': 'manage_staff'})
