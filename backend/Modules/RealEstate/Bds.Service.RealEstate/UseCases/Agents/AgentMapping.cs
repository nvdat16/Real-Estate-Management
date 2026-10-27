using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Agents;

public static class AgentMapping
{
    public static AgentResponse ToResponse(AgentReadModel agent) => new(
        agent.Id,
        agent.UserId,
        agent.FullName,
        agent.Email,
        agent.PhoneNumber,
        agent.LicenseNumber,
        agent.CreatedAt,
        agent.UpdatedAt);
}
