using Bds.Model.Dto.Identity.Responses;
using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands;

public sealed record CreateUserCommand(
    string Email,
    string Password,
    string FullName,
    string? PhoneNumber,
    string Role
) : IRequest<UserResponse>;