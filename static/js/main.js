
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