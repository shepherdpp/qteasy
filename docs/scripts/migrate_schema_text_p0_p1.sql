-- =============================================================================
-- qteasy built-in tables: varchar -> TEXT (P0 + P1 schema alignment)
--
-- Run against your qteasy MySQL database AFTER upgrading datatables.py.
-- Safe to re-run: MODIFY to TEXT is idempotent if already TEXT.
--
-- Tables touched:
--   future_basic   (P0)
--   index_basic    (P1)
--   stock_basic    (P1)
--   hk_stock_basic (P1)
--   us_stock_basic (P1)
--   stock_company  (P1)
--
-- Notes:
-- - Backup the database before running in production.
-- - File-based data sources (csv/hdf/fth) are unaffected; only MySQL needs this.
-- - If a table does not exist yet, skip its ALTER or ignore "table doesn't exist".
-- =============================================================================

-- P0: future_basic
ALTER TABLE `future_basic`
    MODIFY COLUMN `quote_unit` TEXT NULL COMMENT '报价单位',
    MODIFY COLUMN `quote_unit_desc` TEXT NULL COMMENT '最小报价单位说明',
    MODIFY COLUMN `d_mode_desc` TEXT NULL COMMENT '交割方式说明',
    MODIFY COLUMN `trade_time_desc` TEXT NULL COMMENT '交易时间说明';

-- P1: index_basic
ALTER TABLE `index_basic`
    MODIFY COLUMN `name` TEXT NULL COMMENT '简称',
    MODIFY COLUMN `fullname` TEXT NULL COMMENT '指数全称';

-- P1: stock_basic
ALTER TABLE `stock_basic`
    MODIFY COLUMN `fullname` TEXT NULL COMMENT '股票全称',
    MODIFY COLUMN `enname` TEXT NULL COMMENT '英文全称';

-- P1: hk_stock_basic
ALTER TABLE `hk_stock_basic`
    MODIFY COLUMN `enname` TEXT NULL COMMENT '英文名称';

-- P1: us_stock_basic
ALTER TABLE `us_stock_basic`
    MODIFY COLUMN `enname` TEXT NULL COMMENT '英文名称';

-- P1: stock_company
ALTER TABLE `stock_company`
    MODIFY COLUMN `website` TEXT NULL COMMENT '公司主页';
