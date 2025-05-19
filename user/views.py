from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from order.models import Order, OrderProduct
from product.models import Category, Comment
from user.forms import SignUpForm, UserUpdateForm, ProfileUpdateForm
from user.models import UserProfile
from order.models import ShopCart
@login_required(login_url='/login')
def index(request):
    category = Category.objects.all()
    current_user = request.user  # Access User Session information
    profile = UserProfile.objects.get(user_id=current_user.id)
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    totalqty = 0
    for rs in shopcart:
        total += rs.product.price * rs.quantity
        totalqty += rs.quantity
    context = {   'category': category,
        'profile': profile,'shopcart': shopcart,"totalqty":totalqty,
               'total': total}
    return render(request, 'user_profile.html', context)

def login_form(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                userprofile = UserProfile.objects.get(user_id=user.id)
                login(request, user)
                current_user = request.user
                request.session['userimage'] = userprofile.image.url
                return HttpResponseRedirect('/')
            except UserProfile.DoesNotExist:
                # Tạo profile cho tất cả các loại tài khoản nếu chưa có
                userprofile = UserProfile()
                userprofile.user = user
                userprofile.image = "images/users/user.png"
                userprofile.save()
                login(request, user)
                request.session['userimage'] = userprofile.image.url
                return HttpResponseRedirect('/')
        else:
            messages.warning(request,"Lỗi đăng nhập! Sai tên đăng nhập hoặc mật khẩu")
            return HttpResponseRedirect('/login')

    category = Category.objects.all()
    context = {'category': category}
    return render(request, 'login_form.html',context)

def signup_form(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save() #completed sign up
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            #Create data in profile table for user
            data=UserProfile()
            data.user_id=user.id
            data.image="images/users/user.png"
            data.save()
            messages.success(request, 'Tài khoản của bạn đã tạo thành công! Vui lòng đăng nhập.')
            return HttpResponseRedirect('/login')
        else:
            messages.warning(request,form.errors)
            return HttpResponseRedirect('/signup')


    form = SignUpForm()
    category = Category.objects.all()
    context = {'category': category,
               'form': form,
               }
    return render(request, 'signup_form.html', context)

def logout_func(request):
    logout(request)
    # if translation.LANGUAGE_SESSION_KEY in request.session:
    #     del request.session[translation.LANGUAGE_SESSION_KEY]
    #     del request.session['currency']
    return HttpResponseRedirect('/')

@login_required(login_url='/login')
def user_update(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user) # request.user is user  data
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Tài khoản của bạn đã được cập nhật!')
            return HttpResponseRedirect('/user')
    else:
        category = Category.objects.all()
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.userprofile) #"userprofile" model -> OneToOneField relatinon with user
        context = {
            'category': category,
            'user_form': user_form,
            'profile_form': profile_form
        }
        return render(request, 'user_update.html', context)

@login_required(login_url='/login') # Check login
def user_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Đổi mật khẩu thành công!')
            return HttpResponseRedirect('/user')
        else:
            messages.error(request, 'Hãy nhập đúng lỗi bên dưới.<br>'+ str(form.errors))
            return HttpResponseRedirect('/user/password')
    else:
        category = Category.objects.all()
        form = PasswordChangeForm(request.user)
        return render(request, 'user_password.html', {'form': form,'category': category
                       })


@login_required(login_url='/login') # Check login
def user_orders(request):
    category = Category.objects.all()
    current_user = request.user
    orders=Order.objects.filter(user_id=current_user.id)
    context = {'category': category,
               'orders': orders,
               }
    return render(request, 'user_orders.html', context)

@login_required(login_url='/login') # Check login
def user_orderdetail(request,id):
    category = Category.objects.all()
    current_user = request.user
    order = Order.objects.get(user_id=current_user.id, id=id)
    orderitems = OrderProduct.objects.filter(order_id=id)
    context = {
        'category': category,
        'order': order,
        'orderitems': orderitems,
    }
    return render(request, 'user_order_detail.html', context)

@login_required(login_url='/login') # Check login
def user_order_product(request):
    category = Category.objects.all()
    current_user = request.user
    order_product = OrderProduct.objects.filter(user_id=current_user.id).order_by('-id')
    context = {'category': category,
               'order_product': order_product,
               }
    return render(request, 'user_order_products.html', context)

@login_required(login_url='/login') # Check login
def user_order_product_detail(request,id,oid):
    category = Category.objects.all()
    current_user = request.user
    order = Order.objects.get(user_id=current_user.id, id=oid)
    orderitems = OrderProduct.objects.filter(id=id,user_id=current_user.id)
    context = {
        'category': category,
        'order': order,
        'orderitems': orderitems,
    }
    return render(request, 'user_order_detail.html', context)

def user_comments(request):
    category = Category.objects.all()
    current_user = request.user
    comments = Comment.objects.filter(user_id=current_user.id)
    context = {
        'category': category,
        'comments': comments,
    }
    return render(request, 'user_comments.html', context)

@login_required(login_url='/login') # Check login
def user_deletecomment(request,id):
    current_user = request.user
    Comment.objects.filter(id=id, user_id=current_user.id).delete()
    messages.success(request, 'Xóa bình luận.')
    return HttpResponseRedirect('/user/comments')
# from django.shortcuts import render

# Create your views here.
