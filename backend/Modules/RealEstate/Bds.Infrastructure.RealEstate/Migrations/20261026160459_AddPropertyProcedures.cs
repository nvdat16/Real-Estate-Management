using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bds.Infrastructure.RealEstate.Migrations
{
    /// <inheritdoc />
    public partial class AddPropertyProcedures : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                -- "position" is quoted because POSITION is a keyword that cannot name an output column unquoted.
                CREATE OR REPLACE FUNCTION realestate.fn_property_get_by_id(p_id uuid)
                RETURNS TABLE (
                    id uuid, project_id uuid, project_code varchar, project_name varchar,
                    code varchar, area numeric, floor integer, "position" varchar, bedrooms integer,
                    direction varchar, status varchar, created_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT pp.id, pp.project_id, p.code, p.name,
                           pp.code, pp.area, pp.floor, pp.position, pp.bedrooms,
                           pp.direction, pp.status, pp.created_at
                    FROM realestate.properties pp
                    JOIN realestate.projects p ON p.id = pp.project_id
                    WHERE pp.id = p_id AND NOT pp.is_deleted;
                $$;

                -- Sorting uses CASE on a fixed set of keys, so no dynamic SQL is built from client input.
                CREATE OR REPLACE FUNCTION realestate.fn_property_search(
                    p_keyword varchar, p_project_id uuid, p_status varchar, p_direction varchar,
                    p_min_area numeric, p_max_area numeric, p_bedrooms integer,
                    p_sort_by varchar, p_descending boolean, p_limit integer, p_offset integer)
                RETURNS TABLE (
                    id uuid, project_id uuid, project_code varchar, project_name varchar,
                    code varchar, area numeric, floor integer, "position" varchar, bedrooms integer,
                    direction varchar, status varchar, created_at timestamptz,
                    total_count bigint)
                LANGUAGE sql STABLE
                AS $$
                    SELECT pp.id, pp.project_id, p.code, p.name,
                           pp.code, pp.area, pp.floor, pp.position, pp.bedrooms,
                           pp.direction, pp.status, pp.created_at,
                           count(*) OVER ()
                    FROM realestate.properties pp
                    JOIN realestate.projects p ON p.id = pp.project_id
                    WHERE NOT pp.is_deleted
                      AND (p_keyword IS NULL OR pp.code ILIKE '%' || p_keyword || '%' OR pp.position ILIKE '%' || p_keyword || '%')
                      AND (p_project_id IS NULL OR pp.project_id = p_project_id)
                      AND (p_status IS NULL OR pp.status = p_status)
                      AND (p_direction IS NULL OR pp.direction = p_direction)
                      AND (p_min_area IS NULL OR pp.area >= p_min_area)
                      AND (p_max_area IS NULL OR pp.area <= p_max_area)
                      AND (p_bedrooms IS NULL OR pp.bedrooms = p_bedrooms)
                    ORDER BY
                        CASE WHEN lower(p_sort_by) = 'code' AND NOT p_descending THEN pp.code END ASC,
                        CASE WHEN lower(p_sort_by) = 'code' AND p_descending THEN pp.code END DESC,
                        CASE WHEN lower(p_sort_by) = 'area' AND NOT p_descending THEN pp.area END ASC,
                        CASE WHEN lower(p_sort_by) = 'area' AND p_descending THEN pp.area END DESC,
                        CASE WHEN lower(p_sort_by) = 'floor' AND NOT p_descending THEN pp.floor END ASC,
                        CASE WHEN lower(p_sort_by) = 'floor' AND p_descending THEN pp.floor END DESC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('code', 'area', 'floor') AND NOT p_descending THEN pp.created_at END ASC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('code', 'area', 'floor') AND p_descending THEN pp.created_at END DESC,
                        pp.id
                    LIMIT p_limit OFFSET p_offset;
                $$;

                -- p_result: 0 success, 2 code exists, 3 project inactive, 4 project not found.
                -- FOR SHARE on the project blocks a concurrent sp_project_delete/update until this insert commits.
                CREATE OR REPLACE PROCEDURE realestate.sp_property_create(
                    p_id uuid, p_project_id uuid, p_code varchar, p_area numeric, p_floor integer,
                    p_position varchar, p_bedrooms integer, p_direction varchar,
                    INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_project_status varchar;
                BEGIN
                    SELECT status INTO v_project_status
                    FROM realestate.projects
                    WHERE id = p_project_id AND NOT is_deleted
                    FOR SHARE;

                    IF NOT FOUND THEN
                        p_result := 4;
                        RETURN;
                    END IF;

                    IF v_project_status <> 'Active' THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    INSERT INTO realestate.properties (
                        id, project_id, code, area, floor, position, bedrooms, direction,
                        status, is_deleted, created_at)
                    VALUES (
                        p_id, p_project_id, p_code, p_area, p_floor, p_position, p_bedrooms, p_direction,
                        'Available', false, now());
                    p_result := 0;
                EXCEPTION
                    -- The filtered unique index ix_properties_project_id_code guards against concurrent inserts.
                    WHEN unique_violation THEN
                        p_result := 2;
                END;
                $$;

                -- p_result: 0 success, 1 not found.
                CREATE OR REPLACE PROCEDURE realestate.sp_property_update(
                    p_id uuid, p_area numeric, p_floor integer, p_position varchar, p_bedrooms integer,
                    p_direction varchar, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    UPDATE realestate.properties
                    SET area = p_area,
                        floor = p_floor,
                        position = p_position,
                        bedrooms = p_bedrooms,
                        direction = p_direction,
                        updated_at = now()
                    WHERE id = p_id AND NOT is_deleted;

                    p_result := CASE WHEN FOUND THEN 0 ELSE 1 END;
                END;
                $$;

                -- p_result: 0 success, 1 not found, 5 not available (reserved, sold or rented).
                -- The active listing check is added together with the listings table.
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

                -- BR-01: a project that still has properties cannot be deleted.
                -- p_result: 0 success, 1 not found, 4 has properties.
                CREATE OR REPLACE PROCEDURE realestate.sp_project_delete(
                    p_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    PERFORM 1 FROM realestate.projects WHERE id = p_id AND NOT is_deleted FOR UPDATE;
                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM realestate.properties
                        WHERE project_id = p_id AND NOT is_deleted) THEN
                        p_result := 4;
                        RETURN;
                    END IF;

                    UPDATE realestate.projects
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
                DROP PROCEDURE IF EXISTS realestate.sp_property_delete(uuid, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_property_update(uuid, numeric, integer, varchar, integer, varchar, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_property_create(uuid, uuid, varchar, numeric, integer, varchar, integer, varchar, integer);
                DROP FUNCTION IF EXISTS realestate.fn_property_search(varchar, uuid, varchar, varchar, numeric, numeric, integer, varchar, boolean, integer, integer);
                DROP FUNCTION IF EXISTS realestate.fn_property_get_by_id(uuid);

                -- Restore sp_project_delete from AddRealEstateProcedures.
                CREATE OR REPLACE PROCEDURE realestate.sp_project_delete(
                    p_id uuid, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    UPDATE realestate.projects
                    SET is_deleted = true, deleted_at = now(), updated_at = now()
                    WHERE id = p_id AND NOT is_deleted;

                    p_result := CASE WHEN FOUND THEN 0 ELSE 1 END;
                END;
                $$;
                """);
        }
    }
}
