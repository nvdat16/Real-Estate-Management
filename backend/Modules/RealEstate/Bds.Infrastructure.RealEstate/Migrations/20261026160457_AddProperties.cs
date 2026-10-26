using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bds.Infrastructure.RealEstate.Migrations
{
    /// <inheritdoc />
    public partial class AddProperties : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "properties",
                schema: "realestate",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    project_id = table.Column<Guid>(type: "uuid", nullable: false),
                    code = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    area = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    floor = table.Column<int>(type: "integer", nullable: false),
                    position = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    bedrooms = table.Column<int>(type: "integer", nullable: false),
                    direction = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    is_deleted = table.Column<bool>(type: "boolean", nullable: false),
                    deleted_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_properties", x => x.id);
                    table.CheckConstraint("ck_properties_area_positive", "area > 0");
                    table.CheckConstraint("ck_properties_bedrooms_non_negative", "bedrooms >= 0");
                    table.ForeignKey(
                        name: "fk_properties_projects_project_id",
                        column: x => x.project_id,
                        principalSchema: "realestate",
                        principalTable: "projects",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "ix_properties_project_id_code",
                schema: "realestate",
                table: "properties",
                columns: new[] { "project_id", "code" },
                unique: true,
                filter: "is_deleted = false");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "properties",
                schema: "realestate");
        }
    }
}
