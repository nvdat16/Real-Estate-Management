using Bds.Model.Dto.Identity.Responses;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Commands;

public sealed record LoginCommand(
    string Email,
    string Password
) : IRequest<AuthResponse>;