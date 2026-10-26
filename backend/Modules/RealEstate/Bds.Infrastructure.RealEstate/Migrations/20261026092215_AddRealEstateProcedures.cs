using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bds.Infrastructure.RealEstate.Migrations
{
    /// <inheritdoc />
    public partial class AddRealEstateProcedures : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                CREATE OR REPLACE FUNCTION realestate.fn_location_get_provinces()
                RETURNS TABLE (id uuid, code varchar, name varchar)
                LANGUAGE sql STABLE
                AS $$
                    SELECT p.id, p.code, p.name
                    FROM realestate.provinces p
                    ORDER BY p.name;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_location_get_districts(p_province_id uuid)
                RETURNS TABLE (id uuid, province_id uuid, code varchar, name varchar)
                LANGUAGE sql STABLE
                AS $$
                    SELECT d.id, d.province_id, d.code, d.name
                    FROM realestate.districts d
                    WHERE d.province_id = p_province_id
                    ORDER BY d.name;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_project_get_by_id(p_id uuid)
                RETURNS TABLE (
                    id uuid, code varchar, name varchar,
                    province_id uuid, province_name varchar,
                    district_id uuid, district_name varchar,
                    address_line varchar, developer varchar, status varchar, created_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT p.id, p.code, p.name, p.province_id, pr.name, p.district_id, d.name,
                           p.address_line, p.developer, p.status, p.created_at
                    FROM realestate.projects p
                    JOIN realestate.provinces pr ON pr.id = p.province_id
                    JOIN realestate.districts d ON d.id = p.district_id
                    WHERE p.id = p_id AND NOT p.is_deleted;
                $$;

                -- Sorting uses CASE on a fixed set of keys, so no dynamic SQL is built from client input.
                CREATE OR REPLACE FUNCTION realestate.fn_project_search(
                    p_keyword varchar, p_province_id uuid, p_district_id uuid, p_status varchar,
                    p_sort_by varchar, p_descending boolean, p_limit integer, p_offset integer)
                RETURNS TABLE (
                    id uuid, code varchar, name varchar,
                    province_id uuid, province_name varchar,
                    district_id uuid, district_name varchar,
                    address_line varchar, developer varchar, status varchar, created_at timestamptz,
                    total_count bigint)
                LANGUAGE sql STABLE
                AS $$
                    SELECT p.id, p.code, p.name, p.province_id, pr.name, p.district_id, d.name,
                           p.address_line, p.developer, p.status, p.created_at,
                           count(*) OVER ()
                    FROM realestate.projects p
                    JOIN realestate.provinces pr ON pr.id = p.province_id
                    JOIN realestate.districts d ON d.id = p.district_id
                    WHERE NOT p.is_deleted
                      AND (p_keyword IS NULL OR p.name ILIKE '%' || p_keyword || '%' OR p.code ILIKE '%' || p_keyword || '%')
                      AND (p_province_id IS NULL OR p.province_id = p_province_id)
                      AND (p_district_id IS NULL OR p.district_id = p_district_id)
                      AND (p_status IS NULL OR p.status = p_status)
                    ORDER BY
                        CASE WHEN lower(p_sort_by) = 'code' AND NOT p_descending THEN p.code END ASC,
                        CASE WHEN lower(p_sort_by) = 'code' AND p_descending THEN p.code END DESC,
                        CASE WHEN lower(p_sort_by) = 'name' AND NOT p_descending THEN p.name END ASC,
                        CASE WHEN lower(p_sort_by) = 'name' AND p_descending THEN p.name END DESC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('code', 'name') AND NOT p_descending THEN p.created_at END ASC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') NOT IN ('code', 'name') AND p_descending THEN p.created_at END DESC,
                        p.id
                    LIMIT p_limit OFFSET p_offset;
                $$;

                -- p_result: 0 success, 2 code exists, 3 district not in province.
                CREATE OR REPLACE PROCEDURE realestate.sp_project_create(
                    p_id uuid, p_code varchar, p_name varchar, p_province_id uuid, p_district_id uuid,
                    p_address_line varchar, p_developer varchar, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM realestate.districts
                        WHERE id = p_district_id AND province_id = p_province_id) THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    INSERT INTO realestate.projects (
                        id, code, name, province_id, district_id, address_line, developer,
                        status, is_deleted, created_at)
                    VALUES (
                        p_id, p_code, p_name, p_province_id, p_district_id, p_address_line, p_developer,
                        'Active', false, now());
                    p_result := 0;
                EXCEPTION
                    -- The filtered unique index ix_projects_code guards against concurrent inserts.
                    WHEN unique_violation THEN
                        p_result := 2;
                END;
                $$;

                -- p_result: 0 success, 1 not found, 3 district not in province.
                CREATE OR REPLACE PROCEDURE realestate.sp_project_update(
                    p_id uuid, p_name varchar, p_province_id uuid, p_district_id uuid,
                    p_address_line varchar, p_developer varchar, p_status varchar,
                    INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    PERFORM 1 FROM realestate.projects WHERE id = p_id AND NOT is_deleted FOR UPDATE;
                    IF NOT FOUND THEN
                        p_result := 1;
                        RETURN;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM realestate.districts
                        WHERE id = p_district_id AND province_id = p_province_id) THEN
                        p_result := 3;
                        RETURN;
                    END IF;

                    UPDATE realestate.projects
                    SET name = p_name,
                        province_id = p_province_id,
                        district_id = p_district_id,
                        address_line = p_address_line,
                        developer = p_developer,
                        status = p_status,
                        updated_at = now()
                    WHERE id = p_id;
                    p_result := 0;
                END;
                $$;

                -- p_result: 0 success, 1 not found. Soft delete keeps the row for auditing.
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

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                DROP PROCEDURE IF EXISTS realestate.sp_project_delete(uuid, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_project_update(uuid, varchar, uuid, uuid, varchar, varchar, varchar, integer);
                DROP PROCEDURE IF EXISTS realestate.sp_project_create(uuid, varchar, varchar, uuid, uuid, varchar, varchar, integer);
                DROP FUNCTION IF EXISTS realestate.fn_project_search(varchar, uuid, uuid, varchar, varchar, boolean, integer, integer);
                DROP FUNCTION IF EXISTS realestate.fn_project_get_by_id(uuid);
                DROP FUNCTION IF EXISTS realestate.fn_location_get_districts(uuid);
                DROP FUNCTION IF EXISTS realestate.fn_location_get_provinces();
                """);
        }
    }
}
