-- ====================================================================
-- MySQL Database Schema for VIT Vellore Intelligent FAQ Chatbot
-- ====================================================================

CREATE DATABASE IF NOT EXISTS vit_faq_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE vit_faq_db;

-- 1. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. FAQs Knowledge Base Table
CREATE TABLE IF NOT EXISTS faqs (
    faq_id VARCHAR(32) PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    campus VARCHAR(50) DEFAULT 'VIT Vellore',
    academic_year VARCHAR(20) DEFAULT '2025-2026',
    source_url VARCHAR(255),
    source_title VARCHAR(255),
    source_type VARCHAR(50) DEFAULT 'official_website',
    collected_at DATETIME,
    verification_status VARCHAR(50) DEFAULT 'verified_official',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    FULLTEXT idx_faq_search (question, answer)
) ENGINE=InnoDB;

-- 3. Chat Interaction Logs Table
CREATE TABLE IF NOT EXISTS chat_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    query TEXT NOT NULL,
    decision VARCHAR(50),
    faq_id VARCHAR(32),
    category VARCHAR(100),
    confidence DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- 4. User Feedback Table
CREATE TABLE IF NOT EXISTS user_feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    faq_id VARCHAR(32),
    user_query TEXT,
    rating TINYINT NOT NULL COMMENT '1 to 5 scale',
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_feedback_faq (faq_id)
) ENGINE=InnoDB;
