using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Customers.Commands;
using Bds.Service.RealEstate.UseCases.Customers.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface ICustomerService
{
    Task<CustomerResponse> UpsertProfileAsync(UpsertCustomerProfileCommand command, CancellationToken cancellationToken);

    Task<CustomerResponse> GetMyProfileAsync(GetMyCustomerProfileQuery query, CancellationToken cancellationToken);

    Task<CustomerResponse> GetByIdAsync(GetCustomerByIdQuery query, CancellationToken cancellationToken);

    Task<PagedResult<CustomerResponse>> SearchAsync(SearchCustomersQuery query, CancellationToken cancellationToken);
}
