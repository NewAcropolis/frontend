from flask import request, session, current_app

from app import api_client
from app.main import main
from app.main.forms import MissingAddressForm
from app.main.views import render_page
from na_common.delivery import statuses

# ?amt=9.00&cc=GBP&cm=111&st=Completed&tx=14972970SV980564E
@main.route('/order')
def order():
    status = request.args.get('st')
    txn_code = request.args.get('tx')
    linked_txn_code = request.args.get('cm')

    # order = api_client.get_order(txn_code)
    print(statuses.DELIVERY_STATUSES)
    errors = []
    if 'error' in session:
        err = session.pop('error')
        print(err)
        errors.append(err['response']['error']['message'])

    linked_order = None
    # if linked_txn_code:
    #     linked_order = api_client.get_order(linked_txn_code)

    #     if 'error' in session:
    #         err = session.pop('error')
    #         errors.append(err['response']['error']['message'])

    return render_page(
        'views/order.html',
        order=order,
        linked_order=linked_order,
        errors=errors
    )


@main.route('/order/<string:status>/<string:linked_txn_id>', methods=['GET', 'POST'])
@main.route('/order/<string:status>/<string:linked_txn_id>/<string:delivery_zone>/<string:delivery_balance>', methods=['GET', 'POST'])
def complete_order(status, linked_txn_id, delivery_zone='UK', delivery_balance=0):
    missing_address_form = None

    if status == statuses.DELIVERY_MISSING_ADDRESS:
        missing_address_form = MissingAddressForm()
        missing_address_form.setup_country(missing_address_form.data['state'] is None)

    errors = []
    if 'error' in session:
        err = session.pop('error')
        errors.append(err['response']['error']['message'])

    if status == statuses.DELIVERY_MISSING_ADDRESS:
        if missing_address_form.validate_on_submit():
            selected_country = [
                c for c in missing_address_form.country.choices if c[0] == missing_address_form.country.data
            ]
            country_name = selected_country[0][1] if selected_country else 'Unknown'
            data = api_client.update_order_address(
                linked_txn_id,
                missing_address_form.street.data,
                missing_address_form.city.data,
                missing_address_form.state.data,
                missing_address_form.postcode.data,
                missing_address_form.country.data,
                country_name
            )

            return render_page(
                'views/complete_order.html',
                linked_txn_id=linked_txn_id,
                status=data['delivery_status'],
                delivery_zone=data['delivery_zone'],
                delivery_balance=data['delivery_balance'],
                errors=errors
            )
        elif missing_address_form.is_submitted():
            missing_address_form.validate()
            if missing_address_form.errors:
                for field in missing_address_form.errors:
                    for e in missing_address_form.errors[field]:
                        errors.append(e)
    elif status == statuses.DELIVERY_EXTRA:
            return render_page(
                'views/complete_order.html',
                linked_txn_id=linked_txn_id,
                status=statuses.DELIVERY_EXTRA,
                delivery_zone=delivery_zone,
                delivery_balance=delivery_balance,
                errors=errors
            )

    return render_page(
        'views/complete_order.html',
        form=missing_address_form,
        linked_txn_id=linked_txn_id,
        status='missing_address',
        errors=errors
    )


# orders/complete?PayerID=V6ZFRH4FB7MJY&st=Completed&tx=5WW76722PN111923U&cc=GBP&amt=1.50
# orders/complete?old_txn=112233&PayerID=V6ZFRH4FB7MJY&st=Completed&tx=6S3650837T497554X&cc=GBP&amt=1.50
@main.route('/order/end')
def order_end():
    pass
