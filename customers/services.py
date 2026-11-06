
import re

from .models import Customer


def normalize_name(value):
    return " ".join((value or "").strip().split())


def normalize_phone(value):
    raw = (value or "").strip()

    if not raw:
        return ""

    # Remove common display formatting.
    cleaned = re.sub(r"[\s().-]", "", raw)

    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]

    # Normalize UK phone formats.
    if cleaned.startswith("+44"):
        cleaned = "0" + cleaned[3:]

    if not re.fullmatch(r"\+?\d{5,20}", cleaned):
        return ""

    return cleaned


def resolve_customer(*, business, name="", phone=""):
    """
    Resolve a customer for a completed sale.

    - Both empty: no customer.
    - Name only: create a separate customer.
    - Phone only: reuse only an unambiguous phone match.
    - Name + phone: reuse exact matching customer.
    - Conflicting/ambiguous matches: create separate profile.

    Customer matching is limited to the given business.

    The caller must execute this inside transaction.atomic().
    """

    if business is None:
        raise ValueError("Business is required.")

    name = normalize_name(name)
    phone = (phone or "").strip()
    normalized = normalize_phone(phone)

    if not name and not phone:
        return None

    # Invalid phone cannot be reliably matched.
    # Keep its original text, but never use it
    # as an identity key.
    if phone and not normalized:
        return Customer.objects.create(
            business=business,
            name=name,
            phone=phone,
            normalized_phone="",
        )

    if normalized:
        matches = list(
            Customer.objects.select_for_update()
            .filter(
                business=business,
                normalized_phone=normalized,
            )
            .order_by("pk")
        )

        if name:
            exact = [
                customer
                for customer in matches
                if customer.name.casefold() == name.casefold()
            ]

            if len(exact) == 1:
                return exact[0]

            # A single phone-only profile
            # can gain its name.
            if (
                not exact
                and len(matches) == 1
                and not matches[0].name
            ):
                customer = matches[0]
                customer.name = name
                customer.save(
                    update_fields=["name", "updated_at"]
                )
                return customer

        elif len(matches) == 1:
            return matches[0]

        # Ambiguous matches must not
        # be merged automatically.
        return Customer.objects.create(
            business=business,
            name=name,
            phone=phone,
            normalized_phone=normalized,
        )

    # Name-only customers are deliberately
    # not auto-merged.
    return Customer.objects.create(
        business=business,
        name=name,
        phone="",
        normalized_phone="",
    )
