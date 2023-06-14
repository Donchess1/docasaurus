def generate_flw_payment_webhook_html(event, data):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            h1, table {{
                width: 450px;
                margin:0 auto;
                border-collapse: collapse;
            }}

            th, td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}

            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>Payment Details</h1>
        <table>
            <tr>
                <th>Field</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>event</td>
                <td>{event}</td>
            </tr>
            <tr>
                <td>id</td>
                <td>{data["id"]}</td>
            </tr>
            <tr>
                <td>tx_ref</td>
                <td>{data["tx_ref"]}</td>
            </tr>
            <tr>
                <td>flw_ref</td>
                <td>{data["flw_ref"]}</td>
            </tr>
            <tr>
                <td>device_fingerprint</td>
                <td>{data["device_fingerprint"]}</td>
            </tr>
            <tr>
                <td>amount</td>
                <td>{data["amount"]}</td>
            </tr>
            <tr>
                <td>currency</td>
                <td>{data["currency"]}</td>
            </tr>
            <tr>
                <td>charged_amount</td>
                <td>{data["charged_amount"]}</td>
            </tr>
            <tr>
                <td>app_fee</td>
                <td>{data["app_fee"]}</td>
            </tr>
            <tr>
                <td>merchant_fee</td>
                <td>{data["merchant_fee"]}</td>
            </tr>
            <tr>
                <td>processor_response</td>
                <td>{data["processor_response"]}</td>
            </tr>
            <tr>
                <td>auth_model</td>
                <td>{data["auth_model"]}</td>
            </tr>
            <tr>
                <td>ip</td>
                <td>{data["ip"]}</td>
            </tr>
            <tr>
                <td>narration</td>
                <td>{data["narration"]}</td>
            </tr>
            <tr>
                <td>status</td>
                <td>{data["status"]}</td>
            </tr>
            <tr>
                <td>payment_type</td>
                <td>{data["payment_type"]}</td>
            </tr>
            <tr>
                <td>created_at</td>
                <td>{data["created_at"]}</td>
            </tr>
            <tr>
                <td>account_id</td>
                <td>{data["account_id"]}</td>
            </tr>
            <tr>
                <td>customer.id</td>
                <td>{data["customer"]["id"]}</td>
            </tr>
            <tr>
                <td>customer.name</td>
                <td>{data["customer"]["name"]}</td>
            </tr>
            <tr>
                <td>customer.phone_number</td>
                <td>{data["customer"]["phone_number"]}</td>
            </tr>
            <tr>
                <td>customer.email</td>
                <td>{data["customer"]["email"]}</td>
            </tr>
            <tr>
                <td>customer.created_at</td>
                <td>{data["customer"]["created_at"]}</td>
            </tr>
        </table>
    </body>
    </html>
    """
