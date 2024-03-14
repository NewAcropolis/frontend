from decimal import Decimal
from flask import current_app, request, session

from app import api_client, paypal_client
from app.main import main
from app.main.forms import DeliveryForm
from app.main.views import render_page


@main.route('/shop', methods=['GET', 'POST'])
def shop():
    books = None
    delivery_form = DeliveryForm()
    if not current_app.config["SHOW_RESOURCE_MAINTENANCE"]:
        books = api_client.get_books()

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
                        "id": id,
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
