document.addEventListener("DOMContentLoaded", () => {

    "use strict";

    // =====================================================
    // HELPERS
    // =====================================================

    const $ = (selector, root = document) =>
        root.querySelector(selector);

    const $$ = (selector, root = document) =>
        Array.from(root.querySelectorAll(selector));

    const byId = (id) =>
        document.getElementById(id);


    function openDialog(dialog) {

        if (dialog && !dialog.open) {
            dialog.showModal();
        }

    }


    function closeDropdown(dropdown) {

        if (!dropdown) return;

        const menu = $(
            "[data-dropdown-menu]",
            dropdown
        );

        const trigger = $(
            "[data-dropdown-trigger]",
            dropdown
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

    }


    function closeAllDropdowns(except = null) {

        $$("[data-custom-dropdown]").forEach(
            (dropdown) => {

                if (dropdown !== except) {
                    closeDropdown(dropdown);
                }

            }
        );

    }


    // =====================================================
    // PURCHASE FORM REFERENCES
    // =====================================================

    const purchaseForm = byId("purchase-form");

    const itemsContainer = byId("purchase-items");

    const supplierInput = byId("purchase-supplier");

    const addItemButton = byId("add-purchase-item");

    const itemTemplate = byId(
        "empty-purchase-item-template"
    );

    const totalForms = byId(
        "id_items-TOTAL_FORMS"
    );

    const maxForms = byId(
        "id_items-MAX_NUM_FORMS"
    );

    const grandTotal = byId(
        "purchase-grand-total"
    );


    // =====================================================
    // DROPDOWN LABEL
    // =====================================================

    function updateDropdown(dropdown) {

        const input = $(
            "[data-dropdown-input]",
            dropdown
        );

        const label = $(
            "[data-dropdown-label]",
            dropdown
        );

        const options = $$(
            "[data-dropdown-option]",
            dropdown
        );

        if (!input || !label) return;

        const selected = options.find(
            (option) =>
                option.dataset.value === input.value
        );

        if (selected) {

            label.textContent =
                selected.textContent.trim();

        } else if (input.name === "status") {

            label.textContent = "All Status";

        } else if (
            input.classList.contains("purchase-product")
        ) {

            label.textContent = "Select Product";

        } else {

            label.textContent = "Select Supplier";

        }

        options.forEach((option) => {

            const active = option === selected;

            option.classList.toggle(
                "bg-soft-green",
                active
            );

            option.classList.toggle(
                "font-semibold",
                active
            );

            option.classList.toggle(
                "text-primary",
                active
            );

        });

    }


    // =====================================================
    // SUPPLIER PRODUCT MATCHING
    // =====================================================

    function productBelongsToSupplier(
        option,
        supplierId
    ) {

        if (!supplierId) {
            return false;
        }

        const supplierIds = (
            option.dataset.suppliers || ""
        )
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        return supplierIds.includes(
            String(supplierId)
        );

    }


    // =====================================================
    // FILTER PRODUCT DROPDOWN
    // IMPORTANT: SUPPLIER + SEARCH BOTH APPLIED
    // =====================================================

    function filterProductDropdown(dropdown) {

        if (!dropdown) return;

        const productInput = $(
            ".purchase-product",
            dropdown
        );

        if (!productInput) return;

        const supplierId = (
            supplierInput?.value || ""
        ).trim();

        const search = $(
            "[data-dropdown-search]",
            dropdown
        );

        const searchTerm = (
            search?.value || ""
        ).trim().toLowerCase();

        const options = $$(
            "[data-dropdown-option]",
            dropdown
        );

        let visibleCount = 0;
        let allowedCount = 0;

        options.forEach((option) => {

            const allowed = productBelongsToSupplier(
                option,
                supplierId
            );

            const matchesSearch = option.textContent
                .toLowerCase()
                .includes(searchTerm);

            const visible = allowed && matchesSearch;

            option.dataset.supplierAllowed = String(
                allowed
            );

            // Apply both HTML and CSS visibility.
            option.hidden = !visible;

            option.style.display = visible
                ? ""
                : "none";

            option.classList.toggle(
                "hidden",
                !visible
            );

            if (allowed) {
                allowedCount++;
            }

            if (visible) {
                visibleCount++;
            }

        });

        const emptyMessage = $(
            "[data-no-products]",
            dropdown
        );

        if (emptyMessage) {

            emptyMessage.classList.toggle(
                "hidden",
                visibleCount > 0
            );

            if (!supplierId) {

                emptyMessage.textContent =
                    "Select a supplier first.";

            } else if (allowedCount === 0) {

                emptyMessage.textContent =
                    "No products linked to this supplier.";

            } else {

                emptyMessage.textContent =
                    "No matching products found.";

            }

        }

        const trigger = $(
            "[data-dropdown-trigger]",
            dropdown
        );

        if (trigger) {

            trigger.disabled = !supplierId;

            trigger.classList.toggle(
                "opacity-60",
                !supplierId
            );

            trigger.classList.toggle(
                "cursor-not-allowed",
                !supplierId
            );

        }

        if (!productInput.value) {

            const label = $(
                "[data-dropdown-label]",
                dropdown
            );

            if (label) {

                label.textContent = !supplierId
                    ? "Select Supplier First"
                    : allowedCount === 0
                        ? "No Linked Products"
                        : "Select Product";

            }

        }

    }


    // =====================================================
    // FILTER ALL PURCHASE ITEMS
    // =====================================================

    function filterProductsForSupplier(
        resetSelections = false
    ) {

        if (!itemsContainer) return;

        const supplierId = (
            supplierInput?.value || ""
        ).trim();

        $$(
            ".purchase-item-row",
            itemsContainer
        ).forEach((row) => {

            const dropdown = $(
                "[data-custom-dropdown]",
                row
            );

            const productInput = $(
                ".purchase-product",
                row
            );

            if (!dropdown || !productInput) {
                return;
            }

            const options = $$(
                "[data-dropdown-option]",
                dropdown
            );

            const selectedOption = options.find(
                (option) =>
                    option.dataset.value ===
                    productInput.value
            );

            const selectedIsAllowed =
                selectedOption &&
                productBelongsToSupplier(
                    selectedOption,
                    supplierId
                );

            if (
                resetSelections ||
                (
                    productInput.value &&
                    !selectedIsAllowed
                )
            ) {

                productInput.value = "";

                const costInput = $(
                    ".purchase-cost",
                    row
                );

                if (costInput) {
                    costInput.value = "";
                }

            }

            const search = $(
                "[data-dropdown-search]",
                dropdown
            );

            if (search) {
                search.value = "";
            }

            updateDropdown(dropdown);

            filterProductDropdown(dropdown);

            closeDropdown(dropdown);

        });

        calculateTotals();

    }


    // =====================================================
    // CUSTOM DROPDOWN INITIALIZATION
    // =====================================================

    function initializeDropdown(dropdown) {

        if (
            dropdown.dataset.initialized === "true"
        ) {
            return;
        }

        const trigger = $(
            "[data-dropdown-trigger]",
            dropdown
        );

        const menu = $(
            "[data-dropdown-menu]",
            dropdown
        );

        const input = $(
            "[data-dropdown-input]",
            dropdown
        );

        const search = $(
            "[data-dropdown-search]",
            dropdown
        );

        if (!trigger || !menu || !input) {
            return;
        }

        dropdown.dataset.initialized = "true";

        // OPEN / CLOSE
        trigger.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                if (trigger.disabled) {
                    return;
                }

                const opening = menu.classList.contains(
                    "hidden"
                );

                closeAllDropdowns(dropdown);

                // Always refresh supplier filtering
                // before opening a product dropdown.
                if (
                    input.classList.contains(
                        "purchase-product"
                    )
                ) {
                    filterProductDropdown(dropdown);
                }

                menu.classList.toggle(
                    "hidden",
                    !opening
                );

                trigger.setAttribute(
                    "aria-expanded",
                    String(opening)
                );

                if (opening && search) {
                    search.focus();
                }

            }
        );

        // SELECT OPTION
        menu.addEventListener(
            "click",
            (event) => {

                const option = event.target.closest(
                    "[data-dropdown-option]"
                );

                if (!option) return;

                if (
                    input.classList.contains(
                        "purchase-product"
                    )
                ) {

                    const supplierId = (
                        supplierInput?.value || ""
                    ).trim();

                    if (
                        !productBelongsToSupplier(
                            option,
                            supplierId
                        )
                    ) {
                        return;
                    }

                    if (
                        option.hidden ||
                        option.style.display === "none"
                    ) {
                        return;
                    }

                }

                const previousValue = input.value;

                input.value =
                    option.dataset.value || "";

                updateDropdown(dropdown);

                closeDropdown(dropdown);

                // PRODUCT COST AUTO FILL
                if (
                    input.classList.contains(
                        "purchase-product"
                    )
                ) {

                    const row = dropdown.closest(
                        ".purchase-item-row"
                    );

                    const costInput = row?.querySelector(
                        ".purchase-cost"
                    );

                    if (costInput) {

                        const cost = Number(
                            option.dataset.cost
                        );

                        costInput.value =
                            Number.isFinite(cost)
                                ? cost.toFixed(2)
                                : "";

                    }

                    calculateTotals();

                }

                // Trigger change for supplier selection.
                if (
                    previousValue !== input.value
                ) {

                    input.dispatchEvent(
                        new Event(
                            "change",
                            { bubbles: true }
                        )
                    );

                }

            }
        );

        // SEARCH
        if (search) {

            search.addEventListener(
                "input",
                () => {

                    if (
                        input.classList.contains(
                            "purchase-product"
                        )
                    ) {

                        filterProductDropdown(
                            dropdown
                        );

                    } else {

                        const term = search.value
                            .trim()
                            .toLowerCase();

                        $$(
                            "[data-dropdown-option]",
                            dropdown
                        ).forEach((option) => {

                            const matches =
                                option.textContent
                                    .toLowerCase()
                                    .includes(term);

                            option.classList.toggle(
                                "hidden",
                                !matches
                            );

                        });

                    }

                }
            );

        }

        updateDropdown(dropdown);

        if (
            input.classList.contains(
                "purchase-product"
            )
        ) {
            filterProductDropdown(dropdown);
        }

    }


    function initializeAllDropdowns(
        root = document
    ) {

        $$(
            "[data-custom-dropdown]",
            root
        ).forEach(initializeDropdown);

    }


    initializeAllDropdowns();


    // =====================================================
    // OUTSIDE CLICK
    // =====================================================

    document.addEventListener(
        "click",
        (event) => {

            if (
                !event.target.closest(
                    "[data-custom-dropdown]"
                )
            ) {

                closeAllDropdowns();

            }

        }
    );


    // =====================================================
    // ESCAPE KEY
    // =====================================================

    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key === "Escape") {
                closeAllDropdowns();
            }

        }
    );


    // =====================================================
    // DIALOG HELPERS
    // =====================================================

    document.addEventListener(
        "click",
        (event) => {

            const button = event.target.closest(
                "[data-close-dialog]"
            );

            if (!button) return;

            const dialog = byId(
                button.dataset.closeDialog
            );

            if (dialog?.open) {
                dialog.close();
            }

        }
    );


    $$("dialog").forEach((dialog) => {

        dialog.addEventListener(
            "click",
            (event) => {

                if (event.target === dialog) {
                    dialog.close();
                }

            }
        );

    });


    // =====================================================
    // PURCHASE DETAIL MODAL
    // =====================================================

    const detailDialog = byId(
        "purchase-detail-dialog"
    );

    const detailContent = byId(
        "purchase-detail-content"
    );


    async function openPurchaseDetail(url) {

        if (
            !detailDialog ||
            !detailContent ||
            !url
        ) {
            return;
        }

        detailContent.innerHTML = `
            <div class="p-10 text-center text-sm text-text-muted">
                Loading purchase details...
            </div>
        `;

        openDialog(detailDialog);

        try {

            const response = await fetch(
                url,
                {
                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest"
                    },
                    credentials: "same-origin"
                }
            );

            if (!response.ok) {
                throw new Error(
                    "Unable to load purchase details."
                );
            }

            detailContent.innerHTML =
                await response.text();

            if (window.lucide) {
                window.lucide.createIcons();
            }

        } catch (error) {

            detailContent.innerHTML = `
                <div class="p-8 text-center text-red-600">
                    Unable to load purchase details.
                </div>
            `;

        }

    }


    document.addEventListener(
        "click",
        (event) => {

            const button = event.target.closest(
                "[data-view-purchase]"
            );

            if (!button) return;

            openPurchaseDetail(
                button.dataset.url
            );

        }
    );


    // =====================================================
    // AUTO OPEN SAVED PURCHASE
    // =====================================================

    const params = new URLSearchParams(
        window.location.search
    );

    const purchaseId = params.get("view");

    if (purchaseId && detailDialog) {

        const viewButton = $$(
            "[data-view-purchase]"
        ).find((button) => {

            try {

                const url = new URL(
                    button.dataset.url,
                    window.location.origin
                );

                return url.pathname.endsWith(
                    `/${purchaseId}/`
                );

            } catch {

                return false;

            }

        });

        if (viewButton) {

            openPurchaseDetail(
                viewButton.dataset.url
            );

        } else {

            openPurchaseDetail(
                `/purchases/${encodeURIComponent(purchaseId)}/`
            );

        }

        params.delete("view");

        const remaining = params.toString();

        window.history.replaceState(
            {},
            "",
            window.location.pathname +
                (
                    remaining
                        ? `?${remaining}`
                        : ""
                )
        );

    }


    // =====================================================
    // CONFIRM RECEIVE / CANCEL
    // =====================================================

    const confirmDialog = byId(
        "purchase-confirm-dialog"
    );

    const confirmForm = byId(
        "purchase-confirm-form"
    );

    const confirmTitle = byId(
        "purchase-confirm-title"
    );

    const confirmMessage = byId(
        "purchase-confirm-message"
    );

    const confirmSubmit = byId(
        "purchase-confirm-submit"
    );


    document.addEventListener(
        "click",
        (event) => {

            const button = event.target.closest(
                "[data-confirm-action]"
            );

            if (
                !button ||
                !confirmDialog ||
                !confirmForm ||
                !confirmTitle ||
                !confirmMessage ||
                !confirmSubmit
            ) {
                return;
            }

            confirmTitle.textContent =
                button.dataset.title ||
                "Confirm Action";

            confirmMessage.textContent =
                button.dataset.message || "";

            confirmForm.action =
                button.dataset.url;

            confirmSubmit.textContent =
                button.dataset.label ||
                "Confirm";

            const danger =
                button.dataset.danger === "true";

            confirmSubmit.classList.toggle(
                "bg-red-600",
                danger
            );

            confirmSubmit.classList.toggle(
                "bg-primary",
                !danger
            );

            confirmSubmit.classList.toggle(
                "hover:bg-red-700",
                danger
            );

            confirmSubmit.classList.toggle(
                "hover:bg-primary-dark",
                !danger
            );

            openDialog(confirmDialog);

        }
    );


    // =====================================================
    // DELETE PURCHASE
    // =====================================================

    const deleteDialog =
        byId("delete-purchase-modal") ||
        byId("delete-purchase-dialog");

    const deleteForm = byId(
        "delete-purchase-form"
    );

    const deleteName = byId(
        "delete-purchase-name"
    );

    const deleteMessage = byId(
        "delete-purchase-message"
    );

    const deleteSubmit = byId(
        "delete-purchase-submit"
    );

    const deleteStockWarning = byId(
        "delete-stock-warning"
    );


    document.addEventListener(
        "click",
        (event) => {

            const button = event.target.closest(
                "[data-delete-purchase]"
            );

            if (!button || !deleteDialog || !deleteForm) {
                return;
            }

            const reference =
                button.dataset.reference ||
                button.dataset.name ||
                "";

            const status =
                button.dataset.status || "";

            deleteForm.action =
                button.dataset.url || "";

            if (deleteName) {
                deleteName.textContent = reference;
            }

            if (deleteMessage) {

                if (status === "received") {

                    deleteMessage.textContent =
                        `Delete ${reference}? ` +
                        "Purchased stock quantities will " +
                        "be reversed automatically.";

                } else {

                    deleteMessage.textContent =
                        `Delete ${reference}? ` +
                        "This action cannot be undone.";

                }

            }

            if (deleteSubmit) {

                deleteSubmit.textContent =
                    status === "received"
                        ? "Delete & Reverse Stock"
                        : "Delete Purchase";

            }

            if (deleteStockWarning) {

                deleteStockWarning.classList.toggle(
                    "hidden",
                    status !== "received"
                );

            }

            openDialog(deleteDialog);

        }
    );


    if (deleteForm) {

        deleteForm.addEventListener(
            "submit",
            () => {

                const submit = deleteForm.querySelector(
                    '[type="submit"]'
                );

                if (submit) {

                    submit.disabled = true;

                    submit.classList.add(
                        "opacity-60",
                        "cursor-not-allowed"
                    );

                }

            }
        );

        deleteDialog?.addEventListener(
            "close",
            () => {

                const submit = deleteForm.querySelector(
                    '[type="submit"]'
                );

                if (submit) {

                    submit.disabled = false;

                    submit.classList.remove(
                        "opacity-60",
                        "cursor-not-allowed"
                    );

                }

            }
        );

    }


    // =====================================================
    // PURCHASE FORM ONLY
    // =====================================================

    if (!purchaseForm) {
        return;
    }

    if (
        !itemsContainer ||
        !addItemButton ||
        !itemTemplate ||
        !totalForms ||
        !grandTotal
    ) {
        return;
    }


    // =====================================================
    // ACTIVE ROWS
    // =====================================================

    function activeRows() {

        return $$(
            ".purchase-item-row",
            itemsContainer
        ).filter((row) => {

            const deleteInput = $(
                'input[name$="-DELETE"]',
                row
            );

            return (
                !row.classList.contains("hidden") &&
                !(
                    deleteInput &&
                    deleteInput.checked
                )
            );

        });

    }


    // =====================================================
    // CALCULATE TOTALS
    // =====================================================

    function calculateTotals() {

        let grandSum = 0;

        activeRows().forEach((row) => {

            const quantity = Number(
                $(".purchase-quantity", row)?.value || 0
            );

            const cost = Number(
                $(".purchase-cost", row)?.value || 0
            );

            const lineTotal =
                Math.max(0, quantity) *
                Math.max(0, cost);

            const totalLabel = $(
                ".purchase-line-total",
                row
            );

            if (totalLabel) {

                totalLabel.textContent =
                    lineTotal.toFixed(2);

            }

            grandSum += lineTotal;

        });

        grandTotal.textContent =
            grandSum.toFixed(2);

    }


    // =====================================================
    // SUPPLIER CHANGE EVENT
    // =====================================================

    if (supplierInput) {

        supplierInput.addEventListener(
            "change",
            () => {

                // Supplier changed:
                // Clear previously selected products.
                filterProductsForSupplier(true);

            }
        );

    }


    // =====================================================
    // UPDATE REMOVE BUTTONS
    // =====================================================

    function updateRemoveButtons() {

        const rows = activeRows();

        const canRemove = rows.length > 1;

        rows.forEach((row) => {

            const button = $(
                ".remove-purchase-item",
                row
            );

            if (!button) return;

            button.classList.toggle(
                "hidden",
                !canRemove
            );

            button.disabled = !canRemove;

        });

    }


    // =====================================================
    // ADD PURCHASE ITEM
    // =====================================================

    function addItem() {

        const index = Number(
            totalForms.value
        );

        if (
            maxForms &&
            index >= Number(maxForms.value)
        ) {
            return;
        }

        const html = itemTemplate.innerHTML.replaceAll(
            "__prefix__",
            String(index)
        );

        const wrapper =
            document.createElement("div");

        wrapper.innerHTML = html.trim();

        const row = wrapper.firstElementChild;

        if (!row) return;

        itemsContainer.appendChild(row);

        totalForms.value = index + 1;

        initializeAllDropdowns(row);

        // Filter newly added row immediately.
        const dropdown = $(
            "[data-custom-dropdown]",
            row
        );

        if (dropdown) {
            filterProductDropdown(dropdown);
        }

        if (window.lucide) {
            window.lucide.createIcons();
        }

        updateRemoveButtons();

        calculateTotals();

    }


    addItemButton.addEventListener(
        "click",
        addItem
    );


    // =====================================================
    // REMOVE PURCHASE ITEM
    // =====================================================

    itemsContainer.addEventListener(
        "click",
        (event) => {

            const button = event.target.closest(
                ".remove-purchase-item"
            );

            if (!button) return;

            if (activeRows().length <= 1) {
                return;
            }

            const row = button.closest(
                ".purchase-item-row"
            );

            if (!row) return;

            const deleteInput = $(
                'input[name$="-DELETE"]',
                row
            );

            if (deleteInput) {

                deleteInput.checked = true;

            }

            row.classList.add("hidden");

            updateRemoveButtons();

            calculateTotals();

        }
    );


    // =====================================================
    // LIVE TOTALS
    // =====================================================

    itemsContainer.addEventListener(
        "input",
        (event) => {

            if (
                event.target.matches(
                    ".purchase-quantity"
                ) ||
                event.target.matches(
                    ".purchase-cost"
                )
            ) {

                calculateTotals();

            }

        }
    );


    // =====================================================
    // FORM VALIDATION
    // =====================================================

    purchaseForm.addEventListener(
        "submit",
        (event) => {

            const supplierId = (
                supplierInput?.value || ""
            ).trim();

            if (!supplierId) {

                event.preventDefault();

                alert(
                    "Please select a supplier."
                );

                return;

            }

            const date = $(
                'input[name="purchase_date"]',
                purchaseForm
            );

            if (
                !date?.value ||
                (
                    date.max &&
                    date.value > date.max
                )
            ) {

                event.preventDefault();

                alert(
                    "Please select a valid purchase date."
                );

                return;

            }

            const rows = activeRows();

            if (rows.length === 0) {

                event.preventDefault();

                alert(
                    "Add at least one product."
                );

                return;

            }

            const selectedProducts = new Set();

            for (const row of rows) {

                const productInput = $(
                    ".purchase-product",
                    row
                );

                const productId =
                    productInput?.value || "";

                const quantityValue = $(
                    ".purchase-quantity",
                    row
                )?.value || "";

                const costValue = $(
                    ".purchase-cost",
                    row
                )?.value ?? "";

                const quantity = Number(
                    quantityValue
                );

                const cost = Number(
                    costValue
                );

                if (
                    !productId ||
                    !quantityValue ||
                    !Number.isInteger(quantity) ||
                    quantity <= 0 ||
                    costValue === "" ||
                    !Number.isFinite(cost) ||
                    cost < 0
                ) {

                    event.preventDefault();

                    alert(
                        "Enter valid product, quantity and unit cost."
                    );

                    return;

                }

                const dropdown = $(
                    "[data-custom-dropdown]",
                    row
                );

                const selectedOption = $$(
                    "[data-dropdown-option]",
                    dropdown
                ).find(
                    (option) =>
                        option.dataset.value === productId
                );

                if (
                    !selectedOption ||
                    !productBelongsToSupplier(
                        selectedOption,
                        supplierId
                    )
                ) {

                    event.preventDefault();

                    alert(
                        "Selected product is not linked to this supplier."
                    );

                    return;

                }

                if (
                    selectedProducts.has(productId)
                ) {

                    event.preventDefault();

                    alert(
                        "The same product cannot be added twice."
                    );

                    return;

                }

                selectedProducts.add(
                    productId
                );

            }

        }
    );


    // =====================================================
    // INITIAL PURCHASE FORM STATE
    // =====================================================

    if (activeRows().length === 0) {
        addItem();
    }

    // Apply supplier filter when page first loads.
    filterProductsForSupplier(false);

    updateRemoveButtons();

    calculateTotals();

});