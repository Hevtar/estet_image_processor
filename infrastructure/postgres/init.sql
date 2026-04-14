-- ========================================
-- ESTET Platform - Initial Database Schema
-- ========================================

-- Enable PGVector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- Collections
-- ========================================
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    url VARCHAR(500),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_slug ON collections(slug);

-- ========================================
-- Products
-- ========================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,

    -- Основные данные
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,

    -- Описания
    original_description TEXT,
    ai_semantic_description TEXT,

    -- Характеристики
    style VARCHAR(100),
    color_family VARCHAR(50),
    material VARCHAR(255),
    finish_type VARCHAR(100),
    special_features TEXT[],

    -- URLs
    product_url VARCHAR(500) NOT NULL,
    main_image_url VARCHAR(500),

    -- Мета-данные
    price DECIMAL(10, 2),
    available_sizes TEXT[],

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_scraped_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_collection ON products(collection_id);
CREATE INDEX IF NOT EXISTS idx_products_style ON products(style);
CREATE INDEX IF NOT EXISTS idx_products_color ON products(color_family);

-- Full-text search
CREATE INDEX IF NOT EXISTS idx_products_fts ON products
USING gin(to_tsvector('russian', name || ' ' || COALESCE(ai_semantic_description, '')));

-- ========================================
-- Product Images
-- ========================================
CREATE TABLE IF NOT EXISTS product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,

    original_url VARCHAR(500) NOT NULL,
    local_path VARCHAR(500),
    image_hash VARCHAR(64),

    is_primary BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,

    width INTEGER,
    height INTEGER,
    size_bytes INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_images_product ON product_images(product_id);
CREATE INDEX IF NOT EXISTS idx_product_images_primary ON product_images(product_id, is_primary);

-- ========================================
-- Product Embeddings
-- ========================================
CREATE TABLE IF NOT EXISTS product_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,

    embedding vector(768) NOT NULL,
    embedding_type VARCHAR(50) DEFAULT 'semantic',
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- IVFFlat индекс для быстрого векторного поиска
CREATE INDEX IF NOT EXISTS idx_product_embeddings_vector ON product_embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_product_embeddings_product ON product_embeddings(product_id);

-- ========================================
-- Parsing Logs
-- ========================================
CREATE TABLE IF NOT EXISTS parsing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(50),

    products_found INTEGER DEFAULT 0,
    products_processed INTEGER DEFAULT 0,
    products_failed INTEGER DEFAULT 0,

    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parsing_logs_status ON parsing_logs(status);
CREATE INDEX IF NOT EXISTS idx_parsing_logs_started ON parsing_logs(started_at DESC);

-- ========================================
-- Constraints
-- ========================================
ALTER TABLE products DROP CONSTRAINT IF EXISTS valid_category;
ALTER TABLE products ADD CONSTRAINT valid_category
CHECK (category IN (
    'Двери межкомнатные', 'Стеновые панели', 'Порталы каминные', 'Другое',
    'Скрытые двери', 'Входные двери', 'Межкомнатные перегородки',
    'Мебель', 'Декоративные рейки', 'Зеркала', 'Противопожарные двери',
    'Специализированные двери', 'Дверной декор', 'Дверная фурнитура',
    'Системы открывания', 'Корпусная мебель'
));

ALTER TABLE products DROP CONSTRAINT IF EXISTS valid_style;
ALTER TABLE products ADD CONSTRAINT valid_style
CHECK (style IN (
    'классика', 'неоклассика', 'современный', 'минимализм',
    'лофт', 'скандинавский', 'арт-деко', 'unknown',
    'классический', 'неоклассический', 'дизайнерский',
    'джапанди', 'бионика', 'другое'
));

-- ========================================
-- Composite indexes
-- ========================================
CREATE INDEX IF NOT EXISTS idx_products_category_style ON products(category, style);
CREATE INDEX IF NOT EXISTS idx_products_collection_category ON products(collection_id, category);

-- ========================================
-- Success message
-- ========================================
DO $$
BEGIN
    RAISE NOTICE '✅ ESTET Platform database schema initialized successfully';
END $$;
