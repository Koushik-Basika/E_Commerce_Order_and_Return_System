from .helpers import money, format_date

def generate_invoice_html(order: dict, items: list, user: dict) -> str:
    """Generates a clean, professional, printable HTML invoice for an order."""
    order_num = order.get("order_number") or f"ORD-{order.get('id', 1000):05d}"
    order_date = format_date(order.get("created_at", ""))
    cust_name = user.get("name", "Customer")
    cust_email = user.get("email", "")
    cust_phone = user.get("phone", "")
    address = order.get("shipping_address") or order.get("address", "N/A")
    payment_method = order.get("payment_method", "Prepaid")
    payment_status = order.get("payment_status", "Paid")

    subtotal = float(order.get("subtotal", 0) or order.get("total", 0) + float(order.get("discount", 0)))
    discount = float(order.get("discount", 0))
    coupon = order.get("coupon_code", "")
    delivery_fee = float(order.get("delivery_fee", 0))
    tax_amount = float(order.get("tax_amount", 0))
    total = float(order.get("total", 0))

    items_rows = ""
    for idx, item in enumerate(items, start=1):
        pname = item.get("name") or item.get("product_name", f"Product #{item.get('product_id')}")
        brand = item.get("brand", "")
        qty = item.get("quantity", 1)
        price = float(item.get("price", 0))
        row_total = price * qty
        items_rows += f"""
        <tr>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:center;">{idx}</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0;">
                <div style="font-weight:600; color:#1e293b;">{pname}</div>
                <div style="font-size:12px; color:#64748b;">Brand: {brand}</div>
            </td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:center;">{qty}</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">{money(price)}</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right; font-weight:600;">{money(row_total)}</td>
        </tr>
        """

    coupon_line = f"""<tr>
        <td colspan="4" style="text-align:right; padding:6px 10px; color:#16a34a;">Coupon Savings ({coupon}):</td>
        <td style="text-align:right; padding:6px 10px; color:#16a34a; font-weight:600;">- {money(discount)}</td>
    </tr>""" if discount > 0 else ""

    html = f"""
    <div id="invoice-printable" style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:32px; max-width:850px; margin:20px auto; box-shadow:0 10px 25px -5px rgba(0,0,0,0.05); color:#1e293b;">
        <!-- Header -->
        <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #2563eb; padding-bottom:20px; margin-bottom:24px;">
            <div>
                <h1 style="margin:0; font-size:24px; font-weight:800; color:#1e3a8a; letter-spacing:-0.5px;">E-Commerce Order and Return System</h1>
                <p style="margin:4px 0 0; font-size:13px; color:#64748b;">Tax Invoice / Purchase Receipt</p>
                <p style="margin:2px 0 0; font-size:12px; color:#94a3b8;">GSTIN: 29AAAAA0000A1Z5 | CIN: U72200KA2026PTC012345</p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px; font-weight:800; color:#2563eb;">INVOICE</div>
                <div style="font-size:13px; font-weight:600; color:#1e293b; margin-top:4px;">{order_num}</div>
                <div style="font-size:12px; color:#64748b;">Date: {order_date}</div>
            </div>
        </div>

        <!-- Billed to & Shipped to -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:28px;">
            <div style="background:#f8fafc; padding:16px; border-radius:8px; border:1px solid #e2e8f0;">
                <div style="font-size:12px; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:6px;">Billed To</div>
                <div style="font-weight:700; color:#0f172a; font-size:15px;">{cust_name}</div>
                <div style="font-size:13px; color:#475569; margin-top:2px;">Email: {cust_email}</div>
                <div style="font-size:13px; color:#475569;">Phone: {cust_phone or 'N/A'}</div>
            </div>
            <div style="background:#f8fafc; padding:16px; border-radius:8px; border:1px solid #e2e8f0;">
                <div style="font-size:12px; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:6px;">Shipping & Payment</div>
                <div style="font-size:13px; color:#334155; line-height:1.4;"><strong>Address:</strong> {address}</div>
                <div style="font-size:13px; color:#334155; margin-top:4px;"><strong>Payment Method:</strong> {payment_method} ({payment_status})</div>
                <div style="font-size:13px; color:#334155;"><strong>Order Status:</strong> {order.get('status', 'Placed')}</div>
            </div>
        </div>

        <!-- Items Table -->
        <table style="width:100%; border-collapse:collapse; margin-bottom:24px; font-size:13px;">
            <thead>
                <tr style="background:#f1f5f9; color:#475569; font-weight:700;">
                    <th style="padding:10px; border-bottom:2px solid #cbd5e1; text-align:center; width:40px;">#</th>
                    <th style="padding:10px; border-bottom:2px solid #cbd5e1; text-align:left;">Item & Description</th>
                    <th style="padding:10px; border-bottom:2px solid #cbd5e1; text-align:center; width:60px;">Qty</th>
                    <th style="padding:10px; border-bottom:2px solid #cbd5e1; text-align:right; width:110px;">Unit Price</th>
                    <th style="padding:10px; border-bottom:2px solid #cbd5e1; text-align:right; width:110px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="4" style="text-align:right; padding:10px 10px 4px; font-weight:600; color:#475569;">Subtotal:</td>
                    <td style="text-align:right; padding:10px 10px 4px; font-weight:600; color:#1e293b;">{money(subtotal)}</td>
                </tr>
                {coupon_line}
                <tr>
                    <td colspan="4" style="text-align:right; padding:4px 10px; color:#64748b;">GST (18% included):</td>
                    <td style="text-align:right; padding:4px 10px; color:#475569;">{money(tax_amount if tax_amount > 0 else (total * 0.18 / 1.18))}</td>
                </tr>
                <tr>
                    <td colspan="4" style="text-align:right; padding:4px 10px; color:#64748b;">Shipping & Handling:</td>
                    <td style="text-align:right; padding:4px 10px; color:#475569;">{money(delivery_fee) if delivery_fee > 0 else 'FREE'}</td>
                </tr>
                <tr style="border-top:2px solid #0f172a;">
                    <td colspan="4" style="text-align:right; padding:12px 10px; font-size:16px; font-weight:800; color:#0f172a;">Grand Total:</td>
                    <td style="text-align:right; padding:12px 10px; font-size:16px; font-weight:800; color:#2563eb;">{money(total)}</td>
                </tr>
            </tfoot>
        </table>

        <!-- Footer terms -->
        <div style="border-top:1px dashed #cbd5e1; padding-top:16px; font-size:12px; color:#64748b; line-height:1.5;">
            <p style="margin:0 0 4px;"><strong>Return & Refund Policy:</strong> Items eligible for return can be requested within 7 days of delivery through the customer portal under <em>Returns & Refunds</em>.</p>
            <p style="margin:0;">This is a computer-generated tax invoice and requires no physical signature. Thank you for shopping with <strong>E-Commerce Order and Return System</strong>.</p>
        </div>
    </div>
    """
    return html
