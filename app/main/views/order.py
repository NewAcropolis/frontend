from flask import request, session, current_app  # noqa

from app import api_client
from app.main import main
from app.main.forms import MissingAddressForm
from app.main.views import render_page
from na_common.delivery import statuses


@main.route('/order/end')
def order_end():
    current_app.logger.info("Order end: %r" % request.args)
    status = request.args.get('st')
    txn_code = request.args.get('tx')

    return render_page(
        'views/order_end.html',
        status=status,
        txn_code=txn_code
    )


@main.route(
    '/order/<string:status>/<string:linked_txn_id>/<string:delivery_zone>/<string:delivery_balance>',
    methods=['GET', 'POST']
)
def complete_order(status, linked_txn_id, delivery_zone='UK', delivery_balance=0):
    missing_address_form = None

    errors = []
    if 'error' in session:
        err = session.pop('error')
        errors.append(err['response']['error']['message'])

    if status == statuses.DELIVERY_MISSING_ADDRESS:
        missing_address_form = MissingAddressForm()
        missing_address_form.setup_country(missing_address_form.data['state'] is None)

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
