using System.Data;
using Bds.Infrastructure.RealEstate.Interfaces;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

internal static class ProcedureCaller
{
    // Every realestate.sp_* procedure reports its outcome through the INOUT parameter p_result.
    public static async Task<int> CallAsync(
        IRealEstateConnectionFactory connectionFactory,
        string procedure,
        DynamicParameters parameters,
        CancellationToken cancellationToken)
    {
        parameters.Add("p_result", dbType: DbType.Int32, direction: ParameterDirection.InputOutput);

        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        await connection.ExecuteAsync(new CommandDefinition(
            procedure,
            parameters,
            commandType: CommandType.StoredProcedure,
            cancellationToken: cancellationToken));

        return parameters.Get<int>("p_result");
    }
}
