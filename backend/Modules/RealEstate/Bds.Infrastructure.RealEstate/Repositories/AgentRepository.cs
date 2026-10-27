using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class AgentRepository(IRealEstateConnectionFactory connectionFactory) : IAgentRepository
{
    public async Task<AgentReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<AgentReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_agent_get_by_id(@Id)",
            new { Id = id },
            cancellationToken: cancellationToken));
    }

    public async Task<AgentReadModel?> GetByUserIdAsync(Guid userId, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<AgentReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_agent_get_by_user_id(@UserId)",
            new { UserId = userId },
            cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<AgentReadModel> Items, int TotalCount)> SearchAsync(
        ProfileFilter filter,
        CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = (await connection.QueryAsync<AgentSearchRow>(new CommandDefinition(
            "SELECT * FROM realestate.fn_agent_search(@Keyword, @SortBy, @Descending, @Limit, @Offset)",
            new
            {
                Keyword = string.IsNullOrWhiteSpace(filter.Keyword) ? null : filter.Keyword.Trim(),
                filter.Paging.SortBy,
                filter.Paging.Descending,
                Limit = filter.Paging.PageSize,
                filter.Paging.Offset,
            },
            cancellationToken: cancellationToken))).AsList();

        var totalCount = rows.Count == 0 ? 0 : (int)rows[0].TotalCount;
        return (rows, totalCount);
    }

    public async Task<ProfileWriteResult> UpsertAsync(Agent agent, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = agent.Id,
            p_user_id = agent.UserId,
            p_full_name = agent.FullName,
            p_email = agent.Email,
            p_phone_number = agent.PhoneNumber,
            p_license_number = agent.LicenseNumber,
        });

        return (ProfileWriteResult)await ProcedureCaller.CallAsync(
            connectionFactory, "realestate.sp_agent_upsert", parameters, cancellationToken);
    }

    private sealed class AgentSearchRow : AgentReadModel
    {
        public long TotalCount { get; init; }
    }
}
