
document.addEventListener("DOMContentLoaded", function () {

    "use strict";

    // =====================================================
    // 1. MAIN ELEMENTS
    // =====================================================

    const getElement = (id) => document.getElementById(id);

    const supplierModal = getElement("supplier-modal");
    const viewModal = getElement("view-supplier-modal");
    const deleteModal = getElement("delete-supplier-modal");

    const supplierForm = getElement("supplier-form");

    const fields = {
        name: getElement("supplier-name"),
        person: getElement("supplier-person"),
        email: getElement("supplier-email"),
        phone: getElement("supplier-phone"),
        address: getElement("supplier-address"),
        city: getElement("supplier-city"),
        country: getElement("supplier-country"),
        status: getElement("supplier-status"),
        notes: getElement("supplier-notes")
    };

    const modalTitle = getElement("supplier-modal-title");
    const submitText = getElement("supplier-submit-text");

    const addUrl = supplierForm
        ? supplierForm.dataset.addUrl
        : "";

    // =====================================================
    // 2. GENERAL HELPERS
    // =====================================================

    function setValue(element, value) {

        if (element) {
            element.value = value ?? "";
        }

    }

    function setText(id, value) {

        const element = getElement(id);

        if (element) {
            element.textContent = value || "—";
        }

    }

    function openDialog(dialog) {

        if (dialog && !dialog.open) {
            dialog.showModal();
        }

    }

    // =====================================================
    // 3. REUSABLE STATUS DROPDOWN
    // =====================================================

    function setupStatusDropdown(config) {

        const wrapper = getElement(config.wrapper);
        const trigger = getElement(config.trigger);
        const dropdown = getElement(config.dropdown);
        const input = getElement(config.input);
        const label = getElement(config.label);

        if (!wrapper || !trigger || !dropdown || !input || !label) {
            return null;
        }

        const options = Array.from(
            wrapper.querySelectorAll(config.optionClass)
        );

        function close() {

            dropdown.classList.add("hidden");

            trigger.setAttribute(
                "aria-expanded",
                "false"
            );

        }

        function select(value) {

            input.value = value;

            options.forEach(function (option) {

                const selected = option.dataset.value === value;

                option.classList.toggle(
                    "bg-soft-green",
                    selected
                );

                option.classList.toggle(
                    "text-primary",
                    selected
                );

                option.classList.toggle(
                    "font-semibold",
                    selected
                );

                option.setAttribute(
                    "aria-selected",
                    String(selected)
                );

                const check = option.querySelector(".option-check");

                if (check) {
                    check.classList.toggle("hidden", !selected);
                }

                if (selected) {
                    label.textContent = option.dataset.label;
                }

            });

            close();

        }

        trigger.addEventListener("click", function (event) {

            event.preventDefault();

            const isClosed = dropdown.classList.contains(
                "hidden"
            );

            dropdown.classList.toggle(
                "hidden",
                !isClosed
            );

            trigger.setAttribute(
                "aria-expanded",
                String(isClosed)
            );

        });

        options.forEach(function (option) {

            option.addEventListener("click", function () {

                select(option.dataset.value);

                trigger.focus();

            });

        });

        document.addEventListener("click", function (event) {

            if (!wrapper.contains(event.target)) {
                close();
            }

        });

        wrapper.addEventListener("keydown", function (event) {

            if (event.key === "Escape") {

                close();

                trigger.focus();

            }

        });

        const initialOption = options.find(function (option) {

            return option.dataset.value === input.value;

        });

        if (initialOption) {

            select(initialOption.dataset.value);

        } else if (options.length > 0) {

            select(options[0].dataset.value);

        }

        return {
            select: select,
            close: close
        };

    }

    // =====================================================
    // 4. FORM STATUS DROPDOWN
    // =====================================================

    const supplierStatusDropdown = setupStatusDropdown({

        wrapper: "supplier-status-wrapper",
        trigger: "supplier-status-trigger",
        dropdown: "supplier-status-dropdown",
        input: "supplier-status",
        label: "supplier-status-label",
        optionClass: ".supplier-status-option"

    });

    // =====================================================
    // 5. TABLE STATUS FILTER
    // =====================================================

    const filterStatusDropdown = setupStatusDropdown({

        wrapper: "filter-status-wrapper",
        trigger: "filter-status-trigger",
        dropdown: "filter-status-dropdown",
        input: "filter-status-value",
        label: "filter-status-label",
        optionClass: ".filter-status-option"

    });

    // =====================================================
    // 6. LINKED PRODUCTS ELEMENTS
    // =====================================================

    const productsWrapper = getElement(
        "supplier-products-wrapper"
    );

    const productsTrigger = getElement(
        "supplier-products-trigger"
    );

    const productsDropdown = getElement(
        "supplier-products-dropdown"
    );

    const productsSearch = getElement(
        "supplier-products-search"
    );

    const productsSelect = getElement(
        "supplier-products"
    );

    const productsLabel = getElement(
        "supplier-products-label"
    );

    const selectedProductsContainer = getElement(
        "supplier-selected-products"
    );

    const productsEmpty = getElement(
        "supplier-products-empty"
    );

    const productsDone = getElement(
        "supplier-products-done"
    );

    const productOptions = productsWrapper
        ? Array.from(
            productsWrapper.querySelectorAll(
                ".supplier-product-option"
            )
        )
        : [];

    // =====================================================
    // 7. CLOSE LINKED PRODUCTS DROPDOWN
    // =====================================================

    function closeProductsDropdown() {

        if (!productsDropdown || !productsTrigger) {
            return;
        }

        productsDropdown.classList.add("hidden");

        productsTrigger.setAttribute(
            "aria-expanded",
            "false"
        );

    }

    // =====================================================
    // 8. OPEN LINKED PRODUCTS DROPDOWN
    // =====================================================

    function openProductsDropdown() {

        if (!productsDropdown || !productsTrigger) {
            return;
        }

        // Remove hidden so dropdown expands below button.
        productsDropdown.classList.remove("hidden");

        productsTrigger.setAttribute(
            "aria-expanded",
            "true"
        );

        if (productsSearch) {

            productsSearch.value = "";

            filterProductOptions();

            productsSearch.focus();

        }

    }

    // =====================================================
    // 9. SEARCH LINKED PRODUCTS
    // =====================================================

    function filterProductOptions() {

        const query = productsSearch
            ? productsSearch.value.toLowerCase().trim()
            : "";

        let visibleCount = 0;

        productOptions.forEach(function (button) {

            const searchableText = (
                button.dataset.search || ""
            ).toLowerCase();

            const matches = searchableText.includes(query);

            button.classList.toggle(
                "hidden",
                !matches
            );

            if (matches) {
                visibleCount++;
            }

        });

        if (productsEmpty) {

            productsEmpty.classList.toggle(
                "hidden",
                visibleCount > 0 || productOptions.length === 0
            );

        }

    }

    // =====================================================
    // 10. UPDATE SELECTED PRODUCT UI
    // =====================================================

    function updateProductSelectionUI() {

        if (
            !productsSelect ||
            !selectedProductsContainer ||
            !productsLabel
        ) {
            return;
        }

        const selectedOptions = Array.from(
            productsSelect.selectedOptions
        );

        const count = selectedOptions.length;

        productsLabel.textContent = count
            ? count + " Product" + (count === 1 ? "" : "s") + " Selected"
            : "Select products";

        productsLabel.classList.toggle(
            "text-text-muted",
            count === 0
        );

        // Clear existing chips.
        selectedProductsContainer.replaceChildren();

        // Render selected product chips.
        selectedOptions.forEach(function (option) {

            const chip = document.createElement("span");

            chip.className =
                "inline-flex max-w-full items-center gap-2 " +
                "rounded-lg bg-soft-green px-3 py-1.5 " +
                "text-xs font-medium text-primary";

            const chipText = document.createElement("span");

            chipText.className = "max-w-52 truncate";

            chipText.textContent = option.textContent.trim();

            const removeButton = document.createElement("button");

            removeButton.type = "button";

            removeButton.setAttribute(
                "aria-label",
                "Remove " + option.textContent.trim()
            );

            removeButton.className =
                "flex h-4 w-4 items-center justify-center " +
                "rounded-full text-primary hover:bg-primary " +
                "hover:text-white";

            removeButton.textContent = "×";

            removeButton.addEventListener("click", function () {

                option.selected = false;

                updateProductSelectionUI();

            });

            chip.appendChild(chipText);
            chip.appendChild(removeButton);

            selectedProductsContainer.appendChild(chip);

        });

        // Update checkboxes in dropdown.
        productOptions.forEach(function (button) {

            const selected = selectedOptions.some(function (option) {

                return option.value === button.dataset.value;

            });

            button.classList.toggle(
                "bg-soft-green",
                selected
            );

            button.setAttribute(
                "aria-pressed",
                String(selected)
            );

            const checkBox = button.querySelector(
                ".supplier-product-check"
            );

            if (checkBox) {

                checkBox.classList.toggle(
                    "bg-primary",
                    selected
                );

                checkBox.classList.toggle(
                    "border-primary",
                    selected
                );

                const icon = checkBox.querySelector("svg, i");

                if (icon) {

                    icon.classList.toggle(
                        "hidden",
                        !selected
                    );

                }

            }

        });

    }

    // =====================================================
    // 11. SET SELECTED PRODUCTS
    // =====================================================

    function setSelectedProducts(ids) {

        if (!productsSelect) {
            return;
        }

        const selectedIds = new Set(
            ids.map(String)
        );

        Array.from(productsSelect.options).forEach(
            function (option) {

                option.selected = selectedIds.has(
                    option.value
                );

            }
        );

        updateProductSelectionUI();

    }

    // =====================================================
    // 12. LINKED PRODUCTS EVENT LISTENERS
    // =====================================================

    if (
        productsWrapper &&
        productsTrigger &&
        productsDropdown &&
        productsSelect
    ) {

        // Open/close trigger.
        productsTrigger.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                event.stopPropagation();

                const isClosed = productsDropdown.classList.contains(
                    "hidden"
                );

                if (isClosed) {

                    openProductsDropdown();

                } else {

                    closeProductsDropdown();

                }

            }
        );

        // Select/deselect a product.
        productOptions.forEach(function (button) {

            button.addEventListener("click", function (event) {

                event.preventDefault();

                const matchingOption = Array.from(
                    productsSelect.options
                ).find(function (option) {

                    return option.value === button.dataset.value;

                });

                if (!matchingOption) {
                    return;
                }

                matchingOption.selected = !matchingOption.selected;

                updateProductSelectionUI();

            });

        });

        // Search products.
        if (productsSearch) {

            productsSearch.addEventListener(
                "input",
                filterProductOptions
            );

        }

        // Done button.
        if (productsDone) {

            productsDone.addEventListener("click", function () {

                closeProductsDropdown();

                productsTrigger.focus();

            });

        }

        // Outside click.
        document.addEventListener("click", function (event) {

            if (!productsWrapper.contains(event.target)) {

                closeProductsDropdown();

            }

        });

        // Escape key.
        productsWrapper.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Escape") {

                    closeProductsDropdown();

                    productsTrigger.focus();

                }

            }
        );

        // Initial state.
        setSelectedProducts([]);

    }

    // =====================================================
    // 13. GET SUPPLIER PRODUCTS FROM TABLE
    // =====================================================

    function getRowProducts(button) {

        const row = button.closest("tr");

        if (!row) {
            return [];
        }

        return Array.from(
            row.querySelectorAll(
                ".supplier-linked-product"
            )
        ).map(function (element) {

            return {
                id: element.dataset.id,
                name: element.dataset.name || "",
                sku: element.dataset.sku || ""
            };

        });

    }

    // =====================================================
    // 14. OPEN ADD SUPPLIER MODAL
    // =====================================================

    function openAddModal() {

        if (!supplierForm || !supplierModal) {
            return;
        }

        supplierForm.reset();

        supplierForm.action = addUrl;

        if (modalTitle) {
            modalTitle.textContent = "Add New Supplier";
        }

        if (submitText) {
            submitText.textContent = "Save Supplier";
        }

        if (supplierStatusDropdown) {

            supplierStatusDropdown.select("true");

        } else {

            setValue(fields.status, "true");

        }

        setSelectedProducts([]);

        closeProductsDropdown();

        openDialog(supplierModal);

        if (fields.name) {
            fields.name.focus();
        }

    }

    const addButton = getElement("open-add-supplier");

    const emptyAddButton = getElement(
        "empty-add-supplier"
    );

    if (addButton) {

        addButton.addEventListener(
            "click",
            openAddModal
        );

    }

    if (emptyAddButton) {

        emptyAddButton.addEventListener(
            "click",
            openAddModal
        );

    }

    // =====================================================
    // 15. EDIT SUPPLIER MODAL
    // =====================================================

    document.querySelectorAll(
        ".edit-supplier"
    ).forEach(function (button) {

        button.addEventListener("click", function () {

            if (!supplierForm || !supplierModal) {
                return;
            }

            const data = button.dataset;

            supplierForm.reset();

            supplierForm.action = data.url;

            setValue(fields.name, data.name);
            setValue(fields.person, data.person);
            setValue(fields.email, data.email);
            setValue(fields.phone, data.phone);
            setValue(fields.address, data.address);
            setValue(fields.city, data.city);
            setValue(fields.country, data.country);
            setValue(fields.notes, data.notes);

            const statusValue = data.active === "true"
                ? "true"
                : "false";

            if (supplierStatusDropdown) {

                supplierStatusDropdown.select(statusValue);

            } else {

                setValue(fields.status, statusValue);

            }

            const linkedProducts = getRowProducts(button);

            setSelectedProducts(
                linkedProducts.map(function (product) {
                    return product.id;
                })
            );

            closeProductsDropdown();

            if (modalTitle) {
                modalTitle.textContent = "Edit Supplier";
            }

            if (submitText) {
                submitText.textContent = "Save Changes";
            }

            openDialog(supplierModal);

            if (fields.name) {
                fields.name.focus();
            }

        });

    });

    // =====================================================
    // 16. VIEW SUPPLIER MODAL
    // =====================================================

    document.querySelectorAll(
        ".view-supplier"
    ).forEach(function (button) {

        button.addEventListener("click", function () {

            if (!viewModal) {
                return;
            }

            const data = button.dataset;

            setText(
                "view-supplier-name",
                data.name
            );

            setText(
                "view-supplier-person",
                data.person
            );

            setText(
                "view-supplier-email",
                data.email
            );

            setText(
                "view-supplier-phone",
                data.phone
            );

            setText(
                "view-supplier-address",
                data.address
            );

            setText(
                "view-supplier-city",
                data.city
            );

            setText(
                "view-supplier-country",
                data.country
            );

            setText(
                "view-supplier-notes",
                data.notes
            );

            setText(
                "view-supplier-created",
                data.created
            );

            // STATUS BADGE
            const statusBadge = getElement(
                "view-supplier-status"
            );

            const isActive = data.status === "Active";

            if (statusBadge) {

                statusBadge.textContent = isActive
                    ? "Active"
                    : "Inactive";

                statusBadge.className = isActive
                    ? "mt-2 inline-flex rounded-full bg-soft-green px-3 py-1 text-xs font-semibold text-primary"
                    : "mt-2 inline-flex rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600";

            }

            // LINKED PRODUCTS
            const linkedProducts = getRowProducts(button);

            const productsContainer = getElement(
                "view-supplier-products"
            );

            const countElement = getElement(
                "view-supplier-products-count"
            );

            if (countElement) {

                countElement.textContent =
                    linkedProducts.length +
                    " Product" +
                    (linkedProducts.length === 1 ? "" : "s");

            }

            if (productsContainer) {

                productsContainer.replaceChildren();

                if (linkedProducts.length === 0) {

                    const empty = document.createElement("p");

                    empty.className = "text-sm text-text-muted";

                    empty.textContent = "No linked products.";

                    productsContainer.appendChild(empty);

                } else {

                    linkedProducts.forEach(function (product) {

                        const item = document.createElement("div");

                        item.className =
                            "flex items-center gap-3 rounded-xl " +
                            "border border-border-light p-3";

                        const icon = document.createElement("div");

                        icon.className =
                            "flex h-9 w-9 shrink-0 items-center " +
                            "justify-center rounded-lg bg-soft-green " +
                            "text-primary";

                        icon.textContent = "▣";

                        const details = document.createElement("div");

                        details.className = "min-w-0";

                        const name = document.createElement("p");

                        name.className =
                            "truncate text-sm font-semibold text-dark-green";

                        name.textContent = product.name;

                        const sku = document.createElement("p");

                        sku.className =
                            "mt-1 text-xs text-text-muted";

                        sku.textContent = "SKU: " + product.sku;

                        details.appendChild(name);
                        details.appendChild(sku);

                        item.appendChild(icon);
                        item.appendChild(details);

                        productsContainer.appendChild(item);

                    });

                }

            }

            openDialog(viewModal);

        });

    });

    // =====================================================
    // 17. DELETE SUPPLIER MODAL
    // =====================================================

    document.querySelectorAll(
        ".delete-supplier"
    ).forEach(function (button) {

        button.addEventListener("click", function () {

            if (!deleteModal) {
                return;
            }

            setText(
                "delete-supplier-name",
                button.dataset.name
            );

            const deleteForm = getElement(
                "delete-supplier-form"
            );

            if (deleteForm) {
                deleteForm.action = button.dataset.url;
            }

            openDialog(deleteModal);

        });

    });

    // =====================================================
    // 18. CLOSE MODALS
    // =====================================================

    document.querySelectorAll(
        "[data-close-dialog]"
    ).forEach(function (button) {

        button.addEventListener("click", function () {

            const dialog = getElement(
                button.dataset.closeDialog
            );

            if (dialog && dialog.open) {
                dialog.close();
            }

        });

    });

    [
        supplierModal,
        viewModal,
        deleteModal
    ].forEach(function (dialog) {

        if (!dialog) {
            return;
        }

        dialog.addEventListener("click", function (event) {

            if (event.target === dialog) {
                dialog.close();
            }

        });

    });

    // =====================================================
    // 19. RESET FORM ON MODAL CLOSE
    // =====================================================

    if (supplierModal && supplierForm) {

        supplierModal.addEventListener(
            "close",
            function () {

                supplierForm.reset();

                supplierForm.action = addUrl;

                if (modalTitle) {
                    modalTitle.textContent = "Add New Supplier";
                }

                if (submitText) {
                    submitText.textContent = "Save Supplier";
                }

                if (supplierStatusDropdown) {

                    supplierStatusDropdown.select("true");

                }

                setSelectedProducts([]);

                closeProductsDropdown();

            }
        );

    }

    // =====================================================
    // 20. ESCAPE KEY
    // =====================================================

    document.addEventListener("keydown", function (event) {

        if (event.key !== "Escape") {
            return;
        }

        if (supplierStatusDropdown) {
            supplierStatusDropdown.close();
        }

        if (filterStatusDropdown) {
            filterStatusDropdown.close();
        }

        closeProductsDropdown();

    });

});
