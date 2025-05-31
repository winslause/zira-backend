
// Currency Conversion Logic (KES as base currency)
let exchangeRates = {
  EUR: 0.0073, // Fallback rates
  GBP: 0.0061,
  KES: 1,
  USD: 0.0077
};
let currentCurrency = localStorage.getItem('currency') || 'KES';

// API Configuration
const API_URL = '/api/exchange_rates';
const SUPPORTED_CURRENCIES = ['EUR', 'GBP', 'KES', 'USD'].sort();

// Fetch Exchange Rates from Backend
async function fetchExchangeRates() {
  console.log('Fetching exchange rates from:', API_URL);
  try {
    const response = await fetch(API_URL, { credentials: 'include' });
    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`);
      throw new Error('Failed to fetch exchange rates');
    }
    const rates = await response.json();
    if (!rates.EUR || !rates.GBP || !rates.KES || !rates.USD) {
      console.error('Invalid backend response:', rates);
      throw new Error('Invalid exchange rates');
    }
    exchangeRates = { ...rates };
    console.log('Fetched exchange rates:', exchangeRates);
    updatePrices();
  } catch (error) {
    console.error('Error fetching exchange rates:', error);
    console.warn('Using fallback exchange rates');
    updatePrices();
  }
}

// Initialize Currency Button
function initializeCurrencyButton() {
  const storedCountry = localStorage.getItem('country') || 'Kenya';
  const storedFlag = localStorage.getItem('flag') || '🇰🇪';
  const storedCurrency = localStorage.getItem('currency') || currentCurrency;
  currentCurrency = storedCurrency;

  const countryBtn = document.getElementById('country-btn');
  const mobileCountryBtn = document.getElementById('mobile-country-btn');
  if (countryBtn) {
    countryBtn.innerHTML = `<span class="flag">${storedFlag}</span> ${storedCurrency}`;
  }
  if (mobileCountryBtn) {
    mobileCountryBtn.innerHTML = `<span class="flag">${storedFlag}</span> ${storedCurrency}`;
  }
  document.querySelectorAll('#country-btn-container, #mobile-country-btn-container').forEach(container => {
    container.classList.add('currency-loaded');
  });
  updatePrices();
}

// Update Prices
function updatePrices() {
  if (!exchangeRates[currentCurrency]) {
    console.warn(`Invalid currency: ${currentCurrency}, defaulting to KES`);
    currentCurrency = 'KES';
    localStorage.setItem('currency', currentCurrency);
  }

  document.querySelectorAll('#featured-this-month .ftm-card').forEach(card => {
    const priceElement = card.querySelector('.ftm-price');
    const oldPriceElement = card.querySelector('.ftm-old-price');
    const basePriceKES = priceElement ? parseFloat(priceElement.getAttribute('data-price')) : NaN;
    const baseOldPriceKES = oldPriceElement ? parseFloat(oldPriceElement.getAttribute('data-old-price')) : null;

    if (!priceElement || isNaN(basePriceKES)) {
      console.warn('Invalid price data for card:', {
        cardId: card.dataset.productId || 'unknown',
        productName: card.querySelector('.ftm-product-name')?.textContent || 'unknown',
        basePriceKES,
        baseOldPriceKES,
        tab: card.closest('.ftm-tab-content')?.id || 'unknown'
      });
      if (priceElement) priceElement.innerHTML = `${currentCurrency} N/A`;
      return;
    }

    const convertedPrice = (basePriceKES * exchangeRates[currentCurrency]).toFixed(2);
    if (oldPriceElement && !isNaN(baseOldPriceKES) && baseOldPriceKES > basePriceKES) {
      const convertedOldPrice = (baseOldPriceKES * exchangeRates[currentCurrency]).toFixed(2);
      priceElement.innerHTML = `${currentCurrency} ${convertedPrice} <span class="ftm-old-price" data-old-price="${baseOldPriceKES}">${currentCurrency} ${convertedOldPrice}</span>`;
    } else {
      priceElement.innerHTML = `${currentCurrency} ${convertedPrice}`;
    }
  });
}

// Add to Wishlist
function addToWishlist(productId) {
  const productCard = document.querySelector(`.product-card[data-product-id="${productId}"]`) ||
                     document.querySelector(`[data-product-id="${productId}"]`);
  const wishlistBtn = productCard?.querySelector('.wishlist-btn') ||
                     document.querySelector(`.wishlist-btn[onclick*="addToWishlist(${productId})"]`) ||
                     document.querySelector(`button[onclick="addToWishlist(${productId})"]`);
  const icon = wishlistBtn?.querySelector('i');
  const tooltip = wishlistBtn?.querySelector('.tooltip');
  if (!wishlistBtn || !icon) {
    console.error('Wishlist button or icon not found for productId:', productId);
    Toastify({
      text: 'Error: Wishlist button not found.',
      duration: 4000,
      close: true,
      gravity: 'top',
      position: 'right',
      backgroundColor: '#f87171',
      stopOnFocus: true
    }).showToast();
    return;
  }

  const isActive = wishlistBtn.classList.contains('active');
  const method = isActive ? 'DELETE' : 'POST';
  const url = isActive ? `/api/wishlist/${productId}` : '/api/wishlist';

  fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: method === 'POST' ? JSON.stringify({ product_id: productId }) : null,
    credentials: 'include'
  })
    .then(response => {
      if (response.status === 401) {
        Toastify({
          text: 'Please login to add any item to your wishlist.',
          duration: 4000,
          close: true,
          gravity: 'top',
          position: 'right',
          backgroundColor: '#f87171',
          stopOnFocus: true
        }).showToast();
        setTimeout(() => window.location.href = '/user_login', 4000);
        return null;
      }
      if (!response.ok) throw new Error(`Failed to update wishlist: ${response.statusText}`);
      return response.json();
    })
    .then(data => {
      if (data) {
        Toastify({
          text: data.message,
          duration: 3000,
          close: true,
          gravity: 'top',
          position: 'right',
          backgroundColor: '#4ade80',
          stopOnFocus: true
        }).showToast();
        wishlistBtn.classList.toggle('active');
        icon.classList.toggle('fas');
        icon.classList.toggle('far');
        if (tooltip) tooltip.textContent = isActive ? 'Add to Wishlist' : 'Remove from Wishlist';
      }
    })
    .catch(error => {
      if (error.message !== 'Failed to update wishlist: Unauthorized') {
        console.error('Error managing wishlist:', error);
        Toastify({
          text: 'Failed to update wishlist: ' + error.message,
          duration: 4000,
          close: true,
          gravity: 'top',
          position: 'right',
          backgroundColor: '#f87171',
          stopOnFocus: true
        }).showToast();
      }
    });
}

// Open Story Modal
function openStoryModal(storyId) {
  fetch(`/api/stories/${storyId}`, { credentials: 'include' })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
      if (status >= 400) throw new Error(body.error || 'Failed to load story');
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
        gravity: 'top',
        position: 'right',
        backgroundColor: '#f87171',
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

// Featured This Month Tabs
function showTab(tabId) {
  const tabs = document.querySelectorAll('#featured-this-month .ftm-tab');
  const contents = document.querySelectorAll('#featured-this-month .ftm-tab-content');
  tabs.forEach(tab => tab.classList.remove('active'));
  contents.forEach(content => content.classList.remove('active'));
  const tabElement = document.querySelector(`#featured-this-month .ftm-tab[onclick="showTab('${tabId}')"]`);
  const contentElement = document.querySelector(`#tab-${tabId}`);
  if (tabElement && contentElement) {
    tabElement.classList.add('active');
    contentElement.classList.add('active');
    setTimeout(() => updatePrices(), 0);
  } else {
    console.error('Tab or content not found for tabId:', tabId);
  }
}

// jQuery Document Ready
$(document).ready(function() {
  // Mobile Navbar Toggle
  $('#nav-toggler').click(function() {
    $('#mobile-sidebar').toggleClass('-translate-x-full');
    $(this).find('i').toggleClass('fa-bars fa-times');
  });
  $('#close-sidebar').click(function() {
    $('#mobile-sidebar').addClass('-translate-x-full');
    $('#nav-toggler').find('i').removeClass('fa-times').addClass('fa-bars');
  });

  // Mobile Search Bar Toggle
  $('#mobile-search-icon').click(function() {
    $('#mobile-search-bar').toggleClass('hidden');
  });

  // Close Mobile Search Bar on Outside Click
  $(document).click(function(event) {
    const searchBar = $('#mobile-search-bar');
    const searchIcon = $('#mobile-search-icon');
    if (!searchBar.is(event.target) && !searchIcon.is(event.target) && searchBar.has(event.target).length === 0) {
      searchBar.addClass('hidden');
    }
  });

  // Category Dropdowns for Desktop
  $('.nav-hover').each(function() {
    const $dropdown = $(this).find('.dropdown-menu');
    if ($dropdown.length) {
      $(this).hover(
        function() {
          $dropdown.removeClass('hidden').css({
            opacity: 1,
            visibility: 'visible',
            transform: 'translateY(0)'
          });
        },
        function() {
          $dropdown.addClass('hidden').css({
            opacity: 0,
            visibility: 'hidden',
            transform: 'translateY(-10px)'
          });
        }
      );
    }
  });

  // Mobile Sidebar Subcategory Toggle
  $('.toggle-subcategories').click(function() {
    const $button = $(this);
    const $icon = $button.find('.fa-chevron-down');
    const $subcategories = $button.closest('.category-item').find('.subcategories');
    $subcategories.slideToggle(300, function() {
      $subcategories.toggleClass('active');
      $icon.toggleClass('active');
    });
  });

  // Hero Slider
  let currentSlide = 0;
  const slides = $('.hero-slide');
  const dots = $('.dot');
  slides.eq(currentSlide).addClass('active');
  dots.eq(currentSlide).addClass('active');

  function showSlide(index) {
    slides.eq(currentSlide).removeClass('active');
    dots.eq(currentSlide).removeClass('active');
    currentSlide = index;
    slides.eq(currentSlide).addClass('active');
    dots.eq(currentSlide).addClass('active');
  }

  let autoSlide = setInterval(function() {
    let nextSlide = (currentSlide + 1) % slides.length;
    showSlide(nextSlide);
  }, 5000);

  dots.each(function(index) {
    $(this).click(function() {
      clearInterval(autoSlide);
      showSlide(index);
      autoSlide = setInterval(function() {
        let nextSlide = (currentSlide + 1) % slides.length;
        showSlide(nextSlide);
      }, 5000);
    });
  });

  // Discount Popup
  $('.discount-btn-container .floating-btn').click(function() {
    $('#discount-page').removeClass('-translate-x-full');
  });
  $('#close-discount').click(function() {
    $('#discount-page').addClass('-translate-x-full');
  });
});

// Vanilla JS Document Ready
document.addEventListener('DOMContentLoaded', () => {
  // Currency Dropdown Toggle
  const countryBtn = document.getElementById('country-btn');
  const mobileCountryBtn = document.getElementById('mobile-country-btn');

  if (countryBtn) {
    countryBtn.addEventListener('click', () => {
      const dropdown = document.getElementById('country-dropdown');
      if (dropdown) dropdown.classList.toggle('hidden');
    });
  }

  if (mobileCountryBtn) {
    mobileCountryBtn.addEventListener('click', () => {
      const dropdown = document.getElementById('mobile-country-dropdown');
      if (dropdown) dropdown.classList.toggle('hidden');
    });
  }

  // Currency Selection
  document.querySelectorAll('.country-option').forEach(option => {
    option.addEventListener('click', async (e) => {
      e.preventDefault();
      const country = e.target.getAttribute('data-country');
      const flag = e.target.getAttribute('data-flag');
      currentCurrency = e.target.getAttribute('data-currency');

      if (countryBtn) {
        countryBtn.innerHTML = `<span class="flag">${flag}</span> ${currentCurrency}`;
      }
      if (mobileCountryBtn) {
        mobileCountryBtn.innerHTML = `<span class="flag">${flag}</span> ${currentCurrency}`;
      }

      const desktopDropdown = document.getElementById('country-dropdown');
      const mobileDropdown = document.getElementById('mobile-country-dropdown');
      if (desktopDropdown) desktopDropdown.classList.add('hidden');
      if (mobileDropdown) mobileDropdown.classList.add('hidden');

      localStorage.setItem('currency', currentCurrency);
      localStorage.setItem('country', country);
      localStorage.setItem('flag', flag);

      try {
        const response = await fetch('/set_currency', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ currency: currentCurrency }),
          credentials: 'include'
        });
        if (!response.ok) {
          console.error('Failed to set currency:', response.status, response.statusText);
          Toastify({
            text: 'Failed to change currency',
            duration: 3000,
            close: true,
            gravity: 'top',
            position: 'right',
            backgroundColor: '#f87171',
            stopOnFocus: true
          }).showToast();
        } else {
          await fetchExchangeRates();
          Toastify({
            text: `Currency changed to ${currentCurrency}`,
            duration: 3000,
            close: true,
            gravity: 'top',
            position: 'right',
            backgroundColor: '#4ade80',
            stopOnFocus: true
          }).showToast();
        }
      } catch (error) {
        console.error('Error setting currency:', error);
        Toastify({
          text: 'Failed to change currency',
          duration: 3000,
          close: true,
          gravity: 'top',
          position: 'right',
          backgroundColor: '#f87171',
          stopOnFocus: true
        }).showToast();
        updatePrices(); // Fallback to local update
      }
    });
  });

  // Review Slider
  const prevBtn = document.getElementById('prevReview');
  const nextBtn = document.getElementById('nextReview');
  const sliderLarge = document.getElementById('reviewSliderLargeInner');
  const sliderSmall = document.getElementById('reviewSliderSmallInner');
  const reviewSection = document.getElementById('zira-customer-reviews');

  if (prevBtn && nextBtn && sliderLarge && sliderSmall && reviewSection) {
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
        if (currentSlideLarge > 0) currentSlideLarge--;
      } else {
        if (currentSlideSmall > 0) currentSlideSmall--;
      }
      updateSlider();
      stopAutoSlide();
      startAutoSlide();
    });

    nextBtn.addEventListener('click', () => {
      if (window.innerWidth >= 768) {
        if (currentSlideLarge < totalSlidesLarge - 1) currentSlideLarge++;
      } else {
        if (currentSlideSmall < totalSlidesSmall - 1) currentSlideSmall++;
      }
      updateSlider();
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
  }

  // Close Modal on Outside Click
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(modal.id);
    });
  });

  // Apply Animation Delays to Story Cards
  document.querySelectorAll('#craft-stories [data-delay]').forEach(card => {
    const delay = card.getAttribute('data-delay');
    card.classList.add(`delay-${delay}`);
  });

  // Initialize Currency and Fetch Rates
  initializeCurrencyButton();
  fetchExchangeRates();
});
