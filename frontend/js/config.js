/**
 * Dynamic API Configuration for Local Development & Public Production
 * ===================================================================
 * Automatically selects backend API endpoint based on hostname:
 * - Localhost: http://localhost:8000
 * - GitHub Pages: Uses configured Render production URL or custom URL
 */

const CONFIG = (() => {
    const isLocal = window.location.hostname === "localhost" ||
                    window.location.hostname === "127.0.0.1" ||
                    window.location.protocol === "file:";

    // Default production backend URL on Render (will be updated upon deployment)
    const PRODUCTION_API_URL = "https://vit-vellore-faq-chatbot.onrender.com";
    const LOCAL_API_URL = "http://localhost:8000";

    // Allow user or developer override via localStorage
    const storedOverride = localStorage.getItem("vit_chatbot_api_url");

    let apiBase = isLocal ? LOCAL_API_URL : PRODUCTION_API_URL;
    if (storedOverride && storedOverride.trim() !== "") {
        apiBase = storedOverride.trim();
    }

    return {
        API_BASE_URL: apiBase.replace(/\/+$/, ""),
        ENDPOINTS: {
            HEALTH: "/api/health",
            CHAT: "/api/chat",
            FEEDBACK: "/api/feedback",
            CATEGORIES: "/api/categories",
            FAQS: "/api/faqs"
        },
        IS_LOCAL: isLocal,
        setApiBase: (newUrl) => {
            if (newUrl) {
                localStorage.setItem("vit_chatbot_api_url", newUrl.trim());
            } else {
                localStorage.removeItem("vit_chatbot_api_url");
            }
            window.location.reload();
        }
    };
})();

// Expose globally
window.VIT_CONFIG = CONFIG;
