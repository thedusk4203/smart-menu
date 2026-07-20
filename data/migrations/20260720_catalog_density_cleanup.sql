BEGIN;

-- Replace import placeholders with reviewed g/ml conversion factors. Values
-- follow FAO/INFOODS density references; generic "other oil" is used for rice
-- bran and canola where the catalog does not identify a specific product.
UPDATE ingredients AS i
SET grams_per_unit = values.grams_per_unit,
    updated_at = NOW()
FROM (VALUES
    ('ING-0313', 1.0600::numeric),
    ('ING-0314', 1.0100::numeric),
    ('ING-0315', 0.9600::numeric),
    ('ING-0316', 1.0800::numeric),
    ('ING-0317', 1.0700::numeric),
    ('ING-0320', 0.9270::numeric),
    ('ING-0321', 0.9140::numeric),
    ('ING-0322', 0.9600::numeric),
    ('ING-0323', 0.9200::numeric),
    ('ING-0324', 0.9240::numeric),
    ('ING-0325', 0.9200::numeric)
) AS values(code, grams_per_unit)
WHERE i.code = values.code
  AND i.default_unit = 'ml'
  AND i.grams_per_unit = 1;

COMMIT;
