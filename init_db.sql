CREATE DATABASE IF NOT EXISTS minecraft_autologin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE minecraft_autologin;

-- 账号表
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    level INT DEFAULT 0,
    mcname VARCHAR(100) DEFAULT 'Unknown',
    subscription VARCHAR(255) DEFAULT '',
    hypixel TEXT,
    capes TEXT,
    cookie_status VARCHAR(50) DEFAULT 'none',
    last_login DATETIME,
    created_at DATETIME NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    INDEX idx_email (email),
    INDEX idx_disabled (disabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cookie表
CREATE TABLE IF NOT EXISTS cookies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    cookie_data LONGTEXT NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 卡密表
CREATE TABLE IF NOT EXISTS cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_key VARCHAR(100) NOT NULL UNIQUE,
    duration VARCHAR(50) NOT NULL,
    duration_days INT NOT NULL,
    type VARCHAR(20) DEFAULT 'normal',
    created_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at DATETIME,
    expire_at DATETIME,
    INDEX idx_card_key (card_key),
    INDEX idx_used (used)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 管理员表
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
