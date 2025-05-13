$(document).ready(function() {
    // Mobile Navbar Toggle
    $('#nav-toggler').click(function() {
        $('#mobile-sidebar').removeClass('-translate-x-full');
    });
    $('#close-sidebar').click(function() {
        $('#mobile-sidebar').addClass('-translate-x-full');
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
    $('#discount-btn').click(function() {
        $('#discount-page').removeClass('-translate-x-full');
    });
    $('#close-discount').click(function() {
        $('#discount-page').addClass('-translate-x-full');
    });
});

// Featured This Month Tabs
function showTab(tabId) {
    const tabs = document.querySelectorAll('#featured-this-month .ftm-tab');
    const contents = document.querySelectorAll('#featured-this-month .ftm-tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));
    document.querySelector(`#featured-this-month .ftm-tab[onclick="showTab('${tabId}')"]`).classList.add('active');
    document.querySelector(`#tab-${tabId}`).classList.add('active');
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
    const totalSlidesLarge = 3; // 3 slides for large screens (2 reviews each)
    let currentSlideSmall = 0;
    const totalSlidesSmall = 6; // 6 slides for small screens (1 review each)
    let autoSlideInterval = null;

    function updateSlider() {
        console.log('Updating slider:', { currentSlideLarge, currentSlideSmall });
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
        console.log('Previous button clicked');
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
        console.log('Next button clicked');
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
        alert('Error: Wishlist button not found.');
        return;
    }

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: method === 'POST' ? JSON.stringify({ product_id: productId }) : null,
        credentials: 'include' // Ensure session cookie is sent
    })
    .then(response => {
        if (response.status === 401) {
            alert('Please login to add any item to your wishlist.');
            window.location.href = '/user_login';
            return null;
        }
        if (!response.ok) {
            throw new Error(`Failed to update wishlist: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            alert(data.message); // Show success message (e.g., "Added to wishlist successfully")
            // Toggle button state
            wishlistBtn.classList.toggle('active');
            icon.classList.toggle('fas');
            icon.classList.toggle('far');
            // Update tooltip if it exists
            if (tooltip) {
                tooltip.textContent = isActive ? 'Add to Wishlist' : 'Remove from Wishlist';
            }
        }
    })
    .catch(error => {
        if (error.message !== 'Failed to update wishlist: Unauthorized') {
            console.error('Error managing wishlist:', error);
            alert('Failed to update wishlist: ' + error.message);
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
    console.log('Opening modal for storyId:', storyId); // Debug: Confirm storyId
    fetch(`/api/stories/${storyId}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        console.log('API response status:', response.status); // Debug: Log status
        return response.json().then(data => ({ status: response.status, body: data }));
    })
    .then(({ status, body }) => {
        if (status >= 400) {
            throw new Error(body.error || 'Failed to load story');
        }
        console.log('API response body:', body); // Debug: Log response data
        // Populate modal content
        document.getElementById('story-title').textContent = body.title;
        document.getElementById('story-text').textContent = body.content; // Full content
        document.getElementById('story-image').src = body.image ? `/static/uploads/${body.image}` : '/static/images/craft.jpg';
        document.getElementById('story-image').alt = body.title;
        // Open modal
        openModal('story-modal');
    })
    .catch(error => {
        console.error('Error loading story:', error);
        alert('Failed to load story: ' + error.message);
        // Fallback: Open modal with error message
        document.getElementById('story-title').textContent = 'Error';
        document.getElementById('story-text').textContent = 'Failed to load story. Please try again.';
        document.getElementById('story-image').src = '/static/images/craft.jpg';
        document.getElementById('story-image').alt = 'Error';
        openModal('story-modal');
    });
}

// Open modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found`);
        return;
    }
    modal.classList.remove('hidden'); // Remove hidden class
    modal.classList.add('open'); // Add open class
    document.body.style.overflow = 'hidden';
    console.log(`Modal ${modalId} opened`); // Debug: Confirm modal opened
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found`);
        return;
    }
    modal.classList.remove('open');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
    console.log(`Modal ${modalId} closed`); // Debug: Confirm modal closed
}

// Close modal on outside click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(modal.id);
        }
    });
});

// Test modal on page load (optional, remove after testing)
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, modal element:', document.getElementById('story-modal')); // Debug: Check modal exists
});

// send email
document.getElementById('contact-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('Form submitted'); // Debug
    const formData = new FormData(e.target);
    const data = {
        subject: formData.get('subject'),
        message: formData.get('message'),
    };
    console.log('Form data:', data); // Debug

    // Function to show flash message
    const showFlashMessage = (text, isSuccess) => {
        console.log('Showing flash message:', text, isSuccess); // Debug
        const flashMessage = document.getElementById('flash-message1');
        flashMessage.textContent = text;
        flashMessage.className = isSuccess ? 'success' : 'error';
        flashMessage.style.display = 'block';
        flashMessage.classList.add('show');

        // Hide after 5 seconds
        setTimeout(() => {
            flashMessage.classList.remove('show');
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 500); // Wait for fade-out animation
        }, 5000);
    };

    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'include',
        });
        console.log('Response status:', response.status); // Debug
        const result = await response.json();
        console.log('Response data:', result); // Debug
        if (!response.ok) throw new Error(result.error || 'Failed to send message');
        showFlashMessage('Your message has been sent successfully! We will get back to you shortly', true);
        e.target.reset();
    } catch (error) {
        console.error('Error:', error.message); // Debug
        showFlashMessage(`Error: ${error.message}`, false);
    }
});