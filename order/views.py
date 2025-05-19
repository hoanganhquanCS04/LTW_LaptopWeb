from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
import json
# Create your views here.
from django.utils.crypto import get_random_string

from order.models import ShopCart, ShopCartForm, OrderForm, Order, OrderProduct
from product.models import Category, Product
from user.models import UserProfile


def index(request):
    return HttpResponse("Order Page")


@login_required(login_url='/login')  # Check login
def addtoshopcart(request, id):     
    url = request.META.get('HTTP_REFERER')  # get last url
    current_user = request.user  # Access User Session information
    product = Product.objects.get(pk=id)



    checkinproduct = ShopCart.objects.filter(product_id=id, user_id=current_user.id)  # Check product in shopcart
    if checkinproduct:
            control = 1  # The product is in the cart
    else:
            control = 0  # The product is not in the cart"""

    if request.method == 'POST':  # if there is a post
        form = ShopCartForm(request.POST)
        if form.is_valid():
            if control == 1:  # Update  shopcart

                data = ShopCart.objects.get(product_id=id, user_id=current_user.id)

                data.quantity += form.cleaned_data['quantity']
                data.save()  # save data
            else:  # Inser to Shopcart
                data = ShopCart()
                data.user_id = current_user.id
                data.product_id = id

                data.quantity = form.cleaned_data['quantity']
                data.save()
        messages.success(request, "Đã thêm sản phẩm vào giỏ hàng ")
        return HttpResponseRedirect(url)

    else:  # if there is no post
        if control == 1:  # Update  shopcart
            data = ShopCart.objects.get(product_id=id, user_id=current_user.id)
            data.quantity += 1
            data.save()  #
        else:  # Inser to Shopcart
            data = ShopCart()  # model ile bağlantı kur
            data.user_id = current_user.id
            data.product_id = id
            data.quantity = 1
            data.save()  #
        messages.success(request, "Đã thêm sản phẩm vào giỏ hàng")
        return HttpResponseRedirect(url)


def shopcart(request):
    category = Category.objects.all()
    current_user = request.user  # Access User Session information
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    for rs in shopcart:
        total += rs.product.price * rs.quantity
    # return HttpResponse(str(total))
    context = {'shopcart': shopcart,
               'category': category,
               'total': total,
               }
    return render(request, 'shopcart_products.html', context)


@login_required(login_url='/login')  # Check login
def deletefromcart(request, id):
    ShopCart.objects.filter(id=id).delete()
    messages.success(request, "Sản phẩm đã xóa khỏi giỏ hàng.")
    return HttpResponseRedirect("/shopcart")

@login_required(login_url='/accounts/login/')
def orderproduct(request):
    current_user = request.user
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    for rs in shopcart:
        total += rs.product.price * rs.quantity
    
    if request.method == 'POST':  # if form post
        # Process the order
        form = OrderForm(request.POST)
        if form.is_valid():
            # Lưu thông tin đơn hàng
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.phone = form.cleaned_data['phone']
            data.user_id = current_user.id
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.code = timezone.now().strftime('%Y%m%d%H%M%S')  # Tạo mã đơn hàng
            data.save()
            
            # Chuyển các sản phẩm từ giỏ hàng vào chi tiết đơn hàng
            for rs in shopcart:
                detail = OrderProduct()
                detail.order_id = data.id  # Order Id
                detail.product_id = rs.product_id
                detail.user_id = current_user.id
                detail.quantity = rs.quantity
                detail.price = rs.product.price

                detail.amount = rs.amount
                detail.save()
                # ***Reduce quantity of sold product from Amount of Product

                product = Product.objects.get(id=rs.product_id)
                product.amount -= rs.quantity
                product.save()

                # ************ <> *****************

            ShopCart.objects.filter(user_id=current_user.id).delete()  # Clear & Delete shopcart
            request.session['cart_items'] = 0
            messages.success(request, "Đơn hàng của bạn đã đặt thành công. Xin cảm ơn đã ủng hộ ! ")
            
            # Lấy danh mục để truyền vào template
            from product.models import Category
            categories = Category.objects.all()
            
            # Render trang xác nhận đơn hàng
            return render(request, 'Order_Completed.html', {
                'ordercode': data.code,
                'payment_method': 'cod',
                'payment_status': False,  # COD chưa thanh toán
                'category': categories,
                'categories': categories,
                'user': current_user
            })
                
        else:
            messages.warning(request, form.errors)
            return HttpResponseRedirect("/order/orderproduct")
    
    # Thêm các dòng này để fix lỗi
    from product.models import Category
    categories = Category.objects.all()
    
    # Hiển thị form đặt hàng
    form = OrderForm()
    context = {
        'shopcart': shopcart, 
        'total': total, 
        'form': form,
        'category': categories,  # Thêm dòng này 
        'categories': categories  # Thêm cả dòng này để đảm bảo
    }
    return render(request, 'Order_Form.html', context)


from django.shortcuts import render

# Create your views here.
