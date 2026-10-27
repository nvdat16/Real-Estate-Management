using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Customers.Queries.Handlers;

public sealed class SearchCustomersHandler(ICustomerService customerService)
    : IRequestHandler<SearchCustomersQuery, PagedResult<CustomerResponse>>
{
    public Task<PagedResult<CustomerResponse>> Handle(SearchCustomersQuery request, CancellationToken cancellationToken) =>
        customerService.SearchAsync(request, cancellationToken);
}
