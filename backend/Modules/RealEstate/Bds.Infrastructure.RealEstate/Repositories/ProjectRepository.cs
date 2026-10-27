using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class ProjectRepository(IRealEstateConnectionFactory connectionFactory) : IProjectRepository
{
    public async Task<ProjectReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<ProjectReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_project_get_by_id(@Id)",
            new { Id = id },
            cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<ProjectReadModel> Items, int TotalCount)> SearchAsync(
        ProjectFilter filter,
        CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = (await connection.QueryAsync<ProjectSearchRow>(new CommandDefinition(
            """
            SELECT * FROM realestate.fn_project_search(
                @Keyword, @ProvinceId, @DistrictId, @Status, @SortBy, @Descending, @Limit, @Offset)
            """,
            new
            {
                Keyword = string.IsNullOrWhiteSpace(filter.Keyword) ? null : filter.Keyword.Trim(),
                filter.ProvinceId,
                filter.DistrictId,
                Status = filter.Status?.ToString(),
                filter.Paging.SortBy,
                filter.Paging.Descending,
                Limit = filter.Paging.PageSize,
                filter.Paging.Offset,
            },
            cancellationToken: cancellationToken))).AsList();

        var totalCount = rows.Count == 0 ? 0 : (int)rows[0].TotalCount;
        return (rows, totalCount);
    }

    public Task<ProjectWriteResult> CreateAsync(Project project, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = project.Id,
            p_code = project.Code,
            p_name = project.Name,
            p_province_id = project.ProvinceId,
            p_district_id = project.DistrictId,
            p_address_line = project.AddressLine,
            p_developer = project.Developer,
        });

        return CallAsync("realestate.sp_project_create", parameters, cancellationToken);
    }

    public Task<ProjectWriteResult> UpdateAsync(
        Guid id,
        string name,
        Guid provinceId,
        Guid districtId,
        string addressLine,
        string developer,
        ProjectStatus status,
        CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = id,
            p_name = name,
            p_province_id = provinceId,
            p_district_id = districtId,
            p_address_line = addressLine,
            p_developer = developer,
            p_status = status.ToString(),
        });

        return CallAsync("realestate.sp_project_update", parameters, cancellationToken);
    }

    public Task<ProjectWriteResult> DeleteAsync(Guid id, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new { p_id = id });
        return CallAsync("realestate.sp_project_delete", parameters, cancellationToken);
    }

    private async Task<ProjectWriteResult> CallAsync(string procedure, DynamicParameters parameters, CancellationToken cancellationToken) =>
        (ProjectWriteResult)await ProcedureCaller.CallAsync(connectionFactory, procedure, parameters, cancellationToken);

    private sealed class ProjectSearchRow : ProjectReadModel
    {
        public long TotalCount { get; init; }
    }
}
