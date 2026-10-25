/**
 * Interactive Chatbot Interface Controller: Chatbot – Ask Me
 * =========================================================
 * Full client-side session management, API communication,
 * clarification choices, verified sources, and user feedback.
 */

class ChatController {
    constructor() {
        this.apiBase = window.VIT_CONFIG ? window.VIT_CONFIG.API_BASE_URL : "http://localhost:8000";
        this.sessionId = this.getOrInitSessionId();
        this.activeCategory = null;
        this.isWaiting = false;

        // DOM elements
        this.messagesContainer = document.getElementById("chat-messages");
        this.chatForm = document.getElementById("chat-form");
        this.inputField = document.getElementById("chat-input");
        this.sendBtn = document.getElementById("send-btn");
        this.statusPill = document.getElementById("connection-status-pill");
        this.categoryFilterLabel = document.getElementById("active-category-indicator");

        this.init();
    }

    getOrInitSessionId() {
        let sid = sessionStorage.getItem("vit_chat_session_id");
        if (!sid) {
            sid = "sess_" + Math.random().toString(36).substring(2, 12) + "_" + Date.now();
            sessionStorage.setItem("vit_chat_session_id", sid);
        }
        return sid;
    }

    init() {
        this.bindEvents();
        this.checkApiHealth();
        this.handleUrlParameters();
    }

