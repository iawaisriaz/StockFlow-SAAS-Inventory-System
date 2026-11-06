document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // =====================================================
    // COMMON HELPERS
    // =====================================================

    function refreshIcons() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function validQuantity(value) {
        const number = Number(value);

        if (!Number.isSafeInteger(number) || number <= 0) {
            throw new Error(
                "Quantity must be a positive whole number."
            );
        }

        return number;
    }

    // =====================================================
    // CUSTOM TAILWIND DROPDOWNS
    // =====================================================

    const dropdowns = document.querySelectorAll(
        "[data-return-dropdown]"
    );

    function closeDropdowns() {
        dropdowns.forEach(function (dropdown) {
            const menu = dropdown.querySelector(
                "[data-dropdown-menu]"
            );

            const trigger = dropdown.querySelector(
                "[data-dropdown-trigger]"
            );

            if (menu) {
                menu.classList.add("hidden");
            }

            if (trigger) {
                trigger.setAttribute(
                    "aria-expanded",
                    "false"
                );
            }
        });
    }

    dropdowns.forEach(function (dropdown) {
        const trigger = dropdown.querySelector(
            "[data-dropdown-trigger]"
        );

        const menu = dropdown.querySelector(
            "[data-dropdown-menu]"
        );

        const input = dropdown.querySelector(
            "[data-dropdown-input]"
        );

        const label = dropdown.querySelector(
            "[data-dropdown-label]"
        );

        if (!trigger || !menu || !input || !label) {
            return;
        }

        trigger.addEventListener("click", function () {
            const shouldOpen = menu.classList.contains(
                "hidden"
            );

            closeDropdowns();

            if (shouldOpen) {
                menu.classList.remove("hidden");

                trigger.setAttribute(
                    "aria-expanded",
                    "true"
                );
            }
        });

        menu.querySelectorAll(
            "[data-dropdown-option]"
        ).forEach(function (option) {
            option.addEventListener("click", function () {
                input.value = option.dataset.value;

                label.textContent = (
                    option.textContent.trim()
                );

                closeDropdowns();

                if (input.name === "period") {
                    updateDateVisibility();
                }
            });
        });
    });

    document.addEventListener("click", function (event) {
        if (
            !event.target.closest(
                "[data-return-dropdown]"
            )
        ) {
            closeDropdowns();
        }
    });

    // =====================================================
    // RETURNS LIST DATE FILTERS
    // =====================================================

    const periodInput = document.querySelector(
        '#returns-filter-form input[name="period"]'
    );

    const dateWrapper = document.getElementById(
        "returns-date-wrapper"
    );

    const startWrapper = document.getElementById(
        "returns-range-start-wrapper"
    );

    const endWrapper = document.getElementById(
        "returns-range-end-wrapper"
    );

    const dateInput = document.getElementById(
        "returns-date"
    );

    const startInput = document.getElementById(
        "returns-start-date"
    );

    const endInput = document.getElementById(
        "returns-end-date"
    );

    function updateRangeLimits() {
        if (!startInput || !endInput) {
            return;
        }

        endInput.min = startInput.value || "";

        if (
            startInput.value &&
            endInput.value &&
            endInput.value < startInput.value
        ) {
            endInput.value = startInput.value;
        }
    }

    function updateDateVisibility() {
        if (!periodInput) {
            return;
        }

        const period = periodInput.value;

        const showDate = period === "date";
        const showRange = period === "range";

        if (dateWrapper) {
            dateWrapper.classList.toggle(
                "hidden",
                !showDate
            );
        }

        if (startWrapper) {
            startWrapper.classList.toggle(
                "hidden",
                !showRange
            );
        }

        if (endWrapper) {
            endWrapper.classList.toggle(
                "hidden",
                !showRange
            );
        }

        if (dateInput) {
            dateInput.disabled = !showDate;
            dateInput.required = showDate;
        }

        if (startInput) {
            startInput.disabled = !showRange;
            startInput.required = showRange;
        }

        if (endInput) {
            endInput.disabled = !showRange;
            endInput.required = showRange;
        }

        updateRangeLimits();
    }

    if (startInput) {
        startInput.addEventListener(
            "change",
            updateRangeLimits
        );
    }

    if (endInput) {
        endInput.addEventListener(
            "change",
            updateRangeLimits
        );
    }

    updateDateVisibility();

    // =====================================================
    // DISMISS MESSAGES
    // =====================================================

    document.querySelectorAll(
        "[data-dismiss-message]"
    ).forEach(function (button) {
        button.addEventListener("click", function () {
            const message = button.closest(
                ".rounded-xl"
            );

            if (message) {
                message.remove();
            }
        });
    });

    // =====================================================
    // RETURNS LIST DELETE MODAL
    // =====================================================

    const deleteModal = document.getElementById(
        "delete-return-modal"
    );

    const deleteForm = document.getElementById(
        "delete-return-form"
    );

    const deleteReference = document.getElementById(
        "delete-return-reference"
    );

    function closeDeleteModal() {
        if (!deleteModal) {
            return;
        }

        deleteModal.classList.add("hidden");
        deleteModal.classList.remove("flex");

        deleteModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "overflow-hidden"
        );
    }

    function openDeleteModal(reference, url) {
        if (!deleteModal || !deleteForm) {
            return;
        }

        if (deleteReference) {
            deleteReference.textContent = reference;
        }

        deleteForm.action = url;

        deleteModal.classList.remove("hidden");
        deleteModal.classList.add("flex");

        deleteModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "overflow-hidden"
        );
    }

    document.querySelectorAll(
        "[data-delete-return]"
    ).forEach(function (button) {
        button.addEventListener("click", function () {
            openDeleteModal(
                button.dataset.returnReference,
                button.dataset.deleteUrl
            );
        });
    });

    const closeDeleteButton = document.getElementById(
        "close-delete-return-modal"
    );

    if (closeDeleteButton) {
        closeDeleteButton.addEventListener(
            "click",
            closeDeleteModal
        );
    }

    if (deleteModal) {
        deleteModal.addEventListener(
            "click",
            function (event) {
                if (event.target === deleteModal) {
                    closeDeleteModal();
                }
            }
        );
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDropdowns();
            closeDeleteModal();
        }
    });

    if (deleteForm) {
        deleteForm.addEventListener(
            "submit",
            function () {
                const button = document.getElementById(
                    "confirm-delete-return"
                );

                if (button) {
                    button.disabled = true;
                    button.textContent = "Deleting...";
                }
            }
        );
    }

    // =====================================================
    // NEW RETURN FORM
    // =====================================================

    const form = document.getElementById(
        "new-return-form"
    );

    if (!form) {
        refreshIcons();
        return;
    }

    const itemsInput = document.getElementById(
        "return-items-json"
    );

    const errorBox = document.getElementById(
        "return-form-error"
    );

    const submitButton = document.getElementById(
        "submit-return"
    );

    const receiptRows = document.querySelectorAll(
        ".receipt-item"
    );

    function showError(message) {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;
        errorBox.classList.remove("hidden");

        errorBox.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }

    function clearError() {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";
        errorBox.classList.add("hidden");
    }

    function collectReceiptItems() {
        const items = [];

        receiptRows.forEach(function (row) {
            const checkbox = row.querySelector(
                ".receipt-select"
            );

            if (!checkbox || !checkbox.checked) {
                return;
            }

            const quantityInput = row.querySelector(
                ".receipt-quantity"
            );

            const conditionInput = row.querySelector(
                ".receipt-condition"
            );

            const quantity = validQuantity(
                quantityInput.value
            );

            const remaining = Number(
                row.dataset.remaining
            );

            if (quantity > remaining) {
                throw new Error(
                    "Return quantity exceeds the "
                    + "remaining quantity."
                );
            }

            if (
                !conditionInput ||
                !["resellable", "damaged"].includes(
                    conditionInput.value
                )
            ) {
                throw new Error(
                    "Select a valid product condition."
                );
            }

            items.push({
                sale_item_id: Number(
                    row.dataset.saleItemId
                ),
                quantity: quantity,
                condition: conditionInput.value,
            });
        });

        return items;
    }

    // =====================================================
    // FORM SUBMISSION
    // =====================================================

    form.addEventListener("submit", function (event) {
        clearError();

        try {
            const saleId = form.querySelector(
                'input[name="sale_id"]'
            );

            if (!saleId || !saleId.value) {
                throw new Error(
                    "Find the original sale first."
                );
            }

            const items = collectReceiptItems();

            if (!items.length) {
                throw new Error(
                    "Select at least one product to return."
                );
            }

            itemsInput.value = JSON.stringify(items);

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Processing...";
            }

        } catch (error) {
            event.preventDefault();

            showError(
                error.message || "Invalid return details."
            );
        }
    });

    refreshIcons();
});