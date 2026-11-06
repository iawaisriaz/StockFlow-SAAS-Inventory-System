
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // ==========================================
    // STOCKFLOW HEADER
    // ==========================================

    const sidebarToggle = document.getElementById(
        "sidebar-toggle"
    );

    // ==========================================
    // SIDEBAR TOGGLE
    // ==========================================

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function () {

            // Actual sidebar open/close functionality
            // is handled by navbar.js.

            document.dispatchEvent(
                new CustomEvent("stockflow:toggle-sidebar")
            );

        });
    }

});
