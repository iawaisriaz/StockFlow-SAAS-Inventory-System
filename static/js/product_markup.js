
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    // ==========================================
    // 1. GET FORM ELEMENTS
    // ==========================================

    const form = document.getElementById("product-form");
    const modal = document.getElementById("product-modal");

    const cost = document.getElementById("product-cost");
    const markup = document.getElementById("product-markup");
    const selling = document.getElementById("product-price");

    const preview = document.getElementById(
        "product-profit-preview"
    );

    if (!form || !modal || !cost || !markup || !selling) {
        return;
    }

    // ==========================================
    // 2. HELPER FUNCTIONS
    // ==========================================

    const numberOf = (element) => {
        return element.value.trim() === ""
            ? null
            : Number(element.value);
    };

    const valid = (value) => {
        return value !== null && Number.isFinite(value);
    };

    // ==========================================
    // 3. PROFIT PREVIEW
    // ==========================================

    function updatePreview() {
        if (!preview) {
            return;
        }

        const c = numberOf(cost);
        const s = numberOf(selling);

        if (
            !valid(c) ||
            !valid(s) ||
            c < 0 ||
            s < 0
        ) {
            preview.textContent =
                "Enter prices to preview profit per unit.";

            return;
        }

        const profit = s - c;

        preview.textContent =
            `Estimated profit per unit: ${
                profit < 0 ? "-" : ""
            }£${Math.abs(profit).toFixed(2)} (before other expenses).`;
    }

    // ==========================================
    // 4. CALCULATE MARKUP FROM SELLING PRICE
    // ==========================================

    function fromSelling() {
        const c = numberOf(cost);
        const s = numberOf(selling);

        if (
            !valid(c) ||
            !valid(s) ||
            c <= 0
        ) {
            markup.value = "";

            markup.placeholder =
                c === 0
                    ? "Undefined at £0 cost"
                    : "e.g. 20";
        } else {
            markup.placeholder = "e.g. 20";

            markup.value = (
                ((s - c) / c) * 100
            ).toFixed(2);
        }

        updatePreview();
    }

    // ==========================================
    // 5. CALCULATE SELLING PRICE FROM MARKUP
    // ==========================================

    function fromMarkup() {
        const c = numberOf(cost);
        const m = numberOf(markup);

        if (
            valid(c) &&
            valid(m) &&
            c >= 0 &&
            m >= -100
        ) {
            selling.value = (
                Math.round(
                    (
                        c * (1 + m / 100) +
                        Number.EPSILON
                    ) * 100
                ) / 100
            ).toFixed(2);
        }

        updatePreview();
    }

    // ==========================================
    // 6. INPUT EVENT LISTENERS
    // ==========================================

    // Markup change -> Selling Price update
    markup.addEventListener("input", fromMarkup);

    // Selling Price change -> Markup update
    selling.addEventListener("input", fromSelling);

    // Cost change -> Recalculate markup
    // Existing Selling Price remains unchanged
    cost.addEventListener("input", fromSelling);

    // ==========================================
    // 7. ADD / EDIT PRODUCT MODAL
    // ==========================================

    document.addEventListener("click", (event) => {
        if (
            event.target.closest(
                "#open-add-product, #empty-add-product, .edit-product"
            )
        ) {
            queueMicrotask(fromSelling);
        }
    });

    // ==========================================
    // 8. RESET FORM
    // ==========================================

    form.addEventListener("reset", () => {
        queueMicrotask(fromSelling);
    });
});
