from decimal import Decimal
from flask import current_app, request, session
import json
import os

from app import api_client, paypal_client
from app.cache import Cache
from app.main import main
from app.main.forms import DeliveryForm
from app.main.views import render_page


@main.route('/shop', methods=['GET', 'POST'])
def shop():
    books = None
    delivery_form = DeliveryForm()
    books = api_client.get_books()
    if os.environ.get('ENVIRONMENT', 'development') == 'live':
        books = [b for b in books if not b["title"].startswith("TEST")]

    return render_page(
        'views/shop.html',
        books=books,
        delivery_form=delivery_form
    )

@main.route('/shop/cart', methods=['GET', 'POST'])
def cart():
    delivery_form = DeliveryForm()

    if "delivery_address" in session:
        delivery_form.set_delivery_address(session['delivery_address'])

    if delivery_form.validate_on_submit():
        books = api_client.get_books()
        session["delivery_address"] = {
            "first_name": delivery_form.first_name.data,
            "last_name": delivery_form.last_name.data,
            "address1": delivery_form.address1.data,
            "address2": delivery_form.address2.data,
            "city": delivery_form.city.data,
            "zip": delivery_form.zip.data,
        }

        num_items = request.form.get("num_items", "0")
        _cart = {"items": []}
        for i in range(1, int(num_items) + 1):
            id = request.form.get(f"item_number_{i}", "")
            price = request.form.get(f"amount_{i}", "")
            valid = False
            for b in books:
                if b['id'] == id and b['price'] == price:
                    valid = True
            if valid:
                _cart['items'].append(
                    {
                        "product": request.form.get(f"item_name_{i}", ""),
                        "id": f"book-{id}",
                        "price": price,
                        "quantity": request.form.get(f"quantity_{i}", ""),
                    }
                )
        return paypal_client.checkout(delivery_form, _cart)

    return render_page(
        'views/cart.html',
        delivery_form=delivery_form,
        cart=get_cart()
    )


def get_cart():
    books = api_client.get_books()
    items = []
    total = Decimal()
    for c in session.get('cart', []):
        for b in books:
            if b["id"] == c:
                in_cart = False
                for _c in items:
                    if _c["id"] == c:
                        _c["quantity"] += 1
                        in_cart = True
                if not in_cart:
                    item = {
                        "id": c,
                        "quantity": 1,
                        "product": b["title"],
                        "price": b["price"]
                    }

                    items.append(item)
                total += Decimal(b["price"])

    total += Decimal(current_app.config["DELIVERY_UK"])
    return {"items": items, "total": str(total)}


@main.route('/cart/add/<book_id>')
def add_to_cart(book_id):
    cart = session.get('cart', [])
    cart.append(book_id)
    session['cart'] = cart

    return str(len([c for c in cart if c == book_id]))


@main.route('/cart/remove/<book_id>')
def remove_from_cart(book_id):
    cart = session.get('cart', [])
    cart.remove(book_id)
    session['cart'] = cart

    return str(len([c for c in cart if c == book_id]))

@main.route('/cart/empty')
def empty_cart():
    session.pop('cart', [])

    return []


@main.route('/cart/get_account')
def get_account():
    json_obj = json.loads(request.args.get('data')) if request.args.get('data') else None
    if json_obj:
        cached_books = Cache.get_cache('get_books')
        for i in range(1, int(json_obj['item_count']) + 1):
            json_books = json.loads(cached_books['data'])
            item_number = json_obj.get(f'item_number_{i}')[5:]
            matched_book = [book for book in json_books if item_number == book['id']]
            if not matched_book:
                current_app.logger.error(f'Book not found {item_number}, sale aborted')
                return "error"
            elif matched_book:
                price_verify = json_obj.get(f"amount_{i}") == matched_book[0]['price']
                if not price_verify:
                    current_app.logger.error(f'Price is different for {item_number}, sale aborted')
                    return "error"
        return current_app.config.get('PAYPAL_ACCOUNT')
    return "error"
