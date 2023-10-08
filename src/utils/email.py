def validate_email_body(value):
    return (
        [True, "Invalid email address. Cannot contain '+'"]
        if "+" in value
        else [False, None]
    )
