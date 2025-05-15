
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
    }catch (error) {
    showFlashMessage(`Please, login to send your email`, false);
    setTimeout(() => {
        window.location.href = '/user_login';
    }, 2000); // Wait 2 seconds before redirecting (adjust as needed)
}
});