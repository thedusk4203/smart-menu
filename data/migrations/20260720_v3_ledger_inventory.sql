BEGIN;

-- Planner V3 is now the only supported planner contract. Remove the two
-- legacy plan families together with their materialized shopping state.
WITH legacy_plans AS (
    SELECT id
    FROM meal_plans
    WHERE COALESCE((plan_data->>'schema_version')::integer, 1) < 3
)
DELETE FROM shopping_list_shares
WHERE meal_plan_id IN (SELECT id FROM legacy_plans);

WITH legacy_plans AS (
    SELECT id
    FROM meal_plans
    WHERE COALESCE((plan_data->>'schema_version')::integer, 1) < 3
)
DELETE FROM shopping_lists
WHERE meal_plan_id IN (SELECT id FROM legacy_plans);

DELETE FROM meal_plans
WHERE COALESCE((plan_data->>'schema_version')::integer, 1) < 3;

ALTER TABLE shopping_lists ALTER COLUMN item_kind SET DEFAULT 'purchase';
ALTER TABLE shopping_lists DROP CONSTRAINT IF EXISTS ck_shopping_list_item_kind;
ALTER TABLE shopping_lists ADD CONSTRAINT ck_shopping_list_item_kind
    CHECK (item_kind IN ('purchase', 'pantry'));

CREATE TABLE IF NOT EXISTS inventory_lots (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity_remaining NUMERIC(12,2) NOT NULL CHECK (quantity_remaining >= 0),
    unit VARCHAR(20) NOT NULL,
    purchase_increment NUMERIC(10,2) NOT NULL CHECK (purchase_increment > 0),
    available_from DATE NOT NULL,
    expires_on DATE NOT NULL,
    storage_mode VARCHAR(20) NOT NULL
        CHECK (storage_mode IN ('room', 'fridge', 'freezer', 'same_day')),
    cost_basis_per_unit NUMERIC(14,4) NOT NULL DEFAULT 0
        CHECK (cost_basis_per_unit >= 0),
    source_plan_id INTEGER REFERENCES meal_plans(id) ON DELETE RESTRICT,
    source_item_key VARCHAR(160),
    status VARCHAR(20) NOT NULL DEFAULT 'projected'
        CHECK (status IN ('projected', 'available', 'consumed', 'expired', 'discarded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_inventory_lot_dates CHECK (expires_on >= available_from),
    CONSTRAINT uq_inventory_source_lot UNIQUE (source_plan_id, source_item_key)
);

CREATE INDEX IF NOT EXISTS idx_inventory_lots_user_window
    ON inventory_lots(user_id, available_from, expires_on)
    WHERE status IN ('projected', 'available') AND quantity_remaining > 0;

CREATE TABLE IF NOT EXISTS inventory_reservations (
    id BIGSERIAL PRIMARY KEY,
    inventory_lot_id BIGINT NOT NULL REFERENCES inventory_lots(id) ON DELETE CASCADE,
    meal_plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    item_key VARCHAR(160) NOT NULL,
    quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    use_day SMALLINT NOT NULL CHECK (use_day BETWEEN 1 AND 7),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inventory_reservation UNIQUE (meal_plan_id, item_key, use_day)
);

CREATE INDEX IF NOT EXISTS idx_inventory_reservations_lot
    ON inventory_reservations(inventory_lot_id);

COMMIT;
