using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bds.Infrastructure.RealEstate.Migrations
{
    /// <inheritdoc />
    public partial class AddListingProcedures : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                -- p_result codes shared by every sp_listing_* procedure:
                -- 0 success, 1 not found, 2 not the owner, 3 invalid status, 4 agent profile required,
                -- 5 property not found, 6 property not available, 7 property already has an active listing.

                CREATE OR REPLACE FUNCTION realestate.fn_listing_get_by_id(p_id uuid)
                RETURNS TABLE (
                    id uuid, type varchar, price numeric, title varchar, description varchar, image_urls text[],
                    status varchar, rejection_reason varchar, reviewed_at timestamptz, submitted_at timestamptz,
                    created_at timestamptz, updated_at timestamptz, is_public boolean,
                    property_id uuid, property_code varchar, area numeric, floor integer, bedrooms integer, direction varchar,
                    project_id uuid, project_name varchar, province_name varchar, district_name varchar,
                    agent_id uuid, agent_user_id uuid, agent_name varchar, agent_phone_number varchar)
                LANGUAGE sql STABLE
                AS $$
                    SELECT l.id, l.type, l.price, l.title, l.description, l.image_urls,
                           l.status, l.rejection_reason, l.reviewed_at, l.submitted_at,
                           l.created_at, l.updated_at,
                           (l.status = 'Approved' AND pp.status = 'Available' AND NOT pp.is_deleted),
                           pp.id, pp.code, pp.area, pp.floor, pp.bedrooms, pp.direction,
                           p.id, p.name, pr.name, d.name,
                           a.id, a.user_id, a.full_name, a.phone_number
                    FROM realestate.listings l
                    JOIN realestate.properties pp ON pp.id = l.property_id
                    JOIN realestate.projects p ON p.id = pp.project_id
                    JOIN realestate.provinces pr ON pr.id = p.province_id
                    JOIN realestate.districts d ON d.id = p.district_id
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted;
                $$;

                -- Sorting uses CASE on a fixed set of keys, so no dynamic SQL is built from client input.
                CREATE OR REPLACE FUNCTION realestate.fn_listing_search(
                    p_public_only boolean, p_agent_user_id uuid, p_status varchar, p_keyword varchar, p_type varchar,
                    p_min_price numeric, p_max_price numeric, p_province_id uuid, p_district_id uuid, p_project_id uuid,
                    p_min_area numeric, p_max_area numeric, p_bedrooms integer,
                    p_sort_by varchar, p_descending boolean, p_limit integer, p_offset integer)
                RETURNS TABLE (
                    id uuid, type varchar, price numeric, title varchar, description varchar, image_urls text[],
                    status varchar, rejection_reason varchar, reviewed_at timestamptz, submitted_at timestamptz,
                    created_at timestamptz, updated_at timestamptz, is_public boolean,
                    property_id uuid, property_code varchar, area numeric, floor integer, bedrooms integer, direction varchar,
                    project_id uuid, project_name varchar, province_name varchar, district_name varchar,
                    agent_id uuid, agent_user_id uuid, agent_name varchar, agent_phone_number varchar,
                    total_count bigint)
                LANGUAGE sql STABLE
                AS $$
                    SELECT l.id, l.type, l.price, l.title, l.description, l.image_urls,
                           l.status, l.rejection_reason, l.reviewed_at, l.submitted_at,
                           l.created_at, l.updated_at,
                           (l.status = 'Approved' AND pp.status = 'Available' AND NOT pp.is_deleted),
                           pp.id, pp.code, pp.area, pp.floor, pp.bedrooms, pp.direction,
                           p.id, p.name, pr.name, d.name,
                           a.id, a.user_id, a.full_name, a.phone_number,
                           count(*) OVER ()
                    FROM realestate.listings l
                    JOIN realestate.properties pp ON pp.id = l.property_id
                    JOIN realestate.projects p ON p.id = pp.project_id
                    JOIN realestate.provinces pr ON pr.id = p.province_id
                    JOIN realestate.districts d ON d.id = p.district_id
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE NOT l.is_deleted
                      AND (NOT p_public_only OR (l.status = 'Approved' AND pp.status = 'Available' AND NOT pp.is_deleted))
                      AND (p_agent_user_id IS NULL OR a.user_id = p_agent_user_id)
                      AND (p_status IS NULL OR l.status = p_status)
                      AND (p_keyword IS NULL
                           OR l.title ILIKE '%' || p_keyword || '%'
                           OR pp.code ILIKE '%' || p_keyword || '%'
                           OR p.name ILIKE '%' || p_keyword || '%')
                      AND (p_type IS NULL OR l.type = p_type)
                      AND (p_min_price IS NULL OR l.price >= p_min_price)
                      AND (p_max_price IS NULL OR l.price <= p_max_price)
                      AND (p_province_id IS NULL OR p.province_id = p_province_id)
                      AND (p_district_id IS NULL OR p.district_id = p_district_id)
                      AND (p_project_id IS NULL OR p.id = p_project_id)
                      AND (p_min_area IS NULL OR pp.area >= p_min_area)
                      AND (p_max_area IS NULL OR pp.area <= p_max_area)
                      AND (p_bedrooms IS NULL OR pp.bedrooms = p_bedrooms)
                    ORDER BY
                        CASE WHEN lower(p_sort_by) = 'price' AND NOT p_descending THEN l.price END ASC,
                        CASE WHEN lower(p_sort_by) = 'price' AND p_descending THEN l.price END DESC,
                        CASE WHEN lower(p_sort_by) = 'area' AND NOT p_descending THEN pp.area END ASC,
                        CASE WHEN lower(p_sort_by) = 'area' AND p_descending THEN pp.area END DESC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('price', 'area') AND NOT p_descending THEN l.created_at END ASC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('price', 'area') AND p_descending THEN l.created_at END DESC,
                        l.id
                    LIMIT p_limit OFFSET p_offset;
                $$;

                CREATE OR REPLACE PROCEDURE realestate.sp_listing_create(
                    p_id uuid, p_user_id uuid, p_property_id uuid, p_type varchar, p_price numeric,
                    p_title varchar, p_description varchar, p_image_urls text[], INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_agent_id uuid;
                    v_property_id uuid := p_property_id;
                    v_property_status varchar;
                BEGIN
                    SELECT id INTO v_agent_id FROM realestate.agents WHERE user_id = p_user_id;
                    IF NOT FOUND THEN
                        p_result := 4;
                        RETURN;
                    END IF;

                    -- FOR SHARE blocks a concurrent sp_property_delete until this transaction ends.
                    SELECT status INTO v_property_status
                    FROM realestate.properties
                    WHERE id = v_property_id AND NOT is_deleted
                    FOR SHARE;

                    IF NOT FOUND THEN
                        p_result := 5;
                        RETURN;
                    END IF;

                    IF v_property_status <> 'Available' THEN
                        p_result := 6;
                        RETURN;
                    END IF;

                    INSERT INTO realestate.listings (
                        id, property_id, agent_id, type, price, title, description, image_urls,
                        status, is_deleted, created_at)
                    VALUES (
                        p_id, p_property_id, v_agent_id, p_type, p_price, p_title, p_description, p_image_urls,
                        'Draft', false, now());
                    p_result := 0;
                END;
                $$;

                -- Editing a rejected or approved listing sends it back to Draft, so it must be reviewed again (BR-04).
                CREATE OR REPLACE PROCEDURE realestate.sp_listing_update(
                    p_id uuid, p_user_id uuid, p_type varchar, p_price numeric,
                    p_title varchar, p_description varchar, p_image_urls text[], INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_owner_user_id <> p_user_id THEN
                        p_result := 2;
                        RETURN;
                    END IF;

                    IF v_status NOT IN ('Draft', 'Rejected', 'Approved') THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET type = p_type,
                        price = p_price,
                        title = p_title,
                        description = p_description,
                        image_urls = p_image_urls,
                        status = 'Draft',
                        updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                CREATE OR REPLACE PROCEDURE realestate.sp_listing_submit(
                    p_id uuid, p_user_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_owner_user_id <> p_user_id THEN
                        p_result := 2;
                        RETURN;
                    END IF;

                    IF v_status <> 'Draft' THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    -- FOR SHARE blocks a concurrent sp_property_delete until this transaction ends.
                    SELECT status INTO v_property_status
                    FROM realestate.properties
                    WHERE id = v_property_id AND NOT is_deleted
                    FOR SHARE;

                    IF NOT FOUND THEN
                        p_result := 5;
                        RETURN;
                    END IF;

                    IF v_property_status <> 'Available' THEN
                        p_result := 6;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET status = 'PendingReview',
                        submitted_at = now(),
                        rejection_reason = NULL,
                        reviewed_by = NULL,
                        reviewed_at = NULL,
                        updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                EXCEPTION
                    -- RULE-02 is enforced by the filtered unique index ix_listings_property_id_active.
                    WHEN unique_violation THEN
                        p_result := 7;
                END;
                $$;

                CREATE OR REPLACE PROCEDURE realestate.sp_listing_approve(
                    p_id uuid, p_reviewer_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_status <> 'PendingReview' THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    -- FOR SHARE blocks a concurrent sp_property_delete until this transaction ends.
                    SELECT status INTO v_property_status
                    FROM realestate.properties
                    WHERE id = v_property_id AND NOT is_deleted
                    FOR SHARE;

                    IF NOT FOUND THEN
                        p_result := 5;
                        RETURN;
                    END IF;

                    IF v_property_status <> 'Available' THEN
                        p_result := 6;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET status = 'Approved',
                        reviewed_by = p_reviewer_id,
                        reviewed_at = now(),
                        updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                CREATE OR REPLACE PROCEDURE realestate.sp_listing_reject(
                    p_id uuid, p_reviewer_id uuid, p_reason varchar, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_status <> 'PendingReview' THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET status = 'Rejected',
                        rejection_reason = p_reason,
                        reviewed_by = p_reviewer_id,
                        reviewed_at = now(),
                        updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                -- The owner closes their own listing; a reviewer (p_can_close_any) may close any listing.
                CREATE OR REPLACE PROCEDURE realestate.sp_listing_close(
                    p_id uuid, p_user_id uuid, p_can_close_any boolean, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF NOT p_can_close_any AND v_owner_user_id <> p_user_id THEN
                        p_result := 2;
                        RETURN;
                    END IF;

                    IF v_status <> 'Approved' THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET status = 'Closed', updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                -- Listings waiting for review or approved must be closed first, so they never vanish silently.
                CREATE OR REPLACE PROCEDURE realestate.sp_listing_delete(
                    p_id uuid, p_user_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_owner_user_id uuid;
                    v_status varchar;
                    v_property_id uuid;
                    v_property_status varchar;
                BEGIN
                    SELECT a.user_id, l.status, l.property_id
                    INTO v_owner_user_id, v_status, v_property_id
                    FROM realestate.listings l
                    JOIN realestate.agents a ON a.id = l.agent_id
                    WHERE l.id = p_id AND NOT l.is_deleted
                    FOR UPDATE OF l;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_owner_user_id <> p_user_id THEN
                        p_result := 2;
                        RETURN;
                    END IF;

                    IF v_status IN ('PendingReview', 'Approved') THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    UPDATE realestate.listings
                    SET is_deleted = true, deleted_at = now(), updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                -- BR-02: a property with a listing waiting for review or approved cannot be deleted.
                -- p_result: 0 success, 1 not found, 5 not available, 6 has an active listing.
                CREATE OR REPLACE PROCEDURE realestate.sp_property_delete(
                    p_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_status varchar;
                BEGIN
                    SELECT status INTO v_status
                    FROM realestate.properties
                    WHERE id = p_id AND NOT is_deleted
                    FOR UPDATE;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_status <> 'Available' THEN
                        p_result := 5;
                        RETURN;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM realestate.listings
                        WHERE property_id = p_id AND NOT is_deleted AND status IN ('PendingReview', 'Approved')) THEN
                        p_result := 6;
                        RETURN;
                    END IF;

                    UPDATE realestate.properties
                    SET is_deleted = true, deleted_at = now(), updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                DROP PROCEDURE IF EXISTS realestate.sp_listing_delete(uuid, uuid, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_close(uuid, uuid, boolean, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_reject(uuid, uuid, varchar, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_approve(uuid, uuid, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_submit(uuid, uuid, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_update(uuid, uuid, varchar, numeric, varchar, varchar, text[], integer);
                DROP PROCEDURE IF EXISTS realestate.sp_listing_create(uuid, uuid, uuid, varchar, numeric, varchar, varchar, text[], integer);
                DROP FUNCTION IF EXISTS realestate.fn_listing_search(boolean, uuid, varchar, varchar, varchar, numeric, numeric, uuid, uuid, uuid, numeric, numeric, integer, varchar, boolean, integer, integer);
                DROP FUNCTION IF EXISTS realestate.fn_listing_get_by_id(uuid);

                -- Restore sp_property_delete from AddPropertyProcedures.
                CREATE OR REPLACE PROCEDURE realestate.sp_property_delete(
                    p_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_status varchar;
                BEGIN
                    SELECT status INTO v_status
                    FROM realestate.properties
                    WHERE id = p_id AND NOT is_deleted
                    FOR UPDATE;

                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF v_status <> 'Available' THEN
                        p_result := 5;
                        RETURN;
                    END IF;

                    UPDATE realestate.properties
                    SET is_deleted = true, deleted_at = now(), updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;
                """);
        }
    }
}
