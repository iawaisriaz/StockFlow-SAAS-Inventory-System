
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // =====================================================
    // 1. ELEMENT HELPERS
    // =====================================================

    const getElement = (id) => document.getElementById(id);

    const productModal = getElement("product-modal");
    const viewModal = getElement("view-product-modal");
    const deleteModal = getElement("delete-product-modal");

    const productForm = getElement("product-form");

    const nameInput = getElement("product-name");
    const skuInput = getElement("product-sku");
    const categoryInput = getElement("product-category");
    const descriptionInput = getElement("product-description");

    const costInput = getElement("product-cost");
    const priceInput = getElement("product-price");

    const stockInput = getElement("product-stock");
    const alertInput = getElement("product-alert");

    const stockLabel = getElement("product-stock-label");
    const stockHelp = getElement("product-stock-help");

    const imageInput = getElement("product-image");

    // =====================================================
    // 2. GENERAL HELPERS
    // =====================================================

    function setText(id, value) {
        const element = getElement(id);

        if (element) {
            element.textContent = value ?? "";
        }
    }

    function setValue(element, value) {
        if (element) {
            element.value = value ?? "";
        }
    }

    function showDialog(dialog) {
        if (!dialog) {
            return;
        }

        if (!dialog.open) {
            dialog.showModal();
        }
    }

    function formatPrice(value) {
        if (
            value === undefined ||
            value === null ||
            String(value).trim() === ""
        ) {
            return "—";
        }

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "—";
        }

        return "£" + number.toFixed(2);
    }

    // =====================================================
    // 3. REUSABLE CUSTOM DROPDOWN
    // =====================================================

    function setupDropdown(config) {
        const wrapper = getElement(config.wrapper);
        const trigger = getElement(config.trigger);
        const dropdown = getElement(config.dropdown);
        const hiddenInput = getElement(config.hidden);
        const label = getElement(config.label);

        if (
            !wrapper ||
            !trigger ||
            !dropdown ||
            !hiddenInput ||
            !label
        ) {
            console.warn(
                "Dropdown elements missing:",
                config.wrapper
            );
            return null;
        }

        const options = Array.from(
            wrapper.querySelectorAll(config.optionClass)
        );

        const searchInput = config.search
            ? getElement(config.search)
            : null;

        const emptyMessage = config.empty
            ? getElement(config.empty)
            : null;

        // ---------------------------------------------
        // CLOSE DROPDOWN
        // ---------------------------------------------

        function close() {
            dropdown.classList.add("hidden");

            trigger.setAttribute(
                "aria-expanded",
                "false"
            );
        }

        // ---------------------------------------------
        // OPEN DROPDOWN
        // ---------------------------------------------

        function open() {
            dropdown.classList.remove("hidden");

            trigger.setAttribute(
                "aria-expanded",
                "true"
            );

            if (searchInput) {
                resetSearch();
                searchInput.focus();
            }
        }

        // ---------------------------------------------
        // RESET SEARCH
        // ---------------------------------------------

        function resetSearch() {
            if (searchInput) {
                searchInput.value = "";
            }

            options.forEach(function (option) {
                option.classList.remove("hidden");
            });

            if (emptyMessage) {
                emptyMessage.classList.add("hidden");
            }
        }

        // ---------------------------------------------
        // SELECTED OPTION STYLING
        // ---------------------------------------------

        function updateSelectedStyle() {
            options.forEach(function (option) {
                const isSelected =
                    option.dataset.value === hiddenInput.value;

                option.classList.toggle(
                    "bg-soft-green",
                    isSelected
                );

                option.classList.toggle(
                    "text-primary",
                    isSelected
                );

                option.classList.toggle(
                    "font-semibold",
                    isSelected
                );

                option.setAttribute(
                    "aria-selected",
                    String(isSelected)
                );

                const checkIcon = option.querySelector(
                    ".option-check"
                );

                if (checkIcon) {
                    checkIcon.classList.toggle(
                        "hidden",
                        !isSelected
                    );
                }
            });
        }

        // ---------------------------------------------
        // SELECT OPTION
        // ---------------------------------------------

        function select(value, text) {
            hiddenInput.value = value ?? "";
            label.textContent = text ?? "";

            updateSelectedStyle();
            close();
            resetSearch();
        }

        // ---------------------------------------------
        // TOGGLE DROPDOWN
        // ---------------------------------------------

        trigger.addEventListener("click", function (event) {
            event.preventDefault();

            const isClosed = dropdown.classList.contains(
                "hidden"
            );

            if (isClosed) {
                open();
            } else {
                close();
            }
        });

        // ---------------------------------------------
        // OPTION CLICK
        // ---------------------------------------------

        options.forEach(function (option) {
            option.addEventListener("click", function (event) {
                event.preventDefault();

                select(
                    option.dataset.value,
                    option.dataset.label
                );
            });
        });

        // ---------------------------------------------
        // SEARCH OPTIONS
        // ---------------------------------------------

        if (searchInput) {
            searchInput.addEventListener(
                "input",
                function () {
                    const query = searchInput.value
                        .toLowerCase()
                        .trim();

                    let visibleCount = 0;

                    options.forEach(function (option) {
                        const optionLabel = (
                            option.dataset.label || ""
                        ).toLowerCase();

                        const matches = optionLabel.includes(
                            query
                        );

                        option.classList.toggle(
                            "hidden",
                            !matches
                        );

                        if (matches) {
                            visibleCount++;
                        }
                    });

                    if (emptyMessage) {
                        emptyMessage.classList.toggle(
                            "hidden",
                            visibleCount > 0
                        );
                    }
                }
            );
        }

        // ---------------------------------------------
        // CLOSE ON OUTSIDE CLICK
        // ---------------------------------------------

        document.addEventListener("click", function (event) {
            if (!wrapper.contains(event.target)) {
                close();
            }
        });

        // ---------------------------------------------
        // CLOSE WITH ESCAPE
        // ---------------------------------------------

        wrapper.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                close();
                trigger.focus();
            }
        });

        // ---------------------------------------------
        // RESTORE SELECTED OPTION
        // ---------------------------------------------

        const initialOption = options.find(function (option) {
            return option.dataset.value === hiddenInput.value;
        });

        if (initialOption) {
            select(
                initialOption.dataset.value,
                initialOption.dataset.label
            );
        } else if (options.length > 0) {
            select(
                options[0].dataset.value,
                options[0].dataset.label
            );
        }

        return {
            open: open,
            close: close,
            select: select
        };
    }

    // =====================================================
    // 4. CATEGORY FILTER
    // =====================================================

    setupDropdown({
        wrapper: "filter-category-wrapper",
        trigger: "filter-category-trigger",
        dropdown: "filter-category-dropdown",
        hidden: "filter-category-value",
        label: "filter-category-label",
        search: "filter-category-search",
        empty: "filter-category-empty",
        optionClass: ".filter-category-option"
    });

    // =====================================================
    // 5. STOCK FILTER
    // =====================================================

    setupDropdown({
        wrapper: "filter-stock-wrapper",
        trigger: "filter-stock-trigger",
        dropdown: "filter-stock-dropdown",
        hidden: "filter-stock-value",
        label: "filter-stock-label",
        optionClass: ".filter-stock-option"
    });

    // =====================================================
    // 6. COST REVIEW FILTER
    // =====================================================

    setupDropdown({
        wrapper: "filter-review-wrapper",
        trigger: "filter-review-trigger",
        dropdown: "filter-review-dropdown",
        hidden: "filter-review-value",
        label: "filter-review-label",
        optionClass: ".filter-review-option"
    });

    // =====================================================
    // 7. PRODUCT FORM CATEGORY DROPDOWN
    // =====================================================

    const productCategoryDropdown = setupDropdown({
        wrapper: "product-category-wrapper",
        trigger: "product-category-trigger",
        dropdown: "product-category-dropdown",
        hidden: "product-category",
        label: "product-category-label",
        search: "product-category-search",
        empty: "product-category-empty",
        optionClass: ".product-category-option"
    });

    // =====================================================
    // 8. IMAGE HANDLING
    // =====================================================

    const currentImageWrapper = getElement(
        "current-image-wrapper"
    );

    const currentImage = getElement(
        "current-product-image"
    );

    const removeImageButton = getElement(
        "remove-product-image"
    );

    const removeImageFlag = getElement(
        "remove-image-flag"
    );

    const imageRemovalMessage = getElement(
        "image-removal-message"
    );

    function resetImageState() {
        setValue(removeImageFlag, "0");

        if (imageInput) {
            imageInput.value = "";
        }

        if (currentImageWrapper) {
            currentImageWrapper.classList.add("hidden");
        }

        if (imageRemovalMessage) {
            imageRemovalMessage.classList.add("hidden");
        }

        if (currentImage) {
            currentImage.removeAttribute("src");
        }
    }

    // =====================================================
    // 9. ADD PRODUCT MODAL
    // =====================================================

    function openAddModal() {
        if (!productForm || !productModal) {
            return;
        }

        productForm.reset();

        const addUrl = productForm.dataset.addUrl;

        if (addUrl) {
            productForm.action = addUrl;
        }

        if (productCategoryDropdown) {
            productCategoryDropdown.select(
                "",
                "Select Category"
            );
        }

        const categoryError = getElement(
            "product-category-error"
        );

        if (categoryError) {
            categoryError.classList.add("hidden");
        }

        setText(
            "product-modal-title",
            "Add New Product"
        );

        setText(
            "product-submit-text",
            "Save Product"
        );

        if (stockLabel) {
            stockLabel.textContent = "Opening Stock";
        }

        if (stockHelp) {
            stockHelp.textContent =
                "Initial quantity when creating a product.";
        }

        if (stockInput) {
            stockInput.disabled = false;
            stockInput.required = true;
            stockInput.value = "0";
        }

        setValue(alertInput, "5");

        resetImageState();

        showDialog(productModal);

        if (nameInput) {
            nameInput.focus();
        }
    }

    const addProductButton = getElement(
        "open-add-product"
    );

    if (addProductButton) {
        addProductButton.addEventListener(
            "click",
            openAddModal
        );
    }

    const emptyAddButton = getElement(
        "empty-add-product"
    );

    if (emptyAddButton) {
        emptyAddButton.addEventListener(
            "click",
            openAddModal
        );
    }

    // =====================================================
    // 10. EDIT PRODUCT MODAL
    // =====================================================

    document.querySelectorAll(
        ".edit-product"
    ).forEach(function (button) {

        button.addEventListener("click", function () {
            if (!productForm || !productModal) {
                return;
            }

            const data = button.dataset;

            productForm.reset();

            productForm.action = data.url;

            setValue(nameInput, data.name);
            setValue(skuInput, data.sku);

            setValue(
                descriptionInput,
                data.description
            );

            setValue(costInput, data.cost);
            setValue(priceInput, data.price);

            setValue(stockInput, data.stock);
            setValue(alertInput, data.alert);

            if (stockInput) {
                stockInput.disabled = false;
                stockInput.required = true;
            }

            if (stockLabel) {
                stockLabel.textContent = "Stock Quantity";
            }

            if (stockHelp) {
                stockHelp.textContent =
                    "Update the current available stock quantity.";
            }

            // ---------------------------------------------
            // SELECT PRODUCT CATEGORY
            // ---------------------------------------------

            const categoryOption = Array.from(
                document.querySelectorAll(
                    ".product-category-option"
                )
            ).find(function (option) {
                return (
                    option.dataset.value ===
                    data.categoryId
                );
            });

            if (productCategoryDropdown) {
                if (categoryOption) {
                    productCategoryDropdown.select(
                        categoryOption.dataset.value,
                        categoryOption.dataset.label
                    );
                } else {
                    productCategoryDropdown.select(
                        "",
                        "Select Category"
                    );
                }
            }

            // ---------------------------------------------
            // IMAGE
            // ---------------------------------------------

            resetImageState();

            if (
                data.image &&
                currentImage &&
                currentImageWrapper
            ) {
                currentImage.src = data.image;

                currentImageWrapper.classList.remove(
                    "hidden"
                );
            }

            const categoryError = getElement(
                "product-category-error"
            );

            if (categoryError) {
                categoryError.classList.add("hidden");
            }

            setText(
                "product-modal-title",
                "Edit Product"
            );

            setText(
                "product-submit-text",
                "Save Changes"
            );

            showDialog(productModal);
        });

    });

    // =====================================================
    // 11. REMOVE PRODUCT IMAGE
    // =====================================================

    if (removeImageButton) {
        removeImageButton.addEventListener(
            "click",
            function () {
                setValue(removeImageFlag, "1");

                if (imageInput) {
                    imageInput.value = "";
                }

                if (currentImageWrapper) {
                    currentImageWrapper.classList.add(
                        "hidden"
                    );
                }

                if (imageRemovalMessage) {
                    imageRemovalMessage.classList.remove(
                        "hidden"
                    );
                }
            }
        );
    }

    if (imageInput) {
        imageInput.addEventListener(
            "change",
            function () {
                if (imageInput.files.length > 0) {
                    setValue(removeImageFlag, "0");

                    if (currentImageWrapper) {
                        currentImageWrapper.classList.add(
                            "hidden"
                        );
                    }

                    if (imageRemovalMessage) {
                        imageRemovalMessage.classList.add(
                            "hidden"
                        );
                    }
                }
            }
        );
    }

    // =====================================================
    // 12. PRODUCT FORM VALIDATION
    // =====================================================

    if (productForm) {
        productForm.addEventListener(
            "submit",
            function (event) {
                const categoryError = getElement(
                    "product-category-error"
                );

                if (
                    categoryInput &&
                    !categoryInput.value
                ) {
                    event.preventDefault();

                    if (categoryError) {
                        categoryError.classList.remove(
                            "hidden"
                        );
                    }

                    const categoryTrigger = getElement(
                        "product-category-trigger"
                    );

                    if (categoryTrigger) {
                        categoryTrigger.focus();
                    }

                    return;
                }

                if (categoryError) {
                    categoryError.classList.add(
                        "hidden"
                    );
                }
            }
        );
    }

    // =====================================================
    // 13. VIEW PRODUCT MODAL
    // =====================================================

    document.querySelectorAll(
        ".view-product"
    ).forEach(function (button) {

        button.addEventListener("click", function () {
            if (!viewModal) {
                return;
            }

            const data = button.dataset;

            // ---------------------------------------------
            // PRODUCT NAME
            // ---------------------------------------------

            setText(
                "view-name",
                data.name
            );

            // ---------------------------------------------
            // SKU
            // ---------------------------------------------

            setText(
                "view-sku",
                "SKU: " + (data.sku || "")
            );

            // ---------------------------------------------
            // CATEGORY
            // ---------------------------------------------

            setText(
                "view-category",
                data.category
            );

            // ---------------------------------------------
            // DESCRIPTION
            // ---------------------------------------------

            setText(
                "view-description",
                data.description || "No description"
            );

            // ---------------------------------------------
            // LATEST COST
            // ---------------------------------------------

            setText(
                "view-cost",
                formatPrice(data.cost)
            );

            // ---------------------------------------------
            // PREVIOUS COST
            // ---------------------------------------------

            setText(
                "view-previous-cost",
                formatPrice(data.previousCost)
            );

            // ---------------------------------------------
            // AVERAGE COST - FIXED
            // ---------------------------------------------

            setText(
                "view-average-cost",
                formatPrice(data.averageCost)
            );

            // ---------------------------------------------
            // SELLING PRICE
            // ---------------------------------------------

            setText(
                "view-price",
                formatPrice(data.price)
            );

            // ---------------------------------------------
            // STOCK QUANTITY
            // ---------------------------------------------

            setText(
                "view-stock",
                data.stock
            );

            // ---------------------------------------------
            // LOW STOCK ALERT
            // ---------------------------------------------

            setText(
                "view-alert",
                data.alert
            );

            // ---------------------------------------------
            // CREATED DATE
            // ---------------------------------------------

            setText(
                "view-created",
                data.created
            );

            // ---------------------------------------------
            // PRODUCT IMAGE
            // ---------------------------------------------

            const image = getElement(
                "view-image"
            );

            const placeholder = getElement(
                "view-image-placeholder"
            );

            if (data.image) {
                if (image) {
                    image.src = data.image;

                    image.classList.remove(
                        "hidden"
                    );
                }

                if (placeholder) {
                    placeholder.classList.add(
                        "hidden"
                    );
                }
            } else {
                if (image) {
                    image.removeAttribute("src");

                    image.classList.add(
                        "hidden"
                    );
                }

                if (placeholder) {
                    placeholder.classList.remove(
                        "hidden"
                    );
                }
            }

            showDialog(viewModal);
        });

    });

    // =====================================================
    // 14. DELETE PRODUCT MODAL
    // =====================================================

    document.querySelectorAll(
        ".delete-product"
    ).forEach(function (button) {

        button.addEventListener("click", function () {
            if (!deleteModal) {
                return;
            }

            setText(
                "delete-product-name",
                button.dataset.name
            );

            const deleteForm = getElement(
                "delete-product-form"
            );

            if (deleteForm) {
                deleteForm.action =
                    button.dataset.url;
            }

            showDialog(deleteModal);
        });

    });

    // =====================================================
    // 15. CLOSE MODALS USING BUTTONS
    // =====================================================

    document.querySelectorAll(
        "[data-close-dialog]"
    ).forEach(function (button) {

        button.addEventListener("click", function () {
            const dialogId = button.dataset.closeDialog;
            const dialog = getElement(dialogId);

            if (dialog && dialog.open) {
                dialog.close();
            }
        });

    });

    // =====================================================
    // 16. CLOSE MODALS ON BACKDROP CLICK
    // =====================================================

    [
        productModal,
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

});
