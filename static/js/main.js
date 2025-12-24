
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

  function toggleMobileUserMenu() {
    const menu = document.getElementById("mobile-user-menu");
    const arrow = document.getElementById("mobile-user-arrow");

    menu.classList.toggle("hidden");
    arrow.classList.toggle("rotate-180");
  }

   // Toggle dropdown menu
  const button = document.getElementById('userMenuButton');
  const dropdown = document.getElementById('userMenuDropdown');

  button.addEventListener('click', (e) => {
    e.stopPropagation();
    const isHidden = dropdown.classList.contains('hidden');
    dropdown.classList.toggle('hidden');
    button.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.classList.contains('hidden') && 
        !dropdown.contains(e.target) && 
        !button.contains(e.target)) {
      dropdown.classList.add('hidden');
      button.setAttribute('aria-expanded', 'false');
    }
  });

  // Close dropdown on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !dropdown.classList.contains('hidden')) {
      dropdown.classList.add('hidden');
      button.setAttribute('aria-expanded', 'false');
      button.focus();
    }
  });


  // Image preview functionality
    const fileInput = document.getElementById('syndicate_card_input');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeButton = document.getElementById('remove-preview');

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                previewContainer.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });

    removeButton.addEventListener('click', function() {
        fileInput.value = '';
        previewContainer.classList.add('hidden');
        imagePreview.src = '';
    });

    // Drag and drop functionality
    const dropArea = fileInput.nextElementSibling;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('border-green-500', 'bg-green-50');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('border-green-500', 'bg-green-50');
        });
    });

    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    });

    