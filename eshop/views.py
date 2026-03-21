from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product, CartItem, Order, OrderItem, ProductReview, Cart
from django.http import Http404, JsonResponse
from .forms import ReviewForm, OrderForm
from django.views.decorators.csrf import csrf_protect
#users
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, PaymentForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('eshop:login')  
    else:
        form = UserRegisterForm()
    return render(request, 'eshop/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have been logged in!')
            return redirect('eshop:home')  
    else:
        form = AuthenticationForm()
    return render(request, 'eshop/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('eshop:home')  

def home(request):
    categories = Category.objects.all()
    return render(request, 'eshop/home.html', {'categories': categories})

def product_list(request):
    # Get filter params
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort = request.GET.get('sort', 'name')
    available_only = request.GET.get('available_only') == 'on'

    # Base queryset
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()

    # Keyword search
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Category filter
    if category_id:
        products = products.filter(category_id=category_id)

    # Price range
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    # Sorting
    if sort == 'price':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')
    else:
        products = products.order_by('name')

    # Available filter
    if available_only:
        products = products.filter(available=True)

    # Pagination
    paginator = Paginator(products, 12)  
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'price_min': price_min,
        'price_max': price_max,
        'sort': sort,
        'available_only': available_only,
    }

    return render(request, 'eshop/product_list.html', context)

def product_detail(request, slug):
  product = get_object_or_404(Product, slug=slug, available=True)  
  context = {'product': product}
  return render(request, 'eshop/product_detail.html', context)

#category functions
def category_list(request):
  categories = Category.objects.all()
  context = {'categories': categories}
  return render(request, 'eshop/category_list.html', context)

def category_detail(request, slug):
  category = get_object_or_404(Category, slug=slug)
  products = Product.objects.filter(category=category, available=True)  
  context = {'category': category, 'products': products}
  return render(request, 'eshop/category_detail.html', context)

#cart functions
@login_required(login_url='eshop:login')  
def view_cart(request):
    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    cart_items = cart.items.all()
    context = {'cart_items': cart_items, 'cart': cart}
    return render(request, 'eshop/cart.html', context)

@login_required(login_url='eshop:login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if item_created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()
    return redirect('eshop:view_cart')  

@login_required
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id, cart__user=request.user) 
        cart_item.delete()
    except CartItem.DoesNotExist:
        raise Http404("Cart item does not exist")
    return redirect('eshop:view_cart')

@login_required
def update_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1)) 
        if quantity > 0 :
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        raise Http404("Cart item does not exist")
    return redirect('eshop:view_cart')

@login_required(login_url='eshop:login')
def create_order(request):
    cart = Cart.objects.get(user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                postal_code=form.cleaned_data['postal_code'],
                city=form.cleaned_data['city']
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            # Clear cart
            cart.items.all().delete()

            # Redirect to payment page instead of orders list
            return redirect('eshop:payment_select', order_id=order.id)

    else:
        form = OrderForm()

    context = {
        'form': form,
        'cart': cart
    }

    return render(request, 'eshop/create_order.html', context)

@login_required(login_url='eshop:login')
def payment_select(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.pay_with = f"ORDER-{order.id}"
            payment.status = 'PENDING'  
            payment.save()
            
            messages.success(request, 'Payment details submitted successfully! Please make your payment and await admin confirmation.')
            return redirect('eshop:order_detail', order_id=order.id)

    else:
        form = PaymentForm()

    return render(request, 'eshop/payment_select.html', {
        'form': form,
        'order': order
    })

@login_required(login_url='eshop:login')
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    context = {'orders': orders}
    return render(request, 'eshop/orders_list.html', context)

@login_required
def order_detail(request, order_id):
  order = get_object_or_404(Order, pk=order_id, user=request.user)
  context = {'order': order}
  return render(request, 'eshop/order_detail.html', context)

#product review functions
def product_reviews(request, product_slug):
  product = get_object_or_404(Product, slug=product_slug)
  reviews = ProductReview.objects.filter(product=product).order_by('-created')  
  context = {'product': product, 'reviews': reviews}
  return render(request, 'eshop/product_reviews.html', context)

@login_required(login_url='eshop:login')
def add_review(request, product_slug):
  product = get_object_or_404(Product, slug=product_slug)
  if request.method == 'POST':
    form = ReviewForm(request.POST)
    if form.is_valid():
      review = form.save(commit=False)  
      review.product = product
      review.user = request.user  
      review.save()
      return redirect('product_detail', slug=product.slug)  
  else:
    form = ReviewForm()
  context = {'product': product, 'form': form}
  return render(request, 'eshop/add_review.html', context)

def all_reviews(request):
    reviews = ProductReview.objects.all().order_by('-created')
    return render(request, 'eshop/all_reviews.html', {'reviews': reviews})

def choose_product_for_review(request):
    products = Product.objects.filter(available=True)
    return render(request, 'eshop/choose_product_for_review.html', {'products': products})

def support_view(request):
    return render(request, 'eshop/support.html')

def about_view(request):
    return render(request, 'eshop/about.html')

@csrf_exempt
def contact_view(request):
    if request.method == "POST":
        message = request.POST.get("message", "").lower()
        response = "Sorry, I didn't understand that."

        # Product search
        if "product" in message:
            matching_products = Product.objects.filter(name__icontains=message)

            if matching_products.exists():
                response = "Found matching products:\n"
                for p in matching_products:
                    response += f"• {p.name}: ${p.price}\n"
                response += "Visit products page for more."
            else:
                response = "No matching products found. Browse our catalog!"

        # Reviews
        elif "review" in message:
            recent_reviews = ProductReview.objects.order_by('-created')[:3]
            if recent_reviews.exists():
                response = "Recent customer reviews:\n"
                for r in recent_reviews:
                    response += f"• {r.product.name}: {r.rating}/5\n"
            else:
                response = "No reviews yet. Check individual product pages!"

        # General rules
        elif any(word in message for word in ["hello", "hi", "hey"]):
            response = "Hi! Welcome to E-SHOP support. Ask about products, orders, delivery. Type 'help' for examples."

        elif "delivery" in message or "shipping" in message:
            response = "Delivery: 2-3 business days. Free shipping on orders over $100!"

        elif "payment" in message:
            response = "Payments: Mobile Money, Bank Transfer, Cards. Secure checkout process."

        elif "order" in message:
            response = "Log in to track your orders and view status updates."

        elif "contact" in message:
            response = "Contact: support@eshop.com | 1-800-ESHOP | Use footer links."

        # Help response
        if any(word in message for word in ["help", "examples", "what can you do", "?"]):
            help_text = """I can help with:
• Product prices/info (e.g., "iPhone price")
• Delivery/shipping ("delivery time")
• Orders ("order status") 
• Payments ("payment methods")
• Reviews ("show reviews")
• Type naturally!"""
            return JsonResponse({"response": help_text})

        return JsonResponse({"response": response})

    # GET request → render contact page
    return render(request, 'eshop/contact.html')

