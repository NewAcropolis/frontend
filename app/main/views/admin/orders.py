from flask import current_app, render_template, session

from app import api_client
from app.main import main
from app.main.forms import OrderForm, OrderListForm


@main.route('/admin/orders', methods=['GET', 'POST'])
@main.route('/admin/orders/<int:year>', methods=['GET', 'POST'])
def admin_orders(year=None):
    form = OrderListForm()

    if form.is_submitted():
        form.setup_order_year()
        orders = api_client.get_orders(form.order_year.data)
    else:
        form.setup_order_year(year)
        orders = api_client.get_orders(year)

    form.populate_order_list_form(orders)

    return render_template(
        'views/admin/orders.html',
        orders=orders,
        form=form
    )


@main.route('/admin/order/<string:txn_code>', methods=['GET', 'POST'])
def admin_order_update(txn_code):
    order = api_client.get_order(txn_code)
    form = OrderForm()
    updated = False
    errors = None

    if form.validate_on_submit():
        response = api_client.update_order(txn_code, form.delivery_sent.data, form.notes.data)
        current_app.logger.info(response)

        if 'error' in session:
            errors = session.pop('error')['message']
        else:
            order = response
            updated = True

    form.populate_order_form(order)

    return render_template(
        'views/admin/order_update.html',
        order=order,
        form=form,
        updated=updated,
        errors=errors
    )
