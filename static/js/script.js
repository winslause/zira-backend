$(document).ready(function() {
    // Mobile Navbar Toggle
    $('#nav-toggler').click(function() {
        $('#mobile-sidebar').toggleClass('-translate-x-full');
        $(this).find('i').toggleClass('fa-bars fa-times'); // Toggle between hamburger and X
    });
    $('#close-sidebar').click(function() {
        $('#mobile-sidebar').addClass('-translate-x-full');
        $('#nav-toggler').find('i').removeClass('fa-times').addClass('fa-bars'); // Revert to hamburger
    });

    // Mobile Search Bar Toggle
    $('#mobile-search-icon').click(function() {
        $('#mobile-search-bar').toggleClass('active');
    });

    // Close mobile search bar when clicking outside
    $(document).click(function(event) {
        const searchBar = $('#mobile-search-bar');
        const searchIcon = $('#mobile-search-icon');
        if (!searchBar.is(event.target) && !searchIcon.is(event.target) && searchBar.has(event.target).length === 0) {
            searchBar.removeClass('active');
        }
    });

    // Hero Slider
    let currentSlide = 0;
    const slides = $('.hero-slide');
    const dots = $('.dot');
    
    // Initially show the first slide
    slides.eq(currentSlide).addClass('active');

    function showSlide(index) {
        slides.eq(currentSlide).removeClass('active');
        dots.eq(currentSlide).removeClass('active');
        currentSlide = index;
        slides.eq(currentSlide).addClass('active');
        dots.eq(currentSlide).addClass('active');
    }

    // Automatic slideshow for hero
    setInterval(function() {
        let nextSlide = (currentSlide + 1) % slides.length;
        showSlide(nextSlide);
    }, 5000);

    // Discount Popup
    $('.discount-btn-container .floating-btn').click(function() {
        $('#discount-page').removeClass('-translate-x-full');
    });
    $('#close-discount').click(function() {
        $('#discount-page').addClass('-translate-x-full');
    });
});

// Currency Button Logic
const exchangeRates = {
    USD: 0.0077, // 1 KES = 0.0077 USD (1 USD ≈ 130 KES)
    EUR: 0.0073, // 1 KES = 0.0073 EUR
    GBP: 0.0061, // 1 KES = 0.0061 GBP
    KES: 1       // 1 KES = 1 KES
};
let currentCurrency = localStorage.getItem('currency') || 'KES';

function initializeCurrencyButton() {
    const storedCountry = localStorage.getItem('country') || 'Kenya';
    const storedFlag = localStorage.getItem('flag') || '🇰🇪';
    const storedCurrency = localStorage.getItem('currency') || 'KES';
    currentCurrency = storedCurrency;
    const countryBtn = document.getElementById('country-btn');
    const mobileCountryBtn = document.getElementById('mobile-country-btn');
    if (countryBtn) {
        countryBtn.innerHTML = `<span class="flag">${storedFlag}</span> ${storedCurrency}`;
    }
    if (mobileCountryBtn) {
        mobileCountryBtn.innerHTML = `<span class="flag">${storedFlag}</span> ${storedCurrency}`;
    }
    updatePrices();
}

