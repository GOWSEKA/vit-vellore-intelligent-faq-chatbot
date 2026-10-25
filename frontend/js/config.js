/**
 * Dynamic API Configuration for Local Development & Public Production
 * ===================================================================
 * Automatically selects backend API endpoint based on hostname:
 * - Direct on Render (*.onrender.com): Uses same origin window.location.origin
 * - GitHub Pages (*.github.io): Uses live Render backend URL
 * - Localhost / 127.0.0.1: http://localhost:8000
 */

const CONFIG = (() => {
    // Official live Render backend service URL
    const PRODUCTION_API_URL = "https://vit-vellore-intelligent-faq-chatbot.onrender.com";
    const LOCAL_API_URL = "http://localhost:8000";

    const hostname = window.location.hostname;
    const isLocal = hostname === "localhost" ||
                    hostname === "127.0.0.1" ||
                    window.location.protocol === "file:";

    const isServedFromRender = hostname.includes("onrender.com");

    // Allow user or developer override via localStorage
    const storedOverride = localStorage.getItem("vit_chatbot_api_url");

    let apiBase;
    if (storedOverride && storedOverride.trim() !== "") {
        apiBase = storedOverride.trim();
    } else if (isServedFromRender) {
        // When visiting the website directly on Render, stay on same origin
        apiBase = window.location.origin;
    } else if (isLocal) {
        // When running locally
        apiBase = (window.location.port === "8000") ? window.location.origin : LOCAL_API_URL;
    } else {
        // When running on GitHub Pages (e.g. gowseka.github.io)
        apiBase = PRODUCTION_API_URL;
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
        IS_RENDER: isServedFromRender,
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
