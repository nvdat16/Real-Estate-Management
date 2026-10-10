using Bds.Model.Dto.Identity.Responses;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Commands;

public sealed record RegisterCommand(
    string Email,
    string Password,
    string FullName,
    string? PhoneNumber
) : IRequest<UserResponse>;