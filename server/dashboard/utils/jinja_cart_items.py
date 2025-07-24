# server/dashboard/utils/jinja_cart_items.py

from __future__ import annotations

from jinja2 import Template

CART_ITEMS_ROWS = """
{% for item in cart.items %}
<tr data-item-id="{{ item.id }}">
    <td>
        <div>
            <strong>{{ item.product.name }}</strong><br>
            <small class="text-muted">SKU: {{ item.product.sku }}</small>
        </div>
    </td>
    <td class="text-center">
        <input type="number" value="{{ item.quantity }}" min="1" max="999"
               class="form-control form-control-sm text-center item-quantity"
               style="width: 70px;" data-item-id="{{ item.id }}">
    </td>
    <td class="text-end">
        {{ item.price_snapshot|int }} MDL<br>
        <small class="text-muted">{{ item.price_type }}</small>
    </td>
    <td class="text-end">
        <strong class="item-subtotal">{{ (item.quantity * item.price_snapshot)|int }} MDL</strong>
    </td>
    <td class="text-center">
        <button type="button" class="btn btn-sm btn-outline-danger"
                onclick="removeItem({{ item.id }})">
            <i class="bi bi-trash"></i>
        </button>
    </td>
</tr>
{% endfor %}
{% if not cart.items %}
<tr id="emptyCart">
    <td colspan="5" class="text-center text-muted py-3">
        Coșul este gol. Adăugați produse din lista din stânga.
    </td>
</tr>
{% endif %}
"""