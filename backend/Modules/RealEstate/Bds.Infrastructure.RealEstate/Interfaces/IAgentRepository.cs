using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IAgentRepository
{
    Task<AgentReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<AgentReadModel?> GetByUserIdAsync(Guid userId, CancellationToken cancellationToken);

    Task<(IReadOnlyList<AgentReadModel> Items, int TotalCount)> SearchAsync(ProfileFilter filter, CancellationToken cancellationToken);

    Task<ProfileWriteResult> UpsertAsync(Agent agent, CancellationToken cancellationToken);
}
