ALTER TABLE inventory ADD COLUMN markup_percentage FLOAT DEFAULT 0;
ALTER TABLE inventory ADD COLUMN sale_price FLOAT;
ALTER TABLE inventory ADD COLUMN notes TEXT; 