    bindEvents() {
        // Form submit
        if (this.chatForm) {
            this.chatForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.handleUserSubmit();
            });
        }

        // Enter key handling
        if (this.inputField) {
            this.inputField.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.handleUserSubmit();
                }
            });
        }

        // Quick prompt buttons at bottom
        document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const prompt = btn.getAttribute("data-prompt") || btn.innerText;
                this.sendQuery(prompt);
            });
        });

        // Sidebar category filters
        document.querySelectorAll(".quick-category-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".quick-category-btn").forEach(b => b.classList.remove("active"));
                const cat = btn.getAttribute("data-category");
                if (this.activeCategory === cat) {
                    this.activeCategory = null;
                    if (this.categoryFilterLabel) this.categoryFilterLabel.style.display = "none";
                } else {
                    this.activeCategory = cat;
                    btn.classList.add("active");
                    if (this.categoryFilterLabel) {
                        this.categoryFilterLabel.style.display = "inline-flex";
                        this.categoryFilterLabel.innerText = `Filtering: ${cat}`;
                    }
                }
            });
        });

        // Clear Chat button
        const clearBtn = document.getElementById("clear-chat-btn");
        if (clearBtn) {
            clearBtn.addEventListener("click", () => this.clearChat());
        }

        // New Chat button
        const newChatBtn = document.getElementById("new-chat-btn");
        if (newChatBtn) {
            newChatBtn.addEventListener("click", () => this.startNewChat());
        }

        // Mobile sidebar toggle
        const toggleBtn = document.getElementById("sidebar-toggle");
        const sidebar = document.getElementById("chat-sidebar");
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener("click", () => {
                sidebar.classList.toggle("open");
            });
        }

        // Backend Settings Modal
        const settingsBtn = document.getElementById("settings-btn");
        const modal = document.getElementById("settings-modal");
        const saveApiBtn = document.getElementById("save-api-btn");
        const apiInput = document.getElementById("custom-api-input");
        const closeModalBtn = document.getElementById("close-modal-btn");

        if (settingsBtn && modal) {
            settingsBtn.addEventListener("click", () => {
                if (apiInput) apiInput.value = this.apiBase;
                modal.classList.add("active");
            });
        }
        if (closeModalBtn && modal) {
            closeModalBtn.addEventListener("click", () => modal.classList.remove("active"));
        }
        if (saveApiBtn && apiInput) {
            saveApiBtn.addEventListener("click", () => {
                const val = apiInput.value.trim();
                if (window.VIT_CONFIG) {
                    window.VIT_CONFIG.setApiBase(val);
                }
            });
        }
    }

    handleUrlParameters() {
        const params = new URLSearchParams(window.location.search);
        const prompt = params.get("prompt");
        const category = params.get("category");

        if (category) {
            this.activeCategory = category;
            const matchBtn = document.querySelector(`.quick-category-btn[data-category="${category}"]`);
            if (matchBtn) matchBtn.classList.add("active");
            if (this.categoryFilterLabel) {
                this.categoryFilterLabel.style.display = "inline-flex";
                this.categoryFilterLabel.innerText = `Filtering: ${category}`;
            }
        }

        if (prompt) {
            setTimeout(() => {
                this.sendQuery(prompt);
            }, 300);
        }
    }

    async checkApiHealth() {
        try {
            const res = await fetch(`${this.apiBase}/api/health`, { method: "GET" });
            const data = await res.json();
            if (data.status === "healthy" && this.statusPill) {
                this.statusPill.innerHTML = `&bull; Connected (${data.faq_count} verified FAQs)`;
                this.statusPill.style.color = "#16a34a";
            }
        } catch (e) {
            if (this.statusPill) {
                this.statusPill.innerHTML = `&bull; Service Standby (Click settings to verify API)`;
                this.statusPill.style.color = "#d97706";
            }
        }
    }

    handleUserSubmit() {
        const query = this.inputField.value.trim();
        if (!query || this.isWaiting) return;
        this.inputField.value = "";
        this.sendQuery(query);
    }

    async sendQuery(queryText) {
        if (!queryText || this.isWaiting) return;

        // Hide welcome card upon first message
        const welcome = document.getElementById("welcome-card");
        if (welcome) welcome.style.display = "none";

        // 1. Render User Message
        this.appendMessage({
            role: "user",
            text: queryText
        });

        // 2. Render Typing Indicator
        const typingId = this.showTypingIndicator();
        this.setWaiting(true);

        // 3. Make API Call
        try {
            const response = await fetch(`${this.apiBase}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: queryText,
                    session_id: this.sessionId,
                    category: this.activeCategory
                })
            });

            this.removeTypingIndicator(typingId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Server response was not ok`);
            }

            const data = await response.json();
            this.handleBotResponse(data);

        } catch (err) {
            this.removeTypingIndicator(typingId);
            this.appendMessage({
                role: "bot",
                text: "I am having difficulty connecting to the server. If this service was recently deployed on Render, it may be waking up from free-tier standby (takes ~30-40 seconds).",
                error: true,
                official_contacts: {
                    main_website: "https://vit.ac.in/",
                    admissions_email: "ugadmission@vit.ac.in",
                    helpline: "+91-416-2202020"
                }
            });
        } finally {
            this.setWaiting(false);
        }
    }

    handleBotResponse(data) {
        // Direct answer, clarification, or out-of-domain safe fallback
        this.appendMessage({
            role: "bot",
            text: data.answer,
            faq_id: data.faq_id,
            category: data.category,
            source: data.source,
            clarification_choices: data.clarification_choices,
            related_suggestions: data.related_suggestions,
            official_contacts: data.official_contacts,
            decision: data.decision
        });
    }

    appendMessage(msg) {
        const row = document.createElement("div");
        row.className = `message-row ${msg.role === "user" ? "user-row" : "bot-row"}`;

        let innerHtml = "";

        if (msg.role === "bot") {
            innerHtml += `
                <div class="chat-avatar-large" style="width:36px; height:36px; font-size:0.9rem; flex-shrink:0;">
                    VIT
                </div>
            `;
        }

        let bubbleHtml = `<div class="msg-bubble ${msg.role === "user" ? "user-bubble" : "bot-bubble"}">`;

        // Answer / message text with basic formatting
        const formattedText = this.escapeHtml(msg.text).replace(/\n/g, "<br>");
        bubbleHtml += `<div>${formattedText}</div>`;

        // Clarification Choices (if any)
        if (msg.clarification_choices && msg.clarification_choices.length > 0) {
            bubbleHtml += `<div class="clarification-choices-wrap">`;
            msg.clarification_choices.forEach(choice => {
                bubbleHtml += `
                    <button class="clarification-choice-btn" data-question="${this.escapeHtml(choice.question)}">
                        <span>👉 ${this.escapeHtml(choice.question)}</span>
                        <span style="font-size:0.75rem; color:#64748b;">[${this.escapeHtml(choice.category)}]</span>
                    </button>
                `;
            });
            bubbleHtml += `</div>`;
        }

        // Source Attribution Box (if official source exists)
        if (msg.source) {
            bubbleHtml += `
                <div class="source-box">
                    <div class="src-title">Verified Official Source &bull; ${this.escapeHtml(msg.source.title)}</div>
                    <div>Academic Year: ${this.escapeHtml(msg.source.academic_year)} | Verification: <span style="color:#16a34a; font-weight:600;">${this.escapeHtml(msg.source.verification_status)}</span></div>
                    <div>Link: <a href="${this.escapeHtml(msg.source.url)}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(msg.source.url)}</a></div>
                </div>
            `;
        }

        // Official Contacts Box (for out of domain / not found queries)
        if (msg.official_contacts) {
            bubbleHtml += `
                <div class="source-box" style="border-left-color: #d4af37; background: #fffbeb;">
                    <div class="src-title">Official VIT Vellore Contact Channels</div>
                    <div>Website: <a href="https://vit.ac.in/" target="_blank">https://vit.ac.in/</a></div>
                    <div>Admissions: ugadmission@vit.ac.in | 0416-2202020</div>
                    <div>COE Office: coe@vit.ac.in | 0416-2202144</div>
                </div>
            `;
        }

        // Related Question Suggestions (if any)
        if (msg.related_suggestions && msg.related_suggestions.length > 0) {
            bubbleHtml += `
                <div style="font-size:0.8rem; font-weight:600; color:#64748b; margin-top:0.75rem;">Related Topics:</div>
                <div class="suggestions-wrap">
            `;
            msg.related_suggestions.forEach(s => {
                bubbleHtml += `<button class="suggestion-pill" data-prompt="${this.escapeHtml(s)}">${this.escapeHtml(s)}</button>`;
            });
            bubbleHtml += `</div>`;
        }

        // Feedback Rating Buttons for bot answers
        if (msg.role === "bot" && !msg.error && msg.decision === "direct_answer") {
            bubbleHtml += `
                <div class="feedback-actions">
                    <span style="font-size:0.75rem; color:#94a3b8;">Was this helpful?</span>
                    <button class="feedback-btn" data-faq="${msg.faq_id || ''}" data-rating="5">👍 Yes</button>
                    <button class="feedback-btn" data-faq="${msg.faq_id || ''}" data-rating="1">👎 No</button>
                </div>
            `;
        }

        bubbleHtml += `</div>`;
        row.innerHTML = innerHtml + bubbleHtml;

        this.messagesContainer.appendChild(row);
        this.scrollToBottom();

        // Bind clarification and suggestion clicks inside this newly created bubble
        row.querySelectorAll(".clarification-choice-btn").forEach(b => {
            b.addEventListener("click", () => {
                const q = b.getAttribute("data-question");
                this.sendQuery(q);
            });
        });

        row.querySelectorAll(".suggestion-pill").forEach(b => {
            b.addEventListener("click", () => {
                const p = b.getAttribute("data-prompt");
                this.sendQuery(p);
            });
        });

        row.querySelectorAll(".feedback-btn").forEach(fbBtn => {
            fbBtn.addEventListener("click", () => {
                const rating = parseInt(fbBtn.getAttribute("data-rating"));
                const faqId = fbBtn.getAttribute("data-faq");
                this.sendFeedback(faqId, rating, fbBtn);
            });
        });
    }

    async sendFeedback(faqId, rating, btnElement) {
        try {
            await fetch(`${this.apiBase}/api/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    faq_id: faqId,
                    rating: rating
                })
            });
            const parent = btnElement.parentElement;
            if (parent) {
                parent.innerHTML = `<span style="font-size:0.78rem; color:#16a34a; font-weight:600;">✓ Feedback recorded. Thank you!</span>`;
            }
        } catch (e) {
            console.warn("Feedback recording deferred:", e);
        }
    }

    showTypingIndicator() {
        const id = "typing-" + Date.now();
        const row = document.createElement("div");
        row.className = "message-row bot-row";
        row.id = id;
        row.innerHTML = `
            <div class="chat-avatar-large" style="width:36px; height:36px; font-size:0.9rem; flex-shrink:0;">
                VIT
            </div>
            <div class="typing-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.messagesContainer.appendChild(row);
        this.scrollToBottom();
        return id;
    }

    removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    setWaiting(state) {
        this.isWaiting = state;
        if (this.sendBtn) this.sendBtn.disabled = state;
        if (this.inputField) this.inputField.disabled = state;
        if (!state && this.inputField) this.inputField.focus();
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    clearChat() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = "";
            const welcome = document.getElementById("welcome-card");
            if (welcome) welcome.style.display = "block";
        }
    }

    startNewChat() {
        sessionStorage.removeItem("vit_chat_session_id");
        this.sessionId = this.getOrInitSessionId();
        this.clearChat();
    }

    escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.chatController = new ChatController();
});
