"use strict";

/*
 * StockFlow - Supplier Product Fallback
 *
 * Rule:
 * - No linked products: all business products allowed.
 * - Linked products exist: only linked products allowed.
 *
 * Must load before purchases.js executes.
 */

document.addEventListener("DOMContentLoaded", () => {

    const supplierDropdown = document.getElementById(
        "purchase-supplier-dropdown"
    );

    const purchaseItems = document.getElementById(
        "purchase-items"
    );

    const emptyTemplate = document.getElementById(
        "empty-purchase-item-template"
    );

    if (!supplierDropdown || !purchaseItems || !emptyTemplate) {
        return;
    }

    const supplierOptions = Array.from(
        supplierDropdown.querySelectorAll(
            "[data-dropdown-option][data-value]"
        )
    );

    const productOptions = Array.from(
        document.querySelectorAll(
            ".purchase-item-row [data-dropdown-option][data-value], " +
            "#empty-purchase-item-template [data-dropdown-option][data-value]"
        )
    );

    if (!productOptions.length) {
        return;
    }

    const linkedSupplierIds = new Set();

    productOptions.forEach((option) => {

        const supplierIds = (
            option.dataset.suppliers || ""
        )
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        supplierIds.forEach((id) => {
            linkedSupplierIds.add(id);
        });

    });

    const fallbackSupplierIds = supplierOptions
        .map((option) => option.dataset.value)
        .filter((id) => {
            return id && !linkedSupplierIds.has(id);
        });

    if (!fallbackSupplierIds.length) {
        return;
    }

    productOptions.forEach((option) => {

        const existingIds = (
            option.dataset.suppliers || ""
        )
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        const allIds = new Set([
            ...existingIds,
            ...fallbackSupplierIds,
        ]);

        option.dataset.suppliers = Array.from(
            allIds
        ).join(" ");

    });

});
