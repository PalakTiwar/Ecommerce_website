// static/js/script.js

// Wait for the DOM to be fully loaded before running script
document.addEventListener('DOMContentLoaded', (event) => {

    const menuToggle = document.getElementById('menu-toggle');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content'); // Get main content area if needed for shifts

    // Check if elements exist before adding listeners (good practice)
    if (menuToggle && sidebar && closeSidebarBtn) {

        function openSidebar() {
            sidebar.classList.add('open');
            sidebar.setAttribute('aria-hidden', 'false');
            menuToggle.setAttribute('aria-expanded', 'true');
            // Optional: Add class to body or shift main content
            // document.body.classList.add('sidebar-active');
            // mainContent.style.marginLeft = '250px';
        }

        function closeSidebar() {
            sidebar.classList.remove('open');
            sidebar.setAttribute('aria-hidden', 'true');
            menuToggle.setAttribute('aria-expanded', 'false');
            // Optional: Remove class from body or reset main content margin
            // document.body.classList.remove('sidebar-active');
            // mainContent.style.marginLeft = '0';
        }

        // Event listener for the hamburger menu button
        menuToggle.addEventListener('click', () => {
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        // Event listener for the close button inside the sidebar
        closeSidebarBtn.addEventListener('click', closeSidebar);

        // Optional: Close sidebar if user clicks outside of it
        // document.addEventListener('click', (event) => {
        //     if (sidebar.classList.contains('open') && !sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
        //         closeSidebar();
        //     }
        // });

        // Optional: Close sidebar if user presses the Escape key
        // document.addEventListener('keydown', (event) => {
        //     if (event.key === 'Escape' && sidebar.classList.contains('open')) {
        //         closeSidebar();
        //     }
        // });
    } else {
        console.error("Sidebar elements not found. Check IDs: menu-toggle, close-sidebar-btn, sidebar");
    }
}); // End DOMContentLoaded