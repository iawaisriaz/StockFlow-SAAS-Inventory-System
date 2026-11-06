
document.addEventListener("DOMContentLoaded", () => {

    const dropdowns = [
        ...document.querySelectorAll("[data-report-dropdown]")
    ];

    // ==========================================
    // CLOSE DROPDOWN
    // ==========================================
    function closeDropdown(root) {

        const menu = root.querySelector("[data-dropdown-menu]");
        const trigger = root.querySelector("[data-dropdown-trigger]");
        const chevron = root.querySelector("[data-dropdown-chevron]");

        if (!menu || !trigger) return;

        menu.classList.add("hidden");
        trigger.setAttribute("aria-expanded", "false");

        if (chevron) {
            chevron.classList.remove("rotate-180");
        }
    }

    // ==========================================
    // SYNC SELECTED OPTION
    // ==========================================
    function syncDropdown(root) {

        const select = root.querySelector("select");
        const label = root.querySelector("[data-dropdown-label]");

        if (!select || !label) return;

        const selected = select.options[select.selectedIndex];

        label.textContent = selected
            ? selected.textContent.trim()
            : "Select";

        root.querySelectorAll("[data-dropdown-option]").forEach((option) => {

            const active = option.dataset.dropdownOption === select.value;

            option.setAttribute("aria-selected", String(active));

            option.classList.toggle("bg-soft-green", active);
            option.classList.toggle("text-primary", active);
            option.classList.toggle("font-semibold", active);

            option.classList.toggle("text-dark-green", !active);
            option.classList.toggle("hover:bg-soft-green", !active);
        });
    }

    // ==========================================
    // INITIALIZE DROPDOWNS
    // ==========================================
    dropdowns.forEach((root) => {

        const select = root.querySelector("select");
        const trigger = root.querySelector("[data-dropdown-trigger]");
        const menu = root.querySelector("[data-dropdown-menu]");
        const chevron = root.querySelector("[data-dropdown-chevron]");

        if (!select || !trigger || !menu) return;

        syncDropdown(root);

        // OPEN / CLOSE
        trigger.addEventListener("click", () => {

            const shouldOpen = menu.classList.contains("hidden");

            dropdowns.forEach((dropdown) => {
                closeDropdown(dropdown);
            });

            if (shouldOpen) {

                menu.classList.remove("hidden");

                trigger.setAttribute("aria-expanded", "true");

                if (chevron) {
                    chevron.classList.add("rotate-180");
                }
            }
        });

        // OPTION SELECTION
        root.querySelectorAll("[data-dropdown-option]").forEach((option) => {

            option.addEventListener("click", () => {

                select.value = option.dataset.dropdownOption;

                // Notify existing reports.js
                select.dispatchEvent(
                    new Event("change", { bubbles: true })
                );

                syncDropdown(root);
                closeDropdown(root);

                trigger.focus();
            });
        });

        // SYNC WHEN SELECT CHANGES
        select.addEventListener("change", () => {
            syncDropdown(root);
        });

        // KEYBOARD SUPPORT
        trigger.addEventListener("keydown", (event) => {

            if (event.key === "Escape") {
                closeDropdown(root);
                return;
            }

            if (
                event.key !== "ArrowDown" &&
                event.key !== "ArrowUp" &&
                event.key !== "Enter" &&
                event.key !== " "
            ) {
                return;
            }

            event.preventDefault();

            const options = [
                ...root.querySelectorAll("[data-dropdown-option]")
            ];

            const currentIndex = options.findIndex(
                (option) => option.dataset.dropdownOption === select.value
            );

            const nextIndex = event.key === "ArrowUp"
                ? (currentIndex - 1 + options.length) % options.length
                : (currentIndex + 1) % options.length;

            if (menu.classList.contains("hidden")) {
                trigger.click();
            }

            options[nextIndex].focus();
        });

        // KEYBOARD NAVIGATION INSIDE MENU
        menu.addEventListener("keydown", (event) => {

            const options = [
                ...root.querySelectorAll("[data-dropdown-option]")
            ];

            const index = options.indexOf(document.activeElement);

            if (event.key === "Escape") {
                closeDropdown(root);
                trigger.focus();
                return;
            }

            if (
                event.key === "ArrowDown" ||
                event.key === "ArrowUp"
            ) {

                event.preventDefault();

                const direction = event.key === "ArrowDown" ? 1 : -1;

                const nextIndex = (
                    index + direction + options.length
                ) % options.length;

                options[nextIndex].focus();
            }
        });

    });

    // ==========================================
    // CLOSE WHEN CLICKING OUTSIDE
    // ==========================================
    document.addEventListener("click", (event) => {

        dropdowns.forEach((root) => {

            if (!root.contains(event.target)) {
                closeDropdown(root);
            }
        });
    });

    // ==========================================
    // DATE FILTER FIELD VISIBILITY
    // ==========================================
    const period = document.getElementById("report-period");
    const singleDate = document.getElementById("report-single-date");
    const dateRange = document.getElementById("report-date-range");

    if (period && singleDate && dateRange) {

        function updateDateFields() {

            const isSpecificDate = period.value === "date";
            const isDateRange = period.value === "range";

            singleDate.classList.toggle(
                "hidden",
                !isSpecificDate
            );

            dateRange.classList.toggle(
                "hidden",
                !isDateRange
            );

            dateRange.classList.toggle(
                "flex",
                isDateRange
            );
        }

        period.addEventListener("change", updateDateFields);

        updateDateFields();
    }

});
