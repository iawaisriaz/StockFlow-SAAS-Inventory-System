document.addEventListener("DOMContentLoaded", function () {

    // ================= ELEMENTS =================

    const sidebar = document.getElementById("stockflow-sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const closeButton = document.getElementById("sidebar-close");
    const toggleButton = document.getElementById("sidebar-toggle");
    const layout = document.getElementById("app-layout");

    if (!sidebar || !layout) return;

    const desktopQuery = window.matchMedia("(min-width: 1024px)");
    const storageKey = "stockflow-sidebar-collapsed";


    // ================= DESKTOP =================

    function setDesktopCollapsed(collapsed) {

        sidebar.classList.toggle("lg:!w-[72px]", collapsed);
        sidebar.classList.toggle("lg:!w-64", !collapsed);

        layout.classList.toggle("lg:!ml-[72px]", collapsed);
        layout.classList.toggle("lg:!ml-64", !collapsed);

        sidebar.querySelectorAll(".sidebar-label").forEach(function (label) {
            label.classList.toggle("lg:hidden", collapsed);
        });

        sidebar.querySelectorAll(".nav-link").forEach(function (link) {
            link.classList.toggle("lg:justify-center", collapsed);
            link.classList.toggle("lg:!px-0", collapsed);
        });

        sidebar.querySelector(".sidebar-brand")?.classList.toggle(
            "lg:justify-center",
            collapsed
        );

        sidebar.querySelector(".sidebar-user")?.classList.toggle(
            "lg:justify-center",
            collapsed
        );

        sidebar.querySelector(".sidebar-logout")?.classList.toggle(
            "lg:justify-center",
            collapsed
        );

        localStorage.setItem(storageKey, String(collapsed));

        toggleButton?.setAttribute(
            "aria-expanded",
            String(!collapsed)
        );
    }


    // ================= MOBILE =================

    function openMobileSidebar() {

        sidebar.classList.remove("-translate-x-full");
        overlay?.classList.remove("hidden");

        document.body.style.overflow = "hidden";

        toggleButton?.setAttribute("aria-expanded", "true");
    }

    function closeMobileSidebar() {

        sidebar.classList.add("-translate-x-full");
        overlay?.classList.add("hidden");

        document.body.style.overflow = "";

        toggleButton?.setAttribute("aria-expanded", "false");
    }


    // ================= TOGGLE =================

    function toggleSidebar() {

        if (desktopQuery.matches) {

            const collapsed = sidebar.classList.contains("lg:!w-[72px]");
            setDesktopCollapsed(!collapsed);

        } else {

            const isClosed = sidebar.classList.contains("-translate-x-full");

            if (isClosed) {
                openMobileSidebar();
            } else {
                closeMobileSidebar();
            }
        }
    }


    // Event from header.js
    document.addEventListener(
        "stockflow:toggle-sidebar",
        toggleSidebar
    );


    // ================= CLOSE EVENTS =================

    closeButton?.addEventListener("click", closeMobileSidebar);
    overlay?.addEventListener("click", closeMobileSidebar);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !desktopQuery.matches) {
            closeMobileSidebar();
        }
    });


    // ================= RESPONSIVE =================

    function handleResize() {

        if (desktopQuery.matches) {

            sidebar.classList.remove("-translate-x-full");
            overlay?.classList.add("hidden");
            document.body.style.overflow = "";

            const saved = localStorage.getItem(storageKey) === "true";
            setDesktopCollapsed(saved);

        } else {

            sidebar.classList.add("-translate-x-full");
            overlay?.classList.add("hidden");

            document.body.style.overflow = "";

            toggleButton?.setAttribute("aria-expanded", "false");
        }
    }

    desktopQuery.addEventListener("change", handleResize);
    handleResize();


    // ================= ACTIVE MENU =================

    const currentPath = window.location.pathname;

    document.querySelectorAll(".nav-link").forEach(function (link) {

        const href = link.getAttribute("href");

        if (href && href !== "#" && href === currentPath) {

            link.classList.add(
                "bg-[var(--color-primary)]",
                "text-white",
                "font-semibold"
            );

            link.setAttribute("aria-current", "page");
        }

    });

});
