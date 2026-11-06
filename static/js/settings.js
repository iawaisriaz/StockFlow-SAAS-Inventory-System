document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // IMAGE UPLOAD CONFIGURATION
    // =========================================

    const imageConfigs = [
        {
            key: "personal",
            inputId: "id_personal-profile_photo",
            previewId: "personal-photo-preview",
            clearId: "personal-photo-clear",
            statusId: "personal-photo-status",
        },
        {
            key: "business",
            inputId: "id_business-logo",
            previewId: "business-logo-preview",
            clearId: "business-logo-clear",
            statusId: "business-logo-status",
        },
    ];


    // =========================================
    // IMAGE UPLOAD AND PREVIEW
    // =========================================

    imageConfigs.forEach((config) => {

        const input = document.getElementById(
            config.inputId
        );

        const preview = document.getElementById(
            config.previewId
        );

        const clearCheckbox = document.getElementById(
            config.clearId
        );

        const status = document.getElementById(
            config.statusId
        );

        const removeButton = document.querySelector(
            `[data-remove-image="${config.key}"]`
        );

        if (!input || !preview) {
            return;
        }

        const originalMarkup = preview.innerHTML;
        const hasSavedImage = Boolean(
            preview.querySelector("img")
        );

        let previewURL = null;
        let version = 0;


        // =====================================
        // HELPER FUNCTIONS
        // =====================================

        function setStatus(message) {
            if (status) {
                status.textContent = message;
            }
        }

        function setRemoveVisible(visible) {
            if (!removeButton) {
                return;
            }

            removeButton.hidden = !visible;

            // Prevent Tailwind inline-flex from overriding
            // the browser's default [hidden] style.
            removeButton.style.display = visible
                ? ""
                : "none";
        }

        function releasePreviewURL() {
            if (previewURL) {
                URL.revokeObjectURL(previewURL);
                previewURL = null;
            }
        }

        function showFallback() {
            preview.replaceChildren();

            if (config.key === "personal") {
                const span = document.createElement("span");

                span.textContent =
                    preview.dataset.fallback || "U";

                preview.appendChild(span);
            } else {
                const icon = document.createElement("i");

                icon.setAttribute(
                    "data-lucide",
                    "building-2"
                );

                icon.className = "h-8 w-8";

                preview.appendChild(icon);

                if (window.lucide) {
                    window.lucide.createIcons();
                }
            }
        }

        function restoreOriginal() {
            releasePreviewURL();

            preview.innerHTML = originalMarkup;

            if (window.lucide) {
                window.lucide.createIcons();
            }

            setRemoveVisible(hasSavedImage);
        }


        // Initial button visibility
        setRemoveVisible(hasSavedImage);


        // =====================================
        // SELECT IMAGE
        // =====================================

        input.addEventListener("change", () => {

            version += 1;

            const currentVersion = version;

            const file = input.files
                ? input.files[0]
                : null;

            if (!file) {
                return;
            }

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ];

            if (!allowedTypes.includes(file.type)) {

                input.value = "";

                if (clearCheckbox) {
                    clearCheckbox.checked = false;
                }

                restoreOriginal();

                setStatus(
                    "Please select a JPG, PNG or WebP image."
                );

                return;
            }

            const maximumSize = 10 * 1024 * 1024;

            if (file.size > maximumSize) {

                input.value = "";

                if (clearCheckbox) {
                    clearCheckbox.checked = false;
                }

                restoreOriginal();

                setStatus(
                    "Image must not exceed 10 MB."
                );

                return;
            }

            releasePreviewURL();

            const url = URL.createObjectURL(file);

            previewURL = url;

            const image = document.createElement("img");

            image.alt = config.key === "personal"
                ? "Profile photo preview"
                : "Business logo preview";

            image.className = "h-full w-full object-cover";


            image.onload = () => {

                if (currentVersion !== version) {
                    return;
                }

                preview.replaceChildren(image);

                if (clearCheckbox) {
                    clearCheckbox.checked = false;
                }

                setRemoveVisible(true);

                setStatus(
                    `${file.name} selected. Click Save Information to upload.`
                );
            };


            image.onerror = () => {

                if (currentVersion !== version) {
                    return;
                }

                input.value = "";

                if (clearCheckbox) {
                    clearCheckbox.checked = false;
                }

                restoreOriginal();

                setStatus(
                    "Unable to preview this image."
                );
            };


            image.src = url;
        });


        // =====================================
        // REMOVE IMAGE
        // =====================================

        if (removeButton) {

            removeButton.addEventListener("click", () => {

                version += 1;

                input.value = "";

                releasePreviewURL();

                if (clearCheckbox) {
                    clearCheckbox.checked = hasSavedImage;
                }

                showFallback();

                setRemoveVisible(false);

                if (hasSavedImage) {
                    setStatus(
                        "Image will be removed when you click Save Information."
                    );
                } else {
                    setStatus(
                        "Selected image cancelled."
                    );
                }
            });
        }


        // =====================================
        // CLEAN UP PREVIEW URL
        // =====================================

        window.addEventListener(
            "beforeunload",
            releasePreviewURL
        );

    });


    // =========================================
    // SHOW / HIDE PASSWORD
    // =========================================

    const passwordButtons = document.querySelectorAll(
        "[data-password-toggle]"
    );

    passwordButtons.forEach((button) => {

        button.addEventListener("click", () => {

            const inputId = button.dataset.passwordToggle;

            const input = document.getElementById(
                inputId
            );

            if (!input) {
                return;
            }

            const showPassword = input.type === "password";

            input.type = showPassword
                ? "text"
                : "password";

            button.setAttribute(
                "aria-label",
                showPassword
                    ? "Hide password"
                    : "Show password"
            );

            const existingIcon = button.querySelector(
                "svg, i"
            );

            if (existingIcon) {

                const newIcon = document.createElement("i");

                newIcon.setAttribute(
                    "data-lucide",
                    showPassword ? "eye-off" : "eye"
                );

                newIcon.className = "h-5 w-5";

                existingIcon.replaceWith(newIcon);

                if (window.lucide) {
                    window.lucide.createIcons();
                }
            }
        });
    });


    // =========================================
    // DELETE ACCOUNT MODAL
    // =========================================

    const modal = document.getElementById(
        "delete-account-modal"
    );

    const openButton = document.getElementById(
        "open-delete-modal"
    );

    const closeButton = document.getElementById(
        "close-delete-modal"
    );

    if (modal && openButton && closeButton) {

        let previousFocus = null;


        function openModal() {

            previousFocus = document.activeElement;

            modal.classList.remove("hidden");
            modal.classList.add("flex");

            modal.setAttribute(
                "aria-hidden",
                "false"
            );

            document.body.style.overflow = "hidden";

            const passwordInput = document.getElementById(
                "delete-password"
            );

            if (passwordInput) {
                passwordInput.focus();
            }
        }


        function closeModal() {

            modal.classList.add("hidden");
            modal.classList.remove("flex");

            modal.setAttribute(
                "aria-hidden",
                "true"
            );

            document.body.style.overflow = "";

            if (
                previousFocus &&
                typeof previousFocus.focus === "function"
            ) {
                previousFocus.focus();
            } else {
                openButton.focus();
            }
        }


        openButton.addEventListener(
            "click",
            openModal
        );

        closeButton.addEventListener(
            "click",
            closeModal
        );


        // Click outside modal
        modal.addEventListener("click", (event) => {

            if (event.target === modal) {
                closeModal();
            }
        });


        // Escape key
        document.addEventListener("keydown", (event) => {

            if (
                event.key === "Escape" &&
                !modal.classList.contains("hidden")
            ) {
                closeModal();
            }
        });
    }


    // =========================================
    // INITIALIZE ICONS
    // =========================================

    if (window.lucide) {
        window.lucide.createIcons();
    }

});
