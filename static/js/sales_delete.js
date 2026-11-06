document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("cancel-sale-modal");
    const panel = document.getElementById("cancel-sale-modal-panel");
    const openButton = document.getElementById("open-cancel-sale-modal");
    const closeButton = document.getElementById("close-cancel-sale-modal");
    const confirmButton = document.getElementById("confirm-cancel-sale");

    if (!modal || !panel || !openButton || !closeButton) {
        return;
    }

    let previousFocus = null;

    // ==============================================
    // OPEN MODAL
    // ==============================================

    function openModal() {

        previousFocus = document.activeElement;

        modal.classList.remove("hidden");
        modal.classList.add("flex");

        document.body.classList.add("overflow-hidden");

        closeButton.focus();
    }


    // ==============================================
    // CLOSE MODAL
    // ==============================================

    function closeModal() {

        modal.classList.add("hidden");
        modal.classList.remove("flex");

        document.body.classList.remove("overflow-hidden");

        if (previousFocus && typeof previousFocus.focus === "function") {
            previousFocus.focus();
        }
    }


    // ==============================================
    // OPEN BUTTON
    // ==============================================

    openButton.addEventListener("click", openModal);


    // ==============================================
    // CLOSE BUTTON
    // ==============================================

    closeButton.addEventListener("click", closeModal);


    // ==============================================
    // BACKDROP CLICK
    // ==============================================

    modal.addEventListener("click", function (event) {

        if (event.target === modal) {
            closeModal();
        }

    });


    // ==============================================
    // ESCAPE KEY
    // ==============================================

    document.addEventListener("keydown", function (event) {

        if (
            event.key === "Escape" &&
            !modal.classList.contains("hidden")
        ) {
            closeModal();
        }

    });


    // ==============================================
    // PREVENT DOUBLE SUBMISSION
    // ==============================================

    if (confirmButton) {

        const form = confirmButton.closest("form");

        if (form) {

            form.addEventListener("submit", function () {

                confirmButton.disabled = true;
                confirmButton.classList.add(
                    "cursor-not-allowed",
                    "opacity-60"
                );

                confirmButton.textContent = "Cancelling...";

            });

        }

    }

});