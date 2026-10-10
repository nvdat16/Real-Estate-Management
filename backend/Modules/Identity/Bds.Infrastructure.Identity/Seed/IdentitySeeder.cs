using Bds.BuildingBlocks.Application.Security;
using Bds.Domain.Identity.Constants;
using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.Identity.Seed;

public static class IdentitySeeder
{
    private static readonly (string Code, string Name, string Group)[] PermissionCatalog =
    [
        (Permissions.UsersManage, "Quản lý tài khoản", "Tài khoản"),
        (Permissions.ProjectsManage, "Quản lý dự án, căn hộ", "Dự án"),
        (Permissions.ListingsCreate, "Tạo và sửa tin đăng của mình", "Tin đăng"),
        (Permissions.ListingsApprove, "Duyệt tin đăng", "Tin đăng"),
        (Permissions.KycSubmit, "Gửi hồ sơ KYC", "KYC"),
        (Permissions.KycReview, "Xử lý hồ sơ KYC", "KYC"),
        (Permissions.ContractsCreate, "Lập hợp đồng", "Hợp đồng"),
        (Permissions.ContractsSign, "Ký hợp đồng", "Hợp đồng"),
        (Permissions.InvoicesManage, "Quản lý hóa đơn", "Hóa đơn"),
        (Permissions.CommissionsManage, "Duyệt và chi hoa hồng", "Hoa hồng"),
        (Permissions.CommissionsReadOwn, "Xem hoa hồng của mình", "Hoa hồng"),
        (Permissions.ReportsRead, "Xem báo cáo", "Báo cáo"),
        (Permissions.AuditLogsRead, "Xem nhật ký hệ thống", "Hệ thống"),
    ];

    private static readonly Dictionary<string, string[]> PermissionsByRole = new()
    {
        [RoleNames.Admin] = [.. PermissionCatalog.Select(p => p.Code)],
        [RoleNames.Agent] =
        [
            Permissions.ListingsCreate,
            Permissions.ContractsCreate,
            Permissions.CommissionsReadOwn,
            Permissions.ReportsRead,
        ],
        [RoleNames.Customer] =
        [
            Permissions.KycSubmit,
            Permissions.ContractsSign,
        ],
    };

    private static readonly Dictionary<string, string> RoleDescriptions = new()
    {
        [RoleNames.Admin] = "Quản trị hệ thống",
        [RoleNames.Agent] = "Môi giới",
        [RoleNames.Customer] = "Khách hàng",
    };

    public static async Task SeedAsync(
        IdentityContext context,
        IPasswordHasher passwordHasher,
        string adminEmail,
        string adminPassword,
        CancellationToken cancellationToken = default)
    {
        var permissions = await context.Permissions.ToDictionaryAsync(p => p.Code, cancellationToken);
        foreach (var (code, name, group) in PermissionCatalog.Where(p => !permissions.ContainsKey(p.Code)))
        {
            var permission = Permission.Create(code, name, group);
            context.Permissions.Add(permission);
            permissions[code] = permission;
        }

        var roles = await context.Roles
            .Include(r => r.RolePermissions)
            .ToDictionaryAsync(r => r.Name, cancellationToken);
        foreach (var (roleName, codes) in PermissionsByRole)
        {
            if (!roles.TryGetValue(roleName, out var role))
            {
                role = Role.Create(roleName, RoleDescriptions[roleName]);
                context.Roles.Add(role);
                roles[roleName] = role;
            }

            foreach (var code in codes)
            {
                role.GrantPermission(permissions[code]);
            }
        }

        var email = User.NormalizeEmail(adminEmail);
        if (!await context.Users.AnyAsync(u => u.Email == email, cancellationToken))
        {
            var admin = User.Create(email, passwordHasher.Hash(adminPassword), "Quản trị viên", null, roles[RoleNames.Admin]);
            context.Users.Add(admin);
        }

        await context.SaveChangesAsync(cancellationToken);
    }
}