function updatePrices() {
    document.querySelectorAll('#featured-this-month .ftm-card').forEach(card => {
        const priceElement = card.querySelector('.ftm-price');
        const oldPriceElement = card.querySelector('.ftm-old-price');

        // Get base prices from data attributes (in KES)
        const basePriceKES = parseFloat(priceElement.getAttribute('data-price'));
        const baseOldPriceKES = oldPriceElement ? parseFloat(oldPriceElement.getAttribute('data-old-price')) : null;

        // Debugging: Log prices to identify issues
        if (!basePriceKES || (oldPriceElement && !baseOldPriceKES)) {
            console.warn('Invalid price data for card:', {
                cardId: card.dataset.productId || 'unknown',
                productName: card.querySelector('.ftm-product-name')?.textContent || 'unknown',
                basePriceKES,
                baseOldPriceKES,
                tab: card.closest('.ftm-tab-content')?.id || 'unknown'
            });
        }

        if (!isNaN(basePriceKES)) {
            const convertedPrice = (basePriceKES * exchangeRates[currentCurrency]).toFixed(2);

            // Check if the product has a discount (old price exists and is higher)
            if (oldPriceElement && !isNaN(baseOldPriceKES) && baseOldPriceKES > basePriceKES) {
                const convertedOldPrice = (baseOldPriceKES * exchangeRates[currentCurrency]).toFixed(2);
                priceElement.innerHTML = `${currentCurrency} ${convertedPrice} <span class="ftm-old-price" data-old-price="${baseOldPriceKES}">${currentCurrency} ${convertedOldPrice}</span>`;
            } else {
                priceElement.innerHTML = `${currentCurrency} ${convertedPrice}`;
                if (oldPriceElement && baseOldPriceKES <= basePriceKES) {
                    console.warn('Invalid discount detected:', {
                        cardId: card.dataset.productId || 'unknown',
                        productName: card.querySelector('.ftm-product-name')?.textContent || 'unknown',
                        basePriceKES,
                        baseOldPriceKES,
                        tab: card.closest('.ftm-tab-content')?.id || 'unknown'
                    });
                }
            }
        } else {
            console.error('Missing data-price for card:', {
                cardId: card.dataset.productId || 'unknown',
                productName: card.querySelector('.ftm-product-name')?.textContent || 'unknown',
                tab: card.closest('.ftm-tab-content')?.id || 'unknown'
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const countryBtn = document.getElementById('country-btn');
    const mobileCountryBtn = document.getElementById('mobile-country-btn');

    // Desktop currency button
    if (countryBtn) {
        countryBtn.addEventListener('click', () => {
            const dropdown = document.getElementById('country-dropdown');
            dropdown.classList.toggle('hidden');
        });
    }

    // Mobile currency button
    if (mobileCountryBtn) {
        mobileCountryBtn.addEventListener('click', () => {
            const dropdown = document.getElementById('mobile-country-dropdown');
            dropdown.classList.toggle('hidden');
        });
    }

    // Handle currency selection
    document.querySelectorAll('.country-option').forEach(option => {
        option.addEventListener('click', async (e) => {
            e.preventDefault();
            const country = e.target.getAttribute('data-country');
            const flag = e.target.getAttribute('data-flag');
            currentCurrency = e.target.getAttribute('data-currency');
            // Update both buttons
            if (countryBtn) {
                countryBtn.innerHTML = `<span class="flag">${flag}</span> ${currentCurrency}`;
            }
            if (mobileCountryBtn) {
                mobileCountryBtn.innerHTML = `<span class="flag">${flag}</span> ${currentCurrency}`;
            }
            // Hide both dropdowns
            document.getElementById('country-dropdown').classList.add('hidden');
            if (mobileCountryBtn) {
                document.getElementById('mobile-country-dropdown').classList.add('hidden');
            }
            localStorage.setItem('currency', currentCurrency);
            localStorage.setItem('country', country);
            localStorage.setItem('flag', flag);
            try {
                await fetch('/api/set_currency', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ currency: currentCurrency }),
                    credentials: 'include'
                });
            } catch (error) {
                console.error('Failed to sync currency with backend:', error);
            }
            updatePrices();
        });
    });

    initializeCurrencyButton();
});

// Featured This Month Tabs
function showTab(tabId) {
    const tabs = document.querySelectorAll('#featured-this-month .ftm-tab');
    const contents = document.querySelectorAll('#featured-this-month .ftm-tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));
    document.querySelector(`#featured-this-month .ftm-tab[onclick="showTab('${tabId}')"]`).classList.add('active');
    document.querySelector(`#tab-${tabId}`).classList.add('active');
    setTimeout(() => updatePrices(), 0); // Ensure prices update after tab content is visible
}

// Review Slider
document.addEventListener('DOMContentLoaded', () => {
    const prevBtn = document.getElementById('prevReview');
    const nextBtn = document.getElementById('nextReview');
    const sliderLarge = document.getElementById('reviewSliderLargeInner');
    const sliderSmall = document.getElementById('reviewSliderSmallInner');
    const reviewSection = document.getElementById('zira-customer-reviews');

    if (!prevBtn || !nextBtn || !sliderLarge || !sliderSmall || !reviewSection) {
        console.error('Review slider elements not found');
        return;
    }

    let currentSlideLarge = 0;
    const totalSlidesLarge = 3;
    let currentSlideSmall = 0;
    const totalSlidesSmall = 6;
    let autoSlideInterval = null;

    function updateSlider() {
        if (window.innerWidth >= 768) {
            sliderLarge.style.transition = 'transform 0.7s ease-in-out';
            sliderLarge.style.transform = `translateX(-${currentSlideLarge * 100}%)`;
            prevBtn.disabled = currentSlideLarge === 0;
            nextBtn.disabled = currentSlideLarge === totalSlidesLarge - 1;
        } else {
            sliderSmall.style.transition = 'transform 0.7s ease-in-out';
            sliderSmall.style.transform = `translateX(-${currentSlideSmall * 100}%)`;
            prevBtn.disabled = currentSlideSmall === 0;
            nextBtn.disabled = currentSlideSmall === totalSlidesSmall - 1;
        }
    }

    function startAutoSlide() {
        if (autoSlideInterval) clearInterval(autoSlideInterval);
        autoSlideInterval = setInterval(() => {
            if (window.innerWidth >= 768) {
                currentSlideLarge = (currentSlideLarge + 1) % totalSlidesLarge;
            } else {
                currentSlideSmall = (currentSlideSmall + 1) % totalSlidesSmall;
            }
            updateSlider();
        }, 5000);
    }

    function stopAutoSlide() {
        if (autoSlideInterval) clearInterval(autoSlideInterval);
    }

    prevBtn.addEventListener('click', () => {
        if (window.innerWidth >= 768) {
            if (currentSlideLarge > 0) {
                currentSlideLarge--;
                updateSlider();
            }
        } else {
            if (currentSlideSmall > 0) {
                currentSlideSmall--;
                updateSlider();
            }
        }
        stopAutoSlide();
        startAutoSlide();
    });

    nextBtn.addEventListener('click', () => {
        if (window.innerWidth >= 768) {
            if (currentSlideLarge < totalSlidesLarge - 1) {
                currentSlideLarge++;
                updateSlider();
            }
        } else {
            if (currentSlideSmall < totalSlidesSmall - 1) {
                currentSlideSmall++;
                updateSlider();
            }
        }
        stopAutoSlide();
        startAutoSlide();
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            currentSlideLarge = Math.min(currentSlideLarge, totalSlidesLarge - 1);
            currentSlideSmall = currentSlideLarge * 2;
        } else {
            currentSlideSmall = Math.min(currentSlideSmall, totalSlidesSmall - 1);
            currentSlideLarge = Math.floor(currentSlideSmall / 2);
        }
        updateSlider();
    });

    reviewSection.addEventListener('mouseenter', stopAutoSlide);
    reviewSection.addEventListener('mouseleave', startAutoSlide);

    updateSlider();
    startAutoSlide();
});

// Add to Wishlist
function addToWishlist(productId) {
    const productCard = document.querySelector(`.product-card[data-product-id="${productId}"]`) || 
                       document.querySelector(`[data-product-id="${productId}"]`);
    const wishlistBtn = productCard ? productCard.querySelector('.wishlist-btn') : 
                       document.querySelector(`.wishlist-btn[onclick*="addToWishlist(${productId})"]`) || 
                       document.querySelector(`button[onclick="addToWishlist(${productId})"]`);
    const icon = wishlistBtn ? wishlistBtn.querySelector('i') : null;
    const tooltip = wishlistBtn ? wishlistBtn.querySelector('.tooltip') : null;
    const isActive = wishlistBtn && wishlistBtn.classList.contains('active');
    const method = isActive ? 'DELETE' : 'POST';
    const url = isActive ? `/api/wishlist/${productId}` : '/api/wishlist';

    if (!wishlistBtn || !icon) {
        console.error('Wishlist button or icon not found for productId:', productId);
        Toastify({
            text: 'Error: Wishlist button not found.',
            duration: 4000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "#f87171",
            stopOnFocus: true
        }).showToast();
        return;
    }

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: method === 'POST' ? JSON.stringify({ product_id: productId }) : null,
        credentials: 'include'
    })
    .then(response => {
        if (response.status === 401) {
            Toastify({
                text: "Please login to add any item to your wishlist.",
                duration: 4000,
                close: true,
                gravity: "top",
                position: "right",
                backgroundColor: "#f87171",
                stopOnFocus: true
            }).showToast();
            setTimeout(() => {
                window.location.href = '/user_login';
            }, 4000);
            return null;
        }
        if (!response.ok) {
            throw new Error(`Failed to update wishlist: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            Toastify({
                text: data.message,
                duration: 3000,
                close: true,
                gravity: "top",
                position: "right",
                backgroundColor: "#4ade80",
                stopOnFocus: true
            }).showToast();
            wishlistBtn.classList.toggle('active');
            icon.classList.toggle('fas');
            icon.classList.toggle('far');
            if (tooltip) {
                tooltip.textContent = isActive ? 'Add to Wishlist' : 'Remove from Wishlist';
            }
        }
    })
    .catch(error => {
        if (error.message !== 'Failed to update wishlist: Unauthorized') {
            console.error('Error managing wishlist:', error);
            Toastify({
                text: 'Failed to update wishlist: ' + error.message,
                duration: 4000,
                close: true,
                gravity: "top",
                position: "right",
                backgroundColor: "#f87171",
                stopOnFocus: true
            }).showToast();
        }
    });
}

// Apply dynamic animation delays to story cards
document.querySelectorAll('#craft-stories [data-delay]').forEach(card => {
    const delay = card.getAttribute('data-delay');
    card.classList.add(`delay-${delay}`);
});

// Open Story Modal
function openStoryModal(storyId) {
    fetch(`/api/stories/${storyId}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        return response.json().then(data => ({ status: response.status, body: data }));
    })
    .then(({ status, body }) => {
        if (status >= 400) {
            throw new Error(body.error || 'Failed to load story');
        }
        document.getElementById('story-title').textContent = body.title;
        document.getElementById('story-text').textContent = body.content;
        document.getElementById('story-image').src = body.image ? `/static/uploads/${body.image}` : '/static/images/craft.jpg';
        document.getElementById('story-image').alt = body.title;
        openModal('story-modal');
    })
    .catch(error => {
        console.error('Error loading story:', error);
        Toastify({
            text: 'Failed to load story: ' + error.message,
            duration: 4000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "#f87171",
            stopOnFocus: true
        }).showToast();
        document.getElementById('story-title').textContent = 'Error';
        document.getElementById('story-text').textContent = 'Failed to load story. Please try again.';
        document.getElementById('story-image').src = '/static/images/craft.jpg';
        document.getElementById('story-image').alt = 'Error';
        openModal('story-modal');
    });
}

// Open Modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found`);
        return;
    }
    modal.classList.remove('hidden');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

// Close Modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found`);
        return;
    }
    modal.classList.remove('open');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Close modal on outside click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(modal.id);
        }
    });
});

// Send Email
document.getElementById('contact-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        subject: formData.get('subject'),
        message: formData.get('message'),
    };

    const showFlashMessage = (text, isSuccess) => {
        const flashMessage = document.getElementById('flash-message1');
        flashMessage.textContent = text;
        flashMessage.className = isSuccess ? 'success' : 'error';
        flashMessage.style.display = 'block';
        flashMessage.classList.add('show');
        setTimeout(() => {
            flashMessage.classList.remove('show');
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 500);
        }, 5000);
    };

    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'include',
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Failed to send message');
        showFlashMessage('Your message has been sent successfully! We will get back to you shortly', true);
        e.target.reset();
    } catch (error) {
        showFlashMessage(`Error: ${error.message}`, false);
    }
});