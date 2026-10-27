using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Commands;

public sealed record UpsertAgentProfileCommand(
    Guid UserId,
    string Email,
    string FullName,
    string PhoneNumber,
    string? LicenseNumber) : IRequest<AgentResponse>;
