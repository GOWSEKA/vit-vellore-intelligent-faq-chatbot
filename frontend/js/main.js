/**
 * Landing Page Interactivity & Navigation Script
 * ==============================================
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Accordion logic for Popular FAQs
    const faqItems = document.querySelectorAll(".faq-item");
    faqItems.forEach(item => {
        const btn = item.querySelector(".faq-question-btn");
        if (btn) {
            btn.addEventListener("click", () => {
                const isActive = item.classList.contains("active");
                // Close all others
                faqItems.forEach(other => other.classList.remove("active"));
                if (!isActive) {
                    item.classList.add("active");
                }
            });
        }
    });

    // 2. Category Cards Click -> Opens Chatbot with filter
    const catCards = document.querySelectorAll(".cat-card");
    catCards.forEach(card => {
        card.addEventListener("click", () => {
            const cat = card.getAttribute("data-category");
            if (cat) {
                window.location.href = `chat.html?category=${encodeURIComponent(cat)}`;
            } else {
                window.location.href = "chat.html";
            }
        });
    });

    // 3. Mini Sample Prompts in Hero
    const chipTags = document.querySelectorAll(".chip-tag");
    chipTags.forEach(chip => {
        chip.addEventListener("click", (e) => {
            e.preventDefault();
            const prompt = chip.innerText.trim();
            window.location.href = `chat.html?prompt=${encodeURIComponent(prompt)}`;
        });
    });

    // 4. Check backend API status
    const statusPill = document.getElementById("hero-status-pill");
    if (statusPill && window.VIT_CONFIG) {
        fetch(`${window.VIT_CONFIG.API_BASE_URL}${window.VIT_CONFIG.ENDPOINTS.HEALTH}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === "healthy") {
                    statusPill.innerHTML = `<span class="status-dot"></span> Online &bull; ${data.faq_count} Verified FAQs`;
                }
            })
            .catch(() => {
                // Friendly status if backend is sleeping or starting
                statusPill.innerHTML = `<span class="status-dot" style="background:#f59e0b;"></span> Knowledge Base Ready`;
            });
    }
});
