-- ============================================================
-- BlessedBill — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS blessedbill
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE blessedbill;

-- ── Пользователи ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,
    email        VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url   VARCHAR(512) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB;

-- ── Группы ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `groups` (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NULL,
    owner_id    INT UNSIGNED NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_owner (owner_id)
) ENGINE=InnoDB;

-- ── Участники группы (many-to-many) ──────────────────────────
CREATE TABLE IF NOT EXISTS group_members (
    id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id  INT UNSIGNED NOT NULL,
    user_id   INT UNSIGNED NOT NULL,
    role      ENUM('member', 'admin') NOT NULL DEFAULT 'member',
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(id)    ON DELETE CASCADE,
    UNIQUE KEY uq_group_user (group_id, user_id)
) ENGINE=InnoDB;

-- ── Счета ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bills (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id     INT UNSIGNED   NOT NULL,
    payer_id     INT UNSIGNED   NOT NULL,
    title        VARCHAR(200)   NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    currency     CHAR(3)        NOT NULL DEFAULT 'RUB',
    split_type   ENUM('equal', 'custom', 'percentage') NOT NULL DEFAULT 'equal',
    status       ENUM('open', 'settled') NOT NULL DEFAULT 'open',
    created_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    settled_at   DATETIME       NULL,
    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (payer_id) REFERENCES users(id)    ON DELETE RESTRICT,
    INDEX idx_group  (group_id),
    INDEX idx_payer  (payer_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ── Доли участников в счёте ───────────────────────────────────
CREATE TABLE IF NOT EXISTS bill_splits (
    id      INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    bill_id INT UNSIGNED   NOT NULL,
    user_id INT UNSIGNED   NOT NULL,
    amount  DECIMAL(12, 2) NOT NULL,
    is_paid BOOLEAN        NOT NULL DEFAULT FALSE,
    paid_at DATETIME       NULL,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_bill_user (bill_id, user_id),
    INDEX idx_user_paid (user_id, is_paid)
) ENGINE=InnoDB;
