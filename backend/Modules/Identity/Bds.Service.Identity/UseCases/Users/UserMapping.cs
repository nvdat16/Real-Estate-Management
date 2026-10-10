using Bds.Domain.Identity.Entities;
using Bds.Model.Dto.Identity.Responses;

namespace Bds.Service.Identity.UseCases.Users;

public static class UserMapping
{
    public static UserResponse ToResponse(User user) => new(
        user.Id,
        user.Email,
        user.FullName,
        user.PhoneNumber,
        user.Role.Name,
        user.Role.RolePermissions.Select(rp => rp.Permission.Code).Order().ToList()
    );
}