document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // PRODUCT PREVIOUS COST - VIEW MODAL
    // ==========================================

    const viewButtons = document.querySelectorAll(
        ".view-product"
    );

    const previousCostElement = document.getElementById(
        "view-previous-cost"
    );

    if (!previousCostElement) {
        return;
    }

    function formatPrice(value) {

        if (
            value === undefined ||
            value === null ||
            value === ""
        ) {
            return "—";
        }

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "—";
        }

        return "£" + number.toFixed(2);
    }

    viewButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const previousCost = this.dataset.previousCost;

            previousCostElement.textContent = formatPrice(
                previousCost
            );

        });

    });

});