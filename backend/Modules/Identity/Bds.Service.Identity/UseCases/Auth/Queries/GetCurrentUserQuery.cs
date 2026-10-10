using Bds.Model.Dto.Identity.Responses;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Queries;

public sealed record GetCurrentUserQuery(Guid UserId) : IRequest<UserResponse>;