using System.Data.Common;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IRealEstateConnectionFactory
{
    Task<DbConnection> OpenAsync(CancellationToken cancellationToken);
}
