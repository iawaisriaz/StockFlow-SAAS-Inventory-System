document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const form = document.getElementById("sale-form");
    if (!form) return;

    const addButton = document.getElementById("add-product");
    const container = document.getElementById("sale-items-container");
    const itemsInput = document.getElementById("sale-items-json");
    const itemsError = document.getElementById("items-error");

    const discountType = document.getElementById("discount-type");
    const discountValue = document.getElementById("discount-value");
    const discountLabel = document.getElementById("discount-value-label");
    const discountHidden = document.getElementById("sale-discount");
    const percentButton = document.getElementById("discount-percent-btn");
    const fixedButton = document.getElementById("discount-fixed-btn");

    const amountReceived = document.getElementById("amount-received");

    const subtotalDisplay = document.getElementById("sale-subtotal");
    const discountDisplay = document.getElementById("discount-display");
    const percentageDisplay = document.getElementById("discount-percentage-display");
    const totalDisplay = document.getElementById("sale-total");
    const changeDisplay = document.getElementById("sale-change");

    const productsElement = document.getElementById("sales-products-data");

    let products = [];

    try {
        const parsed = JSON.parse(productsElement.textContent);
        products = Array.isArray(parsed) ? parsed : JSON.parse(parsed);
    } catch (error) {
        console.error("Could not load sales products:", error);
    }

    const money = value => `£${Number(value || 0).toFixed(2)}`;
    const toNumber = value => Number(value) || 0;

    function showError(message) {
        itemsError.textContent = message;
        itemsError.classList.remove("hidden");
    }

    function clearError() {
        itemsError.textContent = "";
        itemsError.classList.add("hidden");
    }

    function closeDropdowns(except = null) {
        document.querySelectorAll("[data-sale-dropdown]").forEach(dropdown => {
            if (dropdown === except) return;

            dropdown.querySelector("[data-dropdown-menu]")?.classList.add("hidden");
            dropdown.querySelector("[data-dropdown-trigger]")
                ?.setAttribute("aria-expanded", "false");
        });
    }

    function createProductRow() {
        const row = document.createElement("div");
        row.className = "sale-item-row rounded-xl border border-border-light bg-page-bg p-4";

        
        row.innerHTML = `
            <div class="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:items-start">

                <!-- PRODUCT -->
                <div class="lg:col-span-5">
                    <label class="mb-2 block text-sm font-semibold text-dark-green">
                        Product
                    </label>

                    <div class="relative" data-sale-dropdown>
                        <input
                            type="hidden"
                            class="product-id"
                            data-dropdown-input
                        >

                        <button
                            type="button"
                            data-dropdown-trigger
                            aria-expanded="false"
                            class="flex h-12 w-full items-center justify-between gap-3 rounded-xl border border-border-light bg-white px-4 text-left text-sm font-medium text-dark-green transition hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary/10"
                        >
                            <span data-dropdown-label class="min-w-0 flex-1 truncate">
                                Select Product
                            </span>

                            <svg
                                class="h-4 w-4 shrink-0 text-text-muted"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="m6 9 6 6 6-6"
                                />
                            </svg>
                        </button>

                        <!-- CUSTOM DROPDOWN -->
                        <div
                            data-dropdown-menu
                            class="absolute left-0 top-full z-50 mt-2 hidden max-h-64 w-full overflow-y-auto rounded-xl border border-border-light bg-white p-2 shadow-xl"
                        >
                            <input
                                type="search"
                                placeholder="Search products..."
                                class="product-search mb-2 w-full rounded-lg border border-border-light bg-white px-3 py-2.5 text-sm outline-none focus:border-primary"
                            >

                            <div class="product-options space-y-1"></div>
                        </div>
                    </div>

                    <p class="product-stock mt-2 text-xs text-text-muted">
                        Select a product to view stock.
                    </p>
                </div>

                <!-- QUANTITY -->
                <div class="lg:col-span-2">
                    <label class="mb-2 block text-sm font-semibold text-dark-green">
                        Quantity
                    </label>

                    <input
                        type="number"
                        min="1"
                        step="1"
                        value="1"
                        class="product-quantity h-12 w-full rounded-xl border border-border-light bg-white px-4 text-sm text-dark-green outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                    >
                </div>

                <!-- UNIT PRICE -->
                <div class="lg:col-span-2">
                    <label class="mb-2 block text-sm font-semibold text-dark-green">
                        Unit Price
                    </label>

                    <div class="flex h-12 items-center rounded-xl border border-border-light bg-white px-4">
                        <span class="product-price text-sm font-medium text-dark-green">
                            £0.00
                        </span>
                    </div>
                </div>

                <!-- LINE TOTAL -->
                <div class="lg:col-span-2">
                    <label class="mb-2 block text-sm font-semibold text-dark-green">
                        Line Total
                    </label>

                    <div class="flex h-12 items-center rounded-xl border border-border-light bg-white px-4">
                        <span class="product-line-total text-sm font-semibold text-primary">
                            £0.00
                        </span>
                    </div>
                </div>

                <!-- REMOVE BUTTON -->
                <div class="lg:col-span-1 lg:pt-7">
                    <button
                        type="button"
                        title="Remove product"
                        aria-label="Remove product"
                        class="remove-product flex h-12 w-12 items-center justify-center rounded-xl border border-red-200 bg-white text-red-500 transition hover:bg-red-50"
                    >
                        ✕
                    </button>
                </div>

            </div>
        `;


        container.appendChild(row);

        const dropdown = row.querySelector("[data-sale-dropdown]");
        const menu = dropdown.querySelector("[data-dropdown-menu]");
        const trigger = dropdown.querySelector("[data-dropdown-trigger]");
        const label = dropdown.querySelector("[data-dropdown-label]");
        const hidden = row.querySelector(".product-id");
        const search = row.querySelector(".product-search");
        const options = row.querySelector(".product-options");
        const quantity = row.querySelector(".product-quantity");

        function renderOptions(query = "") {
            options.replaceChildren();

            const selected = products.filter(product =>
                String(product.name || "")
                    .toLowerCase()
                    .includes(query.toLowerCase())
            );

            if (!selected.length) {
                const empty = document.createElement("p");
                empty.className = "px-3 py-3 text-sm text-text-muted";
                empty.textContent = "No products found.";
                options.appendChild(empty);
                return;
            }

            selected.forEach(product => {
                const button = document.createElement("button");
                button.type = "button";
                button.className =
                    "flex w-full items-center justify-between gap-3 rounded-lg px-3 py-3 text-left text-sm hover:bg-soft-green";

                const name = document.createElement("span");
                name.textContent = product.name;

                const stock = document.createElement("span");
                stock.className = "shrink-0 text-xs text-text-muted";
                stock.textContent = `Stock: ${product.stock}`;

                button.append(name, stock);

                button.addEventListener("click", () => {
                    hidden.value = product.id;
                    label.textContent = product.name;
                    menu.classList.add("hidden");
                    trigger.setAttribute("aria-expanded", "false");
                    updateRow(row);
                });

                options.appendChild(button);
            });
        }

        trigger.addEventListener("click", () => {
            const opening = menu.classList.contains("hidden");
            closeDropdowns();

            if (opening) {
                menu.classList.remove("hidden");
                trigger.setAttribute("aria-expanded", "true");
                search.focus();
            }
        });

        search.addEventListener("input", () => renderOptions(search.value));
        quantity.addEventListener("input", () => updateRow(row));

        row.querySelector(".remove-product").addEventListener("click", () => {
            row.remove();
            updateSummary();
        });

        renderOptions();
        updateSummary();
    }

    function getProduct(id) {
        return products.find(product => String(product.id) === String(id));
    }

    function updateRow(row) {
        const id = row.querySelector(".product-id").value;
        const product = getProduct(id);
        const quantity = toNumber(row.querySelector(".product-quantity").value);

        const stockText = row.querySelector(".product-stock");
        const priceText = row.querySelector(".product-price");
        const totalText = row.querySelector(".product-line-total");

        if (!product) {
            stockText.textContent = "Select a product to view stock.";
            priceText.textContent = money(0);
            totalText.textContent = money(0);
            updateSummary();
            return;
        }

        const price = toNumber(product.price);
        const stock = toNumber(product.stock);

        stockText.textContent = `Available Stock: ${stock}`;
        priceText.textContent = money(price);
        totalText.textContent = money(price * quantity);

        stockText.classList.toggle("text-red-600", quantity > stock);

        updateSummary();
    }

    function calculateSubtotal() {
        let subtotal = 0;

        container.querySelectorAll(".sale-item-row").forEach(row => {
            const product = getProduct(row.querySelector(".product-id").value);
            const quantity = toNumber(row.querySelector(".product-quantity").value);

            if (product && Number.isInteger(quantity) && quantity > 0) {
                subtotal += toNumber(product.price) * quantity;
            }
        });

        return Math.round((subtotal + Number.EPSILON) * 100) / 100;
    }

    function updateSummary() {
        const subtotal = calculateSubtotal();
        const value = Math.max(0, toNumber(discountValue.value));

        let discount = 0;

        if (discountType.value === "percent") {
            discount = subtotal * Math.min(value, 100) / 100;
        } else {
            discount = Math.min(value, subtotal);
        }

        discount = Math.round((discount + Number.EPSILON) * 100) / 100;

        const percentage = subtotal > 0
            ? (discount / subtotal) * 100
            : 0;

        const total = Math.max(0, subtotal - discount);
        const received = Math.max(0, toNumber(amountReceived.value));
        const change = Math.max(0, received - total);

        subtotalDisplay.textContent = money(subtotal);
        discountDisplay.textContent = money(discount);
        percentageDisplay.textContent = `${percentage.toFixed(2)}%`;
        totalDisplay.textContent = money(total);
        changeDisplay.textContent = money(change);

        discountHidden.value = discount.toFixed(2);
    }

    function setDiscountType(type) {
        discountType.value = type;
        discountValue.value = "0";

        const percent = type === "percent";

        discountLabel.textContent = percent
            ? "Discount Percentage (%)"
            : "Discount Amount (£)";

        discountValue.max = percent ? "100" : "";

        percentButton.className = percent
            ? "rounded-xl border border-primary bg-soft-green px-4 py-3 text-sm font-semibold text-primary"
            : "rounded-xl border border-border-light bg-white px-4 py-3 text-sm font-semibold text-dark-green";

        fixedButton.className = !percent
            ? "rounded-xl border border-primary bg-soft-green px-4 py-3 text-sm font-semibold text-primary"
            : "rounded-xl border border-border-light bg-white px-4 py-3 text-sm font-semibold text-dark-green";

        updateSummary();
    }

    function setupPaymentDropdown() {
        const dropdown = document.querySelector("[data-sale-dropdown]:has(#payment-method)");
        if (!dropdown) return;

        const trigger = dropdown.querySelector("[data-dropdown-trigger]");
        const menu = dropdown.querySelector("[data-dropdown-menu]");
        const label = dropdown.querySelector("[data-dropdown-label]");
        const input = dropdown.querySelector("[data-dropdown-input]");

        const labels = {
            cash: "Cash",
            card: "Card",
            bank: "Bank Transfer"
        };

        label.textContent = labels[input.value] || "Cash";

        trigger.addEventListener("click", () => {
            const opening = menu.classList.contains("hidden");
            closeDropdowns();

            if (opening) {
                menu.classList.remove("hidden");
                trigger.setAttribute("aria-expanded", "true");
            }
        });

        menu.querySelectorAll("[data-value]").forEach(option => {
            option.addEventListener("click", () => {
                input.value = option.dataset.value;
                label.textContent = labels[input.value];
                closeDropdowns();
            });
        });
    }

    document.addEventListener("click", event => {
        if (!event.target.closest("[data-sale-dropdown]")) {
            closeDropdowns();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeDropdowns();
    });

    addButton.addEventListener("click", createProductRow);

    percentButton.addEventListener("click", () => setDiscountType("percent"));
    fixedButton.addEventListener("click", () => setDiscountType("fixed"));

    discountValue.addEventListener("input", updateSummary);
    amountReceived.addEventListener("input", updateSummary);

    form.addEventListener("submit", event => {
        clearError();

        const rows = [...container.querySelectorAll(".sale-item-row")];

        if (!rows.length) {
            event.preventDefault();
            showError("Please add at least one product.");
            return;
        }

        const items = [];
        const quantities = new Map();

        for (const row of rows) {
            const productId = row.querySelector(".product-id").value;
            const quantity = Number(row.querySelector(".product-quantity").value);
            const product = getProduct(productId);

            if (!product || !Number.isInteger(quantity) || quantity <= 0) {
                event.preventDefault();
                showError("Please select a valid product and quantity.");
                return;
            }

            quantities.set(
                String(productId),
                (quantities.get(String(productId)) || 0) + quantity
            );

            items.push({
                product_id: Number(productId),
                quantity: quantity
            });
        }

        for (const [id, quantity] of quantities) {
            const product = getProduct(id);

            if (quantity > Number(product.stock)) {
                event.preventDefault();
                showError(`Insufficient stock for ${product.name}. Available: ${product.stock}`);
                return;
            }
        }

        const subtotal = calculateSubtotal();
        const rawDiscount = Number(discountValue.value);

        if (
            !Number.isFinite(rawDiscount) ||
            rawDiscount < 0 ||
            (discountType.value === "percent" && rawDiscount > 100) ||
            (discountType.value === "fixed" && rawDiscount > subtotal)
        ) {
            event.preventDefault();
            showError("Please enter a valid discount.");
            return;
        }

        updateSummary();

        const total = subtotal - Number(discountHidden.value);
        const received = Number(amountReceived.value);

        if (!Number.isFinite(received) || received < total) {
            event.preventDefault();
            showError("Amount received must be at least the grand total.");
            return;
        }

        itemsInput.value = JSON.stringify(items);
    });

    setupPaymentDropdown();
    setDiscountType("percent");
    createProductRow();
});


