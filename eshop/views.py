from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, CartItem, Order, OrderItem, ProductReview, Cart
from django.http import Http404
from .forms import ReviewForm, OrderForm
from django.views.decorators.csrf import csrf_protect
#users
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('eshop:login')  # Redirect to login page after registration
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
            return redirect('eshop:home')  # Redirect to home page
    else:
        form = AuthenticationForm()
    return render(request, 'eshop/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('eshop:home')  # Redirect to home page after logout

def home(request):
    categories = Category.objects.all()
    return render(request, 'eshop/home.html', {'categories': categories})

#products functions
def product_list(request):
  products = Product.objects.filter(available=True)  # Only show available products
  context = {'products': products}
  return render(request, 'eshop/product_list.html', context)

def product_detail(request, slug):
  product = get_object_or_404(Product, slug=slug, available=True)  # Only show available products
  context = {'product': product}
  return render(request, 'eshop/product_detail.html', context)

#category functions
def category_list(request):
  categories = Category.objects.all()
  context = {'categories': categories}
  return render(request, 'eshop/category_list.html', context)

def category_detail(request, slug):
  category = get_object_or_404(Category, slug=slug)
  products = Product.objects.filter(category=category, available=True)  # Only show available products
  context = {'category': category, 'products': products}
  return render(request, 'eshop/category_detail.html', context)

#cart functions
@login_required(login_url='eshop:login')  # Redirect to login page if user is not logged in
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
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('eshop:view_cart')  # Redirect to cart view

@login_required
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id, cart__user=request.user) # Ensure user owns the item
        cart_item.delete()
    except CartItem.DoesNotExist:
        raise Http404("Cart item does not exist")
    return redirect('eshop:view_cart')

@login_required
def update_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(pk=cart_item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1)) #Get quantity from form
        if quantity > 0 :
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        raise Http404("Cart item does not exist")
    return redirect('eshop:view_cart')

#order functions
@login_required(login_url='eshop:login')
def create_order(request):
    cart = Cart.objects.get(user=request.user)  # Assuming a user has one cart
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(user=request.user,
                                         first_name=form.cleaned_data['first_name'],
                                         last_name=form.cleaned_data['last_name'],
                                         email=form.cleaned_data['email'],
                                         address=form.cleaned_data['address'],
                                         postal_code=form.cleaned_data['postal_code'],
                                         city=form.cleaned_data['city'])
            for item in cart.items.all():
                OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
            # Clear the cart after successful order creation
            cart.items.all().delete()
            return redirect('eshop:orders_list')  # Use the namespace 'eshop:orders_list'
    else:
        form = OrderForm()
    context = {'form': form, 'cart': cart}
    return render(request, 'eshop/create_order.html', context)

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
  reviews = ProductReview.objects.filter(product=product).order_by('-created')  # Most recent first
  context = {'product': product, 'reviews': reviews}
  return render(request, 'eshop/product_reviews.html', context)

@login_required(login_url='eshop:login')
def add_review(request, product_slug):
  product = get_object_or_404(Product, slug=product_slug)
  if request.method == 'POST':
    form = ReviewForm(request.POST)
    if form.is_valid():
      review = form.save(commit=False)  # Don't save yet
      review.product = product
      review.user = request.user  # Assign current user to review
      review.save()
      return redirect('product_detail', slug=product.slug)  # Redirect back to product detail
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

def about_view(request):
    return render(request, 'eshop/about.html')

def contact_view(request):
    return render(request, 'eshop/contact.html')