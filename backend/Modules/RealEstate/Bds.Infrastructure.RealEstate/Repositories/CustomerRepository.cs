using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class CustomerRepository(IRealEstateConnectionFactory connectionFactory) : ICustomerRepository
{
    public async Task<CustomerReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<CustomerReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_customer_get_by_id(@Id)",
            new { Id = id },
            cancellationToken: cancellationToken));
    }

    public async Task<CustomerReadModel?> GetByUserIdAsync(Guid userId, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<CustomerReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_customer_get_by_user_id(@UserId)",
            new { UserId = userId },
            cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<CustomerReadModel> Items, int TotalCount)> SearchAsync(
        ProfileFilter filter,
        CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = (await connection.QueryAsync<CustomerSearchRow>(new CommandDefinition(
            "SELECT * FROM realestate.fn_customer_search(@Keyword, @SortBy, @Descending, @Limit, @Offset)",
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

    public async Task<ProfileWriteResult> UpsertAsync(Customer customer, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = customer.Id,
            p_user_id = customer.UserId,
            p_full_name = customer.FullName,
            p_email = customer.Email,
            p_phone_number = customer.PhoneNumber,
            p_date_of_birth = customer.DateOfBirth,
            p_address = customer.Address,
        });

        return (ProfileWriteResult)await ProcedureCaller.CallAsync(
            connectionFactory, "realestate.sp_customer_upsert", parameters, cancellationToken);
    }

    private sealed class CustomerSearchRow : CustomerReadModel
    {
        public long TotalCount { get; init; }
    }
}
