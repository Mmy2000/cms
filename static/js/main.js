
document.addEventListener("DOMContentLoaded", function () {

    // MAIN SLIDER
    var mainSwiper = new Swiper(".mySwiper", {
        loop: false,
        navigation: {
            nextEl: ".mySwiper .swiper-button-next",
            prevEl: ".mySwiper .swiper-button-prev",
        },
        pagination: {
            el: ".mySwiper .swiper-pagination",
            clickable: true,
        }
    });

    // MODAL SLIDER
    var modalSwiper = new Swiper(".modalSwiper", {
        loop: false,
        navigation: {
            nextEl: ".modalSwiper .swiper-button-next",
            prevEl: ".modalSwiper .swiper-button-prev",
        },
        pagination: {
            el: ".modalSwiper .swiper-pagination",
            clickable: true,
        }
    });

    // SYNC MODAL WITH CLICKED IMAGE
    document.addEventListener('alpine:init', () => {
        Alpine.effect(() => {
            let root = Alpine.$root;
            let open = Alpine.evaluate(root, 'open');
            let index = Alpine.evaluate(root, 'modalIndex');

            if (open) {
                modalSwiper.slideTo(index);
            }
        });
    });

});

const menuBtn = document.getElementById('menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    menuBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });


document.addEventListener("DOMContentLoaded", function () {

    function calc() {
        // Get field values
        const value_of_work = parseFloat(document.getElementById("id_value_of_work")?.value || 0);
        const invoice_copies = parseFloat(document.getElementById("id_invoice_copies")?.value || 0);
        const stamp_rate = parseFloat(document.getElementById("id_stamp_rate")?.value || 0);
        const exchange_rate = parseFloat(document.getElementById("id_exchange_rate")?.value || 0);

        // =====================
        // ✨ Your Calculations
        // =====================

        const d1 = value_of_work * invoice_copies * stamp_rate * exchange_rate;

        // =====================
        // ✨ Update UI
        // =====================

        document.getElementById("d1-value").textContent = d1.toFixed(2);
    }

    // Attach listeners to ALL inputs
    const inputs = document.querySelectorAll("input, select");
    inputs.forEach(input => {
        input.addEventListener("input", calc);
        input.addEventListener("change", calc);
    });

    // Initial run
    calc();
});
