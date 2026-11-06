
document.addEventListener("DOMContentLoaded", function () {

    // =====================================================
    // 1. MODAL ELEMENTS
    // =====================================================

    const categoryModal = document.getElementById("category-modal");
    const viewModal = document.getElementById("view-category-modal");
    const deleteModal = document.getElementById("delete-category-modal");


    // =====================================================
    // 2. FORM ELEMENTS
    // =====================================================

    const categoryForm = document.getElementById("category-form");

    const categoryNameInput = document.getElementById(
        "category-name"
    );

    const categoryDescriptionInput = document.getElementById(
        "category-description"
    );

    const categoryModalTitle = document.getElementById(
        "category-modal-title"
    );

    const categorySubmitText = document.getElementById(
        "category-submit-text"
    );

    const deleteCategoryForm = document.getElementById(
        "delete-category-form"
    );

    const deleteCategoryName = document.getElementById(
        "delete-category-name"
    );


    // =====================================================
    // 3. OPEN ADD CATEGORY MODAL
    // =====================================================

    function openAddCategoryModal() {

        if (
            !categoryModal ||
            !categoryForm ||
            !categoryNameInput ||
            !categoryDescriptionInput
        ) {
            return;
        }

        const addCategoryUrl = categoryForm.dataset.addUrl;

        if (!addCategoryUrl) {
            return;
        }

        // Reset form
        categoryForm.reset();

        // Set Add URL
        categoryForm.action = addCategoryUrl;

        // Set modal title
        if (categoryModalTitle) {
            categoryModalTitle.textContent = "Add New Category";
        }

        // Set submit button text
        if (categorySubmitText) {
            categorySubmitText.textContent = "Save Category";
        }

        // Open modal
        categoryModal.showModal();

        // Focus name input
        categoryNameInput.focus();
    }


    // =====================================================
    // 4. MAIN ADD CATEGORY BUTTON
    // =====================================================

    const addButton = document.getElementById(
        "open-add-category"
    );

    if (addButton) {

        addButton.addEventListener(
            "click",
            openAddCategoryModal
        );

    }


    // =====================================================
    // 5. EMPTY STATE ADD BUTTON
    // =====================================================

    const emptyAddButton = document.getElementById(
        "empty-add-category"
    );

    if (emptyAddButton) {

        emptyAddButton.addEventListener(
            "click",
            openAddCategoryModal
        );

    }


    // =====================================================
    // 6. VIEW CATEGORY
    // =====================================================

    document.querySelectorAll(".view-category").forEach(
        function (button) {

            button.addEventListener("click", function () {

                if (!viewModal) {
                    return;
                }

                const nameElement = document.getElementById(
                    "view-category-name"
                );

                const descriptionElement = document.getElementById(
                    "view-category-description"
                );

                const createdElement = document.getElementById(
                    "view-category-created"
                );

                // Category name
                if (nameElement) {
                    nameElement.textContent =
                        this.dataset.name || "";
                }

                // Category description
                if (descriptionElement) {
                    descriptionElement.textContent =
                        this.dataset.description || "No description";
                }

                // Created date
                if (createdElement) {
                    createdElement.textContent =
                        this.dataset.created || "";
                }

                // Open View modal
                viewModal.showModal();

            });

        }
    );


    // =====================================================
    // 7. EDIT CATEGORY
    // =====================================================

    document.querySelectorAll(".edit-category").forEach(
        function (button) {

            button.addEventListener("click", function () {

                if (
                    !categoryModal ||
                    !categoryForm ||
                    !categoryNameInput ||
                    !categoryDescriptionInput
                ) {
                    return;
                }

                const editUrl = this.dataset.url;

                if (!editUrl) {
                    return;
                }

                // Reset form
                categoryForm.reset();

                // Set Edit URL
                categoryForm.action = editUrl;

                // Fill existing category data
                categoryNameInput.value =
                    this.dataset.name || "";

                categoryDescriptionInput.value =
                    this.dataset.description || "";

                // Change modal title
                if (categoryModalTitle) {
                    categoryModalTitle.textContent =
                        "Edit Category";
                }

                // Change submit button text
                if (categorySubmitText) {
                    categorySubmitText.textContent =
                        "Save Changes";
                }

                // Open Edit modal
                categoryModal.showModal();

                // Focus name input
                categoryNameInput.focus();

            });

        }
    );


    // =====================================================
    // 8. DELETE CATEGORY
    // =====================================================

    document.querySelectorAll(".delete-category").forEach(
        function (button) {

            button.addEventListener("click", function () {

                if (
                    !deleteModal ||
                    !deleteCategoryForm ||
                    !deleteCategoryName
                ) {
                    return;
                }

                const deleteUrl = this.dataset.url;

                if (!deleteUrl) {
                    return;
                }

                // Display category name
                deleteCategoryName.textContent =
                    this.dataset.name || "";

                // Set Delete URL
                deleteCategoryForm.action = deleteUrl;

                // Open Delete modal
                deleteModal.showModal();

            });

        }
    );


    // =====================================================
    // 9. CLOSE MODALS USING BUTTONS
    // =====================================================

    document.querySelectorAll("[data-close-dialog]").forEach(
        function (button) {

            button.addEventListener("click", function () {

                const dialogId = this.dataset.closeDialog;

                if (!dialogId) {
                    return;
                }

                const dialog = document.getElementById(
                    dialogId
                );

                if (dialog && dialog.open) {
                    dialog.close();
                }

            });

        }
    );


    // =====================================================
    // 10. CLOSE MODALS BY CLICKING BACKDROP
    // =====================================================

    const dialogs = [
        categoryModal,
        viewModal,
        deleteModal
    ];

    dialogs.forEach(function (dialog) {

        // Some modals may not exist due to permissions.
